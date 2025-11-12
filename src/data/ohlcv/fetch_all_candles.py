"""
Moon Dev's Complete Multi-Timeframe Candle Data Fetcher with Incremental Updates
Fetches and saves OHLCV candle data for all configured timeframes
NO API KEYS NEEDED - Uses Binance public data endpoints

EXTENDED Data Configuration:
- 15m: 720 days (69,120 candles) - 24 months
- 1h: 540 days (12,960 candles) - 18 months
- 4h: 480 days (2,880 candles) - 16 months
- 1d: 360 days (360 candles) - 12 months

Features:
- Full Fetch: Downloads all historical data (first run)
- Incremental Update: Adds only new candles (daily updates)
- Auto Prune: Removes old data beyond configured days

Usage:
    # First run (full fetch)
    UPDATE_MODE = False
    python fetch_all_candles.py

    # Daily updates (incremental)
    UPDATE_MODE = True
    python fetch_all_candles.py
"""

import sys
import os
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuration
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

# Update mode configuration
UPDATE_MODE = False  # True = incremental update, False = full fetch (set False for first run)
PRUNE_OLD_DATA = True  # True = remove data older than configured days

# Professional data requirements per timeframe - EXTENDED for deep backtesting
# 2+ years of data across multiple market cycles for reliable strategy validation
# 70% win rate with multi-timeframe vs 50% with single timeframe!
TIMEFRAME_CONFIG = {
    '15m': {'days': 1400, 'candles': 134400, 'purpose': '200 weeks - Deep day trading'},
    '1h': {'days': 3500, 'candles': 84000, 'purpose': '500 weeks - Long-term trends'},
    '4h': {'days': 2100, 'candles': 12600, 'purpose': '300 weeks - Extended swings'},
    '1d': {'days': 700, 'candles': 700, 'purpose': '100 weeks - Full year patterns'}
}

# Output directory - Updated to save in ohlcv folder for clean organization
DATA_DIR = 'src/data/ohlcv'

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def print_header(mode="full"):
    """Print fancy header"""
    print("\n" + "="*70)
    if mode == "update":
        print("  Moon Dev's Multi-Timeframe Candle Data UPDATER")
    else:
        print("  Moon Dev's Multi-Timeframe Candle Data Fetcher")
    print("="*70 + "\n")
    print("  Fetches professional-grade OHLCV data across multiple timeframes")
    print("  NO API KEYS NEEDED - Uses Binance public endpoints")
    if mode == "update":
        print("  MODE: Incremental Update (keeps existing data, adds new)\n")
    else:
        print("  MODE: Full Fetch (downloads all historical data)\n")
    print("="*70 + "\n")

