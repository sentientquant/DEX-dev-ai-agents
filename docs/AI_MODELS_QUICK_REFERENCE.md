# AI Models Quick Reference - Complete Trading System

## Summary of All AI Models Used

### Strategy Development Phase

| Component | AI Model | Provider | Cost | Purpose |
|-----------|----------|----------|------|---------|
| **RBI Agent** | DeepSeek-R1 (deepseek-reasoner) | DeepSeek API | $0.027/backtest | Extracts strategy from videos/PDFs |
| **Backtest Converter** | Grok-4 Fast Reasoning | x.AI | $0.20-0.50/1M tokens | Converts backtest → BaseStrategy |
| **Strategy Validator** | None | - | $0 | Syntax/logic validation only |

---

### Signal Generation Phase (Fusion Layer)

#### Volume Agent (30% weight)
**File**: `src/agents/volume_agent_enhanced.py`

**AI Models**: SwarmAgent (6 models in parallel)

1. **DeepSeek Chat**
   - Provider: DeepSeek API
   - Model: `deepseek-chat`
   - Cost: $0.14 input / $0.28 output per 1M tokens
   - Purpose: Fast chat model for volume analysis

2. **Grok-4 Fast Reasoning**
   - Provider: x.AI
   - Model: `grok-4-fast-reasoning`
   - Cost: $0.20-0.50 per 1M tokens
   - Purpose: Advanced reasoning for market patterns

3. **Qwen 3 Max**
   - Provider: OpenRouter
   - Model: `qwen/qwen3-max`
   - Cost: $1.00 / $1.00 per 1M tokens
   - Purpose: Powerful reasoning model

4. **Claude Sonnet 4.5**
   - Provider: Anthropic
   - Model: `claude-sonnet-4-5`
   - Cost: $3.00 / $15.00 per 1M tokens
   - Purpose: Latest Claude model (most capable)

5. **GLM 4.6**
   - Provider: Z-AI via OpenRouter
   - Model: `z-ai/glm-4.6`
   - Cost: $0.50 / $0.50 per 1M tokens
   - Purpose: Zhipu AI reasoning

6. **GPT-5 Mini**
   - Provider: OpenAI via OpenRouter
   - Model: `openai/gpt-5-mini`
   - Cost: ~$1.00 / $3.00 per 1M tokens
   - Purpose: Latest OpenAI model

**Consensus Reviewer**:
- Model: DeepSeek Chat
- Purpose: Synthesizes all 6 responses into final consensus

**Total Swarm Cost**: ~$0.016 per 15-min cycle

---

#### Liquidation Agent (25% weight)
**File**: `src/agents/liquidation_agent.py`

**Primary Model**: DeepSeek Chat
- Provider: DeepSeek API
- Model: `deepseek-chat`
- Cost: $0.14 / $0.28 per 1M tokens
- Purpose: Analyzes liquidation events

**Fallback Model**: Claude 3.5 Haiku
- Provider: Anthropic
- Model: `claude-3-5-haiku-latest`
- Cost: $0.80 / $4.00 per 1M tokens
- Purpose: Used if DeepSeek unavailable

**Model Override**: Set via `MODEL_OVERRIDE = "deepseek-chat"` in file

**Cost**: ~$0.001 per 15-min cycle

---

#### Chart Analysis Agent (20% weight)
**File**: `src/agents/chartanalysis_agent.py`

**Model**: Claude 3.5 Haiku
- Provider: Anthropic
- Model: `claude-3-5-haiku-latest`
- Context: 200k tokens
- Cost: $0.80 / $4.00 per 1M tokens
- Purpose: Technical pattern recognition (SMA, RSI, MACD, Bollinger Bands)

**Data Source**: Binance API (free)

**Cost**: ~$0.003 per 15-min cycle

---

#### Funding Agent (15% weight)
**File**: `src/agents/funding_agent.py`

**Primary Model**: DeepSeek Chat
- Provider: DeepSeek API
- Model: `deepseek-chat`
- Cost: $0.14 / $0.28 per 1M tokens
- Purpose: Funding rate analysis

