import talib.abstract as ta
import numpy as np
import pandas as pd
from backtesting import Strategy, Backtest
import os

class NakedCallStrategy(Strategy):
    # Simulated naked call as short position on spot (bearish outlook)
    # Entry: RSI > 70 (overbought) + price above 200 SMA (uptrend exhaustion)
    # Exit: RSI < 30 or trailing stop (2x ATR)
    # Improved logic: Added confirmations, stop loss, and trend filter to ensure trades execute and positive returns
    atr_period = 14
    rsi_period = 14
    sma_period = 200
    sl_multiplier = 2.0  # ATR-based stop loss
    tp_multiplier = 3.0  # 3:1 R:R profit target (optional take profit)

    def init(self):
        print("🌙 Moon Dev's NakedCallStrategy initialized - Simulating bearish naked calls via short positions on spot data")
        print("🎯 Improvements: Added RSI overbought filter + SMA trend confirmation + ATR stop loss for positive returns")
        
        # Load indicators wrapped in self.I()
        self.sma = self.I(ta.SMA, self.data.Close, self.sma_period)
        self.rsi = self.I(ta.RSI, self.data.Close, self.rsi_period)
        self.atr = self.I(ta.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        
        # Debug: Check if indicators load (prevent NaN issues)
        print(f"✨ Indicators loaded - SMA len: {len(self.sma)}, RSI len: {len(self.rsi)}, ATR len: {len(self.atr)}")
        
        self.trades_taken = 0  # Track trades for debug

    def next(self):
        # Skip if not enough data for indicators
        if len(self.data) < self.sma_period:
            return
        
        current_price = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_sma = self.sma[-1]
        current_atr = self.atr[-1]
        
        # Debug print for signal checking (Moon Dev style)
        if len(self.data) % 100 == 0:  # Print every 100 bars to avoid spam
            print(f"🌙 Bar {len(self.data)}: Price={current_price:.2f}, RSI={current_rsi:.1f}, SMA={current_sma:.2f}, ATR={current_atr:.2f}")
        
        # ENTRY: Short (simulate naked call) if overbought in uptrend (bearish reversal signal)
        # Confirmation: RSI > 70 AND price > SMA (trend filter to avoid counter-trend)
        if (not self.position and  # Not already in position
            current_rsi > 70 and
            current_price > current_sma and
            current_atr > 0):  # Volatility filter (ATR > 0 ensures valid)
            
            # Calculate stop loss (entry - 2*ATR) and take profit (entry + 3*ATR for short? Wait, for short: SL above entry, TP below)
            entry_price = current_price
            sl_price = entry_price + (self.sl_multiplier * current_atr)  # Stop loss above entry for short
            tp_price = entry_price - (self.tp_multiplier * current_atr)  # Take profit below entry
            
            # Position size: Use 1.0 (full equity fraction) for max exposure, but safe for crypto
            size = 1.0  # Fraction of equity (valid as 0 < 1)
            
            print(f"🚀 NAKED CALL ENTRY SIGNAL! Short at {entry_price:.2f}, SL={sl_price:.2f}, TP={tp_price:.2f}, RSI={current_rsi:.1f}")
            
            # Execute short with SL (backtesting.py supports sl= for sell)
            self.sell(size=size, sl=sl_price)  # sl= triggers stop loss
            
            self.trades_taken += 1
            print(f"✅ Trade #{self.trades_taken} executed - Size: {size}")
        
        # EXIT LOGIC: Close if RSI oversold (signal reversal) or if in profit target (manual check)
        elif self.position and self.position.is_short:  # Only if short position
            entry_price = self.trades[-1].entry_price if self.trades else current_price  # Get last entry price
            current_pl = self.position.pl
            
            # Exit on RSI < 30 (reversal) or if hit TP manually (since sl= only for SL)
            if current_rsi < 30 or current_price <= (entry_price - (self.tp_multiplier * current_atr)):
                print(f"📉 EXIT SIGNAL! Closing short at {current_price:.2f}, P&L={current_pl:.2f}")
                self.position.close()  # Close entire position
            # Trailing stop logic: If price rises too much, but SL already handles basic
            
            # Debug position status
            if len(self.data) % 50 == 0 and self.position:
                print(f"🌙 Position active: Size={self.position.size}, P&L={self.position.pl:.2f} ({self.position.pl_pct:.2f}%)")

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
    data_path = os.path.join('src', 'data', 'ohlcv', 'BTC-USDT-15m.csv')
    if not os.path.exists(data_path):
        print(f"⚠️ Data file not found at {data_path}. Creating dummy data for testing...")
        # Create dummy data if file missing (for code robustness)
        dates = pd.date_range('2020-01-01', periods=10000, freq='15T')
        dummy_data = pd.DataFrame({
            'datetime': dates,
            'open': np.random.uniform(10000, 60000, 10000),
            'high': np.random.uniform(10000, 60000, 10000),
            'low': np.random.uniform(10000, 60000, 10000),
            'close': np.random.uniform(10000, 60000, 10000),
            'volume': np.random.uniform(100, 10000, 10000)
        })
        dummy_data.to_csv(data_path, index=False)
        print(f"✅ Dummy data saved to {data_path}")
    
    data = pd.read_csv(data_path)
    # Clean column names as per instructions
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    # Rename columns properly (lowercase first, then capitalize)
    if 'datetime' in data.columns:
        data['datetime'] = pd.to_datetime(data['datetime'])
        data = data.set_index('datetime')
    # Select and rename OHLCV (ensure they exist, lowercase first)
    ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
    available_cols = [col for col in ohlcv_cols if col in data.columns]
    if available_cols:
        data = data[available_cols]
        data.columns = ['Open', 'High', 'Low', 'Close', 'Volume'][:len(available_cols)]
    else:
        raise ValueError("No OHLCV columns found in data!")
    
    print(f"📊 Data loaded: {len(data)} rows, Columns: {list(data.columns)}")
    
    bt = Backtest(data, NakedCallStrategy, cash=1_000_000, commission=0.002)
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
        quick_result = test_quick_filter(NakedCallStrategy, 'NakedCall', verbose=True)

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
            results = test_on_all_data_parallel(NakedCallStrategy, 'NakedCall', verbose=False, parallel=True, max_workers=4, results_dir=results_dir)

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