"""
Moon Dev's SMART Multi-Timeframe Candle Data Fetcher with Intelligent Backfill
Fetches and maintains OHLCV candle data with smart incremental updates
NO API KEYS NEEDED - Uses Binance public data endpoints

SMART FEATURES:
- Backfill Mode: Continues from where it left off
- Forward Fill: Updates with new candles
- Smart Pruning: Only prunes when exceeding target weeks
- Efficient: Never re-downloads existing data

Usage:
    # First run (backfill to target weeks)
    python fetch_all_candles_smart.py

    # Daily updates (add new candles)
    python fetch_all_candles_smart.py --update
"""

import sys
import os
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

# Professional data requirements per timeframe - EXTENDED for deep backtesting
TIMEFRAME_CONFIG = {
    '5m': {'days': 4900, 'candles': 1411200, 'purpose': '700 weeks - Ultra-deep scalping analysis'},
    '15m': {'days': 1400, 'candles': 134400, 'purpose': '200 weeks - Deep day trading'},
    '30m': {'days': 4200, 'candles': 201600, 'purpose': '600 weeks - Extended intraday patterns'},
    '1h': {'days': 3500, 'candles': 84000, 'purpose': '500 weeks - Long-term trends'},
    '4h': {'days': 2100, 'candles': 12600, 'purpose': '300 weeks - Extended swings'},
    '6h': {'days': 1400, 'candles': 5600, 'purpose': '200 weeks - Deep swing trading analysis'},
    '1d': {'days': 700, 'candles': 700, 'purpose': '100 weeks - Full year patterns'}
}

# Output directory
DATA_DIR = 'src/data/ohlcv'

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def print_header():
    """Print fancy header"""
    print("\n" + "="*80)
    print("  🌙 Moon Dev's SMART Multi-Timeframe Candle Data Fetcher")
    print("="*80 + "\n")
    print("  ✨ Features:")
    print("    • Smart Backfill: Continues from last timestamp")
    print("    • Forward Fill: Adds new candles automatically")
    print("    • Intelligent Pruning: Only when exceeding target")
    print("    • Zero Redundancy: Never re-downloads existing data")
    print("\n" + "="*80 + "\n")

def load_existing_data(symbol, timeframe):
    """
    Load existing candle data if it exists

    Returns:
        tuple: (DataFrame or None, last_timestamp or None, first_timestamp or None)
    """
    clean_symbol = symbol.replace('/', '-')
    filepath = os.path.join(DATA_DIR, f"{clean_symbol}-{timeframe}.csv")

    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')

            last_timestamp = int(df['timestamp'].max())
            first_timestamp = int(df['timestamp'].min())

            print(f"  📂 Found existing {symbol} {timeframe}: {len(df)} candles")
            print(f"     First: {df['datetime'].min()}")
            print(f"     Last: {df['datetime'].max()}")

            return df, last_timestamp, first_timestamp
        except Exception as e:
            print(f"  ❌ Error loading existing file: {str(e)}")
            return None, None, None

    print(f"  📭 No existing data for {symbol} {timeframe}")
    return None, None, None

