# COMPLETE SIGNAL-TO-EXECUTION FLOW

**System**: SCANNER_SWARM_TRADE_FLOW.py
**Mode**: PAPER or LIVE
**Date**: 2025-11-16

---

## 📊 HIGH-LEVEL OVERVIEW

```
SCANNER → AI SWARM → ARBITER → RISK ENGINE → ORDER MANAGER → EXECUTION → DATABASE
  (Math)    (5 AIs)  (Evidence)  (Dynamic)    (SL/TP Calc)   (Trade)    (Storage)
```

**Total Steps**: 6 main phases
**Duration**: ~60-220 seconds per cycle
**Cost**: $0.05-0.15 per cycle (AI validation only)

---

## 🔄 DETAILED FLOW (Step-by-Step)

### STEP 1: SCANNER DISCOVERY (Math-Only, No AI)

**Location**: Lines 500-570
**Duration**: 3-5 minutes (for 432 pairs)
**Cost**: $0.00

#### 1.1 Get Universe
```python
scanner = BinanceAltcoinScanner()
all_pairs = scanner.get_all_usdt_pairs()
# Returns: 432 USDT pairs from Binance
```

**Output**: List of all tradeable USDT pairs

---

#### 1.2 Pre-Filter (Objective Criteria)
```python
filtered = scanner.pre_filter(all_pairs)

# Filters:
- Volume 24h > $10M
- Price > $0.01
- Market cap > $1B (proxy via volume)
```

**Output**: ~52 quality tokens (88% reduction)

---

#### 1.3 Momentum Scoring (5 Math Indicators)
```python
scored = scanner.score_all_tokens(filtered)

# Indicators (100 points total):
1. RSI Trend-Following (20 pts) - PMC 2023: 774% returns
2. Volume-Price Correlation (25 pts) - REPEC 2023
3. Short-Term Momentum (20 pts) - 2-4 week window
4. Relative Strength vs BTC (15 pts) - Outperformance
5. Persistence Check (20 pts) - Volume autocorrelation
```

**Scoring Thresholds**:
- STRONG: ≥75 points
- MODERATE: 60-74 points
- WEAK: 45-59 points

**Output**: Top 2-3 STRONG candidates

---

#### 1.4 Cache to Database
```python
scanner.save_results(scored)

# Saved to:
- src/data/scanner/scanner_results.json
- src/data/scanner/scan_history.csv
- Database: altcoin_pairs table (cached 24h)
```

**Example Output**:
```
Top 3 STRONG Tokens:
1. STRKUSDT - 100 pts (RSI 67, RVOL 3.3x, +81% 2w)
2. RESOLVUSDT - 95 pts (RSI 71, RVOL 1.8x, +245% 2w)
3. DCRUSDT - 80 pts (RSI 58, RVOL 1.7x, +96% 2w)
```

---

### STEP 2: GET MARKET DATA (Real-Time Binance API)

**Location**: Lines 575-580
**Duration**: 1-2 seconds
**Cost**: $0.00 (free Binance API)

```python
# For each STRONG candidate:
ticker = BinanceTruthAPI.token_overview(symbol)

# Fetches:
- Current price (USD)
- 24h volume (USD)
- RSI (14-period)
- MACD histogram
- Volume ratio (current / average)
```

**Output**: Real-time market data for analysis

---

### STEP 3: AI SWARM VALIDATION (5 Independent Models)

**Location**: Lines 581-630
**Duration**: 15-30 seconds
**Cost**: $0.03-0.10 per token

#### 3.1 Generate Prompt
```python
prompt = f"""
INDEPENDENT trading analysis for {symbol}.

CURRENT MARKET DATA:
- Price: ${price:.6f}
- 24h Change: {change_24h:+.2f}%
- 24h Volume: ${volume_24h:,.0f}
- RSI (14): {rsi:.1f}
- MACD Histogram: {macd:.6f}
- Volume vs Avg: {volume_ratio:.2f}x

PROVIDE YOUR INDEPENDENT RECOMMENDATION:

1. Signal: BUY, SELL, or NEUTRAL
2. Confidence: 0-100%
3. Key Reasoning: 2-3 sentences

IMPORTANT:
- Be contrarian if data doesn't support bullish bias
- RSI >70 = overbought risk
- MACD negative = bearish momentum
- Low volume = weak conviction
"""
```

