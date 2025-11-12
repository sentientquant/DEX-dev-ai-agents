# -*- coding: utf-8 -*-
"""
🌙 Moon Dev's RBI AI v3.0 PARALLEL PROCESSOR + MULTI-DATA TESTING 🚀
Built with love by Moon Dev 🚀

PARALLEL PROCESSING + MULTI-DATA VALIDATION: Run up to 5 backtests simultaneously,
each tested on 25+ different data sources!

- Each thread processes a different trading idea
- Thread-safe colored output
- Rate limiting to avoid API throttling
- Massively faster than sequential processing
- 🆕 AUTOMATIC MULTI-DATA TESTING on crypto data sources (BTC, ETH, SOL - multiple timeframes)

HOW IT WORKS:
1. Reads trading ideas from ideas.txt
2. Spawns up to MAX_PARALLEL_THREADS workers
3. Each thread independently: Research → Backtest → Debug → Optimize
4. 🆕 Each successful backtest automatically tests on multiple crypto data sources (BTC, ETH, SOL)!
5. All threads run simultaneously until target returns are hit
6. Thread-safe file naming with unique 2-digit thread IDs
7. 🆕 Multi-data results saved to ./results/ folders for each strategy

NEW FEATURES:
- 🎨 Color-coded output per thread (Thread 1 = cyan, Thread 2 = magenta, etc.)
- ⏱️ Rate limiting to avoid API throttling
- 🔒 Thread-safe file operations
- 📊 Real-time progress tracking across all threads
- 💾 Clean file organization with thread IDs in names
- 🆕 📈 MULTI-DATA TESTING: Validates strategies on crypto assets (BTC, ETH, SOL) across multiple timeframes!
- 🆕 📊 CSV results showing performance across all crypto data sources

Required Setup:
1. Conda environment 'tflow' with backtesting packages
2. Set MAX_PARALLEL_THREADS (default: 5)
3. Multi-data tester at: /Users/md/Dropbox/dev/github/moon-dev-trading-bots/backtests/multi_data_tester.py
4. Run and watch all ideas process in parallel with multi-data validation! 🚀💰

IMPORTANT: Each thread is fully independent and won't interfere with others!
"""

# Import execution functionality
import subprocess
import json
import gc  # Memory management to prevent WinError 1455
from pathlib import Path

# Core imports
import os

# Set UTF-8 encoding for Windows terminal (fixes emoji display issues)
if os.name == 'nt':  # Windows
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import time
import re
import hashlib
import csv
import random
import pandas as pd
from datetime import datetime
from termcolor import cprint
import sys
import argparse  # 🌙 Moon Dev: For command-line args
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Semaphore, Thread
from queue import Queue
import requests
from io import BytesIO

# Load environment variables FIRST
load_dotenv()
# Use ASCII-safe output for Windows compatibility
print("[OK] Environment variables loaded")

# Add config values directly to avoid import issues
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 4096  # GPT-4 Turbo max limit (reduced from 16000)

# Import model factory with proper path handling
import sys
# Add project root to path (works on both Windows and Unix)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.models import model_factory
    print("[OK] Successfully imported model_factory")
except ImportError as e:
    print(f"[ERROR] Could not import model_factory: {e}")
    sys.exit(1)

# ============================================
# 🎯 PARALLEL PROCESSING CONFIGURATION
# ============================================
MAX_PARALLEL_THREADS = 9  # Optimized for xAI Direct API: All 9 threads use grok-4-fast-reasoning
RATE_LIMIT_DELAY = 1.0  # Increased to 1s to help with rate limits
RATE_LIMIT_GLOBAL_DELAY = 0.5  # Global delay between any API calls

# ============================================
# 📁 STRATEGY SOURCE CONFIGURATION - Moon Dev
# ============================================
# IMPORTANT: Choose where to read trading strategies from
#
# Option 1 (Default): STRATEGIES_FROM_FILES = False
#   - Reads from ideas.txt (one strategy per line)
#   - Classic behavior - works exactly as before
#
# Option 2: STRATEGIES_FROM_FILES = True
#   - Reads all .md and .txt files from STRATEGIES_FOLDER
#   - Each FILE = one complete strategy idea
#   - Perfect for auto-generated strategies from web search agent!
#
STRATEGIES_FROM_FILES = True  # Use pre-researched strategies from run_idea_generators.py
STRATEGIES_FOLDER = os.path.join(project_root, "src", "data", "web_search_research", "final_strategies")

# Thread color mapping (9 threads with distinct colors)
THREAD_COLORS = {
    0: "cyan",      # xAI Grok 4
    1: "magenta",   # xAI Grok 4
    2: "yellow",    # xAI Grok 4
    3: "green",     # xAI Grok 4
    4: "blue",      # xAI Grok 4
    5: "red",       # xAI Grok 4
    6: "cyan",      # xAI Grok 4
    7: "magenta",   # xAI Grok 4
    8: "yellow"     # xAI Grok 4
}

# Global locks
console_lock = Lock()
api_lock = Lock()
file_lock = Lock()
date_lock = Lock()  # 🌙 Moon Dev: Lock for date checking/updating

# Rate limiter
rate_limiter = Semaphore(MAX_PARALLEL_THREADS)

# 🌙 Moon Dev's Model Configurations
# Available types: "claude", "openai", "deepseek", "groq", "gemini", "xai", "ollama", "openrouter"
#
# OpenRouter Models (just set type="openrouter" and pick any model below):
# - Gemini: google/gemini-2.5-pro, google/gemini-2.5-flash
# - Qwen: qwen/qwen3-vl-32b-instruct, qwen/qwen3-max
# - DeepSeek: deepseek/deepseek-r1-0528
# - OpenAI: openai/gpt-4.5-preview, openai/gpt-5, openai/gpt-5-mini, openai/gpt-5-nano
# - Claude: anthropic/claude-sonnet-4.5, anthropic/claude-haiku-4.5, anthropic/claude-opus-4.1
# - GLM: z-ai/glm-4.6
# See src/models/openrouter_model.py for ALL available models!
#
# OpenAI Direct Models:
# - gpt-4-turbo, gpt-4, gpt-4-32k, gpt-3.5-turbo, gpt-3.5-turbo-16k
# - o1-preview, o1-mini (reasoning models)

# 🌙 DIRECT API CONFIG: Anthropic Claude + OpenAI GPT
# Uses your existing API keys - no OpenRouter credits needed!

# 🧠 RESEARCH: xAI Grok DIRECT API for strategy generation
# Using direct xAI API (not OpenRouter) for full control and better rate limits
RESEARCH_CONFIG = {
    "type": "xai",
    "name": "grok-4-fast-reasoning"  # xAI Grok 4 Fast with reasoning (2M context, optimized for code)
}

# 🎰 MULTI-MODEL CONFIGURATION FOR LOAD BALANCING
# Each thread will rotate through different models to avoid rate limits

# Model pool for BACKTEST generation (9 models - ALL XAI DIRECT)
# Pattern: xAI Grok 4 Fast Reasoning for all threads - optimized for code generation
# Direct xAI API = Better rate limits + 2M context + $0.20-$0.50/M tokens
BACKTEST_MODELS = [
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 0
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 1
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 2
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 3
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 4
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 5
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 6
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 7
    {"type": "xai", "name": "grok-4-fast-reasoning"},    # Thread 8
]

# Model pool for DEBUG phase (9 models - xAI Direct for debugging)
DEBUG_MODELS = [
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 0
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 1
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 2
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 3
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 4
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 5
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 6
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 7
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 8
]

# Single config for backwards compatibility (will be overridden by thread-specific selection)
BACKTEST_CONFIG = BACKTEST_MODELS[0]
DEBUG_CONFIG = DEBUG_MODELS[0]

# 📦 PACKAGE CHECK: Using xAI Direct for package validation
PACKAGE_CONFIG = {
    "type": "xai",
    "name": "grok-4-fast-reasoning"  # xAI Grok for package validation (2M context, fast)
}

# 🚀 OPTIMIZATION: All using xAI Direct (9 threads)
OPTIMIZE_MODELS = [
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 0
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 1
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 2
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 3
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 4
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 5
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 6
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 7
    {"type": "xai", "name": "grok-4-fast-reasoning"},  # Thread 8
]
OPTIMIZE_CONFIG = OPTIMIZE_MODELS[0]

# 🎯 PROFIT TARGET CONFIGURATION
TARGET_RETURN = 50  # Target return in %
SAVE_IF_OVER_RETURN = 1.0  # Save backtest to CSV and folders if return > this % (Moon Dev's threshold!)

# 🚀 MULTI-DATA TESTING CONFIGURATION (PERMANENT FIX FOR TOKEN EFFICIENCY)
# Set to True to SKIP 15m-only testing and use multi-data as primary test
# This saves 40-60% tokens by not wasting iterations optimizing for wrong timeframe
SKIP_15M_TEST = True  # RECOMMENDED: Strategies often fail on 15m but succeed on other timeframes

# 🐍 PYTHON ENVIRONMENT CONFIGURATION
# Since conda is not installed, use base Python which has all required packages
# Verified: C:\Python313\python.exe has PyPDF2, youtube-transcript-api, backtesting, etc.
CONDA_ENV = None  # Use base Python (not conda) - all packages installed there!

# 🎯 ITERATION LIMITS (OPTIMIZED FOR EFFICIENCY)
# User's wisdom: "If it fails 2-3 times, it's fundamentally broken or wrong timeframe"
# No point wasting 10 attempts on a bad strategy - fail fast and move to next one!
MAX_DEBUG_ITERATIONS = 2        # 2 attempts to fix errors (was 10)
MAX_OPTIMIZATION_ITERATIONS = 2  # 2 attempts to optimize (was 10)
# Total max: 1 initial + 2 debug + 2 optimize = 5 iterations per strategy (was 21)
# Token savings: ~75% reduction in wasted iterations!

EXECUTION_TIMEOUT = 300  # 5 minutes

# DeepSeek Configuration
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ============================================
# 🛡️ MODEL VALIDATION & FALLBACK SYSTEM
# ============================================
# Permanent solution to prevent model initialization failures

# Known valid OpenRouter model IDs (updated 2025-11-10)
VALID_OPENROUTER_MODELS = {
    # xAI Grok models
    "x-ai/grok-4-fast": "Multimodal model with 2M context",
    "x-ai/grok-code-fast-1": "Reasoning model optimized for coding",
    "x-ai/grok-4-07-09": "Standard Grok 4 model",
    "x-ai/grok-3-mini": "Lightweight variant",
    "x-ai/grok-3": "Standard Grok 3 model",
    # OpenAI via OpenRouter
    "openai/gpt-4o": "GPT-4 Omni",
    "openai/gpt-4-turbo": "GPT-4 Turbo",
    # Claude via OpenRouter
    "anthropic/claude-3-5-sonnet": "Claude 3.5 Sonnet",
    "anthropic/claude-3-opus": "Claude 3 Opus",
    # DeepSeek via OpenRouter
    "deepseek/deepseek-r1": "DeepSeek R1 reasoning model",
}

# Fallback model configurations (guaranteed to work)
# All fallbacks use xAI Direct API for consistency
FALLBACK_MODELS = {
    "research": [
        {"type": "xai", "name": "grok-4-fast-reasoning"},  # Primary: xAI Direct with reasoning
        {"type": "xai", "name": "grok-code-fast-1"},  # Backup: Code-specialized xAI
    ],
    "backtest": [
        {"type": "xai", "name": "grok-4-fast-reasoning"},  # Primary: xAI Direct with reasoning
        {"type": "xai", "name": "grok-code-fast-1"},  # Backup: Code-specialized xAI
    ],
    "debug": [
        {"type": "xai", "name": "grok-4-fast-reasoning"},  # Primary: xAI Direct with reasoning
        {"type": "xai", "name": "grok-code-fast-1"},  # Backup: Code-specialized xAI
    ],
    "optimize": [
        {"type": "xai", "name": "grok-4-fast-reasoning"},  # Primary: xAI Direct with reasoning
        {"type": "xai", "name": "grok-code-fast-1"},  # Backup: Code-specialized xAI
    ],
}

