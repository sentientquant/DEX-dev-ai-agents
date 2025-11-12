"""
🌙 Moon Dev's RBI Multi-Timeframe Tester
Enhancement module for RBI Agent

Built with love by Moon Dev 🚀

Purpose:
- Test RBI backtests across multiple timeframes
- Validate strategies work on 15m, 1h, 4h, 1d
- Calculate weighted performance scores
- Filter out strategies that only work on single timeframe

Usage:
    from src.agents.rbi_multi_tf_tester import test_strategy_multi_timeframe

    pass_test, results = test_strategy_multi_timeframe(strategy_code, strategy_name)
"""

import subprocess
import sys
from pathlib import Path
from termcolor import cprint
import pandas as pd
import json

# Professional timeframe configuration (matches Binance Multi-TF approach)
PROFESSIONAL_TIMEFRAMES = {
    '15m': {
        'file': 'BTC-USDT-15m.csv',
        'days': 90,
        'min_candles': 200,
        'weight': 0.40,  # Primary timeframe for entries
        'description': 'Entry timing'
    },
    '1h': {
        'file': 'BTC-USDT-1h.csv',
        'days': 120,
        'min_candles': 200,
        'weight': 0.30,  # Trend filter
        'description': 'Trend filter'
    },
    '4h': {
        'file': 'BTC-USDT-4h.csv',
        'days': 180,
        'min_candles': 180,
        'weight': 0.20,  # Major trend
        'description': 'Major trend'
    },
    '1d': {
        'file': 'BTC-USDT-1d.csv',
        'days': 365,
        'min_candles': 365,
        'weight': 0.10,  # Market context
        'description': 'Market context'
    }
}

# Data directory
DATA_DIR = Path("src/data/rbi")


def check_data_files():
    """Check if all required data files exist"""

    missing_files = []

    for tf, config in PROFESSIONAL_TIMEFRAMES.items():
        filepath = DATA_DIR / config['file']
        if not filepath.exists():
            missing_files.append(config['file'])

    if missing_files:
        cprint("\n⚠️  Missing data files for multi-timeframe testing:", "yellow")
        for file in missing_files:
            cprint(f"   ❌ {file}", "red")

        cprint("\n💡 Run this command to collect data:", "cyan")
        cprint("   python scripts/collect_rbi_data.py\n", "white")

        return False

    return True


def run_backtest_on_timeframe(strategy_code: str, timeframe: str, data_file: str, strategy_name: str = "TestStrategy") -> dict:
    """
    Run backtest on a specific timeframe

    Returns:
        dict with results or None if failed
    """

    try:
        # Create temporary backtest file
        temp_file = DATA_DIR / f"temp_{strategy_name}_{timeframe}.py"

        # Modify strategy code to use correct data file
        modified_code = strategy_code.replace(
            "BTC-USD-15m.csv",
            data_file
        )

        # Also try common variations
        modified_code = modified_code.replace(
            "BTC/USD",
            "BTC/USDT"
        )

        # Write temporary file
        with open(temp_file, 'w') as f:
            f.write(modified_code)

        # Run backtest
        result = subprocess.run(
            [sys.executable, str(temp_file)],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        # Parse output for metrics
        output = result.stdout + result.stderr

        # Extract metrics (simple parsing, adjust based on actual output format)
        metrics = {
            'return': 0.0,
            'sharpe': 0.0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'num_trades': 0,
            'success': False
        }

        # Look for common metric patterns
        lines = output.split('\n')
        for line in lines:
            lower_line = line.lower()

            if 'return' in lower_line and '%' in line:
                try:
                    # Extract percentage
                    import re
                    match = re.search(r'(-?\d+\.?\d*)%', line)
                    if match:
                        metrics['return'] = float(match.group(1))
                        metrics['success'] = True
                except:
                    pass

            if 'sharpe' in lower_line:
                try:
                    import re
                    match = re.search(r'(-?\d+\.?\d+)', line)
                    if match:
                        metrics['sharpe'] = float(match.group(1))
                except:
                    pass

            if 'win' in lower_line and '%' in line:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)%', line)
                    if match:
                        metrics['win_rate'] = float(match.group(1))
                except:
                    pass

            if 'drawdown' in lower_line:
                try:
                    import re
                    match = re.search(r'(-?\d+\.?\d*)%', line)
                    if match:
                        metrics['max_drawdown'] = abs(float(match.group(1)))
                except:
                    pass

            if 'trades' in lower_line:
                try:
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        metrics['num_trades'] = int(match.group(1))
                except:
                    pass

        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()

        return metrics

    except subprocess.TimeoutExpired:
        cprint(f"  ⏱️  Timeout running {timeframe} backtest", "yellow")
        if temp_file.exists():
            temp_file.unlink()
        return None

    except Exception as e:
        cprint(f"  ❌ Error running {timeframe} backtest: {e}", "red")
        if temp_file.exists():
            temp_file.unlink()
        return None


