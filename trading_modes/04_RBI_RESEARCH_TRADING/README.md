# RBI Research Trading Mode
**Research-Based Inference: Automated Strategy Factory**

## Overview
Fully automated system that generates, backtests, and deploys trading strategies from videos, PDFs, and text ideas. This is the **STRATEGY FACTORY** - it creates the strategies used in Strategy-Based Trading mode.

## Key Characteristics
- **Speed**: 6 minutes per strategy (one-time generation + backtest)
- **Cost**: ~$0.027 per strategy (DeepSeek-R1 reasoning)
- **Input**: YouTube URLs, PDF files, trading idea text
- **Output**: Backtested Python strategies ready for deployment
- **Success Rate**: 2 "hits" from 47 tested strategies (4.3%)

## How It Works

### Flow Diagram
```
User Input
(YouTube URL / PDF / Text)
         ↓
DeepSeek-R1 Reasoning Engine
(Extract trading logic)
         ↓
Generate backtesting.py Code
         ↓
Parallel Backtest
(BTC-15m, BTC-1h, ETH-15m, ETH-1h, SOL-15m, SOL-1h)
         ↓
Statistical Analysis
(Return, Sharpe, Drawdown, Trades)
         ↓
Filter Results
(>100% return = "hit")
         ↓
Auto-Deploy to Strategy-Based Mode
```

## Files and Structure

### Main Agent
**File**: `rbi_agent_pp_multi.py`
**Purpose**: Main orchestrator for strategy generation
**Dependencies**: DeepSeek-R1 API, backtesting.py library

### Research Agent
**File**: `research_agent.py`
**Purpose**: Generate strategy ideas using Groq LLMs
**Output**: Text descriptions of trading strategies

### Utility Scripts
- `scripts/backtestdashboard.py` - View backtest results
- `scripts/deepseek_backtest.py` - Direct DeepSeek integration

### Data Folder
**Location**: `rbi_data/` (380+ files)
**Contents**:
- Research ideas (190 text files)
- Backtest code (190 Python files)
- Execution results (190 JSON files)
- Package versions (190 Python files)
- Final deployable versions

## Configuration

```python
TRADING_MODES = {
    'rbi_research': {
        'enabled': True,  # Turn on/off
        'run_continuously': True,  # Keep generating strategies
        'auto_deploy_threshold': 100,  # Deploy if return >100%
        'test_parallel': True  # Test BTC/ETH/SOL simultaneously
    }
}
```

## Running RBI Research

### Generate Strategy from YouTube
```bash
python trading_modes/04_RBI_RESEARCH_TRADING/rbi_agent_pp_multi.py --youtube "https://youtube.com/watch?v=VIDEO_ID"
```

### Generate Strategy from PDF
```bash
python trading_modes/04_RBI_RESEARCH_TRADING/rbi_agent_pp_multi.py --pdf "path/to/strategy.pdf"
```

### Generate Strategy from Text
```bash
python trading_modes/04_RBI_RESEARCH_TRADING/rbi_agent_pp_multi.py --text "RSI oversold strategy with volume confirmation"
```

### Continuous Generation (Auto-mode)
```bash
# In config.py: 'run_continuously': True
python src/main.py
```

## Current Results

### Statistics (from 47 backtests)
- **Total Tested**: 47 strategies
- **Hits (>100% return)**: 2 strategies (4.3%)
- **Best Return**: 1025% (VolatilityBracket)
- **Best Sharpe**: 0.82 (AdaptiveReversal)
- **Average Runtime**: 6 minutes per strategy

### "Hit" Strategies

#### 1. AdaptiveReversal - 116.8% Return
```
File: rbi_data/11_10_2025/backtests_working/T01_AdaptiveReversal_DEBUG_v1_116.8pct.py
Sharpe: 0.82
Max Drawdown: -26.89%
Trades: 21
Timeframe: BTC-15m
Logic: Mean reversion using SMA(20) + STDDEV
Status: DEPLOYED to Strategy-Based Trading
```

#### 2. VolatilityBracket - 1025% Return
```
File: rbi_data/11_11_2025/backtests_package/T05_VolatilityBracket_PKG.py
Sharpe: 0.49
Max Drawdown: -70.61%
Trades: 2
Timeframe: BTC-1hour
Logic: ATR-based dynamic brackets + trend filter
Status: DEPLOYED to Strategy-Based Trading
```

## Input Sources Supported

### 1. YouTube Videos
- Trading strategy tutorials
- Technical analysis explainers
- Trader interviews discussing methods
- Automatic transcript extraction
- Multi-language support