---

#### 3.2 Parallel AI Queries (5 Models)
```python
# Models queried in parallel:
1. GROQ_QWEN (Qwen 2.5 72B)
2. OPENROUTER_GLM (GLM-4)
3. XAI (Grok 2)
4. CLAUDE (Claude 3.5 Sonnet)
5. OPENROUTER_DEEPSEEK_R1 (DeepSeek R1)
```

**Response Time**: 1-18 seconds per model (parallel execution)

---

#### 3.3 Parse Individual Responses (Voting-Based)
```python
# Extract from each model:
ai_signals = []
ai_confidences = []

for model_name, response_data in responses.items():
    response = response_data.get('response', '')

    # Extract signal declaration
    if 'Signal: BUY' in response:
        ai_signals.append('BUY')
    elif 'Signal: SELL' in response:
        ai_signals.append('SELL')
    elif 'Signal: NEUTRAL' in response:
        ai_signals.append('NEUTRAL')

    # Extract confidence percentage
    conf_match = re.search(r'Confidence:?\s*(\d{1,3})%', response)
    if conf_match:
        ai_confidences.append(int(conf_match.group(1)))
```

**Example Output**:
```
AI Votes for DCR:
- GROQ: NEUTRAL (30%)
- GLM: NEUTRAL (75%)
- XAI: NEUTRAL (65%)
- CLAUDE: NEUTRAL (62%)
- DEEPSEEK: NEUTRAL (65%)

Consensus: NEUTRAL (avg 59%)
```

---

#### 3.4 Determine Consensus (Majority Vote)
```python
buy_count = ai_signals.count('BUY')
neutral_count = ai_signals.count('NEUTRAL')
sell_count = ai_signals.count('SELL')

if buy_count >= 3:  # Majority (3/5)
    ai_signal = "BUY"
elif sell_count >= 3:
    ai_signal = "SELL"
else:
    ai_signal = "NEUTRAL"

ai_confidence = sum(ai_confidences) / len(ai_confidences)
```

---

#### 3.5 Apply Text-Based Confidence Penalties
```python
consensus_lower = consensus_summary.lower()

if 'weak' in consensus_lower:
    ai_confidence -= 15

if 'lacking' in consensus_lower:
    ai_confidence -= 10
```

---

### STEP 4: ARBITER DECISION (Evidence-Based Logic)

**Location**: Lines 631-760
**Duration**: <1 second
**Cost**: $0.00

#### 4.1 Volume Divergence Veto (Hard Stop)
```python
if volume_ratio < 0.5:
    # VETO: Manipulation risk / thin orderbook
    # Action: SKIP trade for safety
    continue  # Move to next token
```

**Example**:
```
STRK: Volume 0.26x < 0.5x threshold → VETOED
DCR: Volume 0.19x < 0.5x threshold → VETOED
```

---

#### 4.2 Apply Asymmetric Confidence Thresholds
```python
# EVIDENCE-BASED THRESHOLDS
BUY_CONFIDENCE_MIN = 75.0%      # MDPI 2024, Industry 75%+
BUY_CONFIDENCE_STRONG = 85.0%   # Random Forest 85%
SELL_CONFIDENCE_MIN = 65.0%     # Loss aversion λ=2.25
SELL_CONFIDENCE_STRONG = 80.0%  # Fast exit
HOLD_THRESHOLD = 50.0%          # Baseline predictive power

# Apply thresholds by signal type:
if ai_signal == "BUY":
    if ai_confidence < BUY_CONFIDENCE_MIN:
        ai_signal = "NEUTRAL"  # Downgrade weak BUY
    elif ai_confidence >= BUY_CONFIDENCE_STRONG:
        # Flag as STRONG BUY (1.2x position size)

elif ai_signal == "SELL":
    if ai_confidence < SELL_CONFIDENCE_MIN:
        ai_signal = "NEUTRAL"  # Insufficient conviction
    elif ai_confidence >= SELL_CONFIDENCE_STRONG:
        # Flag as STRONG SELL (immediate exit)
```