def fetch_ohlcv(exchange, symbol, timeframe, days_back, retry_count=0):
    """
    Fetch OHLCV data from exchange with retry logic

    Args:
        exchange: CCXT exchange instance
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe (e.g., '15m', '1h', '4h', '1d')
        days_back: Number of days to fetch
        retry_count: Current retry attempt

    Returns:
        pandas.DataFrame with OHLCV data
    """
    print(f"\n  Fetching {symbol} {timeframe} data ({days_back} days)...")

    try:
        # Calculate start time
        now = datetime.now()
        since = int((now - timedelta(days=days_back)).timestamp() * 1000)

        # Fetch all candles
        all_candles = []
        current_since = since

        while True:
            # Fetch batch (max 1000 candles per request)
            candles = exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_since,
                limit=1000
            )

            if not candles:
                break

            all_candles.extend(candles)

            # Check if we have all the data
            last_timestamp = candles[-1][0]
            if last_timestamp >= int(now.timestamp() * 1000):
                break

            # Move to next batch
            current_since = last_timestamp + 1

            # Rate limiting
            time.sleep(0.5)
            print(f"    Fetched {len(all_candles)} candles...", end='\r')

        # Convert to DataFrame
        df = pd.DataFrame(
            all_candles,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )

        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Reorder columns
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'timestamp']]

        print(f"    SUCCESS: Fetched {len(df)} candles for {symbol} {timeframe}            ")
        return df

    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"    ERROR: {str(e)}")
            print(f"    Retrying in {RETRY_DELAY}s... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
            return fetch_ohlcv(exchange, symbol, timeframe, days_back, retry_count + 1)
        else:
            print(f"    FAILED: Max retries reached for {symbol} {timeframe}: {str(e)}")
            return None

def load_existing_data(symbol, timeframe):
    """
    Load existing candle data if it exists

    Args:
        symbol: Trading pair
        timeframe: Candle timeframe

    Returns:
        DataFrame or None
    """
    clean_symbol = symbol.replace('/', '-')
    filepath = os.path.join(DATA_DIR, f"{clean_symbol}-{timeframe}.csv")

    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            df['datetime'] = pd.to_datetime(df['datetime'])
            print(f"    FOUND: Existing data with {len(df)} candles")
            return df
        except Exception as e:
            print(f"    ERROR loading existing file: {str(e)}")
            return None
    return None

def prune_old_data(df, days_back):
    """
    Remove data older than specified days

    Args:
        df: DataFrame with OHLCV data
        days_back: Number of days to keep

    Returns:
        Pruned DataFrame
    """
    if df is None or df.empty:
        return df

    cutoff_date = datetime.now() - timedelta(days=days_back)
    df['datetime'] = pd.to_datetime(df['datetime'])

    original_len = len(df)
    df_pruned = df[df['datetime'] >= cutoff_date].copy()
    pruned_count = original_len - len(df_pruned)

    if pruned_count > 0:
        print(f"    PRUNED: Removed {pruned_count} old candles (keeping last {days_back} days)")

    return df_pruned

def merge_candles(existing_df, new_df):
    """
    Merge existing and new candle data, removing duplicates

    Args:
        existing_df: Existing DataFrame
        new_df: New DataFrame to merge

    Returns:
        Merged DataFrame
    """
    if existing_df is None or existing_df.empty:
        return new_df

    if new_df is None or new_df.empty:
        return existing_df

    # Concatenate
    merged = pd.concat([existing_df, new_df], ignore_index=True)

    # Remove duplicates based on timestamp
    merged = merged.drop_duplicates(subset=['timestamp'], keep='last')

    # Sort by timestamp
    merged = merged.sort_values('timestamp').reset_index(drop=True)

    # Ensure datetime is correct
    merged['datetime'] = pd.to_datetime(merged['timestamp'], unit='ms')

    added_count = len(merged) - len(existing_df)
    print(f"    MERGED: Added {added_count} new candles ({len(existing_df)} -> {len(merged)})")

    return merged

def save_candles(df, symbol, timeframe):
    """
    Save candles to CSV file

    Args:
        df: DataFrame with OHLCV data
        symbol: Trading pair
        timeframe: Candle timeframe
    """
    if df is None or df.empty:
        return False

    try:
        # Create directory structure: data/rbi/SYMBOL-TIMEFRAME.csv
        os.makedirs(DATA_DIR, exist_ok=True)

        # Clean symbol for filename (BTC/USDT -> BTC-USDT)
        clean_symbol = symbol.replace('/', '-')

        # Save to CSV
        filepath = os.path.join(DATA_DIR, f"{clean_symbol}-{timeframe}.csv")
        df.to_csv(filepath, index=False)

        print(f"    SAVED: {filepath} ({len(df)} candles)")
        return True

    except Exception as e:
        print(f"    ERROR saving file: {str(e)}")
        return False

def main():
    """Main execution"""
    mode = "update" if UPDATE_MODE else "full"
    print_header(mode)

    # Initialize Binance exchange (no API key needed for public data)
    print("  Initializing Binance exchange...")
    try:
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        print("  SUCCESS: Binance exchange initialized\n")
    except Exception as e:
        print(f"  ERROR: Failed to initialize exchange: {str(e)}")
        return

    # Summary tracking
    total_files = len(SYMBOLS) * len(TIMEFRAME_CONFIG)
    successful = 0
    failed = 0

    print(f"  Configuration:")
    print(f"    Symbols: {len(SYMBOLS)}")
    print(f"    Timeframes: {len(TIMEFRAME_CONFIG)}")
    print(f"    Total datasets to fetch: {total_files}\n")

    for tf, config in TIMEFRAME_CONFIG.items():
        print(f"    {tf}: {config['days']} days ({config['candles']:,} candles) - {config['purpose']}")

    print("\n" + "="*70)
    print("  STARTING DATA COLLECTION")
    print("="*70)

    start_time = time.time()

    # Fetch data for each symbol and timeframe
    for symbol in SYMBOLS:
        print(f"\n  Symbol: {symbol}")
        print("  " + "-"*66)

        for timeframe, config in TIMEFRAME_CONFIG.items():
            if UPDATE_MODE:
                # INCREMENTAL UPDATE MODE
                print(f"\n  Fetching {symbol} {timeframe} (INCREMENTAL UPDATE)...")

                # Load existing data
                existing_df = load_existing_data(symbol, timeframe)

                if existing_df is not None and not existing_df.empty:
                    # Calculate how many days to fetch (last 7 days + buffer)
                    update_days = 7
                    print(f"    Fetching last {update_days} days to update...")

                    new_df = fetch_ohlcv(
                        exchange=exchange,
                        symbol=symbol,
                        timeframe=timeframe,
                        days_back=update_days
                    )

                    # Merge new data with existing
                    merged_df = merge_candles(existing_df, new_df)

                    # Prune old data if enabled
                    if PRUNE_OLD_DATA:
                        merged_df = prune_old_data(merged_df, config['days'])

                    # Save merged data
                    if save_candles(merged_df, symbol, timeframe):
                        successful += 1
                    else:
                        failed += 1
                else:
                    # No existing data, do full fetch
                    print(f"    No existing data, doing FULL FETCH...")
                    df = fetch_ohlcv(
                        exchange=exchange,
                        symbol=symbol,
                        timeframe=timeframe,
                        days_back=config['days']
                    )

                    if save_candles(df, symbol, timeframe):
                        successful += 1
                    else:
                        failed += 1
            else:
                # FULL FETCH MODE
                df = fetch_ohlcv(
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=timeframe,
                    days_back=config['days']
                )

                # Save to CSV
                if save_candles(df, symbol, timeframe):
                    successful += 1
                else:
                    failed += 1

            # Rate limiting between requests
            time.sleep(0.5)

    # Summary
    elapsed = time.time() - start_time

    print("\n" + "="*70)
    print("  COLLECTION SUMMARY")
    print("="*70)
    print(f"\n  Total datasets: {total_files}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Time elapsed: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"\n  Data saved to: {DATA_DIR}/")
    print("\n" + "="*70)
    print("  COLLECTION COMPLETE!")
    print("="*70 + "\n")

    # List generated files
    print("  Generated files:")
    try:
        files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and any(tf in f for tf in TIMEFRAME_CONFIG.keys())])

        # Group by symbol
        symbol_groups = {}
        for f in files:
            symbol = f.split('-')[0] + '/' + f.split('-')[1]
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(f)

        for symbol, symbol_files in sorted(symbol_groups.items()):
            print(f"\n    {symbol}:")
            for f in sorted(symbol_files):
                filepath = os.path.join(DATA_DIR, f)
                size = os.path.getsize(filepath) / 1024  # KB

                # Read candle count
                try:
                    df = pd.read_csv(filepath)
                    candle_count = len(df)
                    print(f"      {f:25s} {size:7.1f} KB  ({candle_count:,} candles)")
                except:
                    print(f"      {f:25s} {size:7.1f} KB")
    except Exception as e:
        print(f"    Error listing files: {str(e)}")

    print("\n" + "="*70)
    print("  MULTI-TIMEFRAME DATA READY!")
    print("="*70)
    print("\n  Benefits of multi-timeframe analysis:")
    print("    - 15m: Fast entries on short-term signals")
    print("    - 1h:  Trend confirmation (reduces false signals)")
    print("    - 4h:  Swing trend context")
    print("    - 1d:  Overall market direction (MA200)")
    print("\n  70% win rate with multi-TF vs 50% with single TF!")
    print("\n  Use this data with RBI Agent to generate strategies:")
    print("    python src/agents/rbi_agent.py\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Collection cancelled by user")
    except Exception as e:
        print(f"\n\n  FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