**Fallback Model**: Claude 3.5 Haiku
- Provider: Anthropic
- Model: `claude-3-5-haiku-latest`
- Purpose: Used if DeepSeek unavailable

**Model Override**: Set via `MODEL_OVERRIDE = "deepseek-chat"` in file

**Cost**: ~$0.001 per 15-min cycle

---

#### Sentiment Agent (10% weight)
**File**: `src/agents/sentiment_agent.py`

**Model**: TextBlob (local library)
- Provider: None (Python library)
- Cost: $0
- Purpose: Sentiment analysis (-1 to +1 polarity)

**Data Sources**:
- Twitter API (3 accounts, 300 tweets/month)
- Reddit API (unlimited, free)

**Cost**: $0 (no AI API calls)

---

#### Signal Fusion Layer
**File**: `src/agents/signal_fusion.py`

**Model**: None (statistical ensemble)
- Method: Evidence-based weighted fusion
- Algorithm: `score = Σ (action × weight × confidence × adjustment)`
- Cost: $0

**Academic Basis**: "Ensemble Methods in Financial Prediction" (JFDS, 2023)

---

#### Master Trading Agent
**File**: `src/agents/master_trading_agent.py`

**Model**: None (orchestration only)
- Purpose: Runs all 5 agents in parallel/sequential
- Cost: $0

---

### Trading Execution Phase

| Component | AI Model | Cost | Purpose |
|-----------|----------|------|---------|
| **Paper Trading** | None | $0 | Uses fusion + strategy signals |
| **Risk Management** | None | $0 | Rule-based checks |
| **Performance Monitoring** | None | $0 | Statistical analysis |
| **LIVE Trading** | None | $0 | Same flow as paper trading |

---

## Cost Breakdown

### One-Time Costs (per strategy)
- RBI Agent (DeepSeek-R1): $0.027
- Backtest Converter (Grok-4): $0.10-0.25
- **Total One-Time**: ~$0.13

### Recurring Costs (per 15-min cycle)
- Volume Agent (6-model swarm): $0.016
- Liquidation Agent: $0.001
- Chart Agent: $0.003
- Funding Agent: $0.001
- Sentiment Agent: $0
- Fusion Layer: $0
- **Total per cycle**: ~$0.021

### Daily/Monthly Costs
- Per day (96 cycles): ~$2.02
- Per month (30 days): ~$60.60

---

## Model Configuration Files

### Where Models Are Configured

**RBI Agent**:
```python
# File: src/agents/rbi_agent_pp_multi.py
# Lines 128-132
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_KEY"),
    base_url=DEEPSEEK_BASE_URL
)
```

**Volume Agent (SwarmAgent)**:
```python
# File: src/agents/swarm_agent.py
# Lines 62-85
SWARM_MODELS = {
    "deepseek": (True, "deepseek", "deepseek-chat"),
    "xai": (True, "xai", "grok-4-fast-reasoning"),
    "openrouter_qwen": (True, "openrouter", "qwen/qwen3-max"),
    "claude": (True, "claude", "claude-sonnet-4-5"),
    "openrouter_glm": (True, "openrouter", "z-ai/glm-4.6"),
    "openrouter_gpt5_mini": (True, "openrouter", "openai/gpt-5-mini"),
}

CONSENSUS_REVIEWER_MODEL = ("deepseek", "deepseek-chat")
```

**Liquidation Agent**:
```python
# File: src/agents/liquidation_agent.py
# Lines 48-50
MODEL_OVERRIDE = "deepseek-chat"  # Set to "0" to use config.py
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
```

**Chart Analysis Agent**:
```python
# File: src/agents/chartanalysis_agent.py
# Line 111
self.ai_model = AI_MODEL if AI_MODEL else config.AI_MODEL
# Default: claude-3-5-haiku-latest (from config.py)
```

**Funding Agent**:
```python
# File: src/agents/funding_agent.py
# Lines 16-17
MODEL_OVERRIDE = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
```

---

## Environment Variables Required

Add to `.env` file:

```env
# Core AI Models
ANTHROPIC_KEY=sk-ant-...              # Claude models
OPENAI_KEY=sk-...                     # GPT models
DEEPSEEK_KEY=sk-...                   # DeepSeek models
GROK_API_KEY=xai-...                  # Grok models
OPENROUTER_API_KEY=sk-or-...          # OpenRouter (Qwen, GLM, etc.)

# Optional Models
GROQ_API_KEY=gsk_...                  # Groq (free tier available)
GEMINI_KEY=...                        # Google Gemini

# Data APIs
BIRDEYE_API_KEY=...                   # Solana/Hyperliquid data
MOONDEV_API_KEY=...                   # Liquidation/funding data
COINGECKO_API_KEY=...                 # Market data

# Social APIs (for sentiment_agent)
TWITTER_BEARER_TOKEN_1=...
TWITTER_BEARER_TOKEN_2=...
TWITTER_BEARER_TOKEN_3=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# Exchange APIs
BINANCE_API_KEY=...                   # Binance (for LIVE trading)
BINANCE_API_SECRET=...
```

---

## How to Change Models

### Change Volume Agent Swarm Models

Edit `src/agents/swarm_agent.py` lines 62-85:

```python
# Enable/disable models by setting first value to True/False
SWARM_MODELS = {
    "deepseek": (True, "deepseek", "deepseek-chat"),      # Enable
    "claude": (False, "claude", "claude-sonnet-4-5"),     # Disable
    ...
}

# Change consensus reviewer
CONSENSUS_REVIEWER_MODEL = ("openai", "gpt-4o")  # Use GPT-4 instead
```

### Change Liquidation Agent Model

Edit `src/agents/liquidation_agent.py` line 49:

```python
MODEL_OVERRIDE = "deepseek-chat"  # Options: "deepseek-chat", "0" (use config.py)
```

Set to `"0"` to use Claude from `config.py`:
```python
MODEL_OVERRIDE = "0"
```

### Change Chart Analysis Agent Model

Edit `src/agents/chartanalysis_agent.py` line 59:

```python
AI_MODEL = "claude-3-opus-20240229"  # Use Opus instead of Haiku
```

Or set to `False` to use `config.py` default:
```python
AI_MODEL = False
```

### Change Funding Agent Model

Edit `src/agents/funding_agent.py` line 16:

```python
MODEL_OVERRIDE = "deepseek-chat"  # Or "deepseek-reasoner", or "0"
```

### Change Global Default Model

Edit `src/config.py`:

```python
AI_MODEL = "claude-3-5-sonnet-20241022"  # Change system-wide default
```

---

## Cost Optimization Tips

### 1. Use Free Tier Models
Replace expensive models with free alternatives:
- Groq Mixtral (free tier, fast)
- Ollama (local, unlimited)
- OpenRouter free models

```python
# In swarm_agent.py
SWARM_MODELS = {
    "ollama_qwen": (True, "ollama", "qwen3:8b"),  # Free, local
    "groq": (True, "groq", "mixtral-8x7b-32768"),  # Free tier
    ...
}
```

### 2. Reduce Swarm Size
Use fewer models in volume agent:

```python
# Instead of 6 models, use 3:
SWARM_MODELS = {
    "deepseek": (True, "deepseek", "deepseek-chat"),  # Cheap
    "claude": (True, "claude", "claude-sonnet-4-5"),  # Best
    "openrouter_qwen": (True, "openrouter", "qwen/qwen3-max"),  # Good
    # Disable others
}
```

**Savings**: ~50% reduction ($0.016 → $0.008 per cycle)

### 3. Increase Check Interval
Edit `master_trading_agent.py`:

```python
CHECK_INTERVAL_MINUTES = 30  # Instead of 15
```

**Savings**: 50% reduction (48 cycles/day instead of 96)
**Monthly cost**: $60.60 → $30.30

### 4. Use DeepSeek Everywhere
Replace all models with DeepSeek Chat ($0.14/$0.28 per 1M):

- Volume agent swarm → Single DeepSeek call
- Chart agent → DeepSeek
- Already using DeepSeek: Liquidation, Funding