**Example**:
```
RESOLV:
- Scanner: BUY (75%)
- AI: SELL unanimous (64% avg)
- AI confidence 64% < SELL_MIN 65%
- Action: Downgraded to NEUTRAL → SKIP
```

---

#### 4.3 Negative MACD Override
```python
if macd_hist < 0 and rsi > 35 and ai_signal == "BUY":
    ai_signal = "NEUTRAL"  # Downgrade conflicting signal
```

---

#### 4.4 Decision Matrix (Scanner vs AI)
```python
# Case 1: AGREEMENT (Scanner BUY + AI BUY)
if scanner_signal == "BUY" and ai_signal == "BUY":
    final_action = "BUY"
    final_confidence = (scanner_confidence + ai_confidence) / 2

    is_strong = final_confidence >= BUY_CONFIDENCE_STRONG
    size_multiplier = calculate_fractional_kelly(final_confidence, is_strong_signal=is_strong)

    if size_multiplier > 0:
        # ✅ EXECUTE TRADE
    else:
        # ⏭️ SKIP (confidence too low)

# Case 2: PARTIAL AGREEMENT (Scanner BUY + AI NEUTRAL)
elif scanner_signal == "BUY" and ai_signal == "NEUTRAL":
    final_action = "BUY"
    final_confidence = scanner_confidence * 0.6  # Reduce for disagreement
    size_multiplier = calculate_fractional_kelly(final_confidence) * 0.5  # Extra 50% reduction

    if final_confidence >= BUY_CONFIDENCE_MIN and size_multiplier > 0:
        # ⚠️ EXECUTE with caution (reduced size)
    else:
        # ⏭️ SKIP

# Case 3: CONFLICT (Scanner BUY + AI SELL)
elif scanner_signal == "BUY" and ai_signal == "SELL":
    final_action = "SKIP"
    # ❌ NO TRADE (conflict for safety)
```

---

#### 4.5 Fractional Kelly Position Sizing
```python
def calculate_fractional_kelly(confidence, max_size=0.25, is_strong_signal=False):
    if confidence < 65:
        return 0.0  # Below SELL threshold
    elif confidence >= 95:
        size = 0.25  # Quarter Kelly (max safe)
    elif confidence >= 85:
        size = 0.20  # Strong conviction
    elif confidence >= 75:
        size = 0.15  # BUY threshold met
    elif confidence >= 65:
        size = 0.10  # SELL threshold met

    # Boost for strong signals (85%+ BUY, 80%+ SELL)
    if is_strong_signal and size > 0:
        size *= 1.2  # 20% boost
        size = min(size, max_size)  # Cap at max

    return size
```

**Example**:
```
Confidence 78% BUY → size_multiplier = 0.15 (15% of max position)
Confidence 88% STRONG BUY → size_multiplier = 0.24 (0.20 × 1.2)
```

---

#### 4.6 Create Arbitration Result
```python
if final_action == "BUY" and size_multiplier > 0:
    results[symbol] = ArbitrationResult(
        action="BUY",
        confidence=final_confidence,
        size_multiplier=size_multiplier,
        reasoning=reasoning,
        contributing_signals=[],
        metadata={
            'scanner_signal': scanner_signal,
            'scanner_confidence': scanner_confidence,
            'ai_signal': ai_signal,
            'ai_confidence': ai_confidence,
            'ai_votes': {'BUY': buy_count, 'NEUTRAL': neutral_count, 'SELL': sell_count},
            'market_data': market_data,
            'position_sizing_method': 'fractional_kelly'
        }
    )
```

