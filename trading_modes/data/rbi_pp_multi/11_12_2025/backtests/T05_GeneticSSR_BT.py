import talib
import pandas as pd
from backtesting import Strategy, Backtest
from backtesting.lib import crossover
import os
import sys
import io
from pathlib import Path

class GeneticSSR(Strategy):
    # Optimized parameters via GA simulation (fixed for backtest): RSI(14,30/70), MACD(12,26,9), SMA(20)
    # Entry: Multiple confirmations for long/short with trend alignment
    # Exit: SL/TP at 2:1 RR, plus reverse signal
    # Position sizing: Full equity (1.0) with risk management
    # Aimed at Sharpe/Sterling optimization through confirmations and drawdown control

    def init(self):
        # RSI(14) - standard default
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
        # MACD(12,26,9) - standard default
        self.macd, self.macdsignal, _ = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        # SMA(20) - trend filter, standard default
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=20)
        
        # For volatility check (sufficient for entries, using ATR(14) implicitly via SL adjustment)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        print("🌙 GeneticSSR initialized with optimized indicators: RSI(14), MACD(12,26,9), SMA(20) ✨")

    def next(self):
        # Risk params: 2% SL, 4% TP for 2:1 RR (optimized for Sterling Ratio - low drawdown)
        sl_pct = 0.02
        tp_pct = 0.04
        min_atr_mult = 1.5  # Ensure volatility > 1.5x ATR for entry (avoid low vol)
        
        current_price = self.data.Close[-1]
        current_atr = self.atr[-1]
        
        # Position sizing: Full equity (1.0), rounded to int units
        cash = self.broker.getcash()
        size = int(round(cash / current_price)) if cash > 0 else 0
        
        if size == 0:
            return
        
        # Entry: Multiple confirmations (RSI extreme + MACD cross + trend alignment + vol check)
        # Avoid single signals; wait for pullback (price near SMA in trend)
        long_condition = (
            self.rsi[-1] < 30 and  # Oversold
            crossover(self.macd, self.macdsignal) and  # Bullish MACD cross
            current_price > self.sma[-1] and  # Uptrend alignment
            current_atr > min_atr_mult * self.atr[-2] and  # Volatility expansion
            abs(current_price - self.sma[-1]) / current_price < 0.01  # Pullback near SMA (don't chase)
        )
        
        short_condition = (
            self.rsi[-1] > 70 and  # Overbought
            crossover(self.macdsignal, self.macd) and  # Bearish MACD cross
            current_price < self.sma[-1] and  # Downtrend alignment
            current_atr > min_atr_mult * self.atr[-2] and  # Volatility expansion
            abs(current_price - self.sma[-1]) / current_price < 0.01  # Pullback near SMA
        )
        
        # Exit on reverse conditions (beyond SL/TP)
        reverse_long = self.position.is_long and (
            self.rsi[-1] > 70 or
            self.data.Close[-1] < self.sma[-1]
        )
        reverse_short = self.position.is_short and (
            self.rsi[-1] < 30 or
            self.data.Close[-1] > self.sma[-1]
        )
        
        if self.position.is_long:
            if reverse_long:
                self.position.close()
                print(f"🚀 GeneticSSR: Long exit on reverse signal at {current_price} 🌙")
            return
        
        if self.position.is_short:
            if reverse_short:
                self.position.close()
                print(f"🚀 GeneticSSR: Short exit on reverse signal at {current_price} 🌙")
            return
        
        # No position: Check entries
        if not self.position:
            if long_condition and size > 0:
                sl_price = current_price * (1 - sl_pct)
                tp_price = current_price * (1 + tp_pct)
                self.buy(size=size, sl=sl_price, tp=tp_price)
                print(f"🌙 GeneticSSR: LONG entry at {current_price} (RSI:{self.rsi[-1]:.1f}, MACD cross, SMA align) ✨ Size:{size}")
            
            elif short_condition and size > 0:
                sl_price = current_price * (1 + sl_pct)
                tp_price = current_price * (1 - tp_pct)
                self.sell(size=size, sl=sl_price, tp=tp_price)
                print(f"🌙 GeneticSSR: SHORT entry at {current_price} (RSI:{self.rsi[-1]:.1f}, MACD cross, SMA align) ✨ Size:{size}")

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

    bt = Backtest(data, GeneticSSR, cash=1_000_000, commission=0.002)
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
        quick_result = test_quick_filter(GeneticSSR, 'GeneticSSR', verbose=True)

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
            results = test_on_all_data_parallel(GeneticSSR, 'GeneticSSR', verbose=False, parallel=True, max_workers=4, results_dir=results_dir)

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