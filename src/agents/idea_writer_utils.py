'''
🌙 Moon Dev's Shared Idea Writer Utilities 🌙
Thread-safe utilities for writing trading ideas to RBI Agent input file

Features:
- Thread-safe file locking for concurrent agent writes
- Duplicate detection across all agents
- UTF-8 encoding for Windows compatibility
- Error handling and retry logic
- Cross-agent idea tracking

Created with ❤️ by Moon Dev
'''

import os
import time
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional, Set
from termcolor import cprint
import pandas as pd
import hashlib

# Try to import filelock, install if not available
try:
    from filelock import FileLock, Timeout
except ImportError:
    cprint("⚠️ Installing filelock library for thread-safe file access...", "yellow")
    import subprocess
    subprocess.check_call(["pip", "install", "filelock"])
    from filelock import FileLock, Timeout

# Define paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data" / "rbi_pp_multi"
IDEAS_TXT = DATA_DIR / "ideas.txt"
IDEAS_TXT_LOCK = DATA_DIR / "ideas.txt.lock"

# Agent-specific CSV logs
RESEARCH_AGENT_CSV = DATA_DIR / "strategy_ideas.csv"
POLYMARKET_AGENT_CSV = PROJECT_ROOT / "src" / "data" / "polymarket_trades" / "generated_ideas.csv"
WEBSEARCH_AGENT_CSV = PROJECT_ROOT / "src" / "data" / "web_search_research" / "generated_ideas.csv"

# Configuration
DEFAULT_LOCK_TIMEOUT = 5  # Seconds to wait for file lock
MAX_RETRIES = 3  # Number of retry attempts
SIMILARITY_THRESHOLD = 0.90  # 90% similarity = duplicate

# 🌙 IMPORTANT: Disable ideas.txt writing for research_agent
# Research agent generates raw ideas - should write to ideas.txt
# But WebSearch agent saves researched strategies to final_strategies/ folder
# RBI reads from final_strategies/ directly - no need to also write to ideas.txt
WRITE_TO_IDEAS_TXT = {
    'research_agent': True,  # Raw ideas → write to ideas.txt
    'websearch_agent': False,  # Already saves to final_strategies/
    'polymarket_agent': True  # Market-based ideas → write to ideas.txt
}