---

### STEP 5: DYNAMIC RISK ENGINE + ORDER MANAGER

**Location**: Lines 828-961
**Duration**: 2-5 seconds
**Cost**: $0.00

#### 5.1 Get Real-Time OHLCV Data
```python
from risk_management.binance_truth_paper_trading import BinanceTruthAPI

ohlcv = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe='15m', days_back=3)
entry_price = float(ohlcv['close'].iloc[-1])
```

**Data Fetched**: Last 3 days of 15-minute candles (~288 candles)

---

#### 5.2 Update Market Regime
```python
self.risk_engine.update_regime(ohlcv)

# Detects regime based on volatility:
- VOLATILE: ATR > mean + 1.5 std
- CHOPPY: ATR < mean - 0.5 std
- TRENDING: Between thresholds
```

**Example Output**:
```
Market Regime: TRENDING
```

---

#### 5.3 Score Token Risk
```python
token_data = BinanceTruthAPI.token_overview(symbol)
volume_24h_usd = token_data.get('volume_24h_usd', 1_000_000)
market_cap_usd = token_data.get('market_cap_usd', 100_000_000)
avg_spread_bps = token_data.get('spread_bps', 10)

self.risk_engine.update_token_profile(
    symbol, ohlcv, volume_24h_usd, market_cap_usd, avg_spread_bps
)

token_profile = self.risk_engine.token_profiles[symbol]

# Risk score calculation:
- Volatility (30%)
- Liquidity depth (25%)
- Spread cost (20%)
- Market cap (15%)
- Volume quality (10%)
```

**Example Output**:
```
Token Risk Score: 4.2 (lower = safer)
```

---

#### 5.4 Update Dynamic Limits
```python
self.risk_engine.update_limits(equity_usd, pnl_history)

# Adjusts limits based on:
- Recent PnL performance (last 30 days)
- Current drawdown
- Market regime
```

---

#### 5.5 Calculate Position Size
```python
position_size_usd, _, _ = self.risk_engine.get_position_sizing(
    symbol=symbol,
    equity_usd=equity_usd,
    entry_price=entry_price,
    min_trade_usd=self.config.get('min_trade_usd', 100)
)

# Factors:
- Equity: $10,000 (default)
- Regime config: TRENDING = 3-5% per position
- Token risk score: 4.2
- Arbiter size_multiplier: 0.15

position_size_usd *= result.size_multiplier  # Apply arbiter adjustment
```

**Example Output**:
```
Position Size: $450.00 (4.5% of $10,000 equity × 0.15 Kelly)
```

---

#### 5.6 Calculate Order Plan (SL/TP Levels)
```python
order_plan = self.order_manager.calculate_order_plan(
    symbol=symbol,
    entry_price=entry_price,
    position_size_usd=position_size_usd,
    direction=result.action,
    token_profile=token_profile,
    regime=regime,
    ohlcv_data=ohlcv,
    use_support_resistance=True  # Uses ATR + S/R levels
)

# Calculates:
1. Stop Loss (ATR-based + support/resistance)
2. Take Profit 1 (50% allocation)
3. Take Profit 2 (30% allocation)
4. Take Profit 3 (20% allocation)
```

**Example Output**:
```
Stop Loss: $0.512000 (ATR-based, 2.5% risk)
Take Profit 1: $0.565000 (50% allocation, +5% gain)
Take Profit 2: $0.590000 (30% allocation, +10% gain)
Take Profit 3: $0.615000 (20% allocation, +15% gain)
```

---

### STEP 6: EXECUTION + DATABASE STORAGE

**Location**: Lines 909-954
**Duration**: <1 second
**Cost**: $0.00 (PAPER) or exchange fees (LIVE)

