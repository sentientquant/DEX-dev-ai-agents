# Market Analysis Agents

## Overview
7 specialized agents that analyze market conditions across multiple data sources. All agents feed insights to trading modes but DO NOT execute trades themselves.

## Agents

### 1. Funding Agent
**File**: `agents/funding_agent.py`
**Purpose**: Track perpetual funding rates across exchanges
**Data Sources**: Binance Futures, Hyperliquid
**Signals**:
- High positive funding = Market overheated (potential shorts)
- High negative funding = Market oversold (potential longs)
- Funding rate spikes = Liquidation cascades incoming

**Configuration**:
```python
MARKET_ANALYSIS = {
    'funding_agent': {
        'enabled': True,
        'check_interval_minutes': 15,
        'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    }
}
```

### 2. Liquidation Agent
**File**: `agents/liquidation_agent.py`
**Purpose**: Monitor liquidation levels and clusters
**Data Sources**: Moon Dev API, Binance liquidation data
**Signals**:
- Large liquidation clusters = Support/Resistance zones
- Liquidation cascades = Extreme volatility incoming
- Hunt zones = Where market makers target stops

**Configuration**:
```python
MARKET_ANALYSIS = {
    'liquidation_agent': {
        'enabled': True,
        'check_interval_minutes': 15,
        'track_levels': True
    }
}
```

### 3. Chart Analysis Agent
**File**: `agents/chartanalysis_agent.py`
**Purpose**: Technical analysis using indicators
**Data Sources**: Binance OHLCV data
**Indicators**: RSI, MACD, Bollinger Bands, Volume, Moving Averages
**Signals**:
- Oversold/Overbought conditions
- Trend changes
- Support/Resistance levels
- Volume anomalies

**Configuration**:
```python
MARKET_ANALYSIS = {
    'chartanalysis_agent': {
        'enabled': True,
        'timeframes': ['15m', '1h', '4h'],
        'indicators': ['RSI', 'MACD', 'BB', 'Volume']
    }
}
```

### 4. Whale Agent
**File**: `agents/whale_agent.py`
**Purpose**: Track large wallet movements
**Data Sources**: Blockchain explorers, exchange wallets
**Signals**:
- Large transfers to/from exchanges
- Whale accumulation/distribution
- Smart money movements

**Configuration**:
```python
MARKET_ANALYSIS = {
    'whale_agent': {
        'enabled': True,
        'track_wallets': True,
        'min_trade_size_usd': 100000
    }
}
```

### 5. Sentiment Agent
**File**: `agents/sentiment_agent.py`
**Purpose**: Social media sentiment analysis
**Data Sources**: Twitter, Reddit
**Tokens Tracked**: BTC, ETH, SOL
**Signals**:
- Bullish/Bearish sentiment shifts
- Fear & Greed indicators
- Social volume spikes

**Configuration**:
```python
MARKET_ANALYSIS = {
    'sentiment_agent': {
        'enabled': True,
        'sources': ['twitter', 'reddit', 'tiktok'],
        'tokens': ['BTC', 'ETH', 'SOL'],
        'check_interval_minutes': 15
    }
}
```

### 6. TikTok Sentiment Agent
**File**: `agents/tiktok_sentiment_agent.py`
**Purpose**: Retail sentiment from TikTok trends
**Data Sources**: TikTok API (via RapidAPI)
**Hashtags**: #crypto, #bitcoin, #ethereum, #solana
**Signals**:
- Viral crypto content
- Retail FOMO indicators
- Trend reversals

**Configuration**:
```python
MARKET_ANALYSIS = {
    'tiktok_sentiment_agent': {
        'enabled': True,
        'hashtags': ['crypto', 'bitcoin', 'ethereum', 'solana'],
        'check_interval_minutes': 30
    }
}
```

### 7. Polymarket Agent
**File**: `agents/polymarket_agent.py`
**Purpose**: Prediction market insights (SENTIMENT ONLY - NOT TRADING)
**Data Sources**: Polymarket API
**Markets**: Crypto, Finance, Politics
**Signals**:
- Market probability shifts
- Crowd wisdom on macro events
- Risk-on/Risk-off sentiment

**Configuration**:
```python
MARKET_ANALYSIS = {
    'polymarket_agent': {
        'enabled': True,
        'mode': 'sentiment',  # NOT trading
        'markets': ['crypto', 'finance', 'politics'],
        'check_interval_minutes': 60
    }
}
```

## Data Flow

```
Market Data Sources
        ↓
  Analysis Agents
        ↓
   Insights/Signals
        ↓
  Trading Modes
  (AI Swarm, Strategy-Based, CopyBot, RBI)
        ↓
  Risk Management
        ↓
   Order Execution
```

## Output Data

Each agent stores results in `market_analysis/data/`:
- `funding/funding_history.csv` - Historical funding rates
- `liquidation/liquidation_history.csv` - Liquidation events
- `sentiment/sentiment_scores.csv` - Sentiment analysis results
- `polymarket/predictions.csv` - Polymarket market data

## Running Agents

### Individual Agent
```bash
python market_analysis/agents/funding_agent.py
```

### All Agents via Main Orchestrator
```bash
# Agents run automatically when enabled in config.py
python src/main.py
```

## Agent Frequency
- **Funding Agent**: Every 15 minutes
- **Liquidation Agent**: Every 15 minutes
- **Chart Analysis**: Every 15 minutes
- **Whale Agent**: Continuous monitoring
- **Sentiment Agent**: Every 15 minutes
- **TikTok Sentiment**: Every 30 minutes
- **Polymarket**: Every 60 minutes

## Integration with Trading Modes

### AI Swarm Mode
All 7 agents feed context to 6 AI models for consensus decisions.

### Strategy-Based Mode
Agent signals available as optional inputs to strategy logic.

### CopyBot Mode
Agents help filter whale trades (e.g., ignore during high funding).

### RBI Research Mode
Agent data used to generate new strategy ideas.

## API Keys Required
Set in `.env` file:
```
# Moon Dev API (liquidation, funding, OI data)
MOONDEV_API_KEY=your_key

# Social Media APIs
TWITTER_API_KEY=your_key
REDDIT_CLIENT_ID=your_key
TIKTOK_RAPID_API_KEY=your_key

# Binance (for OHLCV and funding data)
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
```

## Disabling Agents
Edit `config.py`:
```python
MARKET_ANALYSIS = {
    'funding_agent': {'enabled': False},  # Turn off
    'liquidation_agent': {'enabled': True},  # Keep on
    # ... etc
}
```

## Adding New Agents
1. Create `your_agent.py` in `agents/` folder
2. Add to `MARKET_ANALYSIS` in `config.py`
3. Create data output directory: `data/your_agent/`
4. Document in this README

## Performance Impact
- **Low overhead**: Agents run in parallel
- **Cached data**: Avoid redundant API calls
- **Rate limiting**: Respect API limits automatically

## Support
All agents log to console with color-coded output for easy monitoring.