def test_strategy_multi_timeframe(strategy_code: str, strategy_name: str = "UnknownStrategy") -> tuple:
    """
    Test strategy across all timeframes

    Args:
        strategy_code: The backtest code to test
        strategy_name: Name of the strategy

    Returns:
        (pass_test: bool, results: dict)
    """

    cprint("\n" + "="*80, "magenta")
    cprint("🧪 MULTI-TIMEFRAME STRATEGY TESTING", "white", "on_magenta", attrs=["bold"])
    cprint("="*80, "magenta")

    cprint(f"\n📊 Testing strategy: {strategy_name}", "cyan", attrs=["bold"])
    cprint(f"📈 Timeframes: {', '.join(PROFESSIONAL_TIMEFRAMES.keys())}\n", "cyan")

    # Check data files exist
    if not check_data_files():
        cprint("❌ Cannot run multi-timeframe testing without data files", "red")
        cprint("   Falling back to single timeframe test\n", "yellow")
        return None, None

    # Run tests on each timeframe
    results = {}

    for timeframe, config in PROFESSIONAL_TIMEFRAMES.items():
        cprint(f"⏱️  Testing {timeframe} ({config['description']})...", "yellow")

        data_file = config['file']
        result = run_backtest_on_timeframe(strategy_code, timeframe, data_file, strategy_name)

        if result and result['success']:
            results[timeframe] = result
            results[timeframe]['weight'] = config['weight']

            cprint(f"  ✅ Return: {result['return']:.2f}% | Sharpe: {result['sharpe']:.2f} | Win Rate: {result['win_rate']:.1f}%", "green")
        else:
            cprint(f"  ❌ Test failed or no metrics extracted", "red")
            results[timeframe] = {
                'return': 0.0,
                'sharpe': 0.0,
                'win_rate': 0.0,
                'weight': config['weight'],
                'success': False
            }

    # Calculate overall metrics
    cprint("\n" + "-"*80, "cyan")
    cprint("📊 CALCULATING WEIGHTED PERFORMANCE", "cyan", attrs=["bold"])
    cprint("-"*80 + "\n", "cyan")

    # Weighted return
    weighted_return = sum(
        results[tf]['return'] * results[tf]['weight']
        for tf in PROFESSIONAL_TIMEFRAMES.keys()
        if results[tf]['success']
    )

    # Weighted Sharpe
    weighted_sharpe = sum(
        results[tf]['sharpe'] * results[tf]['weight']
        for tf in PROFESSIONAL_TIMEFRAMES.keys()
        if results[tf]['success']
    )

    # Check if all timeframes are profitable
    all_profitable = all(
        results[tf]['return'] > 1.0 and results[tf]['success']
        for tf in PROFESSIONAL_TIMEFRAMES.keys()
    )

    # Check if all timeframes have positive Sharpe
    all_positive_sharpe = all(
        results[tf]['sharpe'] > 0.5 and results[tf]['success']
        for tf in PROFESSIONAL_TIMEFRAMES.keys()
    )

    # Check weighted return threshold
    weighted_return_good = weighted_return > 2.0  # 2% weighted average

    # Display results
    cprint("Weighted Metrics:", "cyan")
    cprint(f"  Return: {weighted_return:.2f}%", "white")
    cprint(f"  Sharpe: {weighted_sharpe:.2f}", "white")
    cprint("", "white")

    cprint("Pass Criteria:", "cyan")
    cprint(f"  {'✅' if all_profitable else '❌'} All timeframes profitable (>1%)", "green" if all_profitable else "red")
    cprint(f"  {'✅' if all_positive_sharpe else '❌'} All timeframes positive Sharpe (>0.5)", "green" if all_positive_sharpe else "red")
    cprint(f"  {'✅' if weighted_return_good else '❌'} Weighted return >2%", "green" if weighted_return_good else "red")

    # Final verdict
    pass_test = all_profitable and all_positive_sharpe and weighted_return_good

    cprint("\n" + "="*80, "magenta")
    if pass_test:
        cprint("✅ STRATEGY VALIDATED - PASSES MULTI-TIMEFRAME TEST!", "white", "on_green", attrs=["bold"])
        cprint(f"   Weighted Return: {weighted_return:.2f}%", "green")
        cprint(f"   Ready for conversion to BaseStrategy format", "green")
    else:
        cprint("❌ STRATEGY REJECTED - FAILS MULTI-TIMEFRAME TEST", "white", "on_red", attrs=["bold"])
        cprint(f"   Weighted Return: {weighted_return:.2f}%", "red")
        cprint(f"   Strategy may only work on specific timeframes", "red")
    cprint("="*80 + "\n", "magenta")

    # Prepare detailed results
    detailed_results = {
        'timeframe_results': results,
        'weighted_return': weighted_return,
        'weighted_sharpe': weighted_sharpe,
        'all_profitable': all_profitable,
        'all_positive_sharpe': all_positive_sharpe,
        'weighted_return_good': weighted_return_good,
        'pass_test': pass_test
    }

    return pass_test, detailed_results


def save_multi_tf_results(strategy_name: str, results: dict, output_dir: Path):
    """Save multi-timeframe test results to JSON"""

    if results is None:
        return

    results_file = output_dir / f"{strategy_name}_multi_tf_results.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    cprint(f"💾 Multi-TF results saved to: {results_file}", "cyan")


if __name__ == "__main__":
    """
    Test the multi-timeframe tester

    Usage:
        python src/agents/rbi_multi_tf_tester.py
    """

    cprint("\n🧪 Testing Multi-Timeframe Tester Module\n", "cyan", attrs=["bold"])

    # Check if data files exist
    if check_data_files():
        cprint("✅ All data files present!", "green")
    else:
        cprint("❌ Some data files missing", "red")

    cprint("\n💡 To use this module in RBI Agent:", "cyan")
    cprint("   from src.agents.rbi_multi_tf_tester import test_strategy_multi_timeframe", "white")
    cprint("   pass_test, results = test_strategy_multi_timeframe(strategy_code, strategy_name)\n", "white")
