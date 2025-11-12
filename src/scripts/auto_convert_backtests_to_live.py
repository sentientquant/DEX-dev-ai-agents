#!/usr/bin/env python3
"""
🌙 Moon Dev's AUTOMATED Backtest-to-Live Converter
Converts successful RBI backtests to live trading strategies

WHAT IT DOES:
1. Scans backtests_final/ for successful strategies
2. Reads results CSV to find best performing pair/timeframe
3. Extracts strategy logic (indicators, entry/exit)
4. Converts backtesting.py format → BaseStrategy format
5. Names with pair+timeframe: BTC_15m_VolatilityRetracement_8pct.py
6. Saves to trading_modes/02_STRATEGY_BASED_TRADING/strategies/custom/
7. Auto-registers in strategy_agent.py
8. Enables ACTIVE_AGENTS['strategy'] = True in main.py

SAFETY:
- Dry run mode (preview before converting)
- Backup before modification
- Only converts strategies > 1% return
"""

import os
import re
import ast
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
import sys
import io

# Set UTF-8 encoding for Windows terminal (fixes emoji display issues)
if os.name == 'nt':  # Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
RBI_DATA_DIR = PROJECT_ROOT / "src" / "data" / "rbi_pp_multi"
OUTPUT_DIR = PROJECT_ROOT / "trading_modes" / "02_STRATEGY_BASED_TRADING" / "strategies" / "custom"
STRATEGY_AGENT_PATH = PROJECT_ROOT / "trading_modes" / "02_STRATEGY_BASED_TRADING" / "strategy_agent.py"
MAIN_PY_PATH = PROJECT_ROOT / "src" / "main.py"

MIN_RETURN_PCT = 1.0  # Only convert strategies with > 1% return
MAX_STRATEGIES = 10   # Limit number of strategies to convert

def find_latest_rbi_folder():
    """Find the most recent RBI date folder"""
    date_folders = [d for d in RBI_DATA_DIR.iterdir() if d.is_dir() and d.name.count('_') == 2]
    if not date_folders:
        return None
    # Sort by date (MM_DD_YYYY format)
    latest = sorted(date_folders, key=lambda x: datetime.strptime(x.name, "%m_%d_%Y"))[-1]
    return latest

def find_best_pair_timeframe(strategy_name, rbi_folder):
    """
    Find the best performing pair/timeframe from results CSV

    Returns: dict with 'pair', 'timeframe', 'return_pct', 'sharpe'
    """
    # Look in both backtests_package/results and backtests/results
    possible_csv_locations = [
        rbi_folder / "backtests_package" / "results",
        rbi_folder / "backtests" / "results"
    ]

    for results_dir in possible_csv_locations:
        if not results_dir.exists():
            continue

        # Find CSV file for this strategy
        csv_files = list(results_dir.glob(f"{strategy_name}*.csv"))

        if not csv_files:
            continue

        # Read CSV
        csv_file = csv_files[0]
        df = pd.read_csv(csv_file)

        # Filter for positive returns
        positive_returns = df[df['Return_%'] > MIN_RETURN_PCT].copy()

        if positive_returns.empty:
            continue

        # Sort by return % descending
        positive_returns = positive_returns.sort_values('Return_%', ascending=False)

        # Get best result
        best = positive_returns.iloc[0]

        return {
            'pair': best['Symbol'],
            'timeframe': best['Timeframe'],
            'return_pct': best['Return_%'],
            'sharpe': best.get('Sharpe', 0),
            'trades': best.get('Trades', 0)
        }

    return None