def validate_model_config(model_config, phase="unknown"):
    """
    🛡️ Validate model configuration before use
    Returns: (is_valid: bool, warning_message: str or None)
    """
    model_type = model_config.get("type", "")
    model_name = model_config.get("name", "")

    # Check if model type is supported
    valid_types = ["claude", "openai", "deepseek", "groq", "gemini", "xai", "ollama", "openrouter"]
    if model_type not in valid_types:
        return False, f"Invalid model type '{model_type}'. Valid types: {valid_types}"

    # Special validation for OpenRouter models
    if model_type == "openrouter":
        if model_name not in VALID_OPENROUTER_MODELS:
            return False, f"OpenRouter model '{model_name}' not in validated list. Check https://openrouter.ai/docs"

    return True, None

def get_fallback_model(phase, thread_id):
    """
    🚨 Get fallback model when primary model fails
    Tries fallback models in order until one works
    """
    fallbacks = FALLBACK_MODELS.get(phase, FALLBACK_MODELS["backtest"])

    with console_lock:
        cprint(f"\n[T{thread_id:02d}] 🔄 Attempting fallback models for {phase}...", "yellow")

    for i, fallback in enumerate(fallbacks):
        is_valid, warning = validate_model_config(fallback, phase)
        if is_valid:
            with console_lock:
                cprint(f"[T{thread_id:02d}]   ✓ Fallback {i+1}/{len(fallbacks)}: {fallback['type']} - {fallback['name']}", "green")
            return fallback
        else:
            with console_lock:
                cprint(f"[T{thread_id:02d}]   ✗ Fallback {i+1}/{len(fallbacks)} invalid: {warning}", "red")

    # Ultimate fallback
    with console_lock:
        cprint(f"[T{thread_id:02d}] ⚠️  All fallbacks failed! Using GPT-4o as last resort", "red", attrs=['bold'])
    return {"type": "openai", "name": "gpt-4o"}

# 🌙 Moon Dev: Date tracking for always-on mode - will update when date changes!
CURRENT_DATE = datetime.now().strftime("%m_%d_%Y")

# Update data directory paths - Parallel Multi-Data version uses its own folder
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data/rbi_pp_multi"

# 🌙 Moon Dev: These will be updated dynamically when date changes
TODAY_DIR = None
RESEARCH_DIR = None
BACKTEST_DIR = None
PACKAGE_DIR = None
WORKING_BACKTEST_DIR = None
FINAL_BACKTEST_DIR = None
OPTIMIZATION_DIR = None
CHARTS_DIR = None
EXECUTION_DIR = None

PROCESSED_IDEAS_LOG = DATA_DIR / "processed_ideas.log"
STATS_CSV = DATA_DIR / "backtest_stats.csv"  # Moon Dev's stats tracker!
IDEAS_FILE = DATA_DIR / "ideas.txt"

def update_date_folders():
    """
    🌙 Moon Dev's Date Folder Updater!
    Checks if date has changed and updates all folder paths accordingly.
    Thread-safe and works in always-on mode! 🚀
    """
    global CURRENT_DATE, TODAY_DIR, RESEARCH_DIR, BACKTEST_DIR, PACKAGE_DIR
    global WORKING_BACKTEST_DIR, FINAL_BACKTEST_DIR, OPTIMIZATION_DIR, CHARTS_DIR, EXECUTION_DIR

    with date_lock:
        new_date = datetime.now().strftime("%m_%d_%Y")

        # Check if date has changed
        if new_date != CURRENT_DATE:
            with console_lock:
                cprint(f"\n🌅 NEW DAY DETECTED! {CURRENT_DATE} → {new_date}", "cyan", attrs=['bold'])
                cprint(f"📁 Creating new folder structure for {new_date}...\n", "yellow")

            CURRENT_DATE = new_date

        # Update all directory paths (whether date changed or first run)
        TODAY_DIR = DATA_DIR / CURRENT_DATE
        RESEARCH_DIR = TODAY_DIR / "research"
        BACKTEST_DIR = TODAY_DIR / "backtests"
        PACKAGE_DIR = TODAY_DIR / "backtests_package"
        WORKING_BACKTEST_DIR = TODAY_DIR / "backtests_working"
        FINAL_BACKTEST_DIR = TODAY_DIR / "backtests_final"
        OPTIMIZATION_DIR = TODAY_DIR / "backtests_optimized"
        CHARTS_DIR = TODAY_DIR / "charts"
        EXECUTION_DIR = TODAY_DIR / "execution_results"

        # Create directories if they don't exist
        for dir in [DATA_DIR, TODAY_DIR, RESEARCH_DIR, BACKTEST_DIR, PACKAGE_DIR,
                    WORKING_BACKTEST_DIR, FINAL_BACKTEST_DIR, OPTIMIZATION_DIR, CHARTS_DIR, EXECUTION_DIR]:
            dir.mkdir(parents=True, exist_ok=True)

# 🌙 Moon Dev: Initialize folders on startup!
update_date_folders()

# ============================================
# 🛡️ STARTUP VALIDATION
# ============================================
def validate_all_configs():
    """
    🚨 Pre-flight validation: Check all model configs BEFORE starting threads
    This prevents runtime failures and wasted API calls
    """
    print("\n" + "="*60)
    cprint("🛡️  SYSTEM STARTUP VALIDATION", "cyan", attrs=['bold'])
    print("="*60 + "\n")

    all_valid = True
    configs_to_check = [
        ("RESEARCH", RESEARCH_CONFIG),
        ("PACKAGE", PACKAGE_CONFIG),
    ]

    # Add all backtest models
    for i, config in enumerate(BACKTEST_MODELS):
        configs_to_check.append((f"BACKTEST_MODEL_{i}", config))

    # Add all debug models
    for i, config in enumerate(DEBUG_MODELS):
        configs_to_check.append((f"DEBUG_MODEL_{i}", config))

    # Add all optimize models
    for i, config in enumerate(OPTIMIZE_MODELS):
        configs_to_check.append((f"OPTIMIZE_MODEL_{i}", config))

    for name, config in configs_to_check:
        is_valid, warning = validate_model_config(config, name)
        if is_valid:
            cprint(f"  ✅ {name:20s} | {config['type']:12s} | {config['name']}", "green")
        else:
            cprint(f"  ❌ {name:20s} | {config['type']:12s} | {config['name']}", "red")
            cprint(f"     └─ {warning}", "yellow")
            all_valid = False

    print("\n" + "="*60)
    if all_valid:
        cprint("✅ ALL CONFIGURATIONS VALID - READY TO START", "green", attrs=['bold'])
    else:
        cprint("⚠️  SOME CONFIGURATIONS INVALID - WILL USE FALLBACKS", "yellow", attrs=['bold'])
    print("="*60 + "\n")

    return all_valid

# Run validation on startup
validate_all_configs()

# ============================================
# 🎨 THREAD-SAFE PRINTING
# ============================================

def thread_print(message, thread_id, color=None, attrs=None):
    """Thread-safe colored print with thread ID prefix"""
    if color is None:
        color = THREAD_COLORS.get(thread_id % 9, "white")

    with console_lock:
        prefix = f"[T{thread_id:02d}]"
        cprint(f"{prefix} {message}", color, attrs=attrs)

def thread_print_status(thread_id, phase, message):
    """Print status update for a specific phase"""
    color = THREAD_COLORS.get(thread_id % 9, "white")
    with console_lock:
        cprint(f"[T{thread_id:02d}] {phase}: {message}", color)

# ============================================
# 🔒 RATE LIMITING
# ============================================

def rate_limited_api_call(func, thread_id, *args, **kwargs):
    """
    Wrapper for API calls with rate limiting and retry logic
    - Per-thread rate limiting (RATE_LIMIT_DELAY)
    - Global rate limiting (RATE_LIMIT_GLOBAL_DELAY)
    - Automatic retry with exponential backoff for rate limits
    """
    max_retries = 5

    for attempt in range(max_retries):
        try:
            # Global rate limit (quick check)
            with api_lock:
                time.sleep(RATE_LIMIT_GLOBAL_DELAY)

            # Execute the API call
            result = func(*args, **kwargs)

            # Per-thread rate limit
            time.sleep(RATE_LIMIT_DELAY)

            return result

        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a rate limit error
            if "rate" in error_str and "limit" in error_str:
                wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                thread_print(f"⏰ Rate limit hit, waiting {wait_time:.1f}s (attempt {attempt+1}/{max_retries})", thread_id)
                time.sleep(wait_time)
                continue
            else:
                # Not a rate limit error, raise immediately
                raise e

    # If we exhausted all retries
    raise Exception(f"Max retries ({max_retries}) reached for API call")

# ============================================
# 📄 PDF & YOUTUBE EXTRACTION - Moon Dev
# ============================================

def get_youtube_transcript(video_id, thread_id):
    """Get transcript from YouTube video - Moon Dev"""
    try:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            thread_print("⚠️ youtube-transcript-api not installed", thread_id, "yellow")
            return None

        thread_print(f"🎥 Fetching transcript for video ID: {video_id}", thread_id, "cyan")

        # 🌙 Moon Dev: Using youtube-transcript-api v1.2.3+ API
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id, languages=['en'])

        # Get the full transcript text
        transcript_text = ' '.join([snippet.text for snippet in transcript_data])

        thread_print(f"✅ Transcript extracted! Length: {len(transcript_text)} characters", thread_id, "green")

        # 🌙 Moon Dev: Print first 300 characters for verification
        preview = transcript_text[:300].replace('\n', ' ')
        thread_print(f"📝 Preview: {preview}...", thread_id, "cyan")

        return transcript_text
    except Exception as e:
        error_msg = str(e)
        if 'TranscriptsDisabled' in str(type(e).__name__) or 'Subtitles are disabled' in error_msg:
            thread_print(f"❌ YouTube transcripts are DISABLED for this video", thread_id, "red")
            thread_print(f"💡 This video has no captions/subtitles available", thread_id, "yellow")
            thread_print(f"💡 Try a different video with captions enabled", thread_id, "yellow")
        else:
            thread_print(f"❌ Error fetching YouTube transcript: {e}", thread_id, "red")
        return None

def get_pdf_text(url, thread_id):
    """Extract text from PDF URL - Moon Dev"""
    try:
        try:
            import PyPDF2
        except ImportError:
            thread_print("⚠️ PyPDF2 not installed", thread_id, "yellow")
            return None

        thread_print(f"📚 Fetching PDF from: {url[:60]}...", thread_id, "cyan")

        # Add headers to simulate browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()

        thread_print("📖 Extracting text from PDF...", thread_id, "cyan")
        reader = PyPDF2.PdfReader(BytesIO(response.content))
        text = ''
        for page in reader.pages:
            page_text = page.extract_text()
            text += page_text + '\n'

        thread_print(f"✅ PDF extracted! Pages: {len(reader.pages)}, Length: {len(text)} characters", thread_id, "green")

        # 🌙 Moon Dev: Print first 300 characters for verification
        preview = text[:300].replace('\n', ' ')
        thread_print(f"📝 Preview: {preview}...", thread_id, "cyan")

        return text
    except Exception as e:
        thread_print(f"❌ Error reading PDF: {e}", thread_id, "red")
        return None

def extract_youtube_id(url):
    """Extract video ID from YouTube URL - Moon Dev"""
    try:
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        else:
            video_id = url.split("/")[-1].split("?")[0]
        return video_id
    except:
        return None

