# 🌙 Converting RBI Backtests to Live Trading Strategies

## The Problem

Files in `src/data/rbi_pp_multi/.../backtests_final/` are **NOT ready for live trading**.

They use the `backtesting.py` library which only works with historical data.

## The Solution

Convert backtest logic to live trading strategies that work with real-time data.

---

## Step-by-Step Conversion Guide

### 1. Identify Your Target Backtest

Find successful strategies in `backtests_final/`:
```bash
cd src/data/rbi_pp_multi/11_11_2025/backtests_final/
ls -lh
```

Example: `T03_VolatilityRetracement_OPT_v1_8.0pct.py` (8.0% return!)

### 2. Extract the Logic

Open the backtest file and identify:
- **Indicators**: What indicators does it use? (RSI, MACD, BB, etc.)
- **Entry Conditions**: When does it buy/sell?
- **Exit Conditions**: When does it close positions?

**Example from VolatilityRetracement:**
```python
# INDICATORS
self.upper_bb, self.middle_bb, self.lower_bb = talib.BBANDS(close)
self.adx = talib.ADX(high, low, close)
self.rsi = talib.RSI(close)

# ENTRY
if (adx_val > 30 and
    plus_di > minus_di and
    close <= middle and
    40 <= rsi_val <= 60):
    self.buy()

# EXIT
if adx_val < 30 or rsi_val > 70:
    self.position.close()
```

### 3. Create Live Strategy File

Copy the template:
```bash
cp src/strategies/custom/example_strategy.py \
   src/strategies/custom/volatility_retracement_live.py
```

### 4. Convert the Logic

**BEFORE (Backtest format):**
```python
from backtesting import Strategy

class VolatilityRetracement(Strategy):
    def init(self):
        # Indicators
        self.upper_bb = self.I(talib.BBANDS, self.data.Close)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close)
        self.rsi = self.I(talib.RSI, self.data.Close)

    def next(self):
        # Logic runs on every bar
        if self.adx[-1] > 30:
            self.buy()
```

**AFTER (Live format):**
```python
from src.strategies.base_strategy import BaseStrategy
import talib
import pandas as pd

class VolatilityRetracementLive(BaseStrategy):
    def __init__(self):
        super().__init__("Volatility Retracement Live")

    def generate_signals(self, token_address, market_data):
        """
        Generate live trading signals

        Args:
            token_address: Solana token address
            market_data: DataFrame with OHLCV data from live market

        Returns:
            dict with 'action', 'confidence', 'reasoning'
        """
        # Get OHLCV data
        high = market_data['High'].values
        low = market_data['Low'].values
        close = market_data['Close'].values

        # Calculate indicators
        upper, middle, lower = talib.BBANDS(close, timeperiod=20)
        adx = talib.ADX(high, low, close, timeperiod=14)
        plus_di = talib.PLUS_DI(high, low, close, timeperiod=14)
        minus_di = talib.MINUS_DI(high, low, close, timeperiod=14)
        rsi = talib.RSI(close, timeperiod=14)

        # Get latest values (most recent bar)
        current_close = close[-1]
        current_adx = adx[-1]
        current_plus_di = plus_di[-1]
        current_minus_di = minus_di[-1]
        current_rsi = rsi[-1]
        current_middle = middle[-1]

        # BULLISH ENTRY CONDITIONS
        if (current_adx > 30 and
            current_plus_di > current_minus_di and
            current_close <= current_middle and
            40 <= current_rsi <= 60):

            return {
                'action': 'BUY',
                'confidence': 85,  # 0-100
                'reasoning': f'Volatility retracement setup: ADX={current_adx:.1f}, RSI={current_rsi:.1f}, Price at BB middle'
            }

        # BEARISH ENTRY CONDITIONS
        if (current_adx > 30 and
            current_minus_di > current_plus_di and
            current_close >= current_middle and
            40 <= current_rsi <= 60):

            return {
                'action': 'SELL',
                'confidence': 85,
                'reasoning': f'Bearish retracement: ADX={current_adx:.1f}, RSI={current_rsi:.1f}, Price at BB middle'
            }

        # EXIT CONDITIONS
        # (These would be checked by the trading agent for existing positions)
        if current_adx < 30 or current_rsi > 70 or current_rsi < 30:
            return {
                'action': 'CLOSE',
                'confidence': 90,
                'reasoning': f'Exit signal: ADX={current_adx:.1f}, RSI={current_rsi:.1f}'
            }

        # NO SIGNAL
        return {
            'action': 'NOTHING',
            'confidence': 0,
            'reasoning': 'No setup detected'
        }
```