#### 6.1 Execute Trade
```python
if self.mode == 'LIVE':
    # LIVE MODE: Real exchange execution
    if result.action == 'BUY':
        order = self.exchange_manager.market_buy(symbol, position_size_usd)
    else:
        order = self.exchange_manager.market_sell(symbol, position_size_usd)

else:
    # PAPER MODE: Simulated trade (no real execution)
    trade_id = f"{symbol}_{timestamp}_{uuid}"
```

---

#### 6.2 Store Trade in Database
```python
self.db.insert_trade(
    trade_id=trade_id,
    symbol=symbol,
    side=result.action,
    entry_price=entry_price,
    position_size_usd=position_size_usd,
    stop_loss=order_plan.stop_loss.price,
    tp1_price=tp1_price,
    tp2_price=tp2_price,
    tp3_price=tp3_price,
    tp1_pct=50.0,
    tp2_pct=30.0,
    tp3_pct=20.0,
    mode=self.mode,
    strategy_name="SCANNER_SWARM_AI",
    confidence=str(result.confidence),
    metadata={
        'regime': regime.value,
        'token_risk_score': token_profile.risk_score,
        'swarm_consensus': result.metadata.get('swarm_consensus'),
        'scanner_score': result.metadata.get('scanner_score'),
        'order_plan_rationale': order_plan.stop_loss.rationale
    }
)
```

**Database Table**: `trades` (SQLite)

---

#### 6.3 Display Summary
```python
cprint(f"  Executed {executed_count} trades using DYNAMIC systems", "cyan")

# Example output:
# Executed 1 trades using DYNAMIC systems
```

---

