from backtesting import Strategy, Backtest
import talib.abstract as ta
import pandas as pd
import numpy as np
import os

class PassiveLonghold(Strategy):
    # 🌙 Passive Long Hold Strategy - Buy and Hold Forever! 🚀
    # No indicators, no signals, just HODL the moon! ✨
    
    # No parameters needed for pure buy-and-hold
    # size = 1.0  # Full equity allocation (default)
    
    def init(self):
        # No indicators or setup required
        # Simply prepare to buy once at the start
        print("🌙 PassiveLonghold initialized - Ready to HODL! 💎🙌")
        pass
    
    def next(self):
        # ENTRY: Buy once at the first opportunity (any time, but only once)
        # No conditions - just buy and hold indefinitely
        if len(self.data) == 0:  # Skip if no data
            return
        
        # Buy only if no position exists (one-time entry)
        if not self.position and len(self.trades) == 0:
            # Use full equity for the position (size=1.0 for 100%)
            # No stop loss or take profit as per strategy (pure hold)
            self.buy(size=1.0)
            print(f"🚀 MOON DEV ENTRY: Bought at {self.data.Close[-1]:.2f} - HODLing forever! 🌙💎")
        
        # EXIT: No exit conditions - hold indefinitely
        # No sells, no stops, no targets - pure passive long hold
        # (Backtest will close at end of data if needed, but we don't sell)
        
        # Debug print every 100 bars for monitoring (optional, reduces spam)
        if len(self.data) % 100 == 0:
            print(f"📊 HODL Update: Bar {len(self.data)}, Price {self.data.Close[-1]:.2f}, Position: {'Active' if self.position else 'None'}")

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
    print("\n🌙 Running initial backtest for stats extraction...")
    import os
    data_path = os.path.join('src', 'data', 'ohlcv', 'BTC-USDT-15m.csv')
    data = pd.read_csv(data_path)
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    # Select only OHLCV columns (exclude timestamp column)
    data = data[['open', 'high', 'low', 'close', 'volume']]
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    bt = Backtest(data, PassiveLonghold, cash=1_000_000, commission=0.002)
    stats = bt.run()

    # 🌙 CRITICAL: Print full stats for Moon Dev's parser!
    print("\n" + "="*80)
    print("📊 BACKTEST STATISTICS (Moon Dev's Format)")
    print("="*80)
    print(stats)
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
        from pathlib import Path

        print("\n" + "="*80)
        print("🎯 QUICK FILTER: Testing 15m + 1h (User's Smart Filter)")
        print("="*80)
        print("💡 Logic: If strategy fails on BOTH, it's fundamentally broken")
        print("   15m = Lower timeframe (noise) | 1h = Basic higher timeframe (trends)")

        # Step 1: Quick filter test (15m + 1h only)
        quick_result = test_quick_filter(PassiveLonghold, 'PassiveLonghold', verbose=True)

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
            results = test_on_all_data_parallel(PassiveLonghold, 'PassiveLonghold', verbose=False, parallel=True, max_workers=4, results_dir=results_dir)

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