### 5. Key Differences

| Backtest Format | Live Format |
|---|---|
| `class Strategy` | `class BaseStrategy` |
| `def init(self)` | `def __init__(self)` |
| `def next(self)` | `def generate_signals(...)` |
| `self.data.Close` | `market_data['Close']` |
| `self.I(talib.RSI, ...)` | `talib.RSI(close)` |
| `self.buy()` / `self.sell()` | `return {'action': 'BUY'}` |
| `self.position.close()` | `return {'action': 'CLOSE'}` |
| `self.adx[-1]` (current) | `adx[-1]` (current) |
| Runs on every bar | Runs every 15 minutes |

### 6. Register Strategy

Edit `src/agents/strategy_agent.py`:
```python
from src.strategies.custom.volatility_retracement_live import VolatilityRetracementLive

class StrategyAgent:
    def __init__(self):
        self.enabled_strategies = [
            VolatilityRetracementLive(),  # Add your strategy
        ]
```

### 7. Enable Strategy Trading

Edit `src/main.py`:
```python
ACTIVE_AGENTS = {
    'strategy': True,  # Enable strategy-based trading
}
```

### 8. Test Before Going Live

**Paper Trading First:**
```python
# In config.py
PAPER_TRADE_MODE = True  # Test without real money
```

Run for 1 week to verify:
- Strategy generates signals correctly
- No runtime errors
- Performance matches backtest expectations

---

## Full Example: Converting T03_VolatilityRetracement

See the complete conversion example:
- **Backtest**: [src/data/rbi_pp_multi/11_11_2025/backtests_final/T03_VolatilityRetracement_OPT_v1_8.0pct.py](../../../data/rbi_pp_multi/11_11_2025/backtests_final/T03_VolatilityRetracement_OPT_v1_8.0pct.py)
- **Live**: [src/strategies/custom/volatility_retracement_live.py](volatility_retracement_live.py) (create this)

---

## Important Notes

### Data Differences
- **Backtest**: Uses 3 days of 15m bars (~288 bars)
- **Live**: Uses real-time data from exchange API

Configure in `config.py`:
```python
DAYSBACK_4_DATA = 3        # 3 days lookback
DATA_TIMEFRAME = '15m'     # 15-minute bars
```

### Indicator Compatibility
All `talib` indicators work the same in both formats:
- `talib.RSI(close)` ✅
- `talib.BBANDS(close)` ✅
- `talib.MACD(close)` ✅

Just pass numpy arrays instead of `self.data.Close`.

### Position Sizing
Backtest uses:
```python
self.buy(size=0.5)  # 50% of capital
```

Live trading uses config:
```python
# config.py
usd_size = 25              # $25 per position
max_usd_order_size = 3     # $3 max order chunks
```

### Risk Management
Live trading includes automatic:
- Stop losses (5% default)
- Position limits (30% max per position)
- Portfolio risk checks (see `risk_agent.py`)

These are NOT in backtests - backtest only tests strategy logic.

---

## Troubleshooting

### "Strategy not generating signals"
- Check market data is loading: `print(market_data.tail())`
- Verify indicators calculate: `print(f"RSI: {rsi[-1]}")`
- Check conditions are met: Lower thresholds temporarily

### "Indicators return NaN"
- Need enough bars for indicator calculation
- RSI(14) needs 14+ bars minimum
- Use `DAYSBACK_4_DATA = 3` for 288 bars (plenty)

### "Performance doesn't match backtest"
- Backtests use hindsight (perfect data)
- Live trading has:
  - Slippage (price moves between signal and execution)
  - Latency (API delays)
  - Market impact (your order moves the price)
- Expect 20-30% lower returns vs backtest

---

## Next Steps

1. ✅ Convert your best backtest strategy
2. ✅ Test in paper trading mode
3. ✅ Monitor for 1 week
4. ✅ Go live with small position size ($10-25)
5. ✅ Scale up if profitable

Good luck! 🌙🚀