def extract_content_from_url(idea: str, thread_id: int) -> str:
    """
    🌙 Moon Dev: Extract content from PDF or YouTube URLs
    Returns extracted content or original idea if not a URL
    """
    idea = idea.strip()

    # Check if it's a YouTube URL
    if "youtube.com" in idea or "youtu.be" in idea:
        video_id = extract_youtube_id(idea)
        if video_id:
            transcript = get_youtube_transcript(video_id, thread_id)
            if transcript:
                return f"Strategy from YouTube video:\n\n{transcript}"
            else:
                # Red background warning
                with console_lock:
                    cprint("="*80, "white", "on_red", attrs=['bold'])
                    cprint(f"⚠️  YOUTUBE EXTRACTION FAILED - Sleeping 30s", "white", "on_red", attrs=['bold'])
                    cprint("="*80, "white", "on_red", attrs=['bold'])
                time.sleep(30)
                return idea  # Return original idea to continue processing

    # Check if it's a PDF URL
    elif idea.endswith(".pdf") or "pdf" in idea.lower():
        pdf_text = get_pdf_text(idea, thread_id)
        if pdf_text:
            return f"Strategy from PDF document:\n\n{pdf_text}"
        else:
            # Red background warning
            with console_lock:
                cprint("="*80, "white", "on_red", attrs=['bold'])
                cprint(f"⚠️  PDF EXTRACTION FAILED - Sleeping 30s", "white", "on_red", attrs=['bold'])
                cprint("="*80, "white", "on_red", attrs=['bold'])
            time.sleep(30)
            return idea  # Return original idea to continue processing

    # Not a URL, return as-is
    return idea

# ============================================
# 📝 PROMPTS (Same as v3)
# ============================================

RESEARCH_PROMPT = """
You are Moon Dev's Research AI 🌙

IMPORTANT NAMING RULES:
1. Create a UNIQUE TWO-WORD NAME for this specific strategy
2. The name must be DIFFERENT from any generic names like "TrendFollower" or "MomentumStrategy"
3. First word should describe the main approach (e.g., Adaptive, Neural, Quantum, Fractal, Dynamic)
4. Second word should describe the specific technique (e.g., Reversal, Breakout, Oscillator, Divergence)
5. Make the name SPECIFIC to this strategy's unique aspects

Examples of good names:
- "AdaptiveBreakout" for a strategy that adjusts breakout levels
- "FractalMomentum" for a strategy using fractal analysis with momentum
- "QuantumReversal" for a complex mean reversion strategy
- "NeuralDivergence" for a strategy focusing on divergence patterns

BAD names to avoid:
- "TrendFollower" (too generic)
- "SimpleMoving" (too basic)
- "PriceAction" (too vague)

🚨 CRITICAL: EXTRACT ALL INDICATORS MENTIONED!

When analyzing the strategy, you MUST identify and list:
1. **Primary indicators used** with exact parameters (e.g., RSI(14), MACD(12,26,9), BB(20,2), ADX(14))
2. **Entry conditions** with specific indicator thresholds (e.g., "RSI < 30", "MACD cross above signal")
3. **Exit conditions** with specific indicator values (e.g., "RSI > 70", "Price touches upper BB")
4. **Additional filters** or confirmations (e.g., "ADX > 25 for trend strength")

If the strategy mentions:
- "RSI divergence" → Extract: RSI(14)
- "MACD cross" → Extract: MACD(12,26,9)
- "Bollinger squeeze" → Extract: BB(20,2)
- "ADX trend filter" → Extract: ADX(14)
- "Moving average" → Extract: SMA(50) or EMA(20) with specific period

Your complete output MUST follow this EXACT format:
STRATEGY_NAME: [Your unique two-word name]

INDICATORS_REQUIRED:
- [Indicator 1 with parameters, e.g., RSI(14)]
- [Indicator 2 with parameters, e.g., MACD(12,26,9)]
- [Indicator 3 with parameters, e.g., BB(20,2)]

ENTRY_CONDITIONS:
[Specific entry logic using the indicators above]

EXIT_CONDITIONS:
[Specific exit logic using the indicators above]

STRATEGY_DETAILS:
[Your detailed analysis]

Remember: The indicators you extract HERE will be used EXACTLY in the backtest code! Be precise!
"""

BACKTEST_PROMPT = """
You are Moon Dev's Backtest AI 🌙

🚨 CRITICAL: Your code MUST have TWO parts:
PART 1: Strategy class definition
PART 2: if __name__ == "__main__" block (SEE TEMPLATE BELOW - MANDATORY!)

If you don't include the if __name__ == "__main__" block with stats printing, the code will FAIL!

Create a backtesting.py implementation for the strategy.
USE BACKTESTING.PY
Include:
1. All necessary imports
2. Strategy class with indicators
3. Entry/exit logic
4. Risk management
5. your size should be 1,000,000
6. If you need indicators use TA lib or pandas TA.

🎯 CRITICAL TRADING LOGIC REQUIREMENTS (PERMANENT FIX FOR POOR PERFORMANCE):

1. ENTRY SIGNAL QUALITY:
   - Entries must have MULTIPLE confirmations (2-3 indicators agreeing)
   - Avoid entering on single indicator crosses alone
   - Check trend alignment before counter-trend trades
   - Ensure sufficient volatility before breakout entries
   - Wait for pullbacks in strong trends (don't chase)

2. EXIT LOGIC:
   - ALWAYS implement proper stop loss (use sl= parameter in buy/sell)
   - Take profit at realistic levels (2:1 or 3:1 risk/reward minimum)
   - Use trailing stops for trend-following strategies
   - Exit when entry conditions reverse (not just stop loss hit)
   - Scale out at multiple profit targets if applicable

3. POSITION SIZING:
   - Start with 1.0 (100% equity) for simplicity
   - Reduce size if strategy has many concurrent signals
   - Never use fractional sizes like 0.5 unless testing partial positions

4. TRADE FREQUENCY:
   - Aim for 20-100 trades on 15m BTC data (not too few, not too many)
   - If 0 trades: signals too strict, conditions never met
   - If 1000+ trades: overtrading, signals too loose
   - Quality over quantity - each trade should have edge

5. INDICATOR USAGE - 🚨 CRITICAL CONSISTENCY REQUIREMENT:

   YOU MUST USE THE EXACT INDICATORS SPECIFIED IN THE STRATEGY RESEARCH!

   The research phase extracted specific indicators with parameters.
   YOU MUST use those EXACT indicators in your code!

   Example:
   - If research says "RSI(14) < 30" → Use: self.I(talib.RSI, self.data.Close, timeperiod=14)
   - If research says "MACD cross" → Use: self.I(talib.MACD, self.data.Close, 12, 26, 9)
   - If research says "ADX > 25" → Use: self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, 14)
   - If research says "BB(20,2) squeeze" → Use: self.I(talib.BBANDS, self.data.Close, 20, 2, 2)

   DO NOT substitute different indicators!
   DO NOT add indicators not mentioned in the research!
   DO NOT change indicator parameters unless research is vague!

   If research doesn't specify parameters (e.g., just says "RSI"):
   - Use standard defaults: RSI(14), MACD(12,26,9), BB(20,2), ADX(14), SMA/EMA(20 or 50)

6. AVOID COMMON FAILURES:
   - ❌ Single indicator strategies (RSI cross alone = poor results)
   - ❌ No stop loss = massive drawdowns
   - ❌ Entry on every bar = overtrading
   - ❌ Fixed stops without ATR adjustment = stopped out too often
   - ❌ No trend filter on mean reversion = catching falling knives

IMPORTANT DATA HANDLING:
1. Clean column names by removing spaces: data.columns = data.columns.str.strip().str.lower()
2. Drop any unnamed columns: data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
3. Ensure proper column mapping to match backtesting requirements:
   - Required columns: 'Open', 'High', 'Low', 'Close', 'Volume'
   - Use proper case (capital first letter)

FOR THE PYTHON BACKTESTING LIBRARY USE BACKTESTING.PY AND SEND BACK ONLY THE CODE, NO OTHER TEXT.

INDICATOR CALCULATION RULES:
1. ALWAYS use self.I() wrapper for ANY indicator calculations
2. Use talib functions instead of pandas operations:
   - Instead of: self.data.Close.rolling(20).mean()
   - Use: self.I(talib.SMA, self.data.Close, timeperiod=20)
3. For swing high/lows use talib.MAX/MIN:
   - Instead of: self.data.High.rolling(window=20).max()
   - Use: self.I(talib.MAX, self.data.High, timeperiod=20)

BACKTEST EXECUTION ORDER:
1. Run initial backtest with default parameters first
2. Print full stats using print(stats) and print(stats._strategy)
3. no optimization code needed, just print the final stats, make sure full stats are printed, not just part or some. stats = bt.run() print(stats) is an example of the last line of code. no need for plotting ever.

❌ NEVER USE bt.plot() - IT CAUSES TIMEOUTS IN PARALLEL PROCESSING!
❌ NO PLOTTING, NO CHARTS, NO VISUALIZATIONS!
✅ ONLY PRINT STATS TO CONSOLE!

CRITICAL POSITION SIZING RULE:
When calculating position sizes in backtesting.py, the size parameter must be either:
1. A fraction between 0 and 1 (for percentage of equity)
2. A whole number (integer) of units

The common error occurs when calculating position_size = risk_amount / risk, which results in floating-point numbers. Always use:
position_size = int(round(position_size))

Example fix:
❌ self.buy(size=3546.0993)  # Will fail
✅ self.buy(size=int(round(3546.0993)))  # Will work

RISK MANAGEMENT:
1. Always calculate position sizes based on risk percentage
2. Use proper stop loss and take profit calculations
4. Print entry/exit signals with Moon Dev themed messages

If you need indicators use TA lib or pandas TA.

Use this data path (relative to project root): src/data/ohlcv/BTC-USDT-15m.csv
Or use absolute Windows path: C:/Users/oia89/OneDrive/Desktop/DEX-dev-ai-agents/src/data/ohlcv/BTC-USDT-15m.csv

The data CSV format:
datetime,open,high,low,close,volume,timestamp
2023-01-01 00:00:00,16531.83,16532.69,16509.11,16510.82,231.05338022,1672531200000
2023-01-01 00:15:00,16509.78,16534.66,16509.11,16533.43,308.12276951,1672532100000

Always add plenty of Moon Dev themed debug prints with emojis to make debugging easier! 🌙 ✨ 🚀

🚨🚨🚨 MANDATORY EXECUTION BLOCK - DO NOT SKIP THIS! 🚨🚨🚨

YOU ABSOLUTELY MUST INCLUDE THIS BLOCK AT THE END OF YOUR CODE!
WITHOUT THIS BLOCK, THE STATS CANNOT BE PARSED AND THE BACKTEST WILL FAIL!

Copy this EXACT template and replace YourStrategyClassName with your actual class name:

```python
# 🌙 MOON DEV'S MULTI-DATA TESTING FRAMEWORK 🚀
# Tests this strategy on 25+ data sources automatically!
if __name__ == "__main__":
    import sys
    import os
    import io
    from backtesting import Backtest
    import pandas as pd

    # Set UTF-8 encoding for Windows terminal (fixes emoji display issues)
    if os.name == 'nt':  # Windows
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # FIRST: Run standard backtest and print stats (REQUIRED for parsing!)
    print("\\n🌙 Running initial backtest for stats extraction...")
    import os
    data_path = os.path.join('src', 'data', 'ohlcv', 'BTC-USDT-15m.csv')
    data = pd.read_csv(data_path)
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    # Select only OHLCV columns (exclude timestamp column)
    data = data[['open', 'high', 'low', 'close', 'volume']]
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    bt = Backtest(data, YourStrategyClassName, cash=1_000_000, commission=0.002)
    stats = bt.run()

    # 🌙 CRITICAL: Print full stats for Moon Dev's parser!
    print("\\n" + "="*80)
    print("📊 BACKTEST STATISTICS (Moon Dev's Format)")
    print("="*80)
    print(stats)
    print("="*80 + "\\n")

    # THEN: Run QUICK FILTER TEST (User's Smart Approach!)
    # 🎯 Test on 15m + 1h first before wasting time on full multi-data test
    # User's wisdom: "If fails on both 15m and 1h, won't work on other timeframes"
    try:
        # Fix: Go up 5 levels from backtests_package to project root
        # backtests_package -> 11_11_2025 -> rbi_pp_multi -> data -> src -> PROJECT_ROOT
        project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')
        project_root = os.path.abspath(project_root)  # Convert to absolute path
        scripts_path = os.path.join(project_root, 'src', 'scripts')
        sys.path.insert(0, scripts_path)  # Insert at front to ensure it's found first
        from multi_data_tester_parallel import test_quick_filter, test_on_all_data_parallel
        from pathlib import Path

        print("\\n" + "="*80)
        print("🎯 QUICK FILTER: Testing 15m + 1h (User's Smart Filter)")
        print("="*80)
        print("💡 Logic: If strategy fails on BOTH, it's fundamentally broken")
        print("   15m = Lower timeframe (noise) | 1h = Basic higher timeframe (trends)")

        # Step 1: Quick filter test (15m + 1h only)
        quick_result = test_quick_filter(YourStrategyClassName, 'YourStrategyName', verbose=True)

        if quick_result['passed']:
            # PASSED FILTER! Run full multi-data test
            print("\\n✅ PASSED QUICK FILTER! Running full multi-data test...")
            print("="*80)
            print("🚀 MOON DEV'S PARALLEL MULTI-DATA BACKTEST - Testing on 12 Crypto Datasets!")
            print("="*80)

            # 🌙 PERMANENT FIX: Use absolute path for results directory
            results_dir = Path(os.path.dirname(__file__)) / "results"
            results_dir = results_dir.resolve()  # Convert to absolute path
            print(f"💾 Results will be saved to: {results_dir}")

            # Test on ALL data sources (BTC, ETH, SOL × 4 timeframes)
            results = test_on_all_data_parallel(YourStrategyClassName, 'YourStrategyName', verbose=False, parallel=True, max_workers=4, results_dir=results_dir)

            if results is not None:
                print(f"\\n✅ Multi-data testing complete! Results saved in {results_dir}")
                print(f"📊 Tested on {len(results)} different data sources")
            else:
                print("\\n⚠️ No results generated - check for errors above")
        else:
            # FAILED FILTER! Don't waste time on full multi-data test
            print("\\n❌ FAILED QUICK FILTER (both 15m and 1h negative)")
            print("💡 Strategy is fundamentally broken - skipping full multi-data test")
            print("🚀 This saves ~80% of testing time by failing fast!")
            print("="*80)
    except (ImportError, ModuleNotFoundError) as e:
        print(f"\\n⚠️ Multi-data testing skipped: {str(e)}")
        print("💡 This is OK - the main backtest above shows the strategy performance")
        print("🔧 To enable multi-data testing, ensure multi_data_tester.py is in src/scripts/")
    except Exception as e:
        print(f"\\n⚠️ Multi-data testing error: {str(e)}")
        print("💡 Main backtest completed successfully above")
```

IMPORTANT: Replace 'YourStrategyClassName' with your actual strategy class name!
IMPORTANT: Replace 'YourStrategyName' with a descriptive name for the CSV output!

🚨 FINAL REMINDER 🚨
Your response MUST include:
1. Import statements
2. Strategy class (with init() and next() methods)
3. The if __name__ == "__main__" block shown above (MANDATORY!)

Do NOT send ONLY the strategy class. You MUST include the execution block!
ONLY SEND BACK CODE, NO OTHER TEXT.

FOR THE PYTHON BACKTESTING LIBRARY USE BACKTESTING.PY AND SEND BACK ONLY THE CODE, NO OTHER TEXT.
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

DEBUG_PROMPT = """
You are Moon Dev's Debug AI 🌙
Fix technical issues AND improve strategy logic to achieve positive returns.

