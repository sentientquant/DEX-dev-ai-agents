# AI Models Configuration - RBI Trading System

Complete breakdown of all AI models used in your trading system.

---

## 🎯 Primary AI System: Multi-Model Swarm

Your RBI Research Trade Flow uses a **multi-model AI swarm** for strategy verification and market analysis. This provides diverse perspectives and reduces single-model bias.

---

## 🌟 Active AI Models (Currently Running)

### Swarm Agent Configuration
**Location:** `src/agents/swarm_agent.py` (Lines 71-94)

Your system is configured to use **5 AI models in parallel**:

| Model | Provider | Model Name | Purpose | Cost |
|-------|----------|------------|---------|------|
| **Qwen 3 32B** | Groq (native API) | `qwen/qwen3-32b` | Ultra-fast reasoning | $0.50/1M tokens |
| **DeepSeek Chat** | OpenRouter | `deepseek/deepseek-chat` | Fast reasoning | $0.14-$0.28/1M tokens |
| **Grok 4 Fast** | xAI (native API) | `grok-4-fast-reasoning` | Code analysis & reasoning | Premium |
| **GLM 4.6** | OpenRouter | `z-ai/glm-4.6` | AI reasoning | $0.50/1M tokens |
| **Llama 3.3 70B** | Groq (native API) | `llama-3.3-70b-versatile` | Large model with 128k context | $0.59/1M tokens |

---

## 🔄 How the Swarm Works

### Strategy Verification Process

When your RBI system analyzes a strategy, it follows this 3-step verification:

**Step 1: Technical Snapshot** *(No AI)*
- Calculates real market indicators from live data
- EMA trends, RSI, ATR, Bollinger Bands, Volume
- Uses strategy's actual parameter settings

**Step 2: Logic Verification** *(No AI)*
- Checks if strategy parameters match market conditions
- Verifies bracket calculations are mathematically sound
- Ensures signal logic is consistent with market reality

**Step 3: AI Swarm Consensus** *(5 AI Models)*
- All 5 models analyze the technical snapshot + strategy logic in parallel
- Each model provides independent verdict
- Final consensus based on majority agreement across models

### Example Swarm Query

```python
# From trading_modes/core/strategy_verification_agent.py

result = swarm.query(prompt=f"""
Analyze this VolatilityBracket strategy:
- Symbol: BTC
- Cycles run: 50
- Signals: 0 (NO SIGNALS)
- Current price: $84,549
- Upper bracket: $85,200 (+0.77%)
- Lower bracket: $83,900 (-0.77%)

Market indicators:
- EMA trend: SIDEWAYS (±0.2%)
- RSI: 52 (neutral)
- ATR: 1.2%
- Bollinger width: 2.1%

Is this strategy working correctly or broken?
""")

# Result includes:
# - Individual responses from 5 models
# - Consensus summary based on model agreement
# - Confidence score (0-100)
# - Verdict: WORKING | BROKEN | NEEDS_TUNING
```

---

## 📊 Model Usage in Your System

### Market Analysis Agent
**File:** `trading_modes/core/market_analysis_agent.py`

**Configured Provider:** `openrouter` (line 147)
```python
self.ai_analyst = get_market_analysis_agent('openrouter')
```

**Models Used:**
- Primary: Uses **Strategy Verification Agent** (which uses the 5-model swarm)
- Fallback: OpenRouter API (access to 200+ models)

---

## 🎛️ Model Factory Available Models

Your system has access to these model providers via `src/models/model_factory.py`:

| Provider | Status | Models Available | API Key |
|----------|--------|------------------|---------|
| **Claude** | ✅ Active | claude-3-5-haiku-latest, claude-sonnet-4-5, claude-opus-4 | ANTHROPIC_KEY |
| **Groq** | ✅ Active | qwen/qwen3-32b, llama-3.3-70b-versatile | GROQ_API_KEY |
| **xAI (Grok)** | ✅ Active | grok-4-fast-reasoning | GROK_API_KEY |
| **OpenRouter** | ✅ Active | 200+ models (Gemini, GPT-5, DeepSeek, etc.) | OPENROUTER_API_KEY |
| **OpenAI** | ✅ Active | gpt-5, gpt-4-turbo | OPENAI_KEY |
| **Gemini** | ⚠️ Not configured | gemini-2.5-flash, gemini-2.5-pro | GEMINI_KEY (missing) |
| **DeepSeek** | ⚠️ Not configured | deepseek-chat | DEEPSEEK_KEY (missing) |

