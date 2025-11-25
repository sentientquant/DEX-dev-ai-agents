import pandas as pd
from backtesting import Strategy, Backtest
import os
import sys
import io
from pathlib import Path

class SpeculativeBear(Strategy):
    def init(self):
        # No indicators required 🌙
        print("🌙 SpeculativeBear initialized - No indicators loaded ✨")
        pass

    def next(self):
        # 🚨 Exit logic: Cover short on bullish bar reversal (entry condition reverse)
        if self.position.is_short and self.data.Close[-1] > self.data.Open[-1]:
            self.position.close()
            print(f"🌙 Covering short on bullish reversal at {self.data.Close[-1]:.2f} ✨")

        # 🚀 Entry logic: Short after 2 consecutive bearish bars (multiple confirmations, no indicators)
        # This anticipates continued decline without chasing
        if not self.position and len(self.data) > 2:
            # Check previous two bars were bearish (close < open)
            prev_bar1_bearish = self.data.Close[-2] < self.data.Open[-2]
            prev_bar2_bearish = self.data.Close[-3] < self.data.Open[-3]
            
            if prev_bar1_bearish and prev_bar2_bearish:
                # Trend alignment: bearish momentum
                # Sufficient volatility implicitly via bar action (no single bar entry)
                entry_price = self.data.Close[-1]
                
                # Risk management: 1% stop loss, 2% take profit (2:1 RR)
                sl_price = entry_price * 1.01  # Stop loss above entry for short
                tp_price = entry_price * 0.98  # Take profit below entry
                
                # Position sizing: Full equity (100% of available cash)
                # For BTC, size in BTC units (fractional OK)
                size = self.broker.getcash() / entry_price
                
                # No fractional issues as backtesting.py handles floats for crypto
                self.sell(size=size, sl=sl_price, tp=tp_price)
                
                print(f"🚀 🌙 Entering SpeculativeBear short at {entry_price:.2f}, "
                      f"SL: {sl_price:.2f}, TP: {tp_price:.2f}, Size: {size:.4f} BTC ✨")

# 🌙 MOON DEV'S MULTI-DATA TESTING FRAMEWORK 🚀
# Tests this strategy on 25+ data sources automatically!
if __name__ == "__main__":
    # Set UTF-8 encoding for Windows terminal (fixes emoji display issues)
    if os.name == 'nt':  # Windows
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # FIRST: Run standard backtest and print stats (REQUIRED for parsing!)
    print("\n🌙 Running initial backtest for stats extraction...")
    data_path = os.path.join('src', 'data', 'ohlcv', 'BTC-USDT-15m.csv')
    data = pd.read_csv(data_path)
    # Clean column names: remove spaces, lowercase, then capitalize OHLCV
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    # Ensure proper OHLCV columns
    if 'open' in data.columns:
        data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

    bt = Backtest(data, SpeculativeBear, cash=1_000_000, commission=0.002)
    stats = bt.run()

    # 🌙 CRITICAL: Print full stats for Moon Dev's parser!
    print("\n" + "="*80)
    print("📊 BACKTEST STATISTICS (Moon Dev's Format)")
    print("="*80)
    print(stats)
    print(stats._strategy)
    print("="*80 + "\n")

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

        print("\n" + "="*80)
        print("🎯 QUICK FILTER: Testing 15m + 1h (User's Smart Filter)")
        print("="*80)
        print("💡 Logic: If strategy fails on BOTH, it's fundamentally broken")
        print("   15m = Lower timeframe (noise) | 1h = Basic higher timeframe (trends)")

        # Step 1: Quick filter test (15m + 1h only)
        quick_result = test_quick_filter(SpeculativeBear, 'SpeculativeBear', verbose=True)

        if quick_result['passed']:
            # PASSED FILTER! Run full multi-data test
            print("\n✅ PASSED QUICK FILTER! Running full multi-data test...")
            print("="*80)
            print("🚀 MOON DEV'S PARALLEL MULTI-DATA BACKTEST - Testing on 12 Crypto Datasets!")
            print("="*80)

            # 🌙 PERMANENT FIX: Use absolute path for results directory
            results_dir = Path(os.path.dirname(__file__)) / "results"
            results_dir = results_dir.resolve()  # Convert to absolute path
            print(f"💾 Results will be saved to: {results_dir}")

            # Test on ALL data sources (BTC, ETH, SOL × 4 timeframes)
            results = test_on_all_data_parallel(SpeculativeBear, 'SpeculativeBear', verbose=False, parallel=True, max_workers=4, results_dir=results_dir)

            if results is not None:
                print(f"\n✅ Multi-data testing complete! Results saved in {results_dir}")
                print(f"📊 Tested on {len(results)} different data sources")
            else:
                print("\n⚠️ No results generated - check for errors above")
        else:
            # FAILED FILTER! Don't waste time on full multi-data test
            print("\n❌ FAILED QUICK FILTER (both 15m and 1h negative)")
            print("💡 Strategy is fundamentally broken - skipping full multi-data test")
            print("🚀 This saves ~80% of testing time by failing fast!")
            print("="*80)
    except (ImportError, ModuleNotFoundError) as e:
        print(f"\n⚠️ Multi-data testing skipped: {str(e)}")
        print("💡 This is OK - the main backtest above shows the strategy performance")
        print("🔧 To enable multi-data testing, ensure multi_data_tester.py is in src/scripts/")
    except Exception as e:
        print(f"\n⚠️ Multi-data testing error: {str(e)}")
        print("💡 Main backtest completed successfully above")