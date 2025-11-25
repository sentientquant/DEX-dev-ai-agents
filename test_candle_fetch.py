"""
Diagnostic: Test Candle Fetching
Check if BinanceTruthAPI can fetch OHLCV data
"""
import sys
sys.path.insert(0, r'c:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents')

from risk_management.binance_truth_paper_trading import BinanceTruthAPI
from termcolor import cprint

def test_candle_fetch():
    """Test fetching candles for BTC, ETH, SOL"""

    symbols = ['BTC', 'ETH', 'SOL']
    timeframe = '1h'
    days_back = 3

    print("="*80)
    print("TESTING CANDLE FETCHING")
    print("="*80)

    for symbol in symbols:
        print(f"\n{'='*80}")
        print(f"Testing {symbol}")
        print(f"{'='*80}")

        try:
            cprint(f"  📊 Fetching {symbol} data (timeframe: {timeframe}, days_back: {days_back})...", "cyan")

            # This is the exact call made by RBI_RESEARCH_TRADE_FLOW
            ohlcv = BinanceTruthAPI.get_ohlcv_data(
                symbol,
                timeframe=timeframe,
                days_back=days_back
            )

            if ohlcv is None:
                cprint(f"  ❌ FAILED: get_ohlcv_data() returned None", "red")
                continue

            if len(ohlcv) == 0:
                cprint(f"  ❌ FAILED: get_ohlcv_data() returned empty DataFrame", "red")
                continue

            # Check if sufficient data
            if len(ohlcv) < 50:
                cprint(f"  ⚠️  WARNING: Only {len(ohlcv)} candles (need 50+)", "yellow")
                cprint(f"     This will cause 'Insufficient OHLCV data' error", "yellow")
            else:
                cprint(f"  ✅ SUCCESS: Fetched {len(ohlcv)} candles", "green")

            # Show data sample
            print(f"\n  Data columns: {list(ohlcv.columns)}")
            print(f"  First candle:")
            print(f"    Timestamp: {ohlcv.iloc[0]['timestamp']}")
            print(f"    Open:  ${ohlcv.iloc[0]['open']:.2f}")
            print(f"    High:  ${ohlcv.iloc[0]['high']:.2f}")
            print(f"    Low:   ${ohlcv.iloc[0]['low']:.2f}")
            print(f"    Close: ${ohlcv.iloc[0]['close']:.2f}")
            print(f"    Volume: {ohlcv.iloc[0]['volume']:.2f}")

            print(f"\n  Last candle:")
            print(f"    Timestamp: {ohlcv.iloc[-1]['timestamp']}")
            print(f"    Close: ${ohlcv.iloc[-1]['close']:.2f}")

        except Exception as e:
            cprint(f"  ❌ EXCEPTION: {type(e).__name__}: {e}", "red")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    test_candle_fetch()