---

## 🚀 Default Models by Component

### Main Trading System
- **Strategy Analysis:** 5-model swarm (Groq Qwen, DeepSeek, xAI Grok, GLM, Groq Llama)
- **Consensus Method:** Majority agreement across all models
- **Fallback:** OpenRouter (any available model)

### Groq Configuration
**File:** `src/models/model_factory.py`
**Default Model:** `qwen/qwen3-32b`
- Context: 32k tokens
- Speed: Very fast
- Cost: $0.50/$0.50 per 1M tokens

### Claude Configuration
**File:** `src/models/model_factory.py`
**Available Models:** `claude-3-5-haiku-latest`, `claude-sonnet-4-5`, `claude-opus-4`
**Note:** Not currently in swarm configuration per user preference

### OpenRouter Configuration
**File:** `src/models/openrouter_model.py`
**Default Model:** `x-ai/grok-code-fast-1`
**Available:** 200+ models from various providers

---

## 🔧 How to Change Models

### Option 1: Edit Swarm Configuration
**File:** `src/agents/swarm_agent.py` (Lines 71-94)

```python
SWARM_MODELS = {
    # Current configuration (5 models active)
    "groq": (True, "groq", "qwen/qwen3-32b"),  # ✅ Native Groq API
    "deepseek": (True, "openrouter", "deepseek/deepseek-chat"),  # ✅ Via OpenRouter
    "xai": (True, "xai", "grok-4-fast-reasoning"),  # ✅ Native xAI API
    "openrouter_glm": (True, "openrouter", "z-ai/glm-4.6"),  # ✅ Via OpenRouter
    "groq_llama": (True, "groq", "llama-3.3-70b-versatile"),  # ✅ Native Groq API - 128k context

    # Disable by setting to False
    "openai": (False, "openai", "gpt-5"),  # ❌ Disabled

    # Add new model via OpenRouter
    "my_model": (True, "openrouter", "model-name"),
}
```

### Option 2: Change Market Analysis Provider
**File:** `trading_modes/RBI_RESEARCH_TRADE_FLOW.py` (Line 147)

```python
# Current: Uses multi-model swarm via openrouter
self.ai_analyst = get_market_analysis_agent('openrouter')

# Change to specific provider:
# self.ai_analyst = get_market_analysis_agent('claude')
# self.ai_analyst = get_market_analysis_agent('groq')
```

---

## 💰 Cost Considerations

### Current Configuration Costs (per 1M tokens)

**Input → Output:**
- Groq Qwen 3 32B: $0.50 → $0.50
- DeepSeek Chat (OpenRouter): $0.14 → $0.28
- xAI Grok 4 Fast: Premium pricing (native API)
- GLM 4.6 (OpenRouter): $0.50 → $0.50
- Groq Llama 3.3 70B: $0.59 → $0.79 (128k context window!)

**Estimated Cost Per Strategy Analysis:**
- Technical snapshot: $0 (no AI)
- Logic verification: $0 (no AI)
- AI swarm consensus (5 models): ~$0.03-$0.10 per analysis
- **Daily cost (100 cycles):** ~$3-$10

---

## 📈 Performance Benchmarks

### Model Response Times (approximate)

| Model | Avg Response Time | Tokens/sec |
|-------|------------------|------------|
| Groq (Qwen 3 32B) | 0.5-1.0s | ~500-1000 |
| DeepSeek (via OpenRouter) | 1.0-2.0s | ~250-500 |
| xAI Grok (native API) | 0.5-1.2s | ~400-800 |
| GLM 4.6 (via OpenRouter) | 1.0-2.0s | ~250-500 |
| Groq (Llama 3.3 70B) | 0.7-1.4s | ~400-700 |