def fetch_backfill(exchange, symbol, timeframe, target_days, existing_df=None, first_timestamp=None):
    """
    Backfill historical data to reach target days

    Args:
        exchange: CCXT exchange instance
        symbol: Trading pair
        timeframe: Candle timeframe
        target_days: Target number of days to have
        existing_df: Existing DataFrame
        first_timestamp: Timestamp of oldest existing candle

    Returns:
        DataFrame with backfilled data
    """
    now = datetime.now()
    target_start = int((now - timedelta(days=target_days)).timestamp() * 1000)

    # Check if we already have enough history
    if existing_df is not None and first_timestamp is not None:
        if first_timestamp <= target_start:
            days_covered = (now - pd.to_datetime(first_timestamp, unit='ms')).days
            print(f"  ✅ Already have {days_covered} days (target: {target_days} days)")
            return existing_df

        print(f"  ⬇️  Backfilling to reach {target_days} days...")
        # Start fetching from target_start to first_timestamp
        current_since = target_start
    else:
        print(f"  ⬇️  Fetching initial {target_days} days...")
        current_since = target_start

    # Fetch historical data in batches going forward from target_start
    all_candles = []

    # If we have existing data, we want to fetch up to (but not including) first_timestamp
    end_timestamp = first_timestamp if first_timestamp else int(now.timestamp() * 1000)

    while current_since < end_timestamp:
        try:
            # Fetch batch (max 1000 candles)
            candles = exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_since,
                limit=1000
            )

            if not candles:
                break

            # Filter out candles that overlap with existing data
            if first_timestamp:
                candles = [c for c in candles if c[0] < first_timestamp]

            if not candles:
                break

            all_candles.extend(candles)

            # Get the newest timestamp from this batch
            newest_timestamp = candles[-1][0]

            # Check if we've reached our target or existing data
            if newest_timestamp >= end_timestamp:
                print(f"    ✅ Reached target date")
                break

            # Move to next batch (start from last timestamp + 1)
            current_since = newest_timestamp + 1

            # Rate limiting
            time.sleep(0.5)
            print(f"    ⬇️  Backfilled {len(all_candles)} candles...", end='\r')

        except Exception as e:
            print(f"    ⚠️  Backfill error: {str(e)}")
            break

    if all_candles:
        # Convert to DataFrame
        new_df = pd.DataFrame(
            all_candles,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        new_df['datetime'] = pd.to_datetime(new_df['timestamp'], unit='ms')
        new_df = new_df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'timestamp']]

        print(f"    ✅ Backfilled {len(new_df)} historical candles")

        # Combine with existing data
        if existing_df is not None:
            combined_df = pd.concat([new_df, existing_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['timestamp'])
            combined_df = combined_df.sort_values('datetime').reset_index(drop=True)
            return combined_df

        return new_df.sort_values('datetime').reset_index(drop=True)

    return existing_df

def fetch_forward(exchange, symbol, timeframe, existing_df=None, last_timestamp=None):
    """
    Fetch new candles since last timestamp (forward fill)

    Args:
        exchange: CCXT exchange instance
        symbol: Trading pair
        timeframe: Candle timeframe
        existing_df: Existing DataFrame
        last_timestamp: Timestamp of newest existing candle

    Returns:
        DataFrame with updated data
    """
    now_timestamp = int(datetime.now().timestamp() * 1000)

    if last_timestamp is None:
        # No existing data, shouldn't happen if backfill worked
        return existing_df

    # Check if we need to update
    if last_timestamp >= now_timestamp - (60 * 1000):  # Within last minute
        print(f"  ✅ Data is up to date")
        return existing_df

    print(f"  ⬆️  Fetching new candles since {pd.to_datetime(last_timestamp, unit='ms')}")

    # Fetch new candles
    all_new_candles = []
    current_since = last_timestamp + 1

    while current_since < now_timestamp:
        try:
            candles = exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_since,
                limit=1000
            )

            if not candles:
                break

            all_new_candles.extend(candles)

            # Check if we're current
            newest = candles[-1][0]
            if newest >= now_timestamp - (60 * 1000):
                break

            current_since = newest + 1
            time.sleep(0.5)
            print(f"    ⬆️  Fetched {len(all_new_candles)} new candles...", end='\r')

        except Exception as e:
            print(f"    ⚠️  Forward fill error: {str(e)}")
            break

    if all_new_candles:
        # Convert to DataFrame
        new_df = pd.DataFrame(
            all_new_candles,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        new_df['datetime'] = pd.to_datetime(new_df['timestamp'], unit='ms')
        new_df = new_df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'timestamp']]

        print(f"    ✅ Added {len(new_df)} new candles")

        # Combine with existing data
        if existing_df is not None:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['timestamp'])
            combined_df = combined_df.sort_values('datetime').reset_index(drop=True)
            return combined_df

        return new_df

    return existing_df

