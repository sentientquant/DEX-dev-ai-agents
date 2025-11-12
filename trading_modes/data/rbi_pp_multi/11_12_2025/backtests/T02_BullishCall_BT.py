from backtesting import Strategy, Backtest
from backtesting.lib import crossover
import pandas as pd
import os
import sys
import io
from pathlib import Path

class BullishCall(Strategy):
    risk_per_trade = 0.02  # 2% risk per trade
    stop_distance = 0.02   # 2% stop loss
    tp_distance = 0.06     # 6% take profit (3:1 RR)
    
    def init(self):
        print("🌙 BullishCall Strategy Initialized - Simulating Long Call with Momentum 🚀")
        # No indicators needed as per strategy research
    
    def next(self):
        current_close = self.data.Close[-1]
        prev_close1 = self.data.Close[-2]
        prev_close2 = self.data.Close[-3]
        
        # Entry: Multiple confirmations via 3 consecutive increasing closes (bullish momentum)
        if not self.position and current_close > prev_close1 > prev_close2:
            entry_price = current_close
            stop_price = entry_price * (1 - self.stop_distance)
            tp_price = entry_price * (1 + self.tp_distance)
            
            # Position sizing based on risk management
            risk_amount = self.equity * self.risk_per_trade
            risk_per_unit = entry_price * self.stop_distance
            size = risk_amount / risk_per_unit
            
            # Ensure size is reasonable (avoid division issues)
            size = max(size, 0.001)  # Minimum size for crypto
            
            self.buy(size=size, sl=stop_price, tp=tp_price)
            print(f"🌙 Bullish Momentum Entry! 🚀 Price: {entry_price:.2f}, Size: {size:.6f}, SL: {stop_price:.2f}, TP: {tp_price:.2f}")
        
        # Exit: Reverse condition - 3 consecutive decreasing closes (momentum reversal)
        if self.position:
            if current_close < prev_close1 < prev_close2:
                self.position.close()
                print(f"🌙 Momentum Reversal Exit! ✨ Price: {current_close:.2f}")

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
    # Clean column names: strip spaces and lowercase (as per instructions)
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    # Select only OHLCV columns (exclude timestamp column)
    data = data[['open', 'high', 'low', 'close', 'volume']]
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    bt = Backtest(data, BullishCall, cash=1_000_000, commission=0.002)
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
        quick_result = test_quick_filter(BullishCall, 'BullishCall', verbose=True)

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
            results = test_on_all_data_parallel(BullishCall, 'BullishCall', verbose=False, parallel=True, max_workers=4, results_dir=results_dir)

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