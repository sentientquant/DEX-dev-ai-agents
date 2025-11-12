# Strategy-Based Trading Mode

## Overview
Python-based algorithmic trading with optional AI validation. This is the **PRIORITY #1** trading mode.

## Key Characteristics
- **Speed**: 5-10 seconds per token analysis
- **Cost**: Cheap (only uses AI for validation if enabled)
- **Strategy Format**: Python classes inheriting from `BaseStrategy`
- **Data Source**: Binance OHLCV data (primary)
- **Execution**: Binance SPOT + Futures trading

## Current Strategies

### RBI "Hit" Strategies (From 47 tested strategies, 2 hits)

1. **AdaptiveReversal** - 116.8% Return
   - File: `T01_AdaptiveReversal_DEBUG_v1_116.8pct.py`
   - Strategy: Mean reversion using SMA + STDDEV
   - Sharpe: 0.82, Drawdown: -26.89%
   - Trades: 21 on BTC-15m
   - Logic: Buy when price < mean - volatility, sell when price > mean + volatility

2. **VolatilityBracket** - 1025% Return
   - File: `T05_VolatilityBracket_PKG.py`
   - Strategy: ATR-based dynamic brackets
   - Sharpe: 0.49, Drawdown: -70.61%
   - Trades: 2 on BTC-1hour
   - Logic: Long on upper bracket breakout + trend up + RSI > 50

## Directory Structure
```
02_STRATEGY_BASED_TRADING/
├── README.md (this file)
├── strategy_agent.py (strategy loader + AI validation)
├── trading_agent.py (6-model AI swarm - for reference)
└── strategies/
    ├── T01_AdaptiveReversal_DEBUG_v1_116.8pct.py
    ├── T05_VolatilityBracket_PKG.py
    └── (add your custom strategies here)
```

## How to Enable
Edit `config.py` in project root:
```python
TRADING_MODES = {
    'strategy_based': {
        'enabled': True,  # Turn on/off
        'strategies': ['adaptive_reversal', 'volatility_bracket'],
        'tokens': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
        'use_ai_validation': True  # Optional AI check before execution
    }
}
```

## How It Works

### Flow Diagram
```
Binance OHLCV Data
         ↓
Strategy.generate_signals()
         ↓
    [Buy/Sell/Nothing]
         ↓
AI Validation (optional)
    ↓ 90%+ confidence required
         ↓
Binance Order Execution
         ↓
    Position Tracking
         ↓
    Risk Management
```

### Strategy Pattern
```python
class YourStrategy(BaseStrategy):
    name = "your_strategy_name"
    description = "What it does"

    def generate_signals(self, token_address, market_data):
        # Your logic here
        return {
            "action": "BUY"|"SELL"|"NOTHING",
            "confidence": 0-100,
            "reasoning": "Why this decision"
        }
```

## Running Strategy-Based Trading

### Standalone
```bash
python trading_modes/02_STRATEGY_BASED_TRADING/strategy_agent.py
```

### With Main Orchestrator
```bash
# Ensure strategy_based is enabled in config.py
python src/main.py
```

## Converting RBI Backtests to Live Strategies

RBI strategies use `backtesting.py` format (historical data):
```python
class AdaptiveReversal(Strategy):
    def init(self):
        self.mean_price = self.I(talib.SMA, self.data.Close, 20)

    def next(self):
        if deviation < -threshold:
            self.buy(size=0.1)
```

Live strategies use `BaseStrategy` format (real-time):
```python
class AdaptiveReversalLive(BaseStrategy):
    def generate_signals(self, token, data):
        mean_price = data['close'].rolling(20).mean()
        if current_price < (mean_price - threshold):
            return {"action": "BUY", "confidence": 80}
```

## Performance Metrics
- **AdaptiveReversal**: 116.8% return, 21 trades, -26.89% max drawdown
- **VolatilityBracket**: 1025% return, 2 trades, -70.61% max drawdown

Both strategies tested on real historical data from Binance.

## Risk Management Integration
All strategies respect:
- `MAX_LOSS_USD` = $50 per 12 hours
- `MAX_GAIN_USD` = $100 per 12 hours
- `MAX_POSITION_PERCENTAGE` = 30% max allocation
- `MINIMUM_BALANCE_USD` = $100 emergency threshold
- AI Override System (90% confidence required to override limits)

## Adding New Strategies
1. Create `your_strategy.py` in `strategies/` folder
2. Inherit from `BaseStrategy`
3. Implement `generate_signals()` method
4. Add to config: `'strategies': ['adaptive_reversal', 'your_strategy']`
5. Test with paper trading first

## Comparison to Other Modes

| Feature | Strategy-Based | AI Swarm | CopyBot | RBI Research |
|---------|---------------|----------|---------|--------------|
| Speed | 5-10 sec | 60 sec | 30-45 sec | 6 min (one-time) |
| Cost | Cheap | Expensive | Medium | Medium |
| Control | High | Low | None | Automated |
| Backtestable | Yes | No | No | Yes |
| Requires | Python code | 6 AI models | Whale wallets | Video/PDF input |

## Next Steps
1. Convert RBI backtests to live BaseStrategy format
2. Backtest on recent Binance data
3. Paper trade for 1 week
4. Live trade with small size ($25-50)
5. Monitor and adjust

## Support
- Discord: Moon Dev's Trading Community
- YouTube: @moon-dev-ai-agents-for-trading
- GitHub Issues: Report bugs/suggestions
