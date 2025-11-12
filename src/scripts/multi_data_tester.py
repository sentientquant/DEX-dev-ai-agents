"""
🌙 Moon Dev's Multi-Data Tester for RBI Agent
Tests trading strategies across multiple cryptocurrencies and timeframes

Built with love by Moon Dev 🚀

Purpose:
- Test strategies on BTC, ETH, SOL across multiple timeframes
- Validate strategies work across different market conditions
- Calculate performance metrics for each data source
- Save results to CSV for analysis

Usage:
    from multi_data_tester import test_on_all_data

    results = test_on_all_data(YourStrategy, 'YourStrategyName', verbose=False)

Integration with rbi_agent_pp_multi.py:
    - Called automatically after successful backtest
    - Tests on 12 crypto datasets (BTC, ETH, SOL × 4 timeframes)
    - Saves results to ./results/{strategy_name}.csv
"""

import sys
import pandas as pd
from pathlib import Path
from backtesting import Backtest
from termcolor import cprint

# Data directory (where fetch_all_candles.py saves data)
DATA_DIR = Path(__file__).parent.parent / "data" / "ohlcv"

# Data sources configuration - BTC, ETH, SOL with 4 timeframes each
DATA_SOURCES = [
    # BTC datasets
    {'name': 'BTC-15min', 'file': 'BTC-USDT-15m.csv', 'symbol': 'BTC', 'timeframe': '15m'},
    {'name': 'BTC-1hour', 'file': 'BTC-USDT-1h.csv', 'symbol': 'BTC', 'timeframe': '1h'},
    {'name': 'BTC-4hour', 'file': 'BTC-USDT-4h.csv', 'symbol': 'BTC', 'timeframe': '4h'},
    {'name': 'BTC-1day', 'file': 'BTC-USDT-1d.csv', 'symbol': 'BTC', 'timeframe': '1d'},

    # ETH datasets
    {'name': 'ETH-15min', 'file': 'ETH-USDT-15m.csv', 'symbol': 'ETH', 'timeframe': '15m'},
    {'name': 'ETH-1hour', 'file': 'ETH-USDT-1h.csv', 'symbol': 'ETH', 'timeframe': '1h'},
    {'name': 'ETH-4hour', 'file': 'ETH-USDT-4h.csv', 'symbol': 'ETH', 'timeframe': '4h'},
    {'name': 'ETH-1day', 'file': 'ETH-USDT-1d.csv', 'symbol': 'ETH', 'timeframe': '1d'},

    # SOL datasets
    {'name': 'SOL-15min', 'file': 'SOL-USDT-15m.csv', 'symbol': 'SOL', 'timeframe': '15m'},
    {'name': 'SOL-1hour', 'file': 'SOL-USDT-1h.csv', 'symbol': 'SOL', 'timeframe': '1h'},
    {'name': 'SOL-4hour', 'file': 'SOL-USDT-4h.csv', 'symbol': 'SOL', 'timeframe': '4h'},
    {'name': 'SOL-1day', 'file': 'SOL-USDT-1d.csv', 'symbol': 'SOL', 'timeframe': '1d'},
]


def load_and_prepare_data(file_path: Path) -> pd.DataFrame:
    """
    Load CSV data and prepare for backtesting

    Args:
        file_path: Path to CSV file

    Returns:
        DataFrame with proper columns and index
    """
    # Read CSV
    df = pd.read_csv(file_path)

    # Convert datetime column
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Set datetime as index
    df = df.set_index('datetime')

    # Rename columns to match backtesting.py requirements (capitalize first letter)
    df = df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })

    # Select only required columns
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

    return df


def run_backtest_on_data(strategy_class, data: pd.DataFrame, data_source_name: str, verbose: bool = False):
    """
    Run backtest on a specific dataset

    Args:
        strategy_class: The Strategy class to test
        data: DataFrame with OHLCV data
        data_source_name: Name of data source for logging
        verbose: If True, print detailed output

    Returns:
        dict with results or None if failed
    """
    try:
        if verbose:
            print(f"  🔄 Testing on {data_source_name}...")

        # Run backtest
        bt = Backtest(
            data,
            strategy_class,
            cash=1_000_000,
            commission=0.002
        )
        stats = bt.run()

        # Extract metrics
        result = {
            'Data_Source': data_source_name,
            'Return_%': stats['Return [%]'],
            'Buy_Hold_%': stats.get('Buy & Hold Return [%]', None),
            'Max_DD_%': stats['Max. Drawdown [%]'],
            'Sharpe': stats.get('Sharpe Ratio', None),
            'Sortino': stats.get('Sortino Ratio', None),
            'Exposure_Time_%': stats.get('Exposure Time [%]', None),
            'Expectancy_%': stats.get('Expectancy [%]', stats.get('Avg. Trade [%]', None)),
            'Trades': stats.get('# Trades', 0)
        }

        if verbose:
            print(f"    ✅ Return: {result['Return_%']:.2f}% | Trades: {result['Trades']} | Sharpe: {result['Sharpe']:.2f}")

        return result

    except Exception as e:
        if verbose:
            print(f"    ❌ Failed: {str(e)}")
        return None