def setup_directories():
    """Ensure all required directories exist"""
    directories = [
        DATA_DIR,
        POLYMARKET_AGENT_CSV.parent,
        WEBSEARCH_AGENT_CSV.parent
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_idea_hash(idea: str) -> str:
    """Generate hash for idea text (for duplicate detection)"""
    # Normalize: lowercase, strip whitespace, remove punctuation
    normalized = ''.join(c.lower() for c in idea if c.isalnum() or c.isspace())
    normalized = ' '.join(normalized.split())  # Remove extra whitespace
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def load_existing_ideas() -> Set[str]:
    """
    Load all existing ideas from ideas.txt and CSV logs

    Returns:
        Set of idea hashes for duplicate detection
    """
    idea_hashes = set()

    # Load from ideas.txt
    if IDEAS_TXT.exists():
        try:
            with open(IDEAS_TXT, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        idea_hashes.add(get_idea_hash(line))
        except Exception as e:
            cprint(f"⚠️ Error loading ideas from ideas.txt: {e}", "yellow")

    # Load from CSV logs
    csv_files = [RESEARCH_AGENT_CSV, POLYMARKET_AGENT_CSV, WEBSEARCH_AGENT_CSV]
    for csv_file in csv_files:
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file)
                if 'idea' in df.columns:
                    for idea in df['idea']:
                        if pd.notna(idea):
                            idea_hashes.add(get_idea_hash(str(idea)))
            except Exception as e:
                cprint(f"⚠️ Error loading ideas from {csv_file.name}: {e}", "yellow")

    return idea_hashes


def is_duplicate_idea(idea: str, existing_hashes: Optional[Set[str]] = None) -> bool:
    """
    Check if idea is a duplicate

    Args:
        idea: Strategy idea text
        existing_hashes: Pre-loaded set of idea hashes (optional, will load if not provided)

    Returns:
        True if duplicate, False if unique
    """
    if existing_hashes is None:
        existing_hashes = load_existing_ideas()

    idea_hash = get_idea_hash(idea)
    return idea_hash in existing_hashes


def clean_idea_text(idea: str) -> str:
    """
    Standardize idea formatting for RBI compatibility

    Args:
        idea: Raw idea text

    Returns:
        Cleaned idea text
    """
    # Remove extra whitespace
    idea = ' '.join(idea.split())

    # Ensure first letter is capitalized
    if idea and not idea[0].isupper():
        idea = idea[0].upper() + idea[1:]

    # Ensure it ends with period
    if idea and not idea[-1] in '.!?':
        idea += '.'

    # Limit length (RBI works best with 1-3 sentences)
    if len(idea) > 500:
        idea = idea[:497] + '...'

    return idea


def log_to_agent_csv(idea: str, source: str, metadata: Optional[dict] = None):
    """
    Log idea to agent-specific CSV file

    Args:
        idea: Strategy idea text
        source: Agent name (research_agent, polymarket_agent, websearch_agent)
        metadata: Optional metadata dict (model, confidence, etc.)
    """
    # Determine CSV file based on source
    csv_mapping = {
        'research_agent': RESEARCH_AGENT_CSV,
        'polymarket_agent': POLYMARKET_AGENT_CSV,
        'websearch_agent': WEBSEARCH_AGENT_CSV
    }

    csv_file = csv_mapping.get(source)
    if not csv_file:
        cprint(f"⚠️ Unknown source: {source}", "yellow")
        return

    # Ensure directory exists
    csv_file.parent.mkdir(parents=True, exist_ok=True)

    # Prepare row data
    row = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': source,
        'idea': idea
    }

    # Add metadata if provided
    if metadata:
        row.update(metadata)

    # Write to CSV
    try:
        file_exists = csv_file.exists()
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            if not file_exists:
                # Create header row with all keys
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writeheader()
            else:
                # Use existing headers + any new ones
                existing_df = pd.read_csv(csv_file)
                all_keys = list(set(list(existing_df.columns) + list(row.keys())))
                writer = csv.DictWriter(f, fieldnames=all_keys)

            writer.writerow(row)
    except Exception as e:
        cprint(f"⚠️ Error writing to CSV {csv_file.name}: {e}", "yellow")


def write_idea_to_file(
    idea: str,
    source: str,
    lock_timeout: int = DEFAULT_LOCK_TIMEOUT,
    metadata: Optional[dict] = None
) -> bool:
    """
    Thread-safe write to ideas.txt with duplicate detection

    Args:
        idea: Strategy idea text (1-3 sentences recommended)
        source: Agent name (research_agent, polymarket_agent, websearch_agent)
        lock_timeout: Max seconds to wait for file lock
        metadata: Optional metadata dict to log to CSV

    Returns:
        True if idea was added successfully, False if duplicate or error
    """
    # Setup directories
    setup_directories()

    # Clean the idea text
    idea = clean_idea_text(idea)

    # Check if this agent should write to ideas.txt
    should_write_to_ideas = WRITE_TO_IDEAS_TXT.get(source, True)  # Default to True for unknown sources

    if not should_write_to_ideas:
        # Agent disabled for ideas.txt - only log to CSV
        cprint(f"📝 [{source}] Skipping ideas.txt (agent saves to folder directly)", "yellow")
        log_to_agent_csv(idea, source, metadata)
        return True  # Return success since CSV log succeeded

    # Check for duplicates (before acquiring lock)
    existing_hashes = load_existing_ideas()
    if is_duplicate_idea(idea, existing_hashes):
        cprint(f"♻️ Duplicate idea detected (skipping): {idea[:60]}...", "cyan")
        return False

    # Retry logic
    for attempt in range(MAX_RETRIES):
        try:
            # Acquire file lock
            lock = FileLock(IDEAS_TXT_LOCK, timeout=lock_timeout)

            with lock:
                # Double-check for duplicates after acquiring lock
                # (another agent might have added it while we were waiting)
                existing_hashes = load_existing_ideas()
                if is_duplicate_idea(idea, existing_hashes):
                    cprint(f"♻️ Duplicate idea detected after lock (skipping): {idea[:60]}...", "cyan")
                    return False

                # Ensure ideas.txt exists
                if not IDEAS_TXT.exists():
                    with open(IDEAS_TXT, 'w', encoding='utf-8') as f:
                        f.write("# Moon Dev's Trading Strategy Ideas 🌙\n")
                        f.write("# Auto-generated by AI Agents - DO NOT EDIT MANUALLY\n")
                        f.write("# One idea per line\n\n")

                # Append idea to ideas.txt
                with open(IDEAS_TXT, 'a', encoding='utf-8') as f:
                    f.write(f"{idea}\n")

                # Log success
                cprint(f"✅ [{source}] Idea added: {idea[:70]}...", "green")

                # Log to agent-specific CSV (outside lock)
                log_to_agent_csv(idea, source, metadata)

                return True

        except Timeout:
            if attempt < MAX_RETRIES - 1:
                cprint(f"⏳ File lock timeout, retrying... (attempt {attempt + 1}/{MAX_RETRIES})", "yellow")
                time.sleep(1)  # Wait before retry
            else:
                cprint(f"❌ Failed to acquire file lock after {MAX_RETRIES} attempts", "red")
                # Fallback: Log to CSV only
                log_to_agent_csv(idea, source, metadata)
                return False

        except Exception as e:
            cprint(f"❌ Error writing idea: {e}", "red")
            # Fallback: Log to CSV only
            log_to_agent_csv(idea, source, metadata)
            return False

    return False


