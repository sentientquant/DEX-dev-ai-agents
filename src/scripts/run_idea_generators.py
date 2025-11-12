'''
🌙 Moon Dev's Idea Generator Orchestrator 🌙
Runs multiple idea-generation agents concurrently

This script runs IDEA GENERATORS ONLY (not RBI processor):
- Research Agent (AI-generated ideas)
- WebSearch Agent (web-scraped strategies)

RBI Agent should be run SEPARATELY to process the generated ideas.

Usage:
    python src/scripts/run_idea_generators.py

Created with ❤️ by Moon Dev
'''

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from termcolor import cprint

# Set UTF-8 encoding for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESEARCH_AGENT = PROJECT_ROOT / "src" / "agents" / "research_agent.py"
WEBSEARCH_AGENT = PROJECT_ROOT / "src" / "agents" / "websearch_agent.py"

# Configuration
ENABLE_RESEARCH_AGENT = True  # AI-generated ideas
ENABLE_WEBSEARCH_AGENT = True  # Web-scraped strategies
RESTART_ON_CRASH = True  # Auto-restart agents if they crash
MONITOR_INTERVAL = 5  # Seconds between status checks

# Agent processes
agent_processes = {}
agent_threads = {}
running = True


def print_banner():
    """Print startup banner"""
    banner = """
    ═══════════════════════════════════════════════════════════
    🌙 MOON DEV'S IDEA GENERATOR ORCHESTRATOR 🌙
    ═══════════════════════════════════════════════════════════

    This orchestrator runs IDEA GENERATORS only:
    - Research Agent (AI-generated ideas)
    - WebSearch Agent (web-scraped strategies)

    ⚠️  IMPORTANT: Run RBI Agent SEPARATELY to process ideas!

    ═══════════════════════════════════════════════════════════
    """
    cprint(banner, "yellow")


def run_agent(name, script_path):
    """
    Run a single agent in a subprocess

    Args:
        name: Agent name
        script_path: Path to agent script
    """
    global running

    while running:
        try:
            cprint(f"\n🚀 Starting {name}...", "green")

            # Start agent process with UTF-8 encoding
            # Set PYTHONIOENCODING to force UTF-8 in subprocess
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 chars instead of crashing
                bufsize=1,
                env=env  # Pass environment with UTF-8 encoding
            )

            agent_processes[name] = process

            # Stream output
            for line in process.stdout:
                if not running:
                    break
                print(f"[{name}] {line.rstrip()}")

            # Check exit code
            exit_code = process.wait()

            if exit_code != 0 and running:
                cprint(f"\n⚠️  {name} crashed with exit code {exit_code}", "red")

                if RESTART_ON_CRASH:
                    cprint(f"🔄 Restarting {name} in 5 seconds...", "yellow")
                    time.sleep(5)
                else:
                    break
            else:
                break

        except Exception as e:
            cprint(f"\n❌ Error running {name}: {e}", "red")

            if RESTART_ON_CRASH and running:
                cprint(f"🔄 Restarting {name} in 5 seconds...", "yellow")
                time.sleep(5)
            else:
                break

    cprint(f"\n🛑 {name} stopped", "yellow")


def monitor_agents():
    """Monitor agent status and print statistics"""
    global running

    while running:
        try:
            time.sleep(MONITOR_INTERVAL)

            # Check agent status
            statuses = []
            for name, process in agent_processes.items():
                if process and process.poll() is None:
                    statuses.append(f"{name}: ✅ Running")
                else:
                    statuses.append(f"{name}: ❌ Stopped")

            # Print status (only if agents are running)
            if statuses:
                timestamp = datetime.now().strftime("%H:%M:%S")
                cprint(f"\n[{timestamp}] Agent Status: {' | '.join(statuses)}", "cyan")

        except Exception as e:
            cprint(f"⚠️  Monitor error: {e}", "yellow")


def shutdown():
    """Gracefully shutdown all agents"""
    global running
    running = False

    cprint("\n\n🛑 Shutting down all agents...", "yellow")

    # Terminate all processes
    for name, process in agent_processes.items():
        if process and process.poll() is None:
            cprint(f"   Stopping {name}...", "yellow")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cprint(f"   Force killing {name}...", "red")
                process.kill()

    cprint("\n✅ All agents stopped", "green")


def main():
    """Main orchestrator function"""
    global running

    print_banner()

    # Check agent files exist
    if ENABLE_RESEARCH_AGENT and not RESEARCH_AGENT.exists():
        cprint(f"❌ Research Agent not found: {RESEARCH_AGENT}", "red")
        return

    if ENABLE_WEBSEARCH_AGENT and not WEBSEARCH_AGENT.exists():
        cprint(f"❌ WebSearch Agent not found: {WEBSEARCH_AGENT}", "red")
        return

    # Show configuration
    cprint("\n📋 Configuration:", "cyan")
    cprint(f"   Research Agent: {'✅ Enabled' if ENABLE_RESEARCH_AGENT else '❌ Disabled'}", "white")
    cprint(f"   WebSearch Agent: {'✅ Enabled' if ENABLE_WEBSEARCH_AGENT else '❌ Disabled'}", "white")
    cprint(f"   Auto-restart: {'✅ Enabled' if RESTART_ON_CRASH else '❌ Disabled'}", "white")

    try:
        # Start agent threads
        if ENABLE_RESEARCH_AGENT:
            thread = threading.Thread(
                target=run_agent,
                args=("Research Agent", RESEARCH_AGENT),
                daemon=True
            )
            thread.start()
            agent_threads["Research Agent"] = thread
            time.sleep(2)  # Stagger starts

        if ENABLE_WEBSEARCH_AGENT:
            thread = threading.Thread(
                target=run_agent,
                args=("WebSearch Agent", WEBSEARCH_AGENT),
                daemon=True
            )
            thread.start()
            agent_threads["WebSearch Agent"] = thread

        # Start monitor thread
        monitor_thread = threading.Thread(target=monitor_agents, daemon=True)
        monitor_thread.start()

        cprint("\n\n🎉 All agents started! Press Ctrl+C to stop.\n", "green")

        # Keep main thread alive
        while running:
            time.sleep(1)

    except KeyboardInterrupt:
        cprint("\n\n⚠️  Keyboard interrupt received", "yellow")
        shutdown()
    except Exception as e:
        cprint(f"\n\n❌ Fatal error: {e}", "red")
        shutdown()


if __name__ == "__main__":
    main()