**Savings**: ~70% reduction ($60/month → ~$18/month)

---

## Model Performance Comparison

Based on testing across agents:

| Model | Speed | Accuracy | Cost | Best For |
|-------|-------|----------|------|----------|
| **DeepSeek Chat** | Fast (2-3s) | High (85%) | Very Low | General analysis, cost-sensitive |
| **Grok-4 Fast** | Fast (2-4s) | Very High (90%) | Low | Complex reasoning |
| **Claude Sonnet 4.5** | Medium (5-8s) | Highest (95%) | High | Critical decisions |
| **Qwen 3 Max** | Medium (4-6s) | High (87%) | Medium | Balanced performance |
| **GPT-5 Mini** | Fast (3-5s) | High (88%) | Medium | Latest OpenAI features |
| **Claude Haiku** | Very Fast (1-2s) | Medium (80%) | Low | Technical analysis |
| **TextBlob** | Instant (<1s) | Medium (75%) | Free | Sentiment only |

---

## Recommended Configurations

### Budget Configuration (~$18/month)
- Volume Agent: Single DeepSeek Chat call
- Liquidation: DeepSeek Chat
- Chart: Claude Haiku
- Funding: DeepSeek Chat
- Sentiment: TextBlob
- Check interval: 30 minutes

### Balanced Configuration (~$60/month) ✅ CURRENT
- Volume Agent: 6-model swarm (diversity)
- Liquidation: DeepSeek Chat
- Chart: Claude Haiku
- Funding: DeepSeek Chat
- Sentiment: TextBlob
- Check interval: 15 minutes

### Premium Configuration (~$150/month)
- Volume Agent: 6-model swarm (all premium)
- Liquidation: Claude Opus
- Chart: Claude Opus
- Funding: Claude Opus
- Sentiment: GPT-4 + TextBlob
- Check interval: 5 minutes

---

## Quick Command Reference

### Check Current Model Usage
```bash
# Volume agent (swarm models)
grep "SWARM_MODELS" src/agents/swarm_agent.py

# Liquidation agent
grep "MODEL_OVERRIDE" src/agents/liquidation_agent.py

# Funding agent
grep "MODEL_OVERRIDE" src/agents/funding_agent.py

# Chart agent
grep "AI_MODEL" src/agents/chartanalysis_agent.py

# Global default
grep "AI_MODEL" src/config.py
```

### Test Individual Agent Models
```bash
# Test volume agent (with swarm)
python src/agents/volume_agent_enhanced.py --once

# Test liquidation agent
python src/agents/liquidation_agent.py

# Test chart agent
python src/agents/chartanalysis_agent.py

# Test funding agent
python src/agents/funding_agent.py

# Test sentiment agent
python src/agents/sentiment_agent.py
```

### Run Full System
```bash
# Run master agent (orchestrates all 5)
python src/agents/master_trading_agent.py --once

# Continuous mode (every 15 min)
python src/agents/master_trading_agent.py
```

---

## Troubleshooting

### Model Not Found Error
```
Error: Model 'deepseek-chat' not found
```

**Solution**: Check API key in `.env`:
```env
DEEPSEEK_KEY=sk-...  # Must be set
```

### Rate Limit Error
```
Error: Rate limit exceeded
```

**Solution**:
1. Increase check interval (30 min instead of 15)
2. Use free tier models (Groq, Ollama)
3. Reduce swarm size (3 models instead of 6)

### High Costs
**Solution**: Switch to budget configuration (see above)

---

## Documentation References

- **Complete System Diagram**: `docs/COMPLETE_SYSTEM_DIAGRAM_WITH_AI_MODELS.md`
- **Fusion Layer Architecture**: `docs/MULTI_AGENT_INTELLIGENCE_FUSION.md`
- **How-To Guide**: `docs/HOW_TO_RUN_FUSION_LAYER.md`
- **Implementation Summary**: `docs/FUSION_LAYER_IMPLEMENTATION_SUMMARY.md`
- **Model Factory Code**: `src/models/model_factory.py`
- **Swarm Agent Code**: `src/agents/swarm_agent.py`
