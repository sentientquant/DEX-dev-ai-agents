from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np
import os

class VolatilityBracket(Strategy):
    # 🌙 MOON DEV'S VOLATILITY BRACKET STRATEGY 🌙
    # Leverages ATR for dynamic brackets, momentum entries, trailing stops, and risk management 🚀

    # Strategy parameters
    atr_period = 14
    multiplier = 1.5  # For brackets
    ma_period = 50  # For trend confirmation
    rsi_period = 14
    risk_pct = 0.01  # 1% risk per trade
    min_atr_pct = 0.005  # Min ATR as 0.5% of price
    max_atr_pct = 0.03  # Max ATR as 3% of price
    trail_multiplier = 1.0  # For trailing stop distance
    sl_multiplier = 2.0  # Stop loss at 2x ATR

    def init(self):
        print("🌙 Initializing Volatility Bracket Strategy... ATR-powered brackets incoming! 🚀")

        # Calculate indicators using self.I() wrapper
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.ma_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)

        # Track previous values for slopes and brackets
        self.prev_sma = None
        self.prev_upper_bracket = None
        self.prev_lower_bracket = None
        self.entry_price = None
        self.stop_loss = None
        self.trailing_stop = None

        print(f"📊 Indicators loaded: ATR({self.atr_period}), SMA({self.ma_period}), RSI({self.rsi_period}) ✨")

    def next(self):
        current_price = self.data.Close[-1]
        atr_value = self.atr[-1]
        sma_value = self.sma[-1]
        rsi_value = self.rsi[-1]

        # 🌙 DEBUG: Print key values every bar (limit to avoid spam in long tests)
        if len(self.data) % 100 == 0:
            print(f"🌙 Bar {len(self.data)}: Price={current_price:.2f}, ATR={atr_value:.4f}, SMA={sma_value:.2f}, RSI={rsi_value:.2f} 🚀")

        # Calculate volatility brackets (Keltner Channel approach)
        # FIXED: Anchor brackets to SMA instead of current price to allow breakouts
        upper_bracket = sma_value + (self.multiplier * atr_value)
        lower_bracket = sma_value - (self.multiplier * atr_value)

        # Check ATR thresholds
        atr_pct = atr_value / current_price
        if atr_pct < self.min_atr_pct or atr_pct > self.max_atr_pct:
            print(f"⚠️ Skipping bar {len(self.data)}: ATR {atr_pct:.3f} out of range ({self.min_atr_pct}-{self.max_atr_pct})")
            return

        # Trend confirmation: SMA slope (simplified as prev vs current)
        sma_slope_up = self.prev_sma is not None and sma_value > self.prev_sma
        sma_slope_down = self.prev_sma is not None and sma_value < self.prev_sma

        # RSI bias
        rsi_up_bias = rsi_value > 50
        rsi_down_bias = rsi_value < 50

        # Update previous values
        self.prev_sma = sma_value
        self.prev_upper_bracket = upper_bracket
        self.prev_lower_bracket = lower_bracket

        # 🌙 ENTRY LOGIC 🌙
        if self.position.size == 0:  # No position
            # Long entry
            if (current_price > upper_bracket and
                sma_slope_up and rsi_up_bias):
                # Calculate position size: risk 1% of equity, stop at 2x ATR below entry
                stop_distance = self.sl_multiplier * atr_value
                risk_amount = self.risk_pct * self.equity
                units = risk_amount / stop_distance
                size_fraction = (units * current_price) / self.equity
                size_fraction = min(size_fraction, 1.0)  # Cap at 100% equity
                self.buy(size=size_fraction, sl=current_price - stop_distance)
                self.entry_price = current_price
                self.stop_loss = current_price - stop_distance
                self.trailing_stop = current_price - (self.trail_multiplier * atr_value)
                print(f"🚀 LONG ENTRY: Price={current_price:.2f}, Bracket={upper_bracket:.2f}, Size={size_fraction:.3f}, SL={self.stop_loss:.2f} 🌙")

            # Short entry
            elif (current_price < lower_bracket and
                  sma_slope_down and rsi_down_bias):
                stop_distance = self.sl_multiplier * atr_value
                risk_amount = self.risk_pct * self.equity
                units = risk_amount / stop_distance
                size_fraction = (units * current_price) / self.equity
                size_fraction = min(size_fraction, 1.0)
                self.sell(size=size_fraction, sl=current_price + stop_distance)
                self.entry_price = current_price
                self.stop_loss = current_price + stop_distance
                self.trailing_stop = current_price + (self.trail_multiplier * atr_value)
                print(f"🚀 SHORT ENTRY: Price={current_price:.2f}, Bracket={lower_bracket:.2f}, Size={size_fraction:.3f}, SL={self.stop_loss:.2f} 🌙")

        # 🌙 EXIT & TRAILING LOGIC 🌙
        elif self.position.size > 0:  # Long position
            # Trailing stop update
            new_trailing_stop = self.data.High[-1] - (self.trail_multiplier * atr_value)
            if new_trailing_stop > self.trailing_stop:
                self.trailing_stop = new_trailing_stop
                self.position.sl = max(self.trailing_stop, self.stop_loss)  # Update SL in backtesting.py

            # Profit-taking: Pull back to lower bracket
            if current_price <= lower_bracket:
                self.position.close()
                print(f"💰 LONG EXIT (Profit): Price={current_price:.2f} hit Lower Bracket={lower_bracket:.2f} 🌙")

        elif self.position.size < 0:  # Short position
            # Trailing stop update
            new_trailing_stop = self.data.Low[-1] + (self.trail_multiplier * atr_value)
            if new_trailing_stop < self.trailing_stop:
                self.trailing_stop = new_trailing_stop
                self.position.sl = min(self.trailing_stop, self.stop_loss)

            # Profit-taking: Rally to upper bracket
            if current_price >= upper_bracket:
                self.position.close()
                print(f"💰 SHORT EXIT (Profit): Price={current_price:.2f} hit Upper Bracket={upper_bracket:.2f} 🌙")

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

    bt = Backtest(data, VolatilityBracket, cash=1_000_000, commission=0.002)
    stats = bt.run()

    # 🌙 CRITICAL: Print full stats for Moon Dev's parser!
    print("\n" + "="*80)
    print("📊 BACKTEST STATISTICS (Moon Dev's Format)")
    print("="*80)
    print(stats)
    print("="*80 + "\n")

    # THEN: Run multi-data testing (OPTIONAL - gracefully handles missing module)
    # CRITICAL FIX: Backtest is at src/data/rbi_pp_multi/DATE/backtests/, need to go to src/scripts
    # Path: ../../../.. (4 levels up to project root) then src/scripts
    try:
        # Fix: Go up 5 levels from backtests_package to project root
        # backtests_package -> 11_11_2025 -> rbi_pp_multi -> data -> src -> PROJECT_ROOT
        project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')
        project_root = os.path.abspath(project_root)  # Convert to absolute path
        scripts_path = os.path.join(project_root, 'src', 'scripts')
        sys.path.insert(0, scripts_path)  # Insert at front to ensure it's found first
        from multi_data_tester_parallel import test_on_all_data_parallel
        from pathlib import Path

        print("\n" + "="*80)
        print("🚀 MOON DEV'S PARALLEL MULTI-DATA BACKTEST - Testing on 12 Crypto Datasets!")
        print("="*80)

        # 🌙 PERMANENT FIX: Use absolute path for results directory
        # This ensures RBI agent can find CSV files in the same location
        results_dir = Path(os.path.dirname(__file__)) / "results"
        results_dir = results_dir.resolve()  # Convert to absolute path
        print(f"💾 Results will be saved to: {results_dir}")

        # Test this strategy on all configured data sources
        # 🌙 ACTIVE TESTING: BTC, ETH, SOL (multiple timeframes)
        # 📊 COMMENTED OUT (in multi_data_tester.py): AAPL, TSLA, ES, NQ, GOOG, NVDA (stocks & futures)
        # IMPORTANT: verbose=False to prevent plotting (causes timeouts in parallel processing!)
        results = test_on_all_data_parallel(VolatilityBracket, 'VolatilityBracket', verbose=False, parallel=True, max_workers=4, results_dir=results_dir)

        if results is not None:
            print(f"\n✅ Multi-data testing complete! Results saved in {results_dir}")
            print(f"📊 Tested on {len(results)} different data sources")
        else:
            print("\n⚠️ No results generated - check for errors above")
    except (ImportError, ModuleNotFoundError) as e:
        print(f"\n⚠️ Multi-data testing skipped: {str(e)}")
        print("💡 This is OK - the main backtest above shows the strategy performance")
        print("🔧 To enable multi-data testing, ensure multi_data_tester.py is in src/scripts/")
    except Exception as e:
        print(f"\n⚠️ Multi-data testing error: {str(e)}")
        print("💡 Main backtest completed successfully above")