def test_on_all_data(strategy_class, strategy_name: str, verbose: bool = False):
    """
    Test strategy across all configured data sources

    This is the main function called by rbi_agent_pp_multi.py

    Args:
        strategy_class: The Strategy class to test (e.g., AdaptiveBreakout)
        strategy_name: String name for CSV output (e.g., 'AdaptiveBreakout')
        verbose: If True, prints detailed output (set False to avoid plotting timeouts)

    Returns:
        pandas.DataFrame with results from all data sources
        Columns: Data_Source, Return_%, Buy_Hold_%, Max_DD_%, Sharpe, Sortino,
                 Exposure_Time_%, Expectancy_%, Trades
    """

    if verbose:
        print("\n" + "="*80)
        print("🌙 MOON DEV'S MULTI-DATA BACKTEST")
        print("="*80)
        print(f"📊 Testing strategy: {strategy_name}")
        print(f"📈 Data sources: {len(DATA_SOURCES)} (BTC, ETH, SOL × 4 timeframes)")
        print("="*80 + "\n")

    # Check if data directory exists
    if not DATA_DIR.exists():
        error_msg = f"❌ Data directory not found: {DATA_DIR}"
        print(error_msg)
        print("💡 Run this command to download data:")
        print("   python src/data/ohlcv/fetch_all_candles.py")
        return None

    # Collect results
    results = []
    successful = 0
    failed = 0

    for source in DATA_SOURCES:
        file_path = DATA_DIR / source['file']

        # Check if file exists
        if not file_path.exists():
            if verbose:
                print(f"  ⚠️  Skipping {source['name']}: File not found")
            failed += 1
            continue

        # Load and prepare data
        try:
            data = load_and_prepare_data(file_path)
        except Exception as e:
            if verbose:
                print(f"  ❌ Error loading {source['name']}: {str(e)}")
            failed += 1
            continue

        # Run backtest
        result = run_backtest_on_data(
            strategy_class,
            data,
            source['name'],
            verbose
        )

        if result:
            results.append(result)
            successful += 1
        else:
            failed += 1

    # Convert to DataFrame
    if len(results) == 0:
        print("❌ No successful backtests - check data files and strategy code")
        return None

    df_results = pd.DataFrame(results)

    # Save results to CSV in ./results/ folder
    results_dir = Path('./results')
    results_dir.mkdir(exist_ok=True)

    csv_path = results_dir / f"{strategy_name}.csv"
    df_results.to_csv(csv_path, index=False)

    if verbose:
        print("\n" + "="*80)
        print(f"✅ Multi-data testing complete!")
        print(f"📊 Successful: {successful}/{len(DATA_SOURCES)}")
        print(f"💾 Results saved to: {csv_path}")
        print("="*80 + "\n")

        # Show summary stats
        print("📊 Summary Statistics:")
        print(f"   Average Return: {df_results['Return_%'].mean():.2f}%")
        print(f"   Best Return: {df_results['Return_%'].max():.2f}% ({df_results.loc[df_results['Return_%'].idxmax(), 'Data_Source']})")
        print(f"   Worst Return: {df_results['Return_%'].min():.2f}% ({df_results.loc[df_results['Return_%'].idxmin(), 'Data_Source']})")
        print(f"   Profitable Datasets: {len(df_results[df_results['Return_%'] > 0])}/{len(df_results)}")
        print("")

    return df_results


def check_data_files():
    """Check which data files exist"""
    print("\n🔍 Checking data files...\n")

    if not DATA_DIR.exists():
        print(f"❌ Data directory not found: {DATA_DIR}")
        print("\n💡 Create it with:")
        print("   python src/data/ohlcv/fetch_all_candles.py\n")
        return False

    missing = []
    found = []

    for source in DATA_SOURCES:
        file_path = DATA_DIR / source['file']
        if file_path.exists():
            # Get file size
            size_mb = file_path.stat().st_size / (1024 * 1024)
            found.append(f"  ✅ {source['file']} ({size_mb:.2f} MB)")
        else:
            missing.append(f"  ❌ {source['file']}")

    # Print found files
    if found:
        print("✅ Found data files:")
        for f in found:
            print(f)

    # Print missing files
    if missing:
        print("\n⚠️  Missing data files:")
        for f in missing:
            print(f)
        print("\n💡 Download missing files with:")
        print("   python src/data/ohlcv/fetch_all_candles.py\n")
    else:
        print("\n🎉 All data files present!\n")

    return len(missing) == 0


if __name__ == "__main__":
    """
    Test the multi-data tester module

    Usage:
        python src/scripts/multi_data_tester.py
    """

    cprint("\n🌙 Moon Dev's Multi-Data Tester", "cyan", attrs=["bold"])
    cprint("="*80, "cyan")

    # Check data files
    check_data_files()

    cprint("\n💡 Usage in rbi_agent_pp_multi.py:", "cyan")
    cprint("   from multi_data_tester import test_on_all_data", "white")
    cprint("   results = test_on_all_data(YourStrategy, 'YourStrategyName', verbose=False)\n", "white")

    cprint("📊 Configured Data Sources:", "cyan")
    for i, source in enumerate(DATA_SOURCES, 1):
        cprint(f"   {i:2d}. {source['name']:15s} - {source['symbol']} {source['timeframe']}", "white")

    print("")