def smart_prune(df, target_days):
    """
    Smart pruning - only remove data if exceeding target

    Args:
        df: DataFrame with OHLCV data
        target_days: Target number of days to keep

    Returns:
        Pruned DataFrame
    """
    if df is None or df.empty:
        return df

    # Calculate current span
    current_days = (df['datetime'].max() - df['datetime'].min()).days

    if current_days <= target_days:
        print(f"  ✅ Data within target: {current_days}/{target_days} days")
        return df

    # Only prune if exceeding target
    cutoff_date = df['datetime'].max() - timedelta(days=target_days)
    df_pruned = df[df['datetime'] >= cutoff_date].copy()
    pruned_count = len(df) - len(df_pruned)

    if pruned_count > 0:
        print(f"  ✂️  Pruned {pruned_count} old candles (keeping {target_days} days)")

    return df_pruned

def save_data(df, symbol, timeframe):
    """Save DataFrame to CSV"""
    if df is None or df.empty:
        return False

    # Create output directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

    # Clean symbol for filename
    clean_symbol = symbol.replace('/', '-')
    filepath = os.path.join(DATA_DIR, f"{clean_symbol}-{timeframe}.csv")

    # Save to CSV
    df.to_csv(filepath, index=False)
    print(f"  💾 Saved {len(df)} candles to {filepath}")

    # Display summary
    days_covered = (df['datetime'].max() - df['datetime'].min()).days
    print(f"     Coverage: {days_covered} days")
    print(f"     From: {df['datetime'].min()}")
    print(f"     To: {df['datetime'].max()}")

    return True

def process_symbol(exchange, symbol, timeframes):
    """
    Process a single symbol across all timeframes

    Args:
        exchange: CCXT exchange instance
        symbol: Trading pair
        timeframes: Dictionary of timeframe configurations
    """
    print(f"\n{'='*60}")
    print(f"  Processing {symbol}")
    print(f"{'='*60}")

    for timeframe, config in timeframes.items():
        print(f"\n  📊 {symbol} - {timeframe} ({config['purpose']})")
        print(f"  {'─'*50}")

        try:
            # Step 1: Load existing data
            existing_df, last_timestamp, first_timestamp = load_existing_data(symbol, timeframe)

            # Step 2: Backfill to reach target days
            df = fetch_backfill(
                exchange, symbol, timeframe,
                config['days'], existing_df, first_timestamp
            )

            # Step 3: Forward fill with new candles
            df = fetch_forward(
                exchange, symbol, timeframe,
                df, last_timestamp if df is existing_df else int(df['timestamp'].max()) if df is not None else None
            )

            # Step 4: Smart prune if needed
            df = smart_prune(df, config['days'])

            # Step 5: Save updated data
            if df is not None:
                save_data(df, symbol, timeframe)
            else:
                print(f"  ⚠️  No data to save for {symbol} {timeframe}")

        except Exception as e:
            print(f"  ❌ Error processing {symbol} {timeframe}: {str(e)}")

def main():
    """Main execution function"""
    print_header()

    # Check if update mode from command line
    update_mode = '--update' in sys.argv

    if update_mode:
        print("  🔄 MODE: Update (forward fill + smart backfill)\n")
    else:
        print("  📥 MODE: Smart Fetch (backfill to target + forward fill)\n")

    # Initialize exchange (Binance - no API key needed for public data)
    print("  🔗 Connecting to Binance...")
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot'
        }
    })

    print(f"  ✅ Connected to {exchange.name}\n")

    # Process each symbol
    start_time = time.time()

    for symbol in SYMBOLS:
        process_symbol(exchange, symbol, TIMEFRAME_CONFIG)

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  ✨ COMPLETE!")
    print(f"{'='*60}")
    print(f"  Total time: {elapsed:.2f} seconds")
    print(f"  Symbols processed: {len(SYMBOLS)}")
    print(f"  Timeframes per symbol: {len(TIMEFRAME_CONFIG)}")
    print(f"  Output directory: {DATA_DIR}")
    print(f"\n  🚀 Data ready for backtesting!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()