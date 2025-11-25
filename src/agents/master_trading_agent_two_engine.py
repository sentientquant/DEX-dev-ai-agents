"""
MASTER TRADING AGENT - TWO-ENGINE SYSTEM
Orchestrates Volume Intelligence + Funding Rate Positioning

Built by Moon Dev - Evidence-based multi-agent intelligence
Research shows: 2 low-correlation engines (r=0.35) outperform 5+ agent swarms

Workflow:
1. Run volume_agent_enhanced.py (ENGINE 1) every 15 minutes
2. Run funding_agent.py (ENGINE 2) every 15 minutes
3. Fuse signals using fusion_layer.py
4. Execute trades on STRONG_BUY/STRONG_SELL signals (confidence >= 80%)
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict
# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Add to path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows Unicode
from src.utils.windows_unicode_fix import fix_windows_unicode
fix_windows_unicode()

# Import fusion layer and config
from src.agents.fusion_layer import TwoEngineFusion
from src import config

# Configuration (from config.py for centralized control)
SYMBOLS = config.HYPERLIQUID_SYMBOLS  # Trading symbols from config
CHECK_INTERVAL_MINUTES = config.TRADING_INTERVAL_MINUTES  # Configurable interval
MAX_AGENT_RUNTIME_SECONDS = 180  # 3 minutes per agent timeout
EXECUTE_TRADES = config.EXECUTE_TRADES  # SAFETY: Controlled in config.py

# Agent scripts (only 2 engines)
VOLUME_AGENT = PROJECT_ROOT / 'src' / 'agents' / 'volume_agent_enhanced.py'
FUNDING_AGENT = PROJECT_ROOT / 'test_funding_signals.py'  # Using test script for now


def run_agent(agent_name: str, script_path: Path) -> Dict:
    """
    Run an agent as a subprocess with timeout

    Returns:
        {'success': bool, 'runtime': float, 'error': str or None}
    """
    start_time = time.time()

    try:
        cprint(f"  [{agent_name:15}] Starting...", "cyan")

        # Run agent script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            timeout=MAX_AGENT_RUNTIME_SECONDS,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'  # Handle Unicode errors gracefully
        )

        runtime = time.time() - start_time

        if result.returncode == 0:
            cprint(f"  [{agent_name:15}] [OK] Complete ({runtime:.1f}s)", "green")
            return {'success': True, 'runtime': runtime, 'error': None}
        else:
            error_msg = result.stderr[-200:] if result.stderr else "Unknown error"
            cprint(f"  [{agent_name:15}] [ERROR] Failed: {error_msg[:80]}", "red")
            return {'success': False, 'runtime': runtime, 'error': error_msg}

    except subprocess.TimeoutExpired:
        runtime = time.time() - start_time
        cprint(f"  [{agent_name:15}] [TIMEOUT] After {runtime:.0f}s", "yellow")
        return {'success': False, 'runtime': runtime, 'error': 'Timeout'}

    except Exception as e:
        runtime = time.time() - start_time
        cprint(f"  [{agent_name:15}] [ERROR] {str(e)[:100]}", "red")
        return {'success': False, 'runtime': runtime, 'error': str(e)}


def execute_trade(symbol: str, action: str, confidence: int, reasoning: str):
    """
    Execute a trade based on fused signal

    Args:
        symbol: Trading symbol (BTC, ETH, SOL)
        action: STRONG_BUY, STRONG_SELL, etc.
        confidence: 0-100
        reasoning: Human-readable explanation
    """
    if not EXECUTE_TRADES:
        cprint(f"  [TRADE] {symbol}: {action} ({confidence}%) - DRY RUN (trading disabled)", "yellow")
        cprint(f"          Reasoning: {reasoning}", "yellow")
        return

    # TODO: Integrate with actual trading functions from nice_funcs.py or nice_funcs_hyperliquid.py
    cprint(f"  [TRADE] {symbol}: {action} ({confidence}%)", "green" if 'BUY' in action else "red")
    cprint(f"          Reasoning: {reasoning}", "white")

    # Example integration (uncomment and modify for live trading):
    # from src import nice_funcs_hyperliquid as hl
    #
    # if action == 'STRONG_BUY' and confidence >= 80:
    #     # Execute buy order
    #     size = calculate_position_size(confidence)  # Scale by confidence
    #     hl.market_buy(symbol, size)
    #     cprint(f"  [EXEC] Bought {size} {symbol}", "green")
    #
    # elif action == 'STRONG_SELL' and confidence >= 80:
    #     # Execute sell order
    #     size = calculate_position_size(confidence)
    #     hl.market_sell(symbol, size)
    #     cprint(f"  [EXEC] Sold {size} {symbol}", "red")


def run_trading_cycle():
    """Run one complete trading cycle"""
    cycle_start = datetime.now()

    print("\n" + "="*80)
    cprint("MASTER TRADING AGENT - TWO-ENGINE SYSTEM", "cyan", attrs=['bold'])
    cprint(f"Cycle Start: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}", "white")
    print("="*80 + "\n")

    # STEP 1: Run both engines
    cprint("[STEP 1/4] Running intelligence engines...", "yellow", attrs=['bold'])

    results = {}

    # ENGINE 1: Volume Intelligence
    results['volume'] = run_agent('Volume Engine', VOLUME_AGENT)

    # ENGINE 2: Funding Intelligence
    results['funding'] = run_agent('Funding Engine', FUNDING_AGENT)

    # Summary
    successful = sum(1 for r in results.values() if r['success'])
    total_runtime = sum(r['runtime'] for r in results.values())

    cprint(f"\n  [SUMMARY] {successful}/2 engines successful ({total_runtime:.1f}s total)", "white")

    # STEP 2: Fuse signals
    cprint("\n[STEP 2/4] Fusing intelligence from both engines...", "yellow", attrs=['bold'])

    fusion = TwoEngineFusion()
    fused_results = fusion.fuse_all_symbols(SYMBOLS)

    # Save fused signals
    fusion.save_fused_signals(fused_results)

    # STEP 3: Analyze fused signals
    cprint("\n[STEP 3/4] Analyzing fused signals...", "yellow", attrs=['bold'])

    # Count actionable signals
    strong_signals = [
        (symbol, result) for symbol, result in fused_results.items()
        if result['action'] in ['STRONG_BUY', 'STRONG_SELL'] and result['confidence'] >= 80
    ]

    medium_signals = [
        (symbol, result) for symbol, result in fused_results.items()
        if result['action'] in ['MEDIUM_BUY', 'MEDIUM_SELL'] and result['confidence'] >= 70
    ]

    cprint(f"  Strong signals (>=80% confidence): {len(strong_signals)}", "green" if strong_signals else "white")
    cprint(f"  Medium signals (>=70% confidence): {len(medium_signals)}", "cyan" if medium_signals else "white")

    # Display all fused signals
    fusion.display_fused_signals(fused_results)

    # STEP 4: Execute trades
    cprint("\n[STEP 4/4] Executing trades...", "yellow", attrs=['bold'])

    if strong_signals:
        for symbol, result in strong_signals:
            execute_trade(
                symbol=symbol,
                action=result['action'],
                confidence=result['confidence'],
                reasoning=result['reasoning']
            )
    else:
        cprint("  [INFO] No strong signals detected - no trades to execute", "white")

    # Cycle complete
    cycle_end = datetime.now()
    cycle_duration = (cycle_end - cycle_start).total_seconds()

    print("\n" + "="*80)
    cprint(f"CYCLE COMPLETE - Duration: {cycle_duration:.1f}s", "green", attrs=['bold'])
    print("="*80 + "\n")


def run_continuous():
    """Run master agent continuously"""
    cprint("\n[MASTER] Starting Two-Engine Trading System...\n", "cyan", attrs=['bold'])

    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            cprint(f"\n[CYCLE #{cycle_count}] Starting...", "magenta", attrs=['bold'])

            # Run trading cycle
            run_trading_cycle()

            # Sleep until next cycle
            cprint(f"\n[SLEEP] Waiting {CHECK_INTERVAL_MINUTES} minutes until next cycle...", "yellow")
            time.sleep(CHECK_INTERVAL_MINUTES * 60)

    except KeyboardInterrupt:
        cprint("\n\n[SHUTDOWN] Master agent shutting down gracefully...", "red", attrs=['bold'])
        cprint(f"Completed {cycle_count} trading cycles\n", "white")


def run_once():
    """Run one trading cycle only"""
    cprint("\n[MASTER] Running ONE trading cycle...\n", "cyan", attrs=['bold'])
    run_trading_cycle()
    cprint("[MASTER] Single cycle complete!\n", "green", attrs=['bold'])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single run mode
        run_once()
    else:
        # Continuous mode
        print("\n" + "="*80)
        cprint("TWO-ENGINE TRADING SYSTEM", "cyan", attrs=['bold'])
        print("="*80)
        print(f"  Engines: Volume Intelligence + Funding Positioning")
        print(f"  Symbols: {', '.join(SYMBOLS)}")
        print(f"  Interval: {CHECK_INTERVAL_MINUTES} minutes ({config.TRADING_INTERVALS.get(CHECK_INTERVAL_MINUTES, 'Custom')})")
        print(f"  Trading: {'LIVE ENABLED (REAL MONEY!)' if EXECUTE_TRADES else 'DRY-RUN MODE (Safe)'}")
        print("="*80)
        print(f"\n  Available Intervals (change in config.py):")
        for minutes, description in config.TRADING_INTERVALS.items():
            current = " <- CURRENT" if minutes == CHECK_INTERVAL_MINUTES else ""
            print(f"    {minutes} min: {description}{current}")
        print("="*80)

        # Confirm before starting
        response = input("\nStart continuous trading? (yes/no): ")

        if response.lower() in ['yes', 'y']:
            run_continuous()
        else:
            cprint("\nCancelled by user.\n", "yellow")