def get_idea_stats() -> dict:
    """
    Get statistics about ideas from all sources

    Returns:
        Dict with counts per source and total
    """
    stats = {
        'total': 0,
        'research_agent': 0,
        'polymarket_agent': 0,
        'websearch_agent': 0,
        'in_ideas_txt': 0
    }

    # Count from ideas.txt
    if IDEAS_TXT.exists():
        try:
            with open(IDEAS_TXT, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.strip().startswith('#'):
                        stats['in_ideas_txt'] += 1
        except Exception:
            pass

    # Count from CSV files
    csv_mapping = {
        'research_agent': RESEARCH_AGENT_CSV,
        'polymarket_agent': POLYMARKET_AGENT_CSV,
        'websearch_agent': WEBSEARCH_AGENT_CSV
    }

    for source, csv_file in csv_mapping.items():
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file)
                stats[source] = len(df)
            except Exception:
                pass

    stats['total'] = sum(stats[k] for k in ['research_agent', 'polymarket_agent', 'websearch_agent'])

    return stats


def print_idea_stats():
    """Print idea generation statistics"""
    stats = get_idea_stats()

    print("\n" + "=" * 60)
    cprint(" 📊 IDEA GENERATION STATISTICS ", "white", "on_blue")
    print("=" * 60)

    cprint(f"  Research Agent:   {stats['research_agent']:,} ideas", "cyan")
    cprint(f"  Polymarket Agent: {stats['polymarket_agent']:,} ideas", "magenta")
    cprint(f"  WebSearch Agent:  {stats['websearch_agent']:,} ideas", "yellow")
    print("  " + "-" * 56)
    cprint(f"  Total Generated:  {stats['total']:,} ideas", "white", "on_green")
    cprint(f"  In ideas.txt:     {stats['in_ideas_txt']:,} ideas (pending RBI)", "white", "on_magenta")
    print("=" * 60 + "\n")


# Convenience function for testing
if __name__ == "__main__":
    import sys

    # Set UTF-8 encoding for Windows
    if os.name == 'nt':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("\n🌙 Moon Dev's Idea Writer Utilities Test 🌙\n")

    # Test 1: Write a test idea
    test_idea = "RSI divergence combined with volume spike detection for mean-reversion entries with ATR-based stops."
    cprint("📝 Test 1: Writing test idea...", "yellow")
    success = write_idea_to_file(test_idea, "research_agent", metadata={'model': 'test'})
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")

    # Test 2: Try duplicate
    cprint("\n📝 Test 2: Testing duplicate detection...", "yellow")
    success = write_idea_to_file(test_idea, "research_agent", metadata={'model': 'test'})
    print(f"   Result: {'♻️ Correctly rejected duplicate' if not success else '⚠️ Failed to detect duplicate'}")

    # Test 3: Load existing ideas
    cprint("\n📝 Test 3: Loading existing ideas...", "yellow")
    hashes = load_existing_ideas()
    print(f"   Found {len(hashes):,} unique idea hashes")

    # Test 4: Statistics
    cprint("\n📝 Test 4: Idea statistics...", "yellow")
    print_idea_stats()

    cprint("\n✅ All tests completed!", "green")