## 📊 COMPLETE FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STEP 1: SCANNER                             │
│                         (3-5 minutes)                               │
├─────────────────────────────────────────────────────────────────────┤
│ 1.1 Get 432 USDT pairs from Binance                                │
│      ↓                                                               │
│ 1.2 Pre-filter: Volume >$10M, Price >$0.01                         │
│      ↓ (88% reduction)                                              │
│ 1.3 Score 52 tokens: RSI, RVOL, Momentum, vs BTC, Persistence      │
│      ↓                                                               │
│ 1.4 Output: Top 2-3 STRONG candidates (≥75 points)                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 2: MARKET DATA                              │
│                      (1-2 seconds)                                  │
├─────────────────────────────────────────────────────────────────────┤
│ For each STRONG candidate:                                          │
│ - Fetch real-time price, volume, RSI, MACD from Binance API        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 3: AI SWARM VALIDATION                        │
│                     (15-30 seconds)                                 │
│                     Cost: $0.03-0.10                                │
├─────────────────────────────────────────────────────────────────────┤
│ 3.1 Generate prompt with market data                                │
│      ↓                                                               │
│ 3.2 Query 5 AI models in parallel:                                 │
│      • GROQ_QWEN (Qwen 2.5 72B)                                     │
│      • OPENROUTER_GLM (GLM-4)                                       │
│      • XAI (Grok 2)                                                 │
│      • CLAUDE (Claude 3.5 Sonnet)                                   │
│      • OPENROUTER_DEEPSEEK_R1 (DeepSeek R1)                         │
│      ↓                                                               │
│ 3.3 Parse individual responses (voting-based extraction)            │
│      ↓                                                               │
│ 3.4 Determine consensus: Majority vote (3/5)                       │
│      ↓                                                               │
│ 3.5 Apply text-based confidence penalties ("weak" = -15%)          │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 STEP 4: ARBITER DECISION                            │
│                      (<1 second)                                    │
│                    Evidence-Based Logic                             │
├─────────────────────────────────────────────────────────────────────┤
│ 4.1 Volume Divergence Veto:                                        │
│      • Volume <0.5x average → SKIP (manipulation risk)              │
│      ↓                                                               │
│ 4.2 Asymmetric Confidence Thresholds:                              │
│      • BUY: min 75%, strong 85%                                     │
│      • SELL: min 65%, strong 80%                                    │
│      • HOLD: 50-75% range                                           │
│      ↓                                                               │
│ 4.3 Negative MACD Override:                                        │
│      • MACD <0 + BUY signal → Downgrade to NEUTRAL                 │
│      ↓                                                               │
│ 4.4 Decision Matrix:                                               │
│      • Scanner BUY + AI BUY → ✅ AGREEMENT (full size)             │
│      • Scanner BUY + AI NEUTRAL → ⚠️ PARTIAL (reduced size)        │
│      • Scanner BUY + AI SELL → ❌ CONFLICT (skip)                  │
│      ↓                                                               │
│ 4.5 Fractional Kelly Position Sizing:                              │
│      • 65%: 0.10x, 75%: 0.15x, 85%: 0.20-0.24x (boosted)          │
│      ↓                                                               │
│ 4.6 Create ArbitrationResult:                                      │
│      • action, confidence, size_multiplier, metadata                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│           STEP 5: DYNAMIC RISK ENGINE + ORDER MANAGER               │
│                      (2-5 seconds)                                  │
├─────────────────────────────────────────────────────────────────────┤
│ 5.1 Get real-time OHLCV data (3 days, 15m candles)                 │
│      ↓                                                               │
│ 5.2 Update market regime: VOLATILE/CHOPPY/TRENDING                 │
│      ↓                                                               │
│ 5.3 Score token risk: Volatility, liquidity, spread, mcap          │
│      ↓                                                               │
│ 5.4 Update dynamic limits based on PnL history                     │
│      ↓                                                               │
│ 5.5 Calculate position size:                                        │
│      • Base: Equity × regime% × risk_score                          │
│      • Apply arbiter size_multiplier                                │
│      ↓                                                               │
│ 5.6 Calculate order plan:                                           │
│      • Stop Loss (ATR-based + S/R levels)                           │
│      • TP1 (50% alloc), TP2 (30%), TP3 (20%)                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                STEP 6: EXECUTION + DATABASE                         │
│                      (<1 second)                                    │
├─────────────────────────────────────────────────────────────────────┤
│ 6.1 Execute trade:                                                  │
│      • LIVE: Real exchange order (market_buy/market_sell)           │
│      • PAPER: Simulated trade (no real execution)                   │
│      ↓                                                               │
│ 6.2 Store trade in database:                                        │
│      • trade_id, symbol, side, entry, size, SL, TP1-3               │
│      • confidence, metadata (regime, risk_score, consensus)         │
│      ↓                                                               │
│ 6.3 Display summary:                                                │
│      • Executed count, position details                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚦 DECISION POINTS (Where Trades Get Filtered)

### Veto Point 1: Volume Divergence
```
Volume <0.5x average → IMMEDIATE SKIP
Example: STRK 0.26x, DCR 0.19x → VETOED
```

### Gate Point 2: Asymmetric Confidence Thresholds
```
BUY signal with <75% confidence → DOWNGRADED to NEUTRAL
SELL signal with <65% confidence → DOWNGRADED to NEUTRAL
Example: RESOLV 64% SELL → SKIPPED
```

### Gate Point 3: Negative MACD Override
```
MACD <0 + BUY signal → DOWNGRADED to NEUTRAL
Example: DCR MACD -0.150 + BUY → NEUTRAL
```

### Decision Point 4: Scanner vs AI Matrix
```
Scanner BUY + AI SELL → CONFLICT → SKIP
Example: RESOLV Scanner BUY vs AI unanimous SELL → SKIPPED
```

### Gate Point 5: Final Confidence Check
```
Final confidence <75% (for BUY) → SKIP
Example: DCR mixed signals 68% avg → SKIPPED
```

---

## 📈 EXAMPLE: SUCCESSFUL TRADE FLOW

### Token: ETHUSDT (Hypothetical)

**STEP 1: Scanner**
```
Score: 85 pts (STRONG)
RSI: 65 (uptrend)
RVOL: 2.1x (strong volume)
2w momentum: +25%
vs BTC: +15% outperformance
Persistence: ESTABLISHED (3 days)
```