**Total Swarm Query Time:** 1-3 seconds (parallel execution, limited by slowest model)

---

## 🎯 Recommended Configuration

### For Production Trading (Current Setup) ✅

```python
# User-specified configuration - 5 MODELS ACTIVE
# Mix of native APIs (Groq x2, xAI) and OpenRouter for optimal performance
SWARM_MODELS = {
    "groq": (True, "groq", "qwen/qwen3-32b"),  # Native Groq API - Ultra fast
    "deepseek": (True, "openrouter", "deepseek/deepseek-chat"),  # Via OpenRouter
    "xai": (True, "xai", "grok-4-fast-reasoning"),  # Native xAI API
    "openrouter_glm": (True, "openrouter", "z-ai/glm-4.6"),  # Via OpenRouter
    "groq_llama": (True, "groq", "llama-3.3-70b-versatile"),  # Groq Llama 3.3 70B - 128k context!
}
```

### For Low-Cost Testing
```python
# Fastest, cheapest - 3 models
SWARM_MODELS = {
    "groq": (True, "groq", "qwen/qwen3-32b"),  # Ultra-fast native API
    "deepseek": (True, "openrouter", "deepseek/deepseek-chat"),  # Cheapest via OpenRouter
    "openrouter_gpt5_mini": (True, "openrouter", "openai/gpt-5-mini"),  # Low cost
}
```

### For Maximum Accuracy (High Cost)
```python
# Best quality, highest cost - 7+ models
SWARM_MODELS = {
    "groq": (True, "groq", "qwen/qwen3-32b"),  # Keep for speed
    "claude_opus": (True, "openrouter", "anthropic/claude-opus-4.1"),  # Best reasoning
    "gpt5": (True, "openai", "gpt-5"),  # OpenAI flagship
    "openrouter_qwen": (True, "openrouter", "qwen/qwen3-max"),  # Advanced reasoning
    "deepseek_r1": (True, "openrouter", "deepseek/deepseek-r1-0528"),  # Deep reasoning
    "xai": (True, "openrouter", "x-ai/grok-code-fast-1"),  # xAI perspective
    "openrouter_glm": (True, "openrouter", "z-ai/glm-4.6"),  # GLM perspective
}
```

---

## 🔍 Model Selection Strategy

### Why Multiple Models?

**Diversity Reduces Bias:**
- Each model has different training data
- Different reasoning approaches
- Cross-validation of strategy health

**Consensus Improves Accuracy:**
- 5 models agreeing = very high confidence
- Split verdict (3-2 or 4-1) = moderate confidence
- Major disagreement = needs human review

**Example Verdict:**

```text
Groq (Qwen 3 32B): "Strategy working correctly - consolidation phase"
DeepSeek: "Confirmed working - brackets properly calculated"
xAI Grok: "No issues detected - waiting for breakout"
GLM 4.6: "Healthy strategy - no signals expected in current conditions"
Groq (Llama 3.3 70B): "Strategy operating as designed - proper bracket calculations verified"

Consensus: STRATEGY_WORKING (100% confidence - unanimous agreement)
```

---

## 📝 Summary

Your RBI trading system uses:

✅ **5 AI models in parallel** for strategy verification
✅ **Native APIs** - Groq x2 (Qwen 3 32B + Llama 3.3 70B) and xAI (Grok 4) for maximum speed
✅ **OpenRouter** - 2/5 models (DeepSeek, GLM) for flexibility
✅ **Multi-model swarm** - Reduces single-model bias
✅ **Production-grade** verification system
✅ **Hybrid approach** - Prioritizes native APIs (3/5) with OpenRouter fallback (2/5)

**Total Cost:** ~$3-10/day for 100 strategy analyses
**Accuracy:** Very high (5-model consensus)
**Speed:** Fast (1-3 seconds per analysis, parallel execution)

---

**Last Updated:** November 23, 2025
