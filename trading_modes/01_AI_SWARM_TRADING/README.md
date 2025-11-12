# AI Swarm Trading Mode

## Overview
6-model AI consensus system for trading decisions. The most intelligent but slowest and most expensive mode.

## Key Characteristics
- **Speed**: 60 seconds per token analysis
- **Cost**: Expensive (~$0.10-0.50 per decision)
- **Accuracy**: Highest (6-model consensus)
- **Use Case**: High-value trades, uncertain markets
- **Default Status**: DISABLED (enable manually if needed)

## How It Works

### 6-Model Swarm Architecture
```
Market Data
    ↓
[Split to 6 AI Models]
    ↓
┌─────────────────────────────────────────┐
│ 1. Claude-3-Opus (Anthropic)            │ → Vote: BUY/SELL/HOLD
│ 2. GPT-4 (OpenAI)                       │ → Vote: BUY/SELL/HOLD
│ 3. DeepSeek-R1 (Reasoning)              │ → Vote: BUY/SELL/HOLD
│ 4. Groq (Fast Inference)                │ → Vote: BUY/SELL/HOLD
│ 5. Gemini-Pro (Google)                  │ → Vote: BUY/SELL/HOLD
│ 6. Ollama-local (Free, Private)         │ → Vote: BUY/SELL/HOLD
└─────────────────────────────────────────┘
    ↓
Consensus Engine
    ↓
FINAL DECISION
(Requires 4/6 agreement = 67% threshold)
    ↓
Order Execution
```

### Voting Logic
- **BUY**: 4+ models vote BUY → Execute buy order
- **SELL**: 4+ models vote SELL → Execute sell order
- **HOLD**: No consensus OR <4 models agree → No action

## Configuration

```python
TRADING_MODES = {
    'ai_swarm': {
        'enabled': False,  # DISABLED by default (expensive)
        'tokens': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
        'models': ['claude', 'gpt4', 'deepseek', 'groq', 'gemini', 'ollama']
    }
}
```

## Running AI Swarm

### Standalone
```bash
python trading_modes/01_AI_SWARM_TRADING/trading_agent.py
```

### With Main Orchestrator
```bash
# Enable in config.py first: 'enabled': True
python src/main.py
```

## Cost Analysis

Per token analysis:
- **Claude-3-Opus**: $0.15 (most expensive, best reasoning)
- **GPT-4**: $0.10
- **DeepSeek-R1**: $0.03
- **Groq**: $0.02 (fastest)
- **Gemini-Pro**: $0.05
- **Ollama**: FREE (runs locally)

**Total per decision**: ~$0.35
**Per day (96 decisions)**: ~$33.60
**Per month**: ~$1,008

## When to Use AI Swarm

### Good Use Cases
1. **High-Value Trades**: $1,000+ positions where accuracy matters
2. **Uncertain Markets**: Choppy/sideways markets
3. **Major Events**: Fed announcements, earnings, elections
4. **Portfolio Rebalancing**: Monthly/quarterly decisions
5. **Risk-Off Mode**: When you want maximum safety

### Bad Use Cases
1. **Scalping**: Too slow (60 sec delay)
2. **High Frequency**: Too expensive
3. **Low Capital**: Not worth the cost for <$100 positions
4. **Trending Markets**: Strategy-Based mode is faster/cheaper

## Advantages

### 1. Highest Accuracy
- 6 different AI perspectives
- Reduces single-model bias
- Catches errors other models miss

### 2. Best for Complex Scenarios
- Multi-factor analysis
- Macro + micro considerations
- Sentiment + technicals + fundamentals

### 3. Risk Reduction
- Consensus requirement prevents impulsive trades
- Multiple models = lower error rate
- Built-in disagreement filter

## Disadvantages

### 1. Expensive
$33.60/day if running continuously

### 2. Slow
60 seconds per token (vs 5-10 sec for Strategy-Based)

### 3. Overkill for Simple Trades
Simple RSI strategy doesn't need 6 AIs

## Model Selection

### Claude-3-Opus (Leader)
- Best reasoning capability
- Excellent risk assessment
- Conservative bias (good for trading)

### GPT-4 (Balanced)
- Fast inference
- Good technical analysis
- Middle-ground decisions

### DeepSeek-R1 (Reasoner)
- Deep reasoning steps
- Finds hidden patterns
- Cheap for quality