**STEP 2: Market Data**
```
Price: $2,450.00
24h Change: +3.5%
24h Volume: $2.5B
RSI: 65.2
MACD: +0.025 (positive)
Volume Ratio: 1.8x
```

**STEP 3: AI Swarm**
```
GROQ: BUY (78%)
GLM: BUY (82%)
XAI: BUY (80%)
CLAUDE: BUY (85%)
DEEPSEEK: NEUTRAL (72%)

Consensus: BUY (4/5 votes)
Avg Confidence: 79%
```

**STEP 4: Arbiter**
```
Volume 1.8x > 0.5x → ✅ PASS veto
AI confidence 79% > 75% BUY threshold → ✅ PASS gate
MACD +0.025 (positive) → ✅ NO override needed
Scanner BUY + AI BUY → ✅ AGREEMENT
Final confidence: (75 + 79) / 2 = 77%
Size multiplier: 0.15 (Kelly for 77%)
Action: ✅ BUY
```

**STEP 5: Risk + Order**
```
Equity: $10,000
Regime: TRENDING (3-5% per position)
Token risk score: 3.5 (moderate)
Base position: $400 (4% of equity)
After arbiter: $400 × 0.15 = $60
Final position size: $60

Entry: $2,450.00
Stop Loss: $2,350.00 (-4.1%, ATR-based)
TP1: $2,550.00 (+4.1%, 50% alloc)
TP2: $2,625.00 (+7.1%, 30% alloc)
TP3: $2,700.00 (+10.2%, 20% alloc)
```

**STEP 6: Execution**
```
✅ PAPER trade logged to database
Trade ID: ETHUSDT_20251116_143022_a3f4b2c1
```

---

## ⏱️ TIMING BREAKDOWN

| Phase | Duration | Notes |
|-------|----------|-------|
| Scanner (Step 1) | 180-300s | Scans 432 pairs, scores 52 |
| Market Data (Step 2) | 1-2s | Real-time Binance API |
| AI Swarm (Step 3) | 15-30s | Parallel queries (5 models) |
| Arbiter (Step 4) | <1s | Pure logic, no external calls |
| Risk + Order (Step 5) | 2-5s | OHLCV fetch + calculations |
| Execution (Step 6) | <1s | Database write |
| **TOTAL** | **200-340s** | **~3-6 minutes per cycle** |

---

## 💰 COST BREAKDOWN

| Component | Cost Per Cycle |
|-----------|----------------|
| Scanner | $0.00 (math-only) |
| Market Data | $0.00 (free Binance API) |
| AI Swarm (5 models × 1-3 tokens) | $0.03-0.15 |
| Arbiter | $0.00 (pure logic) |
| Risk Engine | $0.00 (calculations) |
| Execution (PAPER) | $0.00 (simulated) |
| Execution (LIVE) | Exchange fees |
| **TOTAL (PAPER)** | **$0.03-0.15** |

---

## 🎯 KEY TAKEAWAYS

1. **6-Step Pipeline**: Scanner → AI → Arbiter → Risk → Order → Execute
2. **Multi-Layer Filtering**: Volume veto, confidence gates, MACD override, conflict detection
3. **Evidence-Based**: Academic thresholds (75% BUY, 65% SELL), fractional Kelly sizing
4. **Real Data**: Binance API for prices, volumes, OHLCV (no fake/mock data)
5. **Dynamic Risk**: Market regime detection, token risk scoring, adaptive limits
6. **Order Management**: ATR-based SL/TP, support/resistance levels, 3-tier TP allocation
7. **Complete Auditability**: All trades stored in database with full metadata

---

**Last Updated**: 2025-11-16
**System Version**: SCANNER_SWARM_TRADE_FLOW v2.0 (with asymmetric thresholds)
**Status**: PRODUCTION-READY ✅
