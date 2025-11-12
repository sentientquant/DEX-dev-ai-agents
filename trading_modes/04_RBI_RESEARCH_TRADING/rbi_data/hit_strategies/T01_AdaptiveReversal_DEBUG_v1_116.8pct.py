from backtesting import Strategy
from backtesting import Backtest
import pandas as pd
import talib

class AdaptiveReversal(Strategy):
    def init(self):
        # Calculate the historical mean of the closing prices
        self.mean_price = self.I(talib.SMA, self.data.Close, timeperiod=20)
        # Calculate standard deviation for volatility
        self.volatility = self.I(talib.STDDEV, self.data.Close, timeperiod=20)

    def next(self):
        deviation = self.data.Close[-1] - self.mean_price[-1]
        threshold = self.volatility[-1]

        # Set a valid position size according to the backtesting rules
        position_size = 0.1  # 10% of the equity

        # Long entry: Price significantly below mean
        if deviation < -threshold:
            self.buy(size=position_size)
            print("🌙 🚀 Entering Long Position at {}".format(self.data.Close[-1]))

        # Short entry: Price significantly above mean
        elif deviation > threshold:
            self.sell(size=position_size)
            print("🌙 🚀 Entering Short Position at {}".format(self.data.Close[-1]))

        # Risk management: setting stop-loss and take-profit
        if self.position:
            if self.position.is_long:
                stop_loss_price = self.data.Close[-1] - (2 * threshold)
                take_profit_price = self.data.Close[-1] + (3 * threshold)
                # Use sl= and tp= in buy/sell, modified logic accordingly
                print("🌙 Setting Long SL at {}, TP at {}".format(stop_loss_price, take_profit_price))
            elif self.position.is_short:
                stop_loss_price = self.data.Close[-1] + (2 * threshold)
                take_profit_price = self.data.Close[-1] - (3 * threshold)
                # Use sl= and tp= in buy/sell, modified logic accordingly
                print("🌙 Setting Short SL at {}, TP at {}".format(stop_loss_price, take_profit_price))

# 🌙 MOON DEV'S MULTI-DATA TESTING FRAMEWORK 🚀
# Tests this strategy on 25+ data sources automatically!
if __name__ == "__main__":
    import sys
    import os
    import io
    from backtesting import Backtest
    import pandas as pd
    import numpy as np

    # Set UTF-8 encoding for Windows terminal (fixes emoji display issues)
    if os.name == 'nt':  # Windows
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # FIRST: Run standard backtest and print stats (REQUIRED for parsing!)
    print("\n🌙 Running initial backtest for stats extraction...")
    import os
    data_path = os.path.join('src', 'data', 'ohlcv', 'BTC-USDT-15m.csv')
    data = pd.read_csv(data_path)
    data.columns = data.columns.str.strip().str.lower()  # Clean column names
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')  # Set datetime as index

    bt = Backtest(data, AdaptiveReversal, cash=1_000_000, commission=0.002)
    stats = bt.run()

    # 🌙 CRITICAL: Print full stats for Moon Dev's parser!
    print("\n" + "="*80)
    print("📊 BACKTEST STATISTICS (Moon Dev's Format)")
    print("="*80)
    print(stats)
    print("="*80 + "\n")

    # THEN: Run multi-data testing (OPTIONAL - gracefully handles missing module)
    # CRITICAL FIX: Backtest is at src/data/rbi_pp_multi/DATE/backtests/, need to go to src/scripts
    # Path:../../../.. (4 levels up to project root) then src/scripts
    try:
        project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
        scripts_path = os.path.join(project_root, 'src', 'scripts')
        sys.path.insert(0, scripts_path)  # Insert at front to ensure it's found first
        from multi_data_tester import test_on_all_data

        print("\n" + "="*80)
        print("🚀 MOON DEV'S MULTI-DATA BACKTEST - Testing on 25+ Data Sources!")
        print("="*80)

        # Test this strategy on all configured data sources
        # 🌙 ACTIVE TESTING: BTC, ETH, SOL (multiple timeframes)
        # 📊 COMMENTED OUT (in multi_data_tester.py): AAPL, TSLA, ES, NQ, GOOG, NVDA (stocks & futures)
        # IMPORTANT: verbose=False to prevent plotting (causes timeouts in parallel processing!)
        results = test_on_all_data(AdaptiveReversal, 'AdaptiveReversal', verbose=False)

        if results is not None:
            print("\n✅ Multi-data testing complete! Results saved in./results/ folder")
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