### Groq (Speed)
- Fastest inference (2-3 sec)
- Good for quick decisions
- Low cost

### Gemini-Pro (Google)
- Alternative perspective
- Good at correlations
- Free tier available

### Ollama (Local/Free)
- Runs on your hardware
- Zero API cost
- Privacy-focused

## Consensus Thresholds

**Default**: 4/6 models (67%)
**Conservative**: 5/6 models (83%) - change in code
**Aggressive**: 3/6 models (50%) - change in code

**Recommended**: Keep 4/6 for balanced approach

## Integration with Other Systems

### Market Analysis Agents
All 7 market analysis agents feed context to swarm:
- Funding rates
- Liquidation levels
- Chart patterns
- Whale movements
- Sentiment data
- TikTok trends
- Polymarket odds

### Risk Management
Risk agent still runs first:
- Check portfolio limits
- Verify position sizes
- AI override capability

## Performance Tuning

### Speed Optimization
```python
# Use only fast models
'models': ['groq', 'gemini', 'ollama']  # <10 sec total
```

### Cost Optimization
```python
# Skip expensive models
'models': ['deepseek', 'groq', 'ollama']  # <$0.05 per decision
```

### Accuracy Optimization
```python
# Use all premium models
'models': ['claude', 'gpt4', 'gemini', 'deepseek']  # Best quality
```

## Comparison to Other Modes

| Feature | AI Swarm | Strategy-Based | CopyBot | RBI Research |
|---------|----------|----------------|---------|--------------|
| Speed | 60 sec | 5-10 sec | 30-45 sec | 6 min (one-time) |
| Cost/day | $33 | $1-2 | $5-10 | $2-5 |
| Accuracy | Highest | Medium | Unknown | Backtested |
| Best For | Complex | Algorithmic | Following | Creating |
| Control | Low | High | None | Automated |

## Example Decision Flow

**Input**: BTC/USDT at $105,000
**Context**: RSI 32 (oversold), Funding 0.05% (positive), Volume up 200%

**Model Votes**:
1. Claude-3-Opus: **BUY** (85% confidence) - "Oversold + high volume = reversal likely"
2. GPT-4: **BUY** (78% confidence) - "RSI oversold, volume spike confirms"
3. DeepSeek-R1: **HOLD** (60% confidence) - "Positive funding suggests caution"
4. Groq: **BUY** (82% confidence) - "Strong buy signal"
5. Gemini-Pro: **BUY** (75% confidence) - "Technical indicators aligned"
6. Ollama: **HOLD** (55% confidence) - "Wait for confirmation"

**Result**: 4 BUY votes → **EXECUTE BUY ORDER**

## Monitoring Swarm

### View Model Votes
```bash
python trading_modes/01_AI_SWARM_TRADING/trading_agent.py --verbose
```

Output:
```
==== AI SWARM DECISION: BTC/USDT ====
Claude: BUY (85%)
GPT-4: BUY (78%)
DeepSeek: HOLD (60%)
Groq: BUY (82%)
Gemini: BUY (75%)
Ollama: HOLD (55%)
------------------------------------
CONSENSUS: BUY (4/6 votes)
EXECUTING: Buy 0.001 BTC @ $105,000
====================================
```

## Troubleshooting

### API Errors
- Check all API keys in `.env`
- Verify credits for each service
- Check rate limits

### Slow Performance
- Reduce number of models
- Use only Groq + Ollama for speed
- Increase timeout settings

### No Consensus
- Lower threshold to 3/6
- Add more models
- Check if models are conflicting

## Future Enhancements
- [ ] Model weighting (Claude votes count 2x)
- [ ] Dynamic model selection (use expensive models only when needed)
- [ ] Sentiment-based model choice
- [ ] Adaptive threshold based on market conditions

## Best Practices
1. **Only for high-value trades**: >$1,000 positions
2. **Test with paper trading first**: Verify consensus logic
3. **Monitor model performance**: Track which models are most accurate
4. **Adjust thresholds**: Based on your risk tolerance
5. **Disable during trending markets**: Use Strategy-Based instead

## When to Disable
- **Bull market trending up**: Use Strategy-Based (cheaper, faster)
- **Clear technical signals**: Don't need 6 opinions
- **Low trading capital**: Cost not justified
- **High frequency trading**: Too slow

## Support
AI Swarm is powerful but expensive. Use strategically, not continuously.