CRITICAL ERROR TO FIX:
{error_message}

🎯 PERFORMANCE ANALYSIS (If return is negative or 0 trades):
Current Performance: {current_return}% return, {num_trades} trades

If performance is poor, you MUST analyze and fix:
1. Entry conditions too strict/loose (check if signals ever trigger)
2. Exit logic missing or broken (check if exits happen)
3. Stop loss too tight (getting stopped out prematurely)
4. Position sizing issues (check if trades execute with correct size)
5. Missing confirmations (single indicator = poor results)

🎯 STRATEGY IMPROVEMENT GUIDELINES (PERMANENT FIX):
If return < 0% or trades = 0, you MUST improve the strategy logic:

1. FIX "NO TRADES" ISSUE:
   - Check if entry conditions are ever True (add debug prints)
   - Verify self.buy() or self.sell() is actually called
   - Ensure position size is valid (1.0 or positive integer)
   - Look for logical conflicts (can't enter long if already in position)

2. FIX NEGATIVE RETURNS:
   - Add stop loss if missing (use sl= parameter in buy/sell)
   - Improve entry confirmation (add 2nd indicator filter)
   - Add trend filter (don't counter-trend trade without confirmation)
   - Check if exits are too early or too late
   - Reduce trade frequency if overtrading (>500 trades)

3. IMPROVE ENTRY LOGIC:
   - Add multiple confirmations (e.g., RSI + trend + volume)
   - Wait for pullbacks in trends (don't chase breakouts)
   - Check volatility before entry (use ATR filter)
   - Avoid entries near resistance/support without confirmation

4. IMPROVE EXIT LOGIC:
   - Always use stop loss (ATR-based or percentage)
   - Set realistic profit targets (2:1 or 3:1 R:R minimum)
   - Exit when entry conditions reverse
   - Use trailing stops for trend-following

CRITICAL DATA LOADING REQUIREMENTS:
The CSV file has these exact columns after processing:
- datetime, open, high, low, close, volume (all lowercase after .str.lower())
- After capitalization: Datetime, Open, High, Low, Close, Volume

CRITICAL BACKTESTING REQUIREMENTS:
1. Data Loading Rules:
   - Use data.columns.str.strip().str.lower() to clean columns
   - Drop unnamed columns: data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
   - Rename columns properly: data.rename(columns={{'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}})
   - Set datetime as index: data = data.set_index(pd.to_datetime(data['datetime']))

2. Position Sizing Rules:
   - Must be either a fraction (0 < size < 1) for percentage of equity
   - OR a positive whole number (round integer) for units
   - NEVER use floating point numbers for unit-based sizing

3. Indicator Issues:
   - Cannot use .shift() on backtesting indicators
   - Use array indexing like indicator[-2] for previous values
   - All indicators must be wrapped in self.I()

4. Position Object Issues:
   - Position object does NOT have .entry_price attribute
   - Use self.trades[-1].entry_price if you need entry price from last trade
   - Available position attributes: .size, .pl, .pl_pct
   - For partial closes: use self.position.close() without parameters (closes entire position)
   - For stop losses: use sl= parameter in buy/sell calls, not in position.close()

5. No Trades Issue (Signals but no execution):
   - If strategy prints "ENTRY SIGNAL" but shows 0 trades, the self.buy() call is not executing
   - Common causes: invalid size parameter, insufficient cash, missing self.buy() call
   - Ensure self.buy() is actually called in the entry condition block
   - Check size parameter: must be fraction (0-1) or positive integer
   - Verify cash/equity is sufficient for the trade size

Focus on:
1. KeyError issues with column names
2. Syntax errors and import statements
3. Indicator calculation methods
4. Data loading and preprocessing
5. Position object attribute errors (.entry_price, .close() parameters)
6. STRATEGY LOGIC IMPROVEMENTS (add confirmations, fix exits, improve entries)

YOU CAN AND SHOULD change strategy logic to improve performance if returns are negative!

Return the complete fixed code with Moon Dev themed debug prints! 🌙 ✨
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

PACKAGE_PROMPT = """
You are Moon Dev's Package AI 🌙
Your job is to ensure the backtest code NEVER uses ANY backtesting.lib imports or functions.

❌ STRICTLY FORBIDDEN:
1. from backtesting.lib import *
2. import backtesting.lib
3. from backtesting.lib import crossover
4. ANY use of backtesting.lib

✅ REQUIRED REPLACEMENTS:
1. For crossover detection:
   Instead of: backtesting.lib.crossover(a, b)
   Use: (a[-2] < b[-2] and a[-1] > b[-1])  # for bullish crossover
        (a[-2] > b[-2] and a[-1] < b[-1])  # for bearish crossover

2. For indicators:
   - Use talib for all standard indicators (SMA, RSI, MACD, etc.)
   - Use pandas-ta for specialized indicators
   - ALWAYS wrap in self.I()

3. For signal generation:
   - Use numpy/pandas boolean conditions
   - Use rolling window comparisons with array indexing
   - Use mathematical comparisons (>, <, ==)

Example conversions:
❌ from backtesting.lib import crossover
❌ if crossover(fast_ma, slow_ma):
✅ if fast_ma[-2] < slow_ma[-2] and fast_ma[-1] > slow_ma[-1]:

❌ self.sma = self.I(backtesting.lib.SMA, self.data.Close, 20)
✅ self.sma = self.I(talib.SMA, self.data.Close, timeperiod=20)

IMPORTANT: Scan the ENTIRE code for any backtesting.lib usage and replace ALL instances!
Return the complete fixed code with proper Moon Dev themed debug prints! 🌙 ✨
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

OPTIMIZE_PROMPT = """
You are Moon Dev's Optimization AI 🌙
Your job is to IMPROVE the strategy to achieve higher returns while maintaining good risk management.

CURRENT PERFORMANCE:
Return [%]: {current_return}%
TARGET RETURN: {target_return}%

YOUR MISSION: Optimize this strategy to hit the target return!

OPTIMIZATION TECHNIQUES TO CONSIDER:
1. **Entry Optimization:**
   - Tighten entry conditions to catch better setups
   - Add filters to avoid low-quality signals
   - Use multiple timeframe confirmation
   - Add volume/momentum filters

2. **Exit Optimization:**
   - Improve take profit levels
   - Add trailing stops
   - Use dynamic position sizing based on volatility
   - Scale out of positions

3. **Risk Management:**
   - Adjust position sizing
   - Use volatility-based position sizing (ATR)
   - Add maximum drawdown limits
   - Improve stop loss placement

4. **Indicator Optimization:**
   - Fine-tune indicator parameters
   - Add complementary indicators
   - Use indicator divergence
   - Combine multiple timeframes

5. **Market Regime Filters:**
   - Add trend filters
   - Avoid choppy/ranging markets
   - Only trade in favorable conditions

IMPORTANT RULES:
- DO NOT break the code structure
- Keep all Moon Dev debug prints
- Maintain proper backtesting.py format
- Use self.I() for all indicators
- Position sizes must be int or fraction (0-1)
- Focus on REALISTIC improvements (no curve fitting!)
- Explain your optimization changes in comments

Return the COMPLETE optimized code with Moon Dev themed comments explaining what you improved! 🌙 ✨
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

# ============================================
# 🛠️ HELPER FUNCTIONS (with thread safety)
# ============================================

def parse_return_from_output(stdout: str, thread_id: int) -> float:
    """Extract the Return [%] from backtest output"""
    try:
        match = re.search(r'Return \[%\]\s+([-\d.]+)', stdout)
        if match:
            return_pct = float(match.group(1))
            thread_print(f"📊 Extracted return: {return_pct}%", thread_id)
            return return_pct
        else:
            thread_print("⚠️ Could not find Return [%] in output", thread_id, "yellow")
            return None
    except Exception as e:
        thread_print(f"❌ Error parsing return: {str(e)}", thread_id, "red")
        return None

def parse_all_stats_from_output(stdout: str, thread_id: int) -> dict:
    """
    🌙 Moon Dev's Stats Parser - Extract all key stats from backtest output!
    Returns dict with: return_pct, buy_hold_pct, max_drawdown_pct, sharpe, sortino, expectancy, trades
    """
    stats = {
        'return_pct': None,
        'buy_hold_pct': None,
        'max_drawdown_pct': None,
        'sharpe': None,
        'sortino': None,
        'expectancy': None,
        'trades': None
    }

    try:
        # Return [%]
        match = re.search(r'Return \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['return_pct'] = float(match.group(1))

        # Buy & Hold Return [%]
        match = re.search(r'Buy & Hold Return \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['buy_hold_pct'] = float(match.group(1))

        # Max. Drawdown [%]
        match = re.search(r'Max\. Drawdown \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['max_drawdown_pct'] = float(match.group(1))

        # Sharpe Ratio
        match = re.search(r'Sharpe Ratio\s+([-\d.]+)', stdout)
        if match:
            stats['sharpe'] = float(match.group(1))

        # Sortino Ratio
        match = re.search(r'Sortino Ratio\s+([-\d.]+)', stdout)
        if match:
            stats['sortino'] = float(match.group(1))

        # Expectancy [%] (or Avg. Trade [%])
        match = re.search(r'Expectancy \[%\]\s+([-\d.]+)', stdout)
        if not match:
            match = re.search(r'Avg\. Trade \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['expectancy'] = float(match.group(1))

        # # Trades
        match = re.search(r'# Trades\s+(\d+)', stdout)
        if match:
            stats['trades'] = int(match.group(1))

        # 🌙 Moon Dev: Exposure Time [%]
        match = re.search(r'Exposure Time \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['exposure'] = float(match.group(1))

        thread_print(f"📊 Extracted {sum(1 for v in stats.values() if v is not None)}/8 stats", thread_id)
        return stats

    except Exception as e:
        thread_print(f"❌ Error parsing stats: {str(e)}", thread_id, "red")
        return stats

def log_stats_to_csv(strategy_name: str, thread_id: int, stats: dict, file_path: str, data_source: str = "BTC-USD-15m.csv") -> None:
    """
    🌙 Moon Dev's CSV Logger - Thread-safe stats logging!
    Appends backtest stats to CSV for easy analysis and comparison
    Now includes data source tracking for multi-data testing!
    """
    try:
        with file_lock:
            # Create CSV with headers if it doesn't exist
            file_exists = STATS_CSV.exists()

            with open(STATS_CSV, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header if new file
                if not file_exists:
                    writer.writerow([
                        'Strategy Name',
                        'Thread ID',
                        'Return %',
                        'Buy & Hold %',
                        'Max Drawdown %',
                        'Sharpe Ratio',
                        'Sortino Ratio',
                        'Exposure %',  # 🌙 Moon Dev: Added Exposure Time
                        'EV %',  # 🌙 Moon Dev: Changed from Expectancy %
                        'Trades',  # 🌙 Moon Dev: Added # Trades
                        'File Path',
                        'Data',  # 🌙 Moon Dev: Changed from Data Source
                        'Time'   # 🌙 Moon Dev: Changed from Timestamp
                    ])
                    thread_print("📝 Created new stats CSV with headers", thread_id, "green")

                # Write stats row
                # 🌙 Moon Dev: Format time as "10/25 06:30"
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                writer.writerow([
                    strategy_name,
                    f"T{thread_id:02d}",
                    stats.get('return_pct', 'N/A'),
                    stats.get('buy_hold_pct', 'N/A'),
                    stats.get('max_drawdown_pct', 'N/A'),
                    stats.get('sharpe', 'N/A'),
                    stats.get('sortino', 'N/A'),
                    stats.get('exposure', 'N/A'),  # 🌙 Moon Dev: Added Exposure %
                    stats.get('expectancy', 'N/A'),
                    stats.get('trades', 'N/A'),  # 🌙 Moon Dev: Added # Trades
                    str(file_path),
                    data_source,
                    timestamp
                ])

                thread_print(f"✅ Logged stats to CSV (Return: {stats.get('return_pct', 'N/A')}% on {data_source})", thread_id, "green")

    except Exception as e:
        thread_print(f"❌ Error logging to CSV: {str(e)}", thread_id, "red")

def parse_and_log_multi_data_results(strategy_name: str, thread_id: int, backtest_file_path: Path) -> dict:
    """
    🌙 Moon Dev's Multi-Data Results Parser!
    Parses the multi-data testing results CSV and logs all results that pass the threshold

    Args:
        strategy_name: Name of the strategy
        thread_id: Thread ID
        backtest_file_path: Path to the backtest file that was executed

    Returns:
        dict with 'target_hit': bool, 'best_return': float, 'best_timeframe': str
    """
    try:
        # Multi-data results are saved in ./results/ relative to the backtest file
        backtest_dir = backtest_file_path.parent
        results_dir = backtest_dir / "results"
        results_csv = results_dir / f"{strategy_name}.csv"

        # Check if results exist
        if not results_csv.exists():
            thread_print(f"⚠️ No multi-data results found at {results_csv}", thread_id, "yellow")
            return {'target_hit': False, 'best_return': 0, 'best_timeframe': None}

        # Read the results CSV
        df = pd.read_csv(results_csv)

        thread_print(f"📊 Found {len(df)} multi-data test results", thread_id, "cyan")

        # Find best performing timeframe
        best_idx = df['Return_%'].idxmax()
        best_return = df.loc[best_idx, 'Return_%']
        best_timeframe = df.loc[best_idx, 'Data_Source']

        thread_print(f"📈 Best: {best_return:.2f}% on {best_timeframe}", thread_id, "cyan")

        # Check if target hit on ANY timeframe
        target_hit_results = df[df['Return_%'] >= TARGET_RETURN]
        target_hit = len(target_hit_results) > 0

        if target_hit:
            thread_print(f"🚀🚀🚀 TARGET HIT! {len(target_hit_results)} timeframes >= {TARGET_RETURN}%!", thread_id, "green", attrs=['bold'])
            for idx, row in target_hit_results.iterrows():
                thread_print(f"  🎯 {row['Data_Source']}: {row['Return_%']:.2f}%", thread_id, "green", attrs=['bold'])

        # Filter for results that pass the save threshold
        passing_results = df[df['Return_%'] > SAVE_IF_OVER_RETURN]

        if len(passing_results) == 0:
            thread_print(f"⚠️ No multi-data results passed {SAVE_IF_OVER_RETURN}% threshold", thread_id, "yellow")
            return {'target_hit': target_hit, 'best_return': best_return, 'best_timeframe': best_timeframe}

        thread_print(f"✅ {len(passing_results)} data sources passed threshold!", thread_id, "green", attrs=['bold'])

        # Log each passing result to the main stats CSV
        for idx, row in passing_results.iterrows():
            stats = {
                'return_pct': row['Return_%'],
                'buy_hold_pct': row.get('Buy_Hold_%', None),
                'max_drawdown_pct': row.get('Max_DD_%', None),
                'sharpe': row.get('Sharpe', None),
                'sortino': row.get('Sortino', None),
                'exposure': row.get('Exposure_Time_%', None),  # 🌙 Moon Dev: Added Exposure % (matches multi_data_tester.py column name)
                'expectancy': row.get('Expectancy_%', None),
                'trades': row.get('Trades', None)  # 🌙 Moon Dev: Added # Trades
            }

            data_source = row['Data_Source']

            # Log to CSV with the specific data source
            log_stats_to_csv(
                strategy_name,
                thread_id,
                stats,
                str(backtest_file_path),
                data_source=data_source
            )

        thread_print(f"💾 Logged {len(passing_results)} multi-data results to CSV!", thread_id, "green", attrs=['bold'])

        return {'target_hit': target_hit, 'best_return': best_return, 'best_timeframe': best_timeframe}

    except Exception as e:
        thread_print(f"❌ Error parsing multi-data results: {str(e)}", thread_id, "red")
        return {'target_hit': False, 'best_return': 0, 'best_timeframe': None}

def save_backtest_if_threshold_met(code: str, stats: dict, strategy_name: str, iteration: int, thread_id: int, phase: str = "debug") -> bool:
    """
    🌙 Moon Dev's Threshold Checker - Save backtests that pass the return threshold!

    Args:
        code: The backtest code to save
        stats: Dict of parsed stats
        strategy_name: Name of the strategy
        iteration: Current iteration number
        thread_id: Thread ID
        phase: "debug", "opt", or "final" to determine filename

    Returns:
        True if saved (threshold met), False otherwise
    """
    return_pct = stats.get('return_pct')

    # Check if return meets threshold
    if return_pct is None or return_pct <= SAVE_IF_OVER_RETURN:
        thread_print(f"⚠️ Return {return_pct}% ≤ {SAVE_IF_OVER_RETURN}% threshold - not saving", thread_id, "yellow")
        return False

    try:
        # Determine filename based on phase
        if phase == "debug":
            filename = f"T{thread_id:02d}_{strategy_name}_DEBUG_v{iteration}_{return_pct:.1f}pct.py"
        elif phase == "opt":
            filename = f"T{thread_id:02d}_{strategy_name}_OPT_v{iteration}_{return_pct:.1f}pct.py"
        else:  # final
            filename = f"T{thread_id:02d}_{strategy_name}_FINAL_{return_pct:.1f}pct.py"

        # Save to WORKING folder
        working_file = WORKING_BACKTEST_DIR / filename
        with file_lock:
            with open(working_file, 'w', encoding='utf-8') as f:
                f.write(code)

        # Save to FINAL folder (same logic per Moon Dev's request)
        final_file = FINAL_BACKTEST_DIR / filename
        with file_lock:
            with open(final_file, 'w', encoding='utf-8') as f:
                f.write(code)

        thread_print(f"💾 Saved to working & final! Return: {return_pct:.2f}%", thread_id, "green", attrs=['bold'])

        # Log to CSV
        log_stats_to_csv(strategy_name, thread_id, stats, str(working_file))

        return True

    except Exception as e:
        thread_print(f"❌ Error saving backtest: {str(e)}", thread_id, "red")
        return False

def execute_backtest(file_path: str, strategy_name: str, thread_id: int) -> dict:
    """Execute a backtest file in conda environment and capture output"""
    thread_print(f"🚀 Executing: {strategy_name}", thread_id)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # USING BASE PYTHON: Packages are installed in base Python already!
    # Confirmed by: python -c "import backtesting; import pandas_ta; import talib; print('✅ All packages OK!')"
    # Result: ✅ All packages OK!

    # Use absolute path to Python that has the packages
    python_exe = r"C:\Python313\python.exe"

    # Fallback to sys.executable if the specific path doesn't exist
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    cmd = [
        python_exe,  # Uses the Python that HAS the packages!
        str(file_path)
    ]

    start_time = datetime.now()

    # CRITICAL FIX: Explicitly use UTF-8 encoding for subprocess to avoid UnicodeDecodeError
    # Windows defaults to cp1252, but backtest output contains UTF-8 characters
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',  # Replace undecodable bytes instead of crashing
        timeout=EXECUTION_TIMEOUT
    )

    execution_time = (datetime.now() - start_time).total_seconds()

    output = {
        "success": result.returncode == 0,
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "execution_time": execution_time,
        "timestamp": datetime.now().isoformat()
    }

    # Save execution results with thread ID
    result_file = EXECUTION_DIR / f"T{thread_id:02d}_{strategy_name}_{datetime.now().strftime('%H%M%S')}.json"
    with file_lock:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

    if output['success']:
        thread_print(f"✅ Backtest executed in {execution_time:.2f}s!", thread_id, "green")
    else:
        thread_print(f"❌ Backtest failed: {output['return_code']}", thread_id, "red")

    # CRITICAL FIX: Force garbage collection to free memory and prevent WinError 1455
    gc.collect()

    return output

def parse_execution_error(execution_result: dict) -> str:
    """Extract meaningful error message for debug agent"""
    if execution_result.get('stderr'):
        return execution_result['stderr'].strip()
    return execution_result.get('error', 'Unknown error')

def get_idea_hash(idea: str) -> str:
    """Generate a unique hash for an idea to track processing status"""
    return hashlib.md5(idea.encode('utf-8')).hexdigest()

def is_idea_processed(idea: str) -> bool:
    """Check if an idea has already been processed (thread-safe)"""
    if not PROCESSED_IDEAS_LOG.exists():
        return False

    idea_hash = get_idea_hash(idea)

    try:
        with file_lock:
            with open(PROCESSED_IDEAS_LOG, 'r', encoding='utf-8', errors='replace') as f:
                processed_hashes = [line.strip().split(',')[0] for line in f if line.strip()]
        return idea_hash in processed_hashes
    except Exception as e:
        # If error reading log, assume not processed to avoid losing ideas
        return False

def log_processed_idea(idea: str, strategy_name: str, thread_id: int) -> None:
    """Log an idea as processed with timestamp and strategy name (thread-safe)"""
    idea_hash = get_idea_hash(idea)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with file_lock:
        if not PROCESSED_IDEAS_LOG.exists():
            PROCESSED_IDEAS_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(PROCESSED_IDEAS_LOG, 'w', encoding='utf-8') as f:
                f.write("# Moon Dev's RBI AI - Processed Ideas Log 🌙\n")
                f.write("# Format: hash,timestamp,thread_id,strategy_name,idea_snippet\n")

        idea_snippet = idea[:50].replace(',', ';') + ('...' if len(idea) > 50 else '')
        with open(PROCESSED_IDEAS_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{idea_hash},{timestamp},T{thread_id:02d},{strategy_name},{idea_snippet}\n")

    thread_print(f"📝 Logged processed idea: {strategy_name}", thread_id, "green")

def has_nan_results(execution_result: dict) -> bool:
    """Check if backtest results contain NaN values indicating no trades"""
    if not execution_result.get('success'):
        return False

    stdout = execution_result.get('stdout', '')

    nan_indicators = [
        '# Trades                                    0',
        'Win Rate [%]                              NaN',
        'Exposure Time [%]                         0.0',
        'Return [%]                                0.0'
    ]

    nan_count = sum(1 for indicator in nan_indicators if indicator in stdout)
    return nan_count >= 2

def analyze_no_trades_issue(execution_result: dict) -> str:
    """Analyze why strategy shows signals but no trades"""
    stdout = execution_result.get('stdout', '')

    if 'ENTRY SIGNAL' in stdout and '# Trades                                    0' in stdout:
        return "Strategy is generating entry signals but self.buy() calls are not executing. This usually means: 1) Position sizing issues (size parameter invalid), 2) Insufficient cash/equity, 3) Logic preventing buy execution, or 4) Missing actual self.buy() call in the code. The strategy prints signals but never calls self.buy()."

    elif '# Trades                                    0' in stdout:
        return "Strategy executed but took 0 trades, resulting in NaN values. The entry conditions are likely too restrictive or there are logic errors preventing trade execution."

    return "Strategy executed but took 0 trades, resulting in NaN values. Please adjust the strategy logic to actually generate trading signals and take trades."

def chat_with_model(system_prompt, user_content, model_config, thread_id, phase="unknown"):
    """
    🛡️ Chat with AI model using model factory with validation, fallback, and rate limiting

    Permanent solution that:
    1. Validates model config before attempting
    2. Tries fallback models if primary fails
    3. Never crashes the thread completely
    """
    # First attempt with primary model
    current_config = model_config.copy()
    max_attempts = 3  # Try primary + 2 fallbacks

    for attempt in range(max_attempts):
        # Validate model before attempting
        is_valid, warning = validate_model_config(current_config, phase)
        if not is_valid and attempt == 0:
            with console_lock:
                cprint(f"[T{thread_id:02d}] ⚠️  Primary model validation failed: {warning}", "yellow")
            # Get fallback immediately
            current_config = get_fallback_model(phase, thread_id)
            continue

        def _api_call():
            try:
                model = model_factory.get_model(current_config["type"], current_config["name"])
                if not model:
                    raise ValueError(f"🚨 Could not initialize {current_config['type']} {current_config['name']} model!")

                if current_config["type"] == "ollama":
                    response = model.generate_response(
                        system_prompt=system_prompt,
                        user_content=user_content,
                        temperature=AI_TEMPERATURE
                    )
                    if isinstance(response, str):
                        return response
                    if hasattr(response, 'content'):
                        return response.content
                    return str(response)
                else:
                    response = model.generate_response(
                        system_prompt=system_prompt,
                        user_content=user_content,
                        temperature=AI_TEMPERATURE,
                        max_tokens=AI_MAX_TOKENS
                    )
                    if not response:
                        raise ValueError("Model returned None response")
                    return response.content
            except Exception as e:
                # Log the error but allow fallback logic to handle it
                with console_lock:
                    cprint(f"[T{thread_id:02d}] ❌ Model error: {str(e)[:100]}", "red")
                raise

        try:
            # Apply rate limiting and execute
            result = rate_limited_api_call(_api_call, thread_id)
            if result:
                if attempt > 0:
                    with console_lock:
                        cprint(f"[T{thread_id:02d}] ✅ Fallback model succeeded!", "green", attrs=['bold'])
                return result
        except Exception as e:
            if attempt < max_attempts - 1:
                with console_lock:
                    cprint(f"[T{thread_id:02d}] 🔄 Attempt {attempt + 1} failed, trying fallback...", "yellow")
                # Get next fallback
                current_config = get_fallback_model(phase, thread_id)
                time.sleep(2)  # Brief delay before retry
            else:
                # All attempts exhausted
                with console_lock:
                    cprint(f"[T{thread_id:02d}] ❌ All model attempts failed for {phase}", "red", attrs=['bold'])
                raise ValueError(f"🚨 Could not initialize any model for {phase} after {max_attempts} attempts!")

    raise ValueError(f"🚨 Exhausted all model attempts for {phase}!")

def clean_model_output(output, content_type="text"):
    """Clean model output by removing thinking tags and extracting code from markdown"""
    cleaned_output = output

    if "<think>" in output and "</think>" in output:
        clean_content = output.split("</think>")[-1].strip()
        if not clean_content:
            import re
            clean_content = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL).strip()
        if clean_content:
            cleaned_output = clean_content

    if content_type == "code" and "```" in cleaned_output:
        try:
            import re
            # Try to extract code blocks with closing ```
            code_blocks = re.findall(r'```python\n(.*?)\n```', cleaned_output, re.DOTALL)
            if not code_blocks:
                code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', cleaned_output, re.DOTALL)

            # If no complete blocks found, try extracting from opening fence to end
            if not code_blocks:
                # Handle case where code starts with ```python but no closing ```
                match = re.search(r'```(?:python)?\s*\n(.*)', cleaned_output, re.DOTALL)
                if match:
                    cleaned_output = match.group(1).strip()
                    # Remove any trailing ``` if present
                    if cleaned_output.endswith('```'):
                        cleaned_output = cleaned_output[:-3].strip()
            else:
                cleaned_output = "\n\n".join(code_blocks)
        except Exception as e:
            thread_print(f"❌ Error extracting code: {str(e)}", 0, "red")

    # 🌙 Moon Dev: Final cleanup - strip any remaining markdown fences
    if content_type == "code":
        cleaned_output = cleaned_output.replace('```python', '').replace('```', '').strip()

    return cleaned_output

# ============================================
# 🤖 AI AGENT FUNCTIONS (Thread-safe versions)
# ============================================

def research_strategy(content, thread_id):
    """Research AI: Analyzes and creates trading strategy"""
    thread_print_status(thread_id, "🔍 RESEARCH", "Starting analysis...")

    output = chat_with_model(
        RESEARCH_PROMPT,
        content,
        RESEARCH_CONFIG,
        thread_id,
        phase="research"
    )

    if output:
        output = clean_model_output(output, "text")

        strategy_name = "UnknownStrategy"
        if "STRATEGY_NAME:" in output:
            try:
                name_section = output.split("STRATEGY_NAME:")[1].strip()
                if "\n\n" in name_section:
                    strategy_name = name_section.split("\n\n")[0].strip()
                else:
                    strategy_name = name_section.split("\n")[0].strip()

                strategy_name = re.sub(r'[^\w\s-]', '', strategy_name)
                strategy_name = re.sub(r'[\s]+', '', strategy_name)

                thread_print(f"✅ Strategy: {strategy_name}", thread_id, "green")
            except Exception as e:
                thread_print(f"⚠️ Error extracting strategy name: {str(e)}", thread_id, "yellow")

        # Add thread ID to filename
        filepath = RESEARCH_DIR / f"T{thread_id:02d}_{strategy_name}_strategy.txt"
        with file_lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)

        return output, strategy_name
    return None, None

def create_backtest(strategy, strategy_name, thread_id):
    """Backtest AI: Creates backtest implementation"""
    thread_print_status(thread_id, "📊 BACKTEST", "Creating backtest code...")

    # Select model based on thread ID to distribute load
    model_config = BACKTEST_MODELS[thread_id % len(BACKTEST_MODELS)]
    thread_print(f"Using model: {model_config['type']}/{model_config['name']}", thread_id)

    output = chat_with_model(
        BACKTEST_PROMPT,
        f"Create a backtest for this strategy:\n\n{strategy}",
        model_config,
        thread_id,
        phase="backtest"
    )

    if output:
        output = clean_model_output(output, "code")

        filepath = BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_BT.py"
        with file_lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)

        thread_print(f"🔥 Backtest code saved", thread_id, "green")
        return output
    return None

def package_check(backtest_code, strategy_name, thread_id):
    """Package AI: Ensures correct indicator packages are used"""
    thread_print_status(thread_id, "📦 PACKAGE", "Checking imports...")

    output = chat_with_model(
        PACKAGE_PROMPT,
        f"Check and fix indicator packages in this code:\n\n{backtest_code}",
        PACKAGE_CONFIG,
        thread_id,
        phase="debug"
    )

    if output:
        output = clean_model_output(output, "code")

        filepath = PACKAGE_DIR / f"T{thread_id:02d}_{strategy_name}_PKG.py"
        with file_lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)

        thread_print(f"📦 Package check complete", thread_id, "green")
        return output
    return None

def select_debug_model(thread_id, debug_iteration, error_message=""):
    """
    Strategically select debug model based on iteration.
    Use GPT-4o ONLY for final attempts (iterations 8-10) to maximize success rate
    while staying under rate limits.
    """
    # Strategic GPT-4o usage: Only for final attempts when other models have failed
    if debug_iteration >= 8 and debug_iteration <= 10:
        # Check rate limit safety (simple time-based throttle)
        if hasattr(select_debug_model, 'last_gpt4o_time'):
            time_since = time.time() - select_debug_model.last_gpt4o_time
            if time_since < 2.0:  # Max 30 calls/min = 1 every 2 seconds
                # Too soon, use default Grok instead
                thread_print(f"⏰ GPT-4o rate limit protection, using Grok", thread_id, "yellow")
                return DEBUG_MODELS[thread_id % len(DEBUG_MODELS)]

        # Safe to use GPT-4o for this critical intervention
        select_debug_model.last_gpt4o_time = time.time()
        thread_print(f"🎯 Using GPT-4o for critical debug (iteration {debug_iteration}) - last resort", thread_id, "yellow", ["bold"])
        return {"type": "openai", "name": "gpt-4o"}

    # Check for critical errors that might benefit from GPT-4o earlier (but still after iteration 5)
    critical_errors = [
        "ImportError: cannot import",
        "AttributeError: 'NoneType'",
        "KeyError:",
        "NameError: name",
        "No trades taken"
    ]

    if debug_iteration >= 6 and any(err in str(error_message) for err in critical_errors):
        # Complex error that might benefit from GPT-4o
        if hasattr(select_debug_model, 'critical_gpt4o_count'):
            if select_debug_model.critical_gpt4o_count < 3:  # Limit critical interventions
                select_debug_model.critical_gpt4o_count += 1
                thread_print(f"🔍 Using GPT-4o for critical error (iteration {debug_iteration})", thread_id, "yellow")
                return {"type": "openai", "name": "gpt-4o"}
        else:
            select_debug_model.critical_gpt4o_count = 1

    # Default: Use configured model (Grok) for normal debugging
    model_index = thread_id % len(DEBUG_MODELS)
    return DEBUG_MODELS[model_index]

def debug_backtest(backtest_code, error_message, strategy_name, thread_id, iteration=1, stats=None):
    """Debug AI: Fixes technical issues in backtest code"""
    thread_print_status(thread_id, f"🔧 DEBUG #{iteration}", "Fixing errors...")

    # Strategic model selection based on iteration and error type
    model_config = select_debug_model(thread_id, iteration, error_message)
    thread_print(f"Debug with: {model_config['type']}/{model_config['name']}", thread_id)

    # Extract performance metrics for debug AI guidance
    current_return = stats.get('return_pct', 0) if stats else 0
    num_trades = stats.get('trades', 0) if stats else 0

    debug_prompt_with_error = DEBUG_PROMPT.format(
        error_message=error_message,
        current_return=current_return,
        num_trades=num_trades
    )

    output = chat_with_model(
        debug_prompt_with_error,
        f"Fix this backtest code:\n\n{backtest_code}",
        model_config,
        thread_id,
        phase="debug"
    )

    if output:
        output = clean_model_output(output, "code")

        # 🌙 Moon Dev: Save debug iterations to BACKTEST_DIR, not FINAL
        # Only threshold-passing backtests go to FINAL/WORKING folders!
        filepath = BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_DEBUG_v{iteration}.py"
        with file_lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)

        thread_print(f"🔧 Debug iteration {iteration} complete", thread_id, "green")
        return output
    return None

def optimize_strategy(backtest_code, current_return, target_return, strategy_name, thread_id, iteration=1):
    """Optimization AI: Improves strategy to hit target return"""
    thread_print_status(thread_id, f"🎯 OPTIMIZE #{iteration}", f"{current_return}% → {target_return}%")

    # Rotate through optimize models to distribute load
    model_index = (thread_id + iteration) % len(OPTIMIZE_MODELS)
    model_config = OPTIMIZE_MODELS[model_index]
    thread_print(f"Optimize with: {model_config['type']}/{model_config['name']}", thread_id)

    optimize_prompt_with_stats = OPTIMIZE_PROMPT.format(
        current_return=current_return,
        target_return=target_return
    )

    output = chat_with_model(
        optimize_prompt_with_stats,
        f"Optimize this backtest code to hit the target:\n\n{backtest_code}",
        model_config,
        thread_id,
        phase="optimize"
    )

    if output:
        output = clean_model_output(output, "code")

        filepath = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_OPT_v{iteration}.py"
        with file_lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)

        thread_print(f"🎯 Optimization {iteration} complete", thread_id, "green")
        return output
    return None

# ============================================
# 🚀 PARALLEL PROCESSING CORE
# ============================================

def process_trading_idea_parallel(idea: str, thread_id: int) -> dict:
    """
    Process a single trading idea with full Research → Backtest → Debug → Optimize pipeline
    This is the worker function for each parallel thread
    """
    try:
        # 🌙 Moon Dev: Check if date has changed and update folders!
        update_date_folders()

        thread_print(f"🚀 Starting processing", thread_id, attrs=['bold'])

        # 🌙 Moon Dev: Extract content from PDF/YouTube if URL provided
        processed_idea = extract_content_from_url(idea, thread_id)

        # Phase 1: Research
        strategy, strategy_name = research_strategy(processed_idea, thread_id)

        if not strategy:
            thread_print("❌ Research failed", thread_id, "red")
            return {"success": False, "error": "Research failed", "thread_id": thread_id}

        log_processed_idea(idea, strategy_name, thread_id)

        # Phase 2: Backtest
        backtest = create_backtest(strategy, strategy_name, thread_id)

        if not backtest:
            thread_print("❌ Backtest failed", thread_id, "red")
            return {"success": False, "error": "Backtest failed", "thread_id": thread_id}

        # Phase 3: Package Check
        package_checked = package_check(backtest, strategy_name, thread_id)

        if not package_checked:
            thread_print("❌ Package check failed", thread_id, "red")
            return {"success": False, "error": "Package check failed", "thread_id": thread_id}

        package_file = PACKAGE_DIR / f"T{thread_id:02d}_{strategy_name}_PKG.py"

        # Phase 4: Execution Loop
        debug_iteration = 0
        current_code = package_checked
        current_file = package_file
        error_history = []

        while debug_iteration < MAX_DEBUG_ITERATIONS:
            thread_print_status(thread_id, "🚀 EXECUTE", f"Attempt {debug_iteration + 1}/{MAX_DEBUG_ITERATIONS}")

            execution_result = execute_backtest(current_file, strategy_name, thread_id)

            if execution_result['success']:
                if has_nan_results(execution_result):
                    thread_print("⚠️ No trades taken", thread_id, "yellow")

                    # Parse stats even for failed backtests to help debug AI
                    all_stats = parse_all_stats_from_output(execution_result['stdout'], thread_id)

                    error_message = analyze_no_trades_issue(execution_result)
                    debug_iteration += 1

                    if debug_iteration < MAX_DEBUG_ITERATIONS:
                        debugged_code = debug_backtest(
                            current_code,
                            error_message,
                            strategy_name,
                            thread_id,
                            debug_iteration,
                            stats=all_stats  # Pass stats to help debug AI improve logic
                        )

                        if not debugged_code:
                            thread_print("❌ Debug AI failed", thread_id, "red")
                            return {"success": False, "error": "Debug failed", "thread_id": thread_id}

                        current_code = debugged_code
                        # 🌙 Moon Dev: Update to match new debug file location
                        current_file = BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_DEBUG_v{debug_iteration}.py"
                        continue
                    else:
                        thread_print(f"❌ Max debug iterations reached", thread_id, "red")
                        return {"success": False, "error": "Max debug iterations", "thread_id": thread_id}
                else:
                    # SUCCESS! Code executes with trades!
                    thread_print("🎉 BACKTEST SUCCESSFUL!", thread_id, "green", attrs=['bold'])

                    # 🌙 Moon Dev: Parse ALL stats, not just return!
                    all_stats = parse_all_stats_from_output(execution_result['stdout'], thread_id)
                    current_return = all_stats.get('return_pct')

                    if current_return is None:
                        thread_print("⚠️ Could not parse return", thread_id, "yellow")
                        final_file = FINAL_BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_BTFinal_WORKING.py"
                        with file_lock:
                            with open(final_file, 'w', encoding='utf-8') as f:
                                f.write(current_code)
                        break

                    # 🌙 Moon Dev: Check threshold and save if met!
                    save_backtest_if_threshold_met(
                        current_code,
                        all_stats,
                        strategy_name,
                        debug_iteration,
                        thread_id,
                        phase="debug"
                    )

                    # 🌙 Moon Dev: Parse and log multi-data results!
                    thread_print("🔍 Checking for multi-data test results...", thread_id, "cyan")
                    multi_data_results = parse_and_log_multi_data_results(
                        strategy_name,
                        thread_id,
                        current_file
                    )

                    thread_print(f"📊 15m Return: {current_return}% | Target: {TARGET_RETURN}%", thread_id)

                    # Check if target hit on 15m OR any multi-data timeframe
                    target_hit_15m = current_return >= TARGET_RETURN
                    target_hit_multi = multi_data_results.get('target_hit', False)
                    best_multi_return = multi_data_results.get('best_return', 0)
                    best_multi_timeframe = multi_data_results.get('best_timeframe', None)

                    if target_hit_15m or target_hit_multi:
                        # TARGET HIT!
                        if target_hit_15m:
                            thread_print(f"🚀🚀🚀 TARGET HIT ON 15M! {current_return}% 🚀🚀🚀", thread_id, "green", attrs=['bold'])
                            hit_return = current_return
                            hit_timeframe = "BTC-15m"
                        else:
                            thread_print(f"🚀🚀🚀 TARGET HIT ON {best_multi_timeframe}! {best_multi_return}% 🚀🚀🚀", thread_id, "green", attrs=['bold'])
                            hit_return = best_multi_return
                            hit_timeframe = best_multi_timeframe

                        # 🌙 Moon Dev: Save to OPTIMIZATION_DIR for target hits
                        final_file = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_TARGET_HIT_{hit_return}pct_{hit_timeframe}.py"
                        with file_lock:
                            with open(final_file, 'w', encoding='utf-8') as f:
                                f.write(current_code)

                        return {
                            "success": True,
                            "thread_id": thread_id,
                            "strategy_name": strategy_name,
                            "return": current_return,
                            "target_hit": True
                        }
                    else:
                        # Need to optimize
                        gap = TARGET_RETURN - current_return
                        thread_print(f"📈 Need {gap}% more - Starting optimization", thread_id)

                        optimization_iteration = 0
                        optimization_code = current_code
                        best_return = current_return
                        best_code = current_code

                        while optimization_iteration < MAX_OPTIMIZATION_ITERATIONS:
                            optimization_iteration += 1

                            optimized_code = optimize_strategy(
                                optimization_code,
                                best_return,
                                TARGET_RETURN,
                                strategy_name,
                                thread_id,
                                optimization_iteration
                            )

                            if not optimized_code:
                                thread_print("❌ Optimization AI failed", thread_id, "red")
                                break

                            opt_file = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_OPT_v{optimization_iteration}.py"
                            opt_result = execute_backtest(opt_file, strategy_name, thread_id)

                            if not opt_result['success'] or has_nan_results(opt_result):
                                thread_print(f"⚠️ Optimization {optimization_iteration} failed", thread_id, "yellow")
                                continue

                            # 🌙 Moon Dev: Parse ALL stats from optimization!
                            opt_stats = parse_all_stats_from_output(opt_result['stdout'], thread_id)
                            new_return = opt_stats.get('return_pct')

                            if new_return is None:
                                continue

                            change = new_return - best_return
                            thread_print(f"📊 Opt {optimization_iteration}: {new_return}% ({change:+.2f}%)", thread_id)

                            if new_return > best_return:
                                thread_print(f"✅ Improved by {change:.2f}%!", thread_id, "green")
                                best_return = new_return
                                best_code = optimized_code
                                optimization_code = optimized_code

                                # 🌙 Moon Dev: Check threshold and save if met!
                                save_backtest_if_threshold_met(
                                    optimized_code,
                                    opt_stats,
                                    strategy_name,
                                    optimization_iteration,
                                    thread_id,
                                    phase="opt"
                                )

                                # 🌙 Moon Dev: Parse and log multi-data results from optimization!
                                thread_print("🔍 Checking for multi-data test results...", thread_id, "cyan")
                                multi_data_results = parse_and_log_multi_data_results(
                                    strategy_name,
                                    thread_id,
                                    opt_file
                                )

                                # Check if target hit on 15m OR any multi-data timeframe
                                target_hit_15m = new_return >= TARGET_RETURN
                                target_hit_multi = multi_data_results.get('target_hit', False)
                                best_multi_return = multi_data_results.get('best_return', 0)
                                best_multi_timeframe = multi_data_results.get('best_timeframe', None)

                                if target_hit_15m or target_hit_multi:
                                    # TARGET HIT!
                                    if target_hit_15m:
                                        thread_print(f"🚀🚀🚀 TARGET HIT VIA OPTIMIZATION ON 15M! {new_return}% 🚀🚀🚀", thread_id, "green", attrs=['bold'])
                                        hit_return = new_return
                                        hit_timeframe = "BTC-15m"
                                    else:
                                        thread_print(f"🚀🚀🚀 TARGET HIT VIA OPTIMIZATION ON {best_multi_timeframe}! {best_multi_return}% 🚀🚀🚀", thread_id, "green", attrs=['bold'])
                                        hit_return = best_multi_return
                                        hit_timeframe = best_multi_timeframe

                                    final_file = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_TARGET_HIT_{hit_return}pct_{hit_timeframe}.py"
                                    with file_lock:
                                        with open(final_file, 'w', encoding='utf-8') as f:
                                            f.write(best_code)

                                    return {
                                        "success": True,
                                        "thread_id": thread_id,
                                        "strategy_name": strategy_name,
                                        "return": hit_return,
                                        "timeframe": hit_timeframe,
                                        "target_hit": True,
                                        "optimizations": optimization_iteration
                                    }

                        # Max optimization iterations reached
                        thread_print(f"⚠️ Max optimizations reached. Best: {best_return}%", thread_id, "yellow")

                        best_file = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_BEST_{best_return}pct.py"
                        with file_lock:
                            with open(best_file, 'w', encoding='utf-8') as f:
                                f.write(best_code)

                        return {
                            "success": True,
                            "thread_id": thread_id,
                            "strategy_name": strategy_name,
                            "return": best_return,
                            "target_hit": False
                        }
            else:
                # Execution failed
                error_message = parse_execution_error(execution_result)

                error_signature = error_message.split('\n')[-1] if '\n' in error_message else error_message
                if error_signature in error_history:
                    thread_print(f"🔄 Repeated error detected - stopping", thread_id, "red")
                    return {"success": False, "error": "Repeated error", "thread_id": thread_id}

                error_history.append(error_signature)
                debug_iteration += 1

                if debug_iteration < MAX_DEBUG_ITERATIONS:
                    debugged_code = debug_backtest(
                        current_code,
                        error_message,
                        strategy_name,
                        thread_id,
                        debug_iteration
                    )

                    if not debugged_code:
                        thread_print("❌ Debug AI failed", thread_id, "red")
                        return {"success": False, "error": "Debug failed", "thread_id": thread_id}

                    current_code = debugged_code
                    # 🌙 Moon Dev: Update to match new debug file location
                    current_file = BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_DEBUG_v{debug_iteration}.py"
                else:
                    thread_print(f"❌ Max debug iterations reached", thread_id, "red")
                    return {"success": False, "error": "Max debug iterations", "thread_id": thread_id}

        return {"success": True, "thread_id": thread_id}

    except Exception as e:
        thread_print(f"❌ FATAL ERROR: {str(e)}", thread_id, "red", attrs=['bold'])
        return {"success": False, "error": str(e), "thread_id": thread_id}

def get_strategies_from_files():
    """🌙 Moon Dev: Read all .md and .txt files from STRATEGIES_FOLDER"""
    strategies = []
    folder_path = Path(STRATEGIES_FOLDER)

    if not folder_path.exists():
        return strategies

    # Get all .md and .txt files
    for file_path in folder_path.glob('*'):
        if file_path.suffix.lower() in ['.md', '.txt']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # Only add non-empty files
                        strategies.append(content)
            except Exception as e:
                with console_lock:
                    cprint(f"⚠️ Error reading {file_path.name}: {str(e)}", "yellow")

    return strategies


def idea_monitor_thread(idea_queue: Queue, queued_ideas: set, queued_lock: Lock, stop_flag: dict):
    """🌙 Moon Dev: Producer thread - monitors BOTH ideas.txt AND strategy files"""
    global IDEAS_FILE

    while not stop_flag.get('stop', False):
        try:
            ideas = []

            # 🌙 Moon Dev: DUAL MODE - Check BOTH sources!
            # Priority 1: Check for pre-researched strategies if enabled
            if STRATEGIES_FROM_FILES:
                strategy_ideas = get_strategies_from_files()
                if strategy_ideas:
                    with console_lock:
                        cprint(f"📁 Found {len(strategy_ideas)} pre-researched strategies", "cyan")
                    ideas.extend(strategy_ideas)

            # Priority 2: ALWAYS check ideas.txt for raw ideas
            if IDEAS_FILE.exists():
                try:
                    with open(IDEAS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_ideas = [line.strip() for line in f if line.strip() and not line.startswith('#')]

                    if raw_ideas:
                        with console_lock:
                            cprint(f"💡 Found {len(raw_ideas)} raw ideas in ideas.txt", "yellow")
                        ideas.extend(raw_ideas)
                except Exception as e:
                    with console_lock:
                        cprint(f"⚠️ Error reading ideas.txt: {str(e)}", "yellow")

            # If no ideas from either source, wait and retry
            if not ideas:
                time.sleep(1)
                continue

            # Find new unprocessed ideas
            for idea in ideas:
                idea_hash = get_idea_hash(idea)

                # Check if not processed AND not already queued (thread-safe)
                with queued_lock:
                    already_queued = idea_hash in queued_ideas

                if not is_idea_processed(idea) and not already_queued:
                    idea_queue.put(idea)
                    with queued_lock:
                        queued_ideas.add(idea_hash)
                    with console_lock:
                        cprint(f"🆕 NEW IDEA QUEUED: {idea[:80]}...", "green", attrs=['bold'])

            time.sleep(1)  # Check every 1 second

        except Exception as e:
            with console_lock:
                cprint(f"❌ Monitor thread error: {str(e)}", "red")
            time.sleep(1)


def worker_thread(worker_id: int, idea_queue: Queue, queued_ideas: set, queued_lock: Lock, stats: dict, stop_flag: dict):
    """🌙 Moon Dev: Consumer thread - processes ideas from queue"""
    while not stop_flag.get('stop', False):
        try:
            # Get idea from queue (timeout 1 second to check stop_flag periodically)
            try:
                idea = idea_queue.get(timeout=1)
            except:
                continue  # Queue empty, check again

            with console_lock:
                stats['active'] += 1
                cprint(f"\n🚀 Thread {worker_id:02d} starting: {idea[:80]}...", "cyan")

            # Process the idea
            start_time = datetime.now()
            result = process_trading_idea_parallel(idea, worker_id)
            total_time = (datetime.now() - start_time).total_seconds()

            # Remove from queued set when done (thread-safe)
            idea_hash = get_idea_hash(idea)
            with queued_lock:
                if idea_hash in queued_ideas:
                    queued_ideas.remove(idea_hash)

            # Update stats
            with console_lock:
                stats['completed'] += 1
                stats['active'] -= 1

                cprint(f"\n{'='*60}", "green")
                cprint(f"✅ Thread {worker_id:02d} COMPLETED ({stats['completed']} total) - {total_time:.1f}s", "green", attrs=['bold'])
                if result.get('success'):
                    stats['successful'] += 1
                    if result.get('target_hit'):
                        stats['targets_hit'] += 1
                        cprint(f"🎯 TARGET HIT: {result.get('strategy_name')} @ {result.get('return')}%", "green", attrs=['bold'])
                    else:
                        cprint(f"📊 Best return: {result.get('return', 'N/A')}%", "yellow")
                else:
                    stats['failed'] += 1
                    cprint(f"❌ Failed: {result.get('error', 'Unknown error')}", "red")
                cprint(f"{'='*60}\n", "green")

            idea_queue.task_done()

        except Exception as e:
            with console_lock:
                cprint(f"\n❌ Worker thread {worker_id:02d} error: {str(e)}", "red", attrs=['bold'])


def main(ideas_file_path=None, run_name=None):
    """Main parallel processing orchestrator with multi-data testing - CONTINUOUS QUEUE MODE"""
    # 🌙 Moon Dev: Use custom ideas file if provided
    global IDEAS_FILE
    if ideas_file_path:
        IDEAS_FILE = Path(ideas_file_path)

    cprint(f"\n{'='*60}", "cyan", attrs=['bold'])
    cprint(f"🌟 Moon Dev's RBI AI v3.0 PARALLEL PROCESSOR + MULTI-DATA 🚀", "cyan", attrs=['bold'])
    cprint(f"{'='*60}", "cyan", attrs=['bold'])

    cprint(f"\n📅 Date: {CURRENT_DATE}", "magenta")
    cprint(f"🎯 Target Return: {TARGET_RETURN}%", "green", attrs=['bold'])
    cprint(f"🔀 Max Parallel Threads: {MAX_PARALLEL_THREADS}", "yellow", attrs=['bold'])
    cprint(f"🐍 Conda env: {CONDA_ENV}", "cyan")
    cprint(f"📂 Data dir: {DATA_DIR}", "magenta")
    cprint(f"📝 Ideas file: {IDEAS_FILE}", "magenta")
    if run_name:
        cprint(f"📁 Run Name: {run_name}\n", "green", attrs=['bold'])
    else:
        cprint("", "white")

    # 🌙 Moon Dev: Show VERY CLEAR configuration mode
    cprint(f"\n{'='*60}", "white", attrs=['bold'])
    if STRATEGIES_FROM_FILES:
        cprint(f"📁 STRATEGY SOURCE: FILES FROM FOLDER", "green", attrs=['bold'])
        cprint(f"📂 Folder: {STRATEGIES_FOLDER}", "yellow")
        # Count files
        folder_path = Path(STRATEGIES_FOLDER)
        if folder_path.exists():
            file_count = len([f for f in folder_path.glob('*') if f.suffix.lower() in ['.md', '.txt']])
            cprint(f"📊 Found {file_count} strategy files (.md/.txt)", "cyan", attrs=['bold'])
        else:
            cprint(f"⚠️  Folder does not exist yet!", "red")
    else:
        cprint(f"📝 STRATEGY SOURCE: ideas.txt (line by line)", "cyan", attrs=['bold'])
        cprint(f"📄 File: {IDEAS_FILE}", "yellow")
        cprint(f"💡 Classic mode - one strategy per line", "white")
    cprint(f"{'='*60}\n", "white", attrs=['bold'])

    # Create template if needed
    if not IDEAS_FILE.exists():
        cprint(f"❌ ideas.txt not found! Creating template...", "red")
        IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(IDEAS_FILE, 'w', encoding='utf-8') as f:
            f.write("# Add your trading ideas here (one per line)\n")
            f.write("# Can be YouTube URLs, PDF links, or text descriptions\n")
            f.write("# Lines starting with # are ignored\n\n")
            f.write("Create a simple RSI strategy that buys when RSI < 30 and sells when RSI > 70\n")
            f.write("Momentum strategy using 20/50 SMA crossover with volume confirmation\n")
        cprint(f"📝 Created template ideas.txt at: {IDEAS_FILE}", "yellow")

    # 🌙 Moon Dev: CONTINUOUS QUEUE MODE
    cprint(f"\n🔄 CONTINUOUS QUEUE MODE ACTIVATED", "cyan", attrs=['bold'])
    if STRATEGIES_FROM_FILES:
        cprint(f"⏰ Monitoring strategy files in folder every 1 second", "yellow")
    else:
        cprint(f"⏰ Monitoring ideas.txt every 1 second", "yellow")
    cprint(f"🧵 {MAX_PARALLEL_THREADS} worker threads ready\n", "yellow")

    # Shared queue, queued ideas set, and stats
    idea_queue = Queue()
    queued_ideas = set()  # Track which ideas are currently queued (by hash)
    queued_lock = Lock()  # Protect access to queued_ideas set
    stats = {
        'completed': 0,
        'successful': 0,
        'failed': 0,
        'targets_hit': 0,
        'active': 0
    }
    stop_flag = {'stop': False}

    # Start monitor thread (producer)
    monitor = Thread(target=idea_monitor_thread, args=(idea_queue, queued_ideas, queued_lock, stop_flag), daemon=True)
    monitor.start()
    cprint("✅ Idea monitor thread started", "green")

    # Start worker threads (consumers)
    workers = []
    for worker_id in range(MAX_PARALLEL_THREADS):
        worker = Thread(target=worker_thread, args=(worker_id, idea_queue, queued_ideas, queued_lock, stats, stop_flag), daemon=True)
        worker.start()
        workers.append(worker)
    cprint(f"✅ {MAX_PARALLEL_THREADS} worker threads started (IDs 00-{MAX_PARALLEL_THREADS-1:02d})\n", "green")

    # Main thread just monitors stats and waits
    try:
        while True:
            time.sleep(5)  # Status update every 5 seconds

            # 🌙 Moon Dev: Check for date changes periodically (even when idle!)
            update_date_folders()

            with console_lock:
                if stats['active'] > 0 or not idea_queue.empty():
                    cprint(f"📊 Status: {stats['active']} active | {idea_queue.qsize()} queued | {stats['completed']} completed | {stats['targets_hit']} targets hit", "cyan")
                else:
                    cprint(f"💤 AI swarm waiting... ({stats['completed']} total completed, {stats['targets_hit']} targets hit) - {datetime.now().strftime('%I:%M:%S %p')}", "yellow")

    except KeyboardInterrupt:
        cprint(f"\n\n🛑 Shutting down gracefully...", "yellow", attrs=['bold'])
        stop_flag['stop'] = True

        cprint(f"\n{'='*60}", "cyan", attrs=['bold'])
        cprint(f"📊 FINAL STATS", "cyan", attrs=['bold'])
        cprint(f"{'='*60}", "cyan", attrs=['bold'])
        cprint(f"✅ Successful: {stats['successful']}", "green")
        cprint(f"🎯 Targets hit: {stats['targets_hit']}", "green", attrs=['bold'])
        cprint(f"❌ Failed: {stats['failed']}", "red")
        cprint(f"📊 Total completed: {stats['completed']}", "cyan")
        cprint(f"{'='*60}\n", "cyan", attrs=['bold'])

if __name__ == "__main__":
    # 🌙 Moon Dev: Parse command-line arguments for custom ideas file and run name
    parser = argparse.ArgumentParser(description="Moon Dev's RBI Agent - Parallel Backtest Processor")
    parser.add_argument('--ideas-file', type=str, help='Custom ideas file path (overrides default ideas.txt)')
    parser.add_argument('--run-name', type=str, help='Run name for folder organization')
    args = parser.parse_args()

    # Call main with optional parameters
    main(ideas_file_path=args.ideas_file, run_name=args.run_name)