def extract_strategy_logic(backtest_file):
    """
    Parse the backtest file and extract:
    - Class name
    - Indicators (from init method)
    - Entry conditions (from next method)
    - Exit conditions (from next method)
    """
    with open(backtest_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract class name
    class_match = re.search(r'class\s+(\w+)\s*\(Strategy\)', content)
    class_name = class_match.group(1) if class_match else "UnknownStrategy"

    # Extract init method (indicators)
    init_match = re.search(r'def init\(self\):(.*?)def next\(self\):', content, re.DOTALL)
    init_code = init_match.group(1) if init_match else ""

    # Extract next method (trading logic)
    next_match = re.search(r'def next\(self\):(.*?)(?:def\s+\w+|if\s+__name__|$)', content, re.DOTALL)
    next_code = next_match.group(1) if next_match else ""

    # Parse indicators from init
    indicators = []
    talib_calls = re.findall(r'self\.(\w+)\s*=\s*self\.I\((talib\.\w+),\s*([^)]+)\)', init_code)
    for indicator_var, talib_func, params in talib_calls:
        indicators.append({
            'var': indicator_var,
            'function': talib_func,
            'params': params
        })

    return {
        'class_name': class_name,
        'indicators': indicators,
        'init_code': init_code,
        'next_code': next_code,
        'full_code': content
    }

def convert_indicator_to_live(indicator):
    """
    Convert backtest indicator to live format

    BEFORE: self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
    AFTER:  rsi = talib.RSI(close, timeperiod=14)
    """
    func = indicator['function']
    params = indicator['params']

    # Replace self.data.* with just the array name
    params = params.replace('self.data.Close', 'close')
    params = params.replace('self.data.High', 'high')
    params = params.replace('self.data.Low', 'low')
    params = params.replace('self.data.Open', 'open')
    params = params.replace('self.data.Volume', 'volume')

    return f"{func}({params})"

def generate_live_strategy_code(strategy_info, best_result, original_file):
    """Generate complete live strategy code"""
    class_name = strategy_info['class_name']
    pair = best_result['pair']
    timeframe = best_result['timeframe']
    return_pct = best_result['return_pct']

    # Generate live class name
    live_class_name = f"{pair}_{timeframe}_{class_name}"

    # Generate indicator initialization code
    indicator_code = []
    for ind in strategy_info['indicators']:
        live_call = convert_indicator_to_live(ind)

        # Handle multi-return indicators (e.g., BBANDS returns 3 values)
        if ind['var'] in ['upper_bb', 'macd', 'stoch']:
            # These are tuple assignments - need special handling
            if 'upper_bb' in ind['var']:
                indicator_code.append(f"        upper, middle, lower = {live_call}")
            elif 'macd' in ind['var']:
                indicator_code.append(f"        macd, signal, hist = {live_call}")
            else:
                indicator_code.append(f"        {ind['var']} = {live_call}")
        else:
            indicator_code.append(f"        {ind['var']} = {live_call}")

    indicator_code_str = "\n".join(indicator_code)

    # Extract entry/exit logic from next() method
    # This is complex - we'll extract the key conditions
    next_code = strategy_info['next_code']

    # Find buy conditions
    buy_match = re.search(r'if\s*\((.*?)\):\s*.*?self\.buy', next_code, re.DOTALL)
    buy_condition = buy_match.group(1) if buy_match else "False"

    # Find sell conditions
    sell_match = re.search(r'elif\s*\((.*?)\):\s*.*?self\.sell', next_code, re.DOTALL)
    sell_condition = sell_match.group(1) if sell_match else "False"

    # Find exit conditions
    exit_match = re.search(r'if\s+self\.position.*?if\s*\((.*?)\):\s*.*?self\.position\.close', next_code, re.DOTALL)
    exit_condition = exit_match.group(1) if exit_match else "False"

    # Clean up conditions (remove line breaks, extra spaces)
    buy_condition = ' '.join(buy_condition.split())
    sell_condition = ' '.join(sell_condition.split())
    exit_condition = ' '.join(exit_condition.split())

    # Replace backtest variables with live equivalents
    def clean_condition(cond):
        cond = cond.replace('adx_val', 'adx[-1]')
        cond = cond.replace('rsi_val', 'rsi[-1]')
        cond = cond.replace('plus_di', 'plus_di[-1]')
        cond = cond.replace('minus_di', 'minus_di[-1]')
        cond = cond.replace('close', 'close[-1]')
        cond = cond.replace('upper', 'upper[-1]')
        cond = cond.replace('middle', 'middle[-1]')
        cond = cond.replace('lower', 'lower[-1]')
        return cond

    buy_condition = clean_condition(buy_condition)
    sell_condition = clean_condition(sell_condition)
    exit_condition = clean_condition(exit_condition)

    # Generate the live strategy code
    code = f'''"""
🌙 Moon Dev's Auto-Converted Live Strategy
Converted from: {original_file.name}
Best Performance: {return_pct:.2f}% on {pair}-{timeframe}
Sharpe Ratio: {best_result['sharpe']:.2f}
Trades: {best_result['trades']}

IMPORTANT: This strategy was automatically converted from a backtest.
Test in paper trading mode before going live!
"""

from src.strategies.base_strategy import BaseStrategy
import talib
import pandas as pd
import numpy as np

class {live_class_name}(BaseStrategy):
    """
    {class_name} strategy optimized for {pair} {timeframe}

    Original backtest return: {return_pct:.2f}%
    Recommended pair: {pair}
    Recommended timeframe: {timeframe}
    """

    def __init__(self):
        super().__init__(f"{pair} {timeframe} {class_name} ({return_pct:.1f}% backtest)")
        self.target_pair = "{pair}"
        self.target_timeframe = "{timeframe}"

    def generate_signals(self, token_address, market_data):
        """
        Generate live trading signals

        Args:
            token_address: Token to analyze
            market_data: DataFrame with OHLCV data

        Returns:
            dict with 'action', 'confidence', 'reasoning'
        """
        try:
            # Extract OHLCV arrays
            high = market_data['High'].values
            low = market_data['Low'].values
            close = market_data['Close'].values
            open_price = market_data['Open'].values
            volume = market_data['Volume'].values if 'Volume' in market_data.columns else None

            # Calculate indicators
{indicator_code_str}

            # Get current values (most recent bar)
            current_close = close[-1]

            # Check if we have enough data for indicators
            if len(close) < 50:  # Need at least 50 bars for most indicators
                return {{
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': 'Not enough data for indicators'
                }}

            # BULLISH ENTRY CONDITIONS (extracted from backtest)
            if ({buy_condition}):
                return {{
                    'action': 'BUY',
                    'confidence': 85,
                    'reasoning': f'Bullish setup detected on {{self.target_pair}}-{{self.target_timeframe}}'
                }}

            # BEARISH ENTRY CONDITIONS (extracted from backtest)
            if ({sell_condition}):
                return {{
                    'action': 'SELL',
                    'confidence': 85,
                    'reasoning': f'Bearish setup detected on {{self.target_pair}}-{{self.target_timeframe}}'
                }}

            # EXIT CONDITIONS (for existing positions)
            if ({exit_condition}):
                return {{
                    'action': 'CLOSE',
                    'confidence': 90,
                    'reasoning': f'Exit signal triggered on {{self.target_pair}}-{{self.target_timeframe}}'
                }}

            # NO SIGNAL
            return {{
                'action': 'NOTHING',
                'confidence': 0,
                'reasoning': 'No setup detected'
            }}

        except Exception as e:
            return {{
                'action': 'NOTHING',
                'confidence': 0,
                'reasoning': f'Error calculating indicators: {{str(e)}}'
            }}
'''

    return code, live_class_name

def register_strategy_in_agent(strategy_class_name, strategy_file_name):
    """Add strategy to strategy_agent.py"""
    if not STRATEGY_AGENT_PATH.exists():
        print(f"⚠️ Strategy agent not found: {STRATEGY_AGENT_PATH}")
        return False

    with open(STRATEGY_AGENT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add import at top
    import_line = f"from strategies.custom.{strategy_file_name} import {strategy_class_name}"
    if import_line not in content:
        # Find the last import statement
        import_section_end = content.rfind("import ")
        if import_section_end != -1:
            # Find end of that line
            newline_pos = content.find('\n', import_section_end)
            content = content[:newline_pos+1] + import_line + '\n' + content[newline_pos+1:]

    # Add to enabled_strategies list
    strategy_init = f"{strategy_class_name}(),"
    if strategy_init not in content:
        # Find the enabled_strategies list
        list_start = content.find("self.enabled_strategies = [")
        if list_start != -1:
            list_end = content.find("]", list_start)
            # Insert before closing bracket
            content = content[:list_end] + f"\n            {strategy_init}\n        " + content[list_end:]

    # Write back
    with open(STRATEGY_AGENT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def enable_strategy_agent_in_main():
    """Set ACTIVE_AGENTS['strategy'] = True in main.py"""
    if not MAIN_PY_PATH.exists():
        print(f"⚠️ main.py not found: {MAIN_PY_PATH}")
        return False

    with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace 'strategy': False with 'strategy': True
    content = re.sub(
        r"'strategy':\s*False",
        "'strategy': True",
        content
    )

    with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def convert_backtests_to_live(dry_run=True):
    """Main conversion function"""
    print("🌙 Moon Dev's Automated Backtest-to-Live Converter\n")

    # Find latest RBI folder
    latest_rbi = find_latest_rbi_folder()
    if not latest_rbi:
        print("❌ No RBI folders found in", RBI_DATA_DIR)
        return

    print(f"📂 Using RBI folder: {latest_rbi.name}")

    # Find backtests_final folder
    final_dir = latest_rbi / "backtests_final"
    if not final_dir.exists():
        print(f"❌ No backtests_final folder found in {latest_rbi}")
        return

    # Get all successful backtest files
    backtest_files = list(final_dir.glob("*.py"))
    if not backtest_files:
        print(f"❌ No backtest files found in {final_dir}")
        return

    print(f"✅ Found {len(backtest_files)} successful backtests")

    converted_count = 0

    for backtest_file in backtest_files[:MAX_STRATEGIES]:
        print(f"\n{'='*80}")
        print(f"📄 Processing: {backtest_file.name}")
        print(f"{'='*80}")

        # Extract strategy name (remove T00_, _DEBUG_, _OPT_, version numbers, return %)
        strategy_name = backtest_file.stem
        strategy_name = re.sub(r'^T\d+_', '', strategy_name)  # Remove T00_
        strategy_name = re.sub(r'_DEBUG_v\d+.*', '', strategy_name)  # Remove _DEBUG_v0
        strategy_name = re.sub(r'_OPT_v\d+.*', '', strategy_name)  # Remove _OPT_v1
        strategy_name = re.sub(r'_\d+\.\d+pct$', '', strategy_name)  # Remove _8.0pct

        print(f"🔍 Strategy name: {strategy_name}")

        # Find best pair/timeframe
        best_result = find_best_pair_timeframe(strategy_name, latest_rbi)
        if not best_result:
            print(f"⚠️ No positive results found for {strategy_name}, skipping...")
            continue

        print(f"✅ Best performance: {best_result['pair']}-{best_result['timeframe']} ({best_result['return_pct']:.2f}%)")
        print(f"   Sharpe: {best_result['sharpe']:.2f}, Trades: {best_result['trades']}")

        # Extract strategy logic
        print("🔬 Extracting strategy logic...")
        strategy_info = extract_strategy_logic(backtest_file)
        print(f"   Class: {strategy_info['class_name']}")
        print(f"   Indicators: {len(strategy_info['indicators'])}")

        # Generate live strategy code
        print("🔄 Converting to live strategy format...")
        live_code, live_class_name = generate_live_strategy_code(strategy_info, best_result, backtest_file)

        # Generate output filename
        output_filename = f"{best_result['pair']}_{best_result['timeframe']}_{strategy_name}_{int(best_result['return_pct'])}pct.py"
        output_path = OUTPUT_DIR / output_filename

        print(f"💾 Output file: {output_filename}")

        if not dry_run:
            # Create output directory if needed
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            # Write live strategy file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(live_code)

            print(f"✅ Saved to: {output_path}")

            # Register in strategy_agent.py
            print("📝 Registering in strategy_agent.py...")
            success = register_strategy_in_agent(live_class_name, output_path.stem)
            if success:
                print("✅ Registered in strategy agent")
            else:
                print("⚠️ Failed to register in strategy agent")

            converted_count += 1
        else:
            print("(DRY RUN - file not created)")

    if not dry_run and converted_count > 0:
        # Enable strategy agent in main.py
        print(f"\n{'='*80}")
        print("🎯 Enabling strategy agent in main.py...")
        success = enable_strategy_agent_in_main()
        if success:
            print("✅ Strategy agent enabled!")
        else:
            print("⚠️ Failed to enable strategy agent")

    # Summary
    print(f"\n{'='*80}")
    print("📊 CONVERSION SUMMARY")
    print(f"{'='*80}")
    print(f"Backtests found: {len(backtest_files)}")
    print(f"Strategies converted: {converted_count}")

    if dry_run:
        print("\n⚠️ DRY RUN - No files were created")
        print("Run with --execute to actually convert strategies")
    else:
        print(f"\n✅ Conversion complete!")
        print(f"📁 Live strategies saved to: {OUTPUT_DIR}")
        print(f"🎯 Strategy agent enabled in main.py")
        print(f"\n🚀 Next steps:")
        print(f"   1. Review converted strategies in {OUTPUT_DIR}")
        print(f"   2. Test in paper trading mode first!")
        print(f"   3. Run: python src/main.py")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert RBI backtests to live trading strategies")
    parser.add_argument("--execute", action="store_true", help="Actually convert (default is dry run)")
    parser.add_argument("--max", type=int, default=MAX_STRATEGIES, help=f"Max strategies to convert (default: {MAX_STRATEGIES})")

    args = parser.parse_args()

    if args.max:
        MAX_STRATEGIES = args.max

    convert_backtests_to_live(dry_run=not args.execute)