**Example**:
```bash
python rbi_agent_pp_multi.py --youtube "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

### 2. PDF Documents
- Trading books
- Research papers
- Strategy documentation
- Broker reports
- Automatic text extraction

**Example**:
```bash
python rbi_agent_pp_multi.py --pdf "path/to/strategy_guide.pdf"
```

### 3. Text Ideas
- Quick strategy concepts
- Reddit/Twitter ideas
- Custom descriptions
- Plain English explanations

**Example**:
```bash
python rbi_agent_pp_multi.py --text "Buy when RSI < 30 and volume > 2x average, sell when RSI > 70"
```

## Parallel Backtesting

RBI tests each strategy on 6 datasets simultaneously:
1. BTC-USD 15-minute
2. BTC-USD 1-hour
3. ETH-USD 15-minute
4. ETH-USD 1-hour
5. SOL-USD 15-minute
6. SOL-USD 1-hour

**Why?**
- Find best timeframe for strategy
- Avoid curve-fitting to single asset
- Discover multi-asset strategies
- Validate robustness

## Strategy Lifecycle

```
Idea → Research → Code Generation → Backtest → Results Analysis → Deployment
```

### 1. Idea Generation
- User provides input (video/PDF/text)
- OR Research Agent generates ideas automatically

### 2. Research Phase
- DeepSeek-R1 analyzes input
- Extracts trading logic
- Identifies entry/exit rules
- Determines indicators needed

### 3. Code Generation
- Generates backtesting.py compatible code
- Includes proper indicators (talib)
- Implements position sizing
- Adds risk management

### 4. Backtest Execution
- Tests on 6 datasets in parallel
- Calculates metrics (return, Sharpe, drawdown, trades)
- Generates execution results JSON

### 5. Results Analysis
- Filters by return threshold (>100% default)
- Ranks by Sharpe ratio
- Checks drawdown limits
- Validates trade count (min 10 trades)

### 6. Deployment (Automatic)
- Copy to Strategy-Based Trading mode
- Convert to live trading format
- Add to config.py
- Enable for live trading

## Viewing Results

### Backtest Dashboard
```bash
python trading_modes/04_RBI_RESEARCH_TRADING/scripts/backtestdashboard.py
```

Output:
```
==== RBI BACKTEST RESULTS ====
Total Strategies: 47
Hits (>100%): 2
Average Return: 23.4%
Best Strategy: VolatilityBracket (1025%)
Worst Drawdown: -70.61%
==============================
```

### Individual Strategy Results
Check `rbi_data/execution_results/` for detailed JSON files:
```json
{
  "strategy": "AdaptiveReversal",
  "return": 116.8,
  "sharpe": 0.82,
  "max_drawdown": -26.89,
  "trades": 21,
  "win_rate": 0.62,
  "timeframe": "15m",
  "symbol": "BTC-USD"
}
```

## AI Model Used

**DeepSeek-R1**: Reasoning-optimized model
- **Cost**: ~$0.027 per strategy
- **Reasoning Steps**: 5,000-10,000 tokens
- **Context**: 128k tokens (entire strategy documents)
- **Output**: Clean Python code

**Why DeepSeek?**
- Best cost/performance for reasoning
- Excellent at extracting logic from text
- Generates clean backtesting.py code
- Cheap enough for mass generation

## Auto-Deployment

When a strategy hits >100% return:
1. ✅ Mark as "hit" in database
2. ✅ Copy to Strategy-Based Trading mode
3. ✅ Convert to live trading format
4. ⏸️ Paper trade for 1 week (optional)
5. ✅ Enable in config.py
6. ✅ Start live trading

**Config**:
```python
'auto_deploy_threshold': 100,  # Auto-deploy at >100% return
```

## Cost Analysis

Per strategy generation:
- **DeepSeek API**: $0.027
- **Binance data**: Free (cached)
- **Compute**: Negligible

For 47 strategies:
- **Total cost**: $1.27
- **Cost per hit**: $0.64
- **ROI**: 1025% / $0.027 = 37,963x

## Continuous Operation

Set `'run_continuously': True` to:
1. Generate strategy idea (research agent)
2. Generate code (DeepSeek)
3. Backtest (parallel)
4. Analyze results
5. Deploy if hit
6. Repeat every 15 minutes

**Scaling**:
- 4 strategies/hour
- 96 strategies/day
- ~2 hits/day expected (4.3% hit rate)

## Limitations

1. **Historical Data**: Backtests use past data (no guarantee of future performance)
2. **Overfitting**: Strategies may be curve-fit to specific market conditions
3. **Execution**: Backtest assumes perfect fills (slippage in live trading)
4. **Sample Size**: Some strategies have <10 trades (statistical noise)
5. **Market Regime**: Strategies may fail in new market conditions

## Best Practices

1. **Paper Trade First**: Test live strategies for 1 week before real money
2. **Small Position Sizes**: Start with $25-50 per strategy
3. **Monitor Drawdowns**: Exit if drawdown exceeds backtest by 50%
4. **Diversify**: Run multiple strategies simultaneously
5. **Regular Review**: Check performance weekly, disable underperformers

## Troubleshooting

### DeepSeek API Errors
- Check API key in `.env`
- Verify credits available
- Check rate limits

### Backtest Failures
- Ensure pandas_ta installed
- Check OHLCV data availability
- Verify backtesting.py version

### No Hits Found
- Lower threshold: `'auto_deploy_threshold': 50`
- Generate more strategies
- Try different input sources

## Future Enhancements

- [ ] Live forward testing before deployment
- [ ] Multi-timeframe optimization
- [ ] Strategy combination (ensemble)
- [ ] Adaptive position sizing
- [ ] Real-time monitoring dashboard

## Integration

RBI strategies feed into **Strategy-Based Trading** mode:
```
RBI Research → Generate Strategies → Strategy-Based Trading → Live Execution
```

## Support

RBI Research is experimental. Results vary. Not financial advice.
