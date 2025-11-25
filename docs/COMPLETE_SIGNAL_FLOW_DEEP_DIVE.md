# COMPLETE SIGNAL FLOW: RBI Agent to Signal Execution - DEEP DIVE

**Generated**: 2025-11-13
**System**: Moon Dev AI Trading Agents

---

## TABLE OF CONTENTS

1. [Phase 2: Strategy Deployment - Detailed Breakdown](#phase-2-strategy-deployment)
2. [Phase 3: Signal Generation - Two Systems Explained](#phase-3-signal-generation)
3. [Complete System Diagram](#complete-system-diagram)
4. [Integration Points Reference](#integration-points-reference)

---

## PHASE 2: STRATEGY DEPLOYMENT - DETAILED BREAKDOWN

### Overview
This phase takes successful strategies from RBI Agent and deploys them into the live trading database. Every single action is tracked and validated.

### File: `risk_management/rbi_strategy_deployer.py`

---

### STEP-BY-STEP PROCESS

#### **STEP 1: Initialization** (Lines 46-67)

```python
deployer = RBIStrategyDeployer(min_return_pct=50.0)
```

**What Happens:**
1. Creates instance with minimum return threshold (default: 50%)
2. Connects to `trading_system.db` via `get_trading_db()`
3. Initializes `StrategyValidator` with 20% tolerance + auto-debug enabled
4. Sets up directory paths:
   - `self.rbi_data_dir` → `src/data/rbi_pp_multi/`
   - `self.ohlcv_dir` → `src/data/ohlcv/`
   - `self.strategies_dir` → `trading_modes/02_STRATEGY_BASED_TRADING/strategies/rbi/`
5. Creates strategies directory if it doesn't exist

**Output:**
```
RBI Strategy Deployer initialized
Minimum return: 50.0%
Database: C:\...\trading_system.db
```

---

#### **STEP 2: Find Latest RBI Results** (Lines 68-82)

```python
rbi_folder = deployer.find_latest_rbi_results()
```

**What Happens:**
1. Scans `src/data/rbi_pp_multi/` directory
2. Looks for date folders in format `MM_DD_YYYY` (e.g., `11_09_2025`)
3. Filters folders with exactly 2 underscores (validates date format)
4. Sorts chronologically using `datetime.strptime()`
5. Returns most recent folder path

**Example Output:**
```
Found latest RBI folder: 11_09_2025
```

**Folder Structure Found:**
```
src/data/rbi_pp_multi/11_09_2025/
├── backtests_package/
├── backtests_optimized/
│   ├── MeanReversion_OPT_v18.py
│   ├── BreakoutStrategy_OPT_v12.py
│   └── results/
│       ├── MeanReversion_OPT_v18.csv
│       └── BreakoutStrategy_OPT_v12.csv
└── backtests_final/
```

---

#### **STEP 3: Load Strategy Results** (Lines 84-115)

```python
results_dict = deployer.load_strategy_results(rbi_folder)
```

**What Happens:**
1. Checks 3 possible result locations (in order):
   - `backtests_package/results/`
   - `backtests_optimized/results/`
   - `backtests/results/`

2. For each location:
   - Lists all `.csv` files
   - Reads each CSV with pandas
   - Validates presence of `Return_%` column
   - Adds to `results_dict` with strategy name as key

3. Handles errors gracefully (continues if one CSV fails)

**Example CSV Structure:**
```csv
Symbol,Timeframe,Return_%,Sharpe,Trades,Win_Rate,Max_DD
BTC,15m,52.4,1.8,45,64.4,-12.3
ETH,1H,48.2,1.5,38,61.1,-15.8
SOL,15m,67.8,2.1,52,68.2,-10.2
```

**Output:**
```
Found 2 result files in backtests_optimized/results/
```

**Returns:**
```python
{
    'MeanReversion_OPT_v18': DataFrame(Symbol, Timeframe, Return_%, ...),
    'BreakoutStrategy_OPT_v12': DataFrame(...)
}
```

---

#### **STEP 4: Filter Passing Strategies** (Lines 117-149)

```python
passing_strategies = deployer.filter_passing_strategies(results_dict)
```

**What Happens:**

1. For each strategy in `results_dict`:
   - Finds row with maximum `Return_%`
   - Checks if `Return_%` >= `min_return_pct` (50%)

2. If passing, creates strategy info dict:
   ```python
   {
       'strategy_name': 'MeanReversion_OPT_v18',
       'token': 'BTC',              # Best performing token
       'timeframe': '15m',          # Best performing timeframe
       'return_pct': 52.4,          # Best return
       'sharpe': 1.8,
       'trades': 45,
       'win_rate': 64.4,
       'max_drawdown': -12.3,
       'all_results': DataFrame     # ALL token/timeframe results
   }
   ```

3. Keeps **ALL results** in `all_results` field for multi-token support

**Output:**
```
Found 2 strategies >= 50.0%
  MeanReversion_OPT_v18: 52.40% on BTC-15m
  BreakoutStrategy_OPT_v12: 67.80% on SOL-15m
```

---

#### **STEP 5: Find Backtest Files** (Lines 151-174)

For each passing strategy:

```python
backtest_file = deployer.find_backtest_file(rbi_folder, strategy_name)
```

**What Happens:**
1. Searches 5 possible locations:
   - `backtests_package/`
   - `backtests_optimized/`
   - `backtests_final/`
   - `backtests_working/`
   - `backtests/`

2. Uses glob pattern `*{strategy_name}*.py`
3. Returns first match or `None`

**Example Match:**
```
Found: src/data/rbi_pp_multi/11_09_2025/backtests_optimized/MeanReversion_OPT_v18.py
```

---

#### **STEP 6: Convert Strategy** (Lines 176-203)

```python
converted_path = deployer.convert_strategy(backtest_file, strategy_info)
```

**What Happens:**
1. Extracts info from `strategy_info`:
   - `strategy_name` = "MeanReversion_OPT_v18"
   - `token` = "BTC"
   - `timeframe` = "15m"
   - `return_pct` = 52.4

2. Creates descriptive filename:
   ```
   BTC_15m_MeanReversion_OPT_v18_52pct.py
   ```

3. Copies file to:
   ```
   trading_modes/02_STRATEGY_BASED_TRADING/strategies/rbi/BTC_15m_MeanReversion_OPT_v18_52pct.py
   ```

**Output:**
```
  Converted: BTC_15m_MeanReversion_OPT_v18_52pct.py
```

---

#### **STEP 7: Deploy Strategy (Complete Process)** (Lines 223-340)

```python
success = deployer.deploy_strategy(strategy_info, converted_path, rbi_folder)
```

This is the **MOST IMPORTANT** step - it has 4 sub-steps:

##### **SUB-STEP 7.1: Save to Database** (Lines 246-258)

```python
self.db.insert_strategy(
    strategy_name="MeanReversion_OPT_v18",
    source_type="RBI",
    source_url="src/data/rbi_pp_multi/11_09_2025",
    backtest_return=52.4,
    backtest_sharpe=1.8,
    backtest_max_drawdown=-12.3,
    backtest_win_rate=64.4,
    backtest_trades=45,
    code_path="trading_modes/.../BTC_15m_MeanReversion_OPT_v18_52pct.py"
)
```

**Database INSERT:**
```sql
INSERT INTO strategies (
    strategy_name, created_timestamp, source_type, source_url,
    backtest_return, backtest_sharpe, backtest_max_drawdown,
    backtest_win_rate, backtest_trades, code_path, metadata
) VALUES (
    'MeanReversion_OPT_v18',
    '2025-11-13 10:30:00',
    'RBI',
    'src/data/rbi_pp_multi/11_09_2025',
    52.4, 1.8, -12.3, 64.4, 45,
    'trading_modes/.../BTC_15m_MeanReversion_OPT_v18_52pct.py',
    NULL
)
```

**Fields Set:**
- `deployed = 0` (not deployed yet)
- `validation_timestamp = NULL` (not validated yet)

---

##### **SUB-STEP 7.2: Add Token/Timeframe Assignments** (Lines 260-297)

**What Happens:**

1. **Add PRIMARY token** (best performer):
   ```python
   self.db.add_strategy_token(
       strategy_name="MeanReversion_OPT_v18",
       token="BTC",
       timeframe="15m",
       data_file="src/data/ohlcv/BTC-USDT-15m.csv",
       backtest_return=52.4,
       backtest_sharpe=1.8,
       backtest_trades=45,
       is_primary=True  # ← PRIMARY flag
   )
   ```

   **Database INSERT:**
   ```sql
   INSERT INTO strategy_tokens (
       strategy_name, token, timeframe, data_file,
       backtest_return, backtest_sharpe, backtest_trades,
       is_primary, created_timestamp
   ) VALUES (
       'MeanReversion_OPT_v18', 'BTC', '15m',
       'src/data/ohlcv/BTC-USDT-15m.csv',
       52.4, 1.8, 45, 1, '2025-11-13 10:30:00'
   )
   ```

2. **Add OTHER passing tokens** (>= 50% return):
   - Loops through `all_results` DataFrame
   - Finds rows where `Return_%` >= 50%
   - Skips primary token (already added)
   - Adds each with `is_primary=False`

   **Example:**
   ```python
   # ETH passed with 48.2% - SKIPPED (below 50%)
   # SOL passed with 67.8% - ADDED
   self.db.add_strategy_token(
       strategy_name="MeanReversion_OPT_v18",
       token="SOL",
       timeframe="15m",
       data_file="src/data/ohlcv/SOL-USDT-15m.csv",
       backtest_return=67.8,
       is_primary=False  # ← Not primary
   )
   ```

**Output:**
```
Step 2: Adding token/timeframe assignments...
  Added PRIMARY: BTC-15m (52.40%)
  Added: SOL-15m (67.80%)
```

**Database State (strategy_tokens table):**
```
id | strategy_name           | token | timeframe | backtest_return | is_primary
1  | MeanReversion_OPT_v18  | BTC   | 15m       | 52.4           | 1
2  | MeanReversion_OPT_v18  | SOL   | 15m       | 67.8           | 0
```

---

##### **SUB-STEP 7.3: Validate Strategy** (Lines 299-329)

```python
passed, validation_metrics, message = self.validator.validate_with_auto_debug(
    strategy_name="MeanReversion_OPT_v18",
    strategy_code_path="trading_modes/.../BTC_15m_MeanReversion_OPT_v18_52pct.py",
    original_metrics={
        'return_pct': 52.4,
        'sharpe_ratio': 1.8,
        'max_drawdown': -12.3,
        'win_rate': 64.4,
        'total_trades': 45
    },
    data_file="src/data/ohlcv/BTC-USDT-15m.csv",
    symbol="BTC",
    timeframe="15m"
)
```

**Validation Process:**

1. **Loads strategy code** dynamically
2. **Runs backtest** on out-of-sample data (recent data not used in training)
3. **Compares metrics** with tolerance (20%):
   - Return: 52.4% → validates if result is 42% to 63%
   - Sharpe: 1.8 → validates if result is 1.4 to 2.2
   - Win Rate: 64.4% → validates if result is 51% to 77%

4. **Auto-Debug** if fails:
   - Le Goues et al. (2019): 67% success rate
   - Uses AI to fix code errors
   - Max 2 retry attempts

**Example Result:**
```python
passed = True
validation_metrics = {
    'return_pct': 48.6,      # Within 20% tolerance
    'sharpe_ratio': 1.7,     # Within tolerance
    'max_drawdown': -14.1,   # Acceptable
    'win_rate': 61.2,        # Within tolerance
    'total_trades': 41
}
message = "Validation passed: Return 48.6% vs expected 52.4% (within 20%)"
```

**Update Database:**
```python
self.db.update_strategy_token_validation(
    strategy_name="MeanReversion_OPT_v18",
    token="BTC",
    timeframe="15m",
    validation_return=48.6,
    validation_passed=True
)
```

**SQL:**
```sql
UPDATE strategy_tokens
SET validation_return = 48.6, validation_passed = 1
WHERE strategy_name = 'MeanReversion_OPT_v18'
  AND token = 'BTC' AND timeframe = '15m'
```

---

##### **SUB-STEP 7.4: Deploy if Passed** (Lines 331-340)

```python
if passed:
    self.db.deploy_strategy("MeanReversion_OPT_v18")
```

**SQL:**
```sql
UPDATE strategies
SET deployed = 1, deployed_timestamp = '2025-11-13 10:32:00'
WHERE strategy_name = 'MeanReversion_OPT_v18'
```

**Output:**
```
================================================================================
DEPLOYING: MeanReversion_OPT_v18
================================================================================
Step 1: Saving to database...
  Strategy saved to database

Step 2: Adding token/timeframe assignments...
  Added PRIMARY: BTC-15m (52.40%)
  Added: SOL-15m (67.80%)

Step 3: Validating on BTC-15m...
  [Validation] Return: 48.6% vs 52.4% (within 20%) ✓
  [Validation] Sharpe: 1.7 vs 1.8 (within 20%) ✓
  [Validation] Win Rate: 61.2% vs 64.4% (within 20%) ✓

  DEPLOYED: MeanReversion_OPT_v18
  Validation passed: Return 48.6% vs expected 52.4% (within 20%)
```

---

#### **STEP 8: Summary Report** (Lines 397-418)

**Output:**
```
================================================================================
DEPLOYMENT SUMMARY
================================================================================
Deployed: 2
Failed: 0

Deployed strategies:
  - MeanReversion_OPT_v18
  - BreakoutStrategy_OPT_v12
```

---

### FINAL DATABASE STATE (After Phase 2)

**strategies table:**
```
| strategy_name           | deployed | deployed_timestamp   | code_path                              |
|------------------------|----------|----------------------|----------------------------------------|
| MeanReversion_OPT_v18  | 1        | 2025-11-13 10:32:00 | trading_modes/.../BTC_15m_...52pct.py |
| BreakoutStrategy_...   | 1        | 2025-11-13 10:33:00 | trading_modes/.../SOL_15m_...67pct.py |
```

**strategy_tokens table:**
```
| strategy_name           | token | timeframe | validation_passed | is_primary |
|------------------------|-------|-----------|-------------------|------------|
| MeanReversion_OPT_v18  | BTC   | 15m       | 1                 | 1          |
| MeanReversion_OPT_v18  | SOL   | 15m       | 1                 | 0          |
| BreakoutStrategy_...   | SOL   | 15m       | 1                 | 1          |
```

---

## PHASE 3: SIGNAL GENERATION - TWO SYSTEMS EXPLAINED

There are **TWO COMPLETELY SEPARATE** signal generation systems:

1. **System A**: RBI Deployed Strategies (from Phase 2)
2. **System B**: Two-Engine Fusion (Volume + Funding)

---

### SYSTEM A: RBI DEPLOYED STRATEGIES

**File**: `src/agents/strategy_agent.py`

---

#### **INITIALIZATION** (Lines 56-91)

```python
agent = StrategyAgent()
```

**What Happens:**

1. **Creates Anthropic client** for LLM evaluation:
   ```python
   self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
   ```

2. **Loads custom strategies** (if `ENABLE_STRATEGIES = True`):
   ```python
   from src.strategies.custom.example_strategy import ExampleStrategy
   from src.strategies.custom.private_my_strategy import MyStrategy

   self.enabled_strategies = [ExampleStrategy(), MyStrategy()]
   ```

3. **IMPORTANT**: In the current codebase, these are **hardcoded imports**
   - Database-loaded strategies would require dynamic loading
   - Expected implementation:
     ```python
     deployed = db.get_deployed_strategies()  # SQL: WHERE deployed=1
     for strat in deployed:
         module = importlib.import_module(strat['code_path'])
         strategy_class = getattr(module, 'Strategy')
         self.enabled_strategies.append(strategy_class())
     ```

**Output:**
```
✅ Strategy Agent using ExchangeManager for HYPERLIQUID
✅ Loaded 2 strategies!
  • ExampleStrategy
  • MyStrategy
🤖 Moon Dev's Strategy Agent initialized with 2 strategies!
```

---

#### **SIGNAL GENERATION** (Lines 137-204)

```python
signals = agent.get_signals(token="BTC")
```

**Complete Flow:**

##### **STEP 1: Collect Signals from All Strategies** (Lines 141-153)

```python
for strategy in self.enabled_strategies:
    signal = strategy.generate_signals()  # Calls BaseStrategy method
    if signal and signal['token'] == token:
        signals.append({
            'token': signal['token'],
            'strategy_name': strategy.name,
            'signal': signal['signal'],        # 0.0 to 1.0
            'direction': signal['direction'],  # BUY/SELL/NEUTRAL
            'metadata': signal.get('metadata', {})
        })
```

**Example `generate_signals()` implementation:**
```python
class MeanReversionStrategy(BaseStrategy):
    def generate_signals(self):
        # Get market data
        df = get_ohlcv_data('BTC', timeframe='15m')

        # Calculate indicators
        rsi = ta.rsi(df['close'], length=14)
        bb = ta.bbands(df['close'], length=20)

        # Generate signal
        if rsi[-1] < 30 and df['close'][-1] < bb['BBL_20'][-1]:
            return {
                'token': 'BTC',
                'signal': 0.78,      # 78% confidence
                'direction': 'BUY',
                'metadata': {
                    'rsi': rsi[-1],
                    'bb_position': 'below_lower',
                    'entry_reason': 'RSI oversold + price below BB lower'
                }
            }
        return {'token': 'BTC', 'signal': 0, 'direction': 'NEUTRAL'}
```

**Collected Signals:**
```python
signals = [
    {
        'token': 'BTC',
        'strategy_name': 'MeanReversion_OPT_v18',
        'signal': 0.78,
        'direction': 'BUY',
        'metadata': {'rsi': 28.5, 'bb_position': 'below_lower'}
    },
    {
        'token': 'BTC',
        'strategy_name': 'BreakoutStrategy_OPT_v12',
        'signal': 0.65,
        'direction': 'BUY',
        'metadata': {'volume_spike': 2.3, 'resistance_break': True}
    }
]
```

**Output:**
```
🔍 Analyzing BTC with 2 strategies...

📊 Raw Strategy Signals for BTC:
  • MeanReversion_OPT_v18: BUY (0.78) for BTC
  • BreakoutStrategy_OPT_v12: BUY (0.65) for BTC
```

---

##### **STEP 2: Get Market Context** (Lines 164-169)

```python
from src.data.ohlcv_collector import collect_token_data
market_data = collect_token_data("BTC")
```

**Returns:**
```python
{
    'price': 43250.00,
    'volume_24h': 28500000000,
    'price_change_24h': 2.3,
    'volatility': 0.023,
    'trend': 'BULLISH',
    'support': 42800,
    'resistance': 43800
}
```

---

##### **STEP 3: LLM Evaluation** (Lines 172-173, 93-135)

```python
evaluation = self.evaluate_signals(signals, market_data)
```

**Prompt Sent to Claude:**
```
You are Moon Dev's Strategy Validation Assistant 🌙

Analyze the following strategy signals and validate their recommendations:

Strategy Signals:
[
  {
    "token": "BTC",
    "strategy_name": "MeanReversion_OPT_v18",
    "signal": 0.78,
    "direction": "BUY",
    "metadata": {"rsi": 28.5, "bb_position": "below_lower"}
  },
  {
    "token": "BTC",
    "strategy_name": "BreakoutStrategy_OPT_v12",
    "signal": 0.65,
    "direction": "BUY",
    "metadata": {"volume_spike": 2.3, "resistance_break": true}
  }
]

Market Context:
{
  "price": 43250.00,
  "volume_24h": 28500000000,
  "price_change_24h": 2.3,
  "trend": "BULLISH"
}

Your task:
1. Evaluate each strategy signal's reasoning
2. Check if signals align with current market conditions
3. Look for confirmation/contradiction between different strategies
4. Consider risk factors

Respond in this format:
1. First line: EXECUTE or REJECT for each signal
2. Then explain your reasoning
```

**Claude Response:**
```
EXECUTE signal_1, EXECUTE signal_2

ANALYSIS:

Signal 1 (MeanReversion_OPT_v18 - BUY):
✓ RSI at 28.5 indicates oversold conditions
✓ Price below lower Bollinger Band confirms mean reversion setup
✓ High confidence (78%) based on clear technical setup
✓ Risk: Minimal in current bullish trend
Verdict: EXECUTE with confidence 85%

Signal 2 (BreakoutStrategy_OPT_v12 - BUY):
✓ Volume spike (2.3x) confirms breakout strength
✓ Resistance break aligns with bullish market context
✓ Price change +2.3% shows momentum
✓ Both signals agree (BUY+BUY) = high conviction
Verdict: EXECUTE with confidence 80%

OVERALL:
- Both signals align (BUY confirmation)
- Market context supports bullish position
- Risk/reward favorable
- Recommend execution on both signals
```

**Parsed:**
```python
evaluation = {
    'decisions': ['EXECUTE signal_1', 'EXECUTE signal_2'],
    'reasoning': '...(full analysis)...'
}
```

---

##### **STEP 4: Filter Approved Signals** (Lines 179-186)

```python
approved_signals = []
for signal, decision in zip(signals, evaluation['decisions']):
    if "EXECUTE" in decision.upper():
        approved_signals.append(signal)
```

**Output:**
```
🤖 Strategy Evaluation:
Decisions: ['EXECUTE signal_1', 'EXECUTE signal_2']
Reasoning: ...

✅ LLM approved MeanReversion_OPT_v18's BUY signal
✅ LLM approved BreakoutStrategy_OPT_v12's BUY signal

🎯 Final Approved Signals for BTC:
  • MeanReversion_OPT_v18: BUY (0.78)
  • BreakoutStrategy_OPT_v12: BUY (0.65)
```

---

##### **STEP 5: Execute Approved Signals** (Lines 194-196, 231-305)

```python
self.execute_strategy_signals(approved_signals)
```

**For Each Signal:**

1. **Calculate Position Size:**
   ```python
   max_position = usd_size * (MAX_POSITION_PERCENTAGE / 100)
   # usd_size = 10000, MAX_POSITION_PERCENTAGE = 10
   # max_position = 1000 USD

   target_size = max_position * signal['signal']
   # signal = 0.78
   # target_size = 1000 * 0.78 = 780 USD
   ```

2. **Get Current Position:**
   ```python
   current_position = self.em.get_token_balance_usd('BTC')
   # Returns: 250 USD (existing position)
   ```

3. **Execute Trade:**
   ```python
   if direction == 'BUY' and current_position < target_size:
       self.em.ai_entry('BTC', target_size)
       # Buys: 780 - 250 = 530 USD worth of BTC
   ```

**Output:**
```
💫 Executing approved strategy signals...
📝 Received 2 signals to execute

🎯 Processing signal for BTC...
📊 Signal strength: 0.78
🎯 Target position: $780.00 USD
📈 Current position: $250.00 USD
✨ Executing BUY for BTC
✅ Entry complete for BTC

🎯 Processing signal for BTC...
📊 Signal strength: 0.65
🎯 Target position: $650.00 USD
📈 Current position: $780.00 USD
⏸️ Position already at or above target size
```

---

### SYSTEM B: TWO-ENGINE FUSION SYSTEM

**Files**:
- `src/agents/master_trading_agent_two_engine.py` (Orchestrator)
- `src/agents/fusion_layer.py` (Fusion Logic)
- `src/agents/volume_agent_enhanced.py` (Engine 1)
- `src/agents/funding_agent.py` (Engine 2)

---

#### **ARCHITECTURE OVERVIEW**

```
┌─────────────────────────────────────────────────────────────┐
│         MASTER TRADING AGENT (Orchestrator)                 │
│                                                              │
│  Every 15 minutes:                                          │
│  1. Run ENGINE 1 (volume_agent_enhanced.py)                 │
│  2. Run ENGINE 2 (funding_agent.py)                         │
│  3. Fuse signals (fusion_layer.py)                          │
│  4. Execute STRONG signals (confidence >= 80%)              │
└─────────────────────────────────────────────────────────────┘
```

---

#### **STEP 1: Run Both Engines** (Lines 128-152)

```python
def run_trading_cycle():
    # ENGINE 1: Volume Intelligence
    results['volume'] = run_agent('Volume Engine', VOLUME_AGENT)

    # ENGINE 2: Funding Intelligence
    results['funding'] = run_agent('Funding Engine', FUNDING_AGENT)
```

**Each Agent Runs as Subprocess:**
```python
result = subprocess.run(
    [sys.executable, 'src/agents/volume_agent_enhanced.py'],
    timeout=180,  # 3 minutes max
    capture_output=True
)
```

**ENGINE 1 Output** (`volume_signals.json`):
```json
{
  "BTC": {
    "action": "BUY",
    "confidence": 85,
    "timestamp": "2025-11-13T10:30:00Z",
    "data": {
      "rvol": 2.3,
      "z_score": 3.2,
      "persistence_class": "HIGH",
      "signal_quality": "EXCELLENT"
    }
  },
  "ETH": {
    "action": "NOTHING",
    "confidence": 0,
    "timestamp": "2025-11-13T10:30:00Z"
  }
}
```

**ENGINE 2 Output** (`funding_signals.json`):
```json
{
  "BTC": {
    "action": "BUY",
    "confidence": 78,
    "timestamp": "2025-11-13T10:30:00Z",
    "data": {
      "annual_rate": -45.2,
      "positioning": "SHORTS_CROWDED",
      "squeeze_risk": "HIGH"
    },
    "reasoning": "Funding rate -45% APR indicates short squeeze risk"
  }
}
```

**Output:**
```
[STEP 1/4] Running intelligence engines...
  [Volume Engine  ] Starting...
  [Volume Engine  ] [OK] Complete (12.3s)
  [Funding Engine ] Starting...
  [Funding Engine ] [OK] Complete (8.7s)

  [SUMMARY] 2/2 engines successful (21.0s total)
```

---

#### **STEP 2: Fuse Signals** (Lines 154-161)

```python
fusion = TwoEngineFusion()
fused_results = fusion.fuse_all_symbols(['BTC', 'ETH', 'SOL'])
```

##### **Fusion Process (fusion_layer.py)**

**STEP 2.1: Collect Signals** (Lines 95-146)

```python
signals = fusion.collect_signals('BTC', max_age_minutes=30)
```

**Returns:**
```python
{
    'volume': {
        'action': 'BUY',
        'confidence': 85,
        'timestamp': '2025-11-13T10:30:00Z',
        'age_minutes': 2.3,
        'data': {'rvol': 2.3, 'z_score': 3.2, ...}
    },
    'funding': {
        'action': 'BUY',
        'confidence': 78,
        'timestamp': '2025-11-13T10:30:00Z',
        'age_minutes': 1.8,
        'data': {'annual_rate': -45.2, ...},
        'reasoning': 'Funding rate -45% APR...'
    }
}
```

**Age Validation:**
- If signal older than 30 minutes → marked as `stale`
- If signal file missing → marked as `missing`

---

**STEP 2.2: Calculate Fusion** (Lines 148-256)

**Decision Matrix Logic:**

```python
vol_action = 'BUY'
vol_conf = 85

fund_action = 'BUY'
fund_conf = 78
```

**Matrix Check:**
```python
# BOTH ENGINES AGREE → STRONG SIGNAL
if vol_action == fund_action == 'BUY':
    action = 'STRONG_BUY'
    confidence = min(100, int((85 + 78) / 2 + 10))  # = 91%
    reasoning = "Volume spike + Short squeeze setup = High conviction"
```

**Full Decision Matrix:**

| Volume | Funding | Result       | Confidence | Reasoning                          |
|--------|---------|--------------|------------|------------------------------------|
| BUY    | BUY     | STRONG_BUY   | 95%        | Volume spike + Short squeeze       |
| BUY    | NEUTRAL | MEDIUM_BUY   | 75%        | Volume spike, neutral positioning  |
| BUY    | SELL    | WAIT         | 50%        | Conflicting signals                |
| SELL   | SELL    | STRONG_SELL  | 90%        | Distribution + Long squeeze        |
| SELL   | NEUTRAL | MEDIUM_SELL  | 70%        | Distribution, neutral positioning  |
| NEUTRAL| BUY     | WAIT         | 60%        | Wait for volume confirmation       |
| NEUTRAL| SELL    | WAIT         | 60%        | Wait for volume confirmation       |

**Fused Result:**
```python
{
    'action': 'STRONG_BUY',
    'confidence': 91,
    'fusion_score': 45.7,
    'reasoning': 'Volume spike + Short squeeze setup = High conviction',
    'engines': {
        'volume': {
            'action': 'BUY',
            'confidence': 85,
            'rvol': 2.3,
            'z_score': 3.2,
            'persistence': 'HIGH',
            'signal_quality': 'EXCELLENT',
            'age_minutes': 2.3
        },
        'funding': {
            'action': 'BUY',
            'confidence': 78,
            'annual_rate': -45.2,
            'positioning': 'SHORTS_CROWDED',
            'squeeze_risk': 'HIGH',
            'reasoning': 'Funding rate -45% APR...',
            'age_minutes': 1.8
        }
    },
    'timestamp': '2025-11-13T10:32:00Z'
}
```

**Saved to**: `src/data/signals/fused_signals.json`

---

#### **STEP 3: Analyze Fused Signals** (Lines 163-181)

```python
strong_signals = [
    (symbol, result) for symbol, result in fused_results.items()
    if result['action'] in ['STRONG_BUY', 'STRONG_SELL']
    and result['confidence'] >= 80
]
```

**Output:**
```
[STEP 3/4] Analyzing fused signals...
  Strong signals (>=80% confidence): 1
  Medium signals (>=70% confidence): 0

================================================================================
TWO-ENGINE FUSION: Volume Intelligence + Funding Positioning
================================================================================

BTC: STRONG_BUY
  Confidence: 91%
  Reasoning: Volume spike + Short squeeze setup = High conviction

  ENGINE 1 (Volume):
    Action: BUY (85%)
    RVOL: 2.30x | Z-Score: 3.20 | Persistence: HIGH
    Signal Quality: EXCELLENT | Age: 2 min

  ENGINE 2 (Funding):
    Action: BUY (78%)
    Annual Rate: -45.20% | Positioning: SHORTS_CROWDED
    Squeeze Risk: HIGH | Age: 2 min
    Note: Funding rate -45% APR indicates short squeeze risk

--------------------------------------------------------------------------------
```

---

#### **STEP 4: Execute Trades** (Lines 184-195, 93-126)

```python
for symbol, result in strong_signals:
    execute_trade(
        symbol='BTC',
        action='STRONG_BUY',
        confidence=91,
        reasoning='Volume spike + Short squeeze setup = High conviction'
    )
```

**If `EXECUTE_TRADES = True` (LIVE MODE):**
```python
from src import nice_funcs_hyperliquid as hl

if action == 'STRONG_BUY' and confidence >= 80:
    size = calculate_position_size(confidence)
    hl.market_buy('BTC', size)
```

**Output:**
```
[STEP 4/4] Executing trades...
  [TRADE] BTC: STRONG_BUY (91%)
          Reasoning: Volume spike + Short squeeze setup = High conviction
  [EXEC] Bought 0.0462 BTC
```

**If `EXECUTE_TRADES = False` (DRY-RUN):**
```
  [TRADE] BTC: STRONG_BUY (91%) - DRY RUN (trading disabled)
          Reasoning: Volume spike + Short squeeze setup = High conviction
```

---

#### **CONTINUOUS OPERATION** (Lines 206-227)

```python
while True:
    run_trading_cycle()
    time.sleep(CHECK_INTERVAL_MINUTES * 60)  # Default: 15 minutes
```

**Output:**
```
[CYCLE #1] Starting...
...
CYCLE COMPLETE - Duration: 23.4s
================================================================================

[SLEEP] Waiting 15 minutes until next cycle...

[CYCLE #2] Starting...
...
```

---

## COMPLETE SYSTEM DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COMPLETE SIGNAL FLOW                                │
│                   From RBI Agent to Trading Execution                        │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
PHASE 1: STRATEGY GENERATION (rbi_agent_pp_multi.py)
═══════════════════════════════════════════════════════════════════════════════

    ┌──────────────────┐
    │  Trading Ideas   │
    │ (YouTube, PDFs)  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ RBI Agent        │ ← 9 Parallel Threads
    │ (xAI Grok-4)     │ ← Research → Code → Test → Debug → Optimize
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │ src/data/rbi_pp_multi/{MM_DD_YYYY}/      │
    │   backtests_optimized/                   │
    │     ├── MeanReversion_OPT_v18.py         │
    │     ├── BreakoutStrategy_OPT_v12.py      │
    │     └── results/                         │
    │         ├── MeanReversion_OPT_v18.csv    │
    │         └── BreakoutStrategy_OPT_v12.csv │
    └──────────────────┬───────────────────────┘
                       │
                       │ SUCCESS: 2 strategies
                       │ Return: 52.4%, 67.8%
                       ▼

═══════════════════════════════════════════════════════════════════════════════
PHASE 2: STRATEGY DEPLOYMENT (rbi_strategy_deployer.py)
═══════════════════════════════════════════════════════════════════════════════

    ┌──────────────────────────┐
    │ RBI Strategy Deployer    │
    │ min_return_pct = 50%     │
    └──────────┬───────────────┘
               │
               ├─[1]─► Find Latest RBI Folder: 11_09_2025/
               │
               ├─[2]─► Load Strategy Results (CSV files)
               │       ├── MeanReversion_OPT_v18: 52.4% ✓
               │       └── BreakoutStrategy_OPT_v12: 67.8% ✓
               │
               ├─[3]─► Filter Passing Strategies (>= 50%)
               │       └── 2 strategies passed
               │
               └─[4]─► For Each Strategy:
                       │
                       ├── Find Backtest File (.py)
                       │
                       ├── Convert to BaseStrategy Format
                       │   └── Copy to: trading_modes/.../strategies/rbi/
                       │
                       └── DEPLOY STRATEGY ──┐
                                             │
                ┌────────────────────────────┘
                │
                ├─[4.1]─► INSERT INTO strategies table
                │         ├── strategy_name: 'MeanReversion_OPT_v18'
                │         ├── source_type: 'RBI'
                │         ├── backtest_return: 52.4
                │         ├── code_path: 'trading_modes/.../BTC_15m_...52pct.py'
                │         └── deployed: 0 (not yet)
                │
                ├─[4.2]─► INSERT INTO strategy_tokens table
                │         ├── PRIMARY: BTC-15m (52.4%) is_primary=1
                │         └── SECONDARY: SOL-15m (67.8%) is_primary=0
                │
                ├─[4.3]─► VALIDATE STRATEGY
                │         ├── Load strategy code
                │         ├── Run backtest on out-of-sample data
                │         ├── Compare with original metrics (20% tolerance)
                │         ├── Auto-debug if failed (max 2 retries)
                │         └── UPDATE strategy_tokens:
                │             └── validation_return: 48.6, validation_passed: 1
                │
                └─[4.4]─► DEPLOY if validation passed
                          └── UPDATE strategies SET deployed=1

                ▼
    ┌──────────────────────────────────────────────────┐
    │         trading_system.db (SQLite)                │
    ├──────────────────────────────────────────────────┤
    │ strategies table:                                 │
    │  ┌───────────────────────┬──────────┬────────┐   │
    │  │ strategy_name         │ deployed │ return │   │
    │  ├───────────────────────┼──────────┼────────┤   │
    │  │ MeanReversion_OPT_v18 │    1     │  52.4  │   │
    │  │ BreakoutStrategy_...  │    1     │  67.8  │   │
    │  └───────────────────────┴──────────┴────────┘   │
    │                                                    │
    │ strategy_tokens table:                            │
    │  ┌───────────────────────┬───────┬──────┬────┐   │
    │  │ strategy_name         │ token │ tf   │ pr │   │
    │  ├───────────────────────┼───────┼──────┼────┤   │
    │  │ MeanReversion_OPT_v18 │ BTC   │ 15m  │ 1  │   │
    │  │ MeanReversion_OPT_v18 │ SOL   │ 15m  │ 0  │   │
    │  │ BreakoutStrategy_...  │ SOL   │ 15m  │ 1  │   │
    │  └───────────────────────┴───────┴──────┴────┘   │
    └──────────────────────────────────────────────────┘
                          │
                          │ DATABASE READY
                          ▼

═══════════════════════════════════════════════════════════════════════════════
PHASE 3A: SIGNAL GENERATION - RBI STRATEGIES (strategy_agent.py)
═══════════════════════════════════════════════════════════════════════════════

    ┌──────────────────────────┐
    │  Strategy Agent Init     │
    └──────────┬───────────────┘
               │
               ├─► db.get_deployed_strategies()
               │   └── SQL: SELECT * FROM strategies WHERE deployed=1
               │
               ├─► For each deployed strategy:
               │   ├── Load code from code_path
               │   ├── Import strategy class (BaseStrategy)
               │   └── Add to self.enabled_strategies[]
               │
               ▼
    ┌──────────────────────────┐
    │ self.enabled_strategies  │
    │  [MeanReversion_v18,     │
    │   BreakoutStrategy_v12]  │
    └──────────┬───────────────┘
               │
               │ get_signals(token='BTC')
               ▼
    ┌────────────────────────────────────────┐
    │ STEP 1: Collect Raw Signals            │
    ├────────────────────────────────────────┤
    │ For each strategy:                     │
    │   signal = strategy.generate_signals() │
    │                                         │
    │ Returns:                                │
    │  ┌────────────────────────────────┐    │
    │  │ MeanReversion_OPT_v18:         │    │
    │  │   token: 'BTC'                 │    │
    │  │   signal: 0.78 (78% conf)      │    │
    │  │   direction: 'BUY'             │    │
    │  │   metadata: {rsi: 28.5, ...}   │    │
    │  └────────────────────────────────┘    │
    │  ┌────────────────────────────────┐    │
    │  │ BreakoutStrategy_OPT_v12:      │    │
    │  │   token: 'BTC'                 │    │
    │  │   signal: 0.65 (65% conf)      │    │
    │  │   direction: 'BUY'             │    │
    │  │   metadata: {vol: 2.3x, ...}   │    │
    │  └────────────────────────────────┘    │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ STEP 2: Get Market Context             │
    ├────────────────────────────────────────┤
    │ collect_token_data('BTC')              │
    │                                         │
    │ Returns:                                │
    │  {price: 43250, volume_24h: 28.5B,     │
    │   trend: 'BULLISH', volatility: 0.023} │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ STEP 3: LLM Evaluation (Claude)        │
    ├────────────────────────────────────────┤
    │ Prompt:                                 │
    │  "Analyze these signals:                │
    │   - MeanReversion: BUY (0.78)          │
    │   - Breakout: BUY (0.65)               │
    │                                         │
    │   Market: BULLISH trend, $43,250       │
    │                                         │
    │   Validate each signal..."             │
    │                                         │
    │ Response:                               │
    │  "EXECUTE signal_1, EXECUTE signal_2   │
    │                                         │
    │   Analysis:                             │
    │   - Both signals agree (BUY+BUY)       │
    │   - RSI oversold confirms mean rev     │
    │   - Volume spike confirms breakout     │
    │   - Market context supports            │
    │   Confidence: 85%, 80%"                │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ STEP 4: Filter Approved Signals        │
    ├────────────────────────────────────────┤
    │ approved_signals = [                   │
    │   MeanReversion_OPT_v18 (BUY, 0.78),   │
    │   BreakoutStrategy_OPT_v12 (BUY, 0.65) │
    │ ]                                       │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ STEP 5: Execute Strategy Signals       │
    ├────────────────────────────────────────┤
    │ For signal in approved_signals:        │
    │                                         │
    │   Calculate position size:             │
    │     max_position = $10,000 * 10% = $1k │
    │     target_size = $1k * 0.78 = $780    │
    │                                         │
    │   Get current position: $250           │
    │                                         │
    │   Execute:                              │
    │     if BUY and current < target:       │
    │       em.ai_entry('BTC', $780)         │
    │       → Buys $530 worth                │
    │                                         │
    │   INSERT INTO trades table             │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────────┐
    │    Trade Executed & Tracked          │
    │  Position: $780 BTC                  │
    │  Entry: $43,250                      │
    │  Strategy: MeanReversion_OPT_v18     │
    └──────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
PHASE 3B: SIGNAL GENERATION - TWO-ENGINE FUSION
═══════════════════════════════════════════════════════════════════════════════

    ┌──────────────────────────────────────┐
    │  Master Trading Agent (Orchestrator) │
    │  Every 15 minutes                    │
    └──────────┬───────────────────────────┘
               │
               ├─[1]─► Run ENGINE 1: volume_agent_enhanced.py
               │       │
               │       ├── Analyze volume patterns
               │       ├── Calculate RVOL, Z-Score
               │       ├── Detect spikes & persistence
               │       └── Output: src/data/signals/volume_signals.json
               │           {
               │             "BTC": {
               │               "action": "BUY",
               │               "confidence": 85,
               │               "data": {"rvol": 2.3, "z_score": 3.2}
               │             }
               │           }
               │
               ├─[2]─► Run ENGINE 2: funding_agent.py
               │       │
               │       ├── Analyze funding rates
               │       ├── Detect squeeze setups
               │       ├── Calculate positioning
               │       └── Output: src/data/signals/funding_signals.json
               │           {
               │             "BTC": {
               │               "action": "BUY",
               │               "confidence": 78,
               │               "data": {
               │                 "annual_rate": -45.2,
               │                 "positioning": "SHORTS_CROWDED",
               │                 "squeeze_risk": "HIGH"
               │               }
               │             }
               │           }
               │
               └─[3]─► FUSE SIGNALS (fusion_layer.py)
                       │
                       ├── Collect signals for each symbol
                       │   └── Validate age (<30 min)
                       │
                       ├── DECISION MATRIX:
                       │   ┌────────┬─────────┬──────────────┬──────┐
                       │   │ Volume │ Funding │ Result       │ Conf │
                       │   ├────────┼─────────┼──────────────┼──────┤
                       │   │ BUY    │ BUY     │ STRONG_BUY   │ 95%  │ ← THIS
                       │   │ BUY    │ NEUTRAL │ MEDIUM_BUY   │ 75%  │
                       │   │ BUY    │ SELL    │ WAIT         │ 50%  │
                       │   │ SELL   │ SELL    │ STRONG_SELL  │ 90%  │
                       │   │ SELL   │ NEUTRAL │ MEDIUM_SELL  │ 70%  │
                       │   │ NEUTRAL│ BUY     │ WAIT         │ 60%  │
                       │   └────────┴─────────┴──────────────┴──────┘
                       │
                       ├── Calculate fusion:
                       │   vol_action = 'BUY' (85%)
                       │   fund_action = 'BUY' (78%)
                       │   → BOTH AGREE = STRONG_BUY
                       │   → confidence = (85+78)/2 + 10 = 91%
                       │
                       └── Output: src/data/signals/fused_signals.json
                           {
                             "BTC": {
                               "action": "STRONG_BUY",
                               "confidence": 91,
                               "reasoning": "Volume spike + Short squeeze",
                               "engines": {
                                 "volume": {...},
                                 "funding": {...}
                               }
                             }
                           }

                       ▼
    ┌────────────────────────────────────────┐
    │ STEP 4: Analyze Fused Signals          │
    ├────────────────────────────────────────┤
    │ Filter:                                 │
    │   strong_signals = [                   │
    │     ('BTC', STRONG_BUY, 91%)           │
    │   ]                                     │
    │                                         │
    │ Display in color-coded format          │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ STEP 5: Execute Trades                 │
    ├────────────────────────────────────────┤
    │ For each STRONG signal (conf >= 80%):  │
    │                                         │
    │   execute_trade(                       │
    │     symbol='BTC',                      │
    │     action='STRONG_BUY',               │
    │     confidence=91,                     │
    │     reasoning='Volume spike + ...'     │
    │   )                                     │
    │                                         │
    │   If EXECUTE_TRADES=True:              │
    │     hl.market_buy('BTC', size)         │
    │     → REAL TRADE EXECUTED              │
    │                                         │
    │   If EXECUTE_TRADES=False:             │
    │     → DRY RUN (log only)               │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │  Trade Executed & Logged               │
    │  Position: 0.0462 BTC                  │
    │  Entry: $43,250                        │
    │  Signal: Two-Engine Fusion (91%)       │
    └────────────────────────────────────────┘
                     │
                     │ Sleep 15 minutes
                     ▼
    ┌────────────────────────────────────────┐
    │  CYCLE REPEATS                         │
    └────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DATABASE TRACKING (Throughout All Phases)
═══════════════════════════════════════════════════════════════════════════════

    ┌──────────────────────────────────────────────────────────────┐
    │                   trading_system.db                           │
    ├──────────────────────────────────────────────────────────────┤
    │                                                               │
    │  [strategies] - Deployed RBI strategies                      │
    │   ├── strategy_name (UNIQUE)                                 │
    │   ├── deployed (0/1)                                         │
    │   ├── deployed_timestamp                                     │
    │   ├── code_path (→ .py file)                                 │
    │   ├── backtest_return, sharpe, win_rate, etc.               │
    │   └── validation_return, validation_passed                   │
    │                                                               │
    │  [strategy_tokens] - Token/timeframe assignments             │
    │   ├── strategy_name (FK → strategies)                        │
    │   ├── token (BTC, ETH, SOL)                                  │
    │   ├── timeframe (15m, 1H, 4H)                                │
    │   ├── data_file (→ OHLCV CSV)                                │
    │   ├── backtest_return                                        │
    │   ├── validation_return, validation_passed                   │
    │   └── is_primary (1=best, 0=secondary)                       │
    │                                                               │
    │  [trades] - All executed trades                              │
    │   ├── trade_id (UNIQUE)                                      │
    │   ├── symbol, side, entry_price, position_size_usd          │
    │   ├── stop_loss, tp1_price, tp2_price, tp3_price            │
    │   ├── mode (PAPER/LIVE)                                      │
    │   ├── status (OPEN/CLOSED)                                   │
    │   ├── exit_price, pnl_usd, pnl_pct                           │
    │   ├── strategy_name (FK → strategies)                        │
    │   └── metadata (JSON)                                        │
    │                                                               │
    │  [strategy_performance] - Performance tracking               │
    │   ├── strategy_name (FK → strategies)                        │
    │   ├── timestamp                                              │
    │   ├── trades_count, win_rate, avg_pnl_pct                   │
    │   └── total_pnl_usd, sharpe_ratio, max_drawdown             │
    │                                                               │
    │  [risk_events] - Risk monitoring                             │
    │   ├── trade_id (FK → trades)                                 │
    │   ├── event_type, risk_level, risk_score                    │
    │   └── action_taken, reasoning                                │
    │                                                               │
    │  [system_events] - System health                             │
    │   ├── event_type, component, status                         │
    │   └── message                                                │
    │                                                               │
    └──────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
SUMMARY: TWO PARALLEL SIGNAL SYSTEMS
═══════════════════════════════════════════════════════════════════════════════

    SYSTEM A: RBI Deployed Strategies
    ──────────────────────────────────
    Source: RBI Agent → Database → Strategy Agent
    Frequency: On-demand or periodic
    Method: LLM-validated strategy signals
    Execution: Direct position sizing based on signal strength

    SYSTEM B: Two-Engine Fusion
    ───────────────────────────
    Source: Volume Agent + Funding Agent → Fusion Layer
    Frequency: Every 15 minutes (configurable)
    Method: Decision matrix fusion with confidence scoring
    Execution: Only STRONG signals (confidence >= 80%)

    Both systems can run:
    ✓ Independently
    ✓ Simultaneously
    ✓ With different tokens/timeframes
    ✓ In PAPER or LIVE mode (config-controlled)

═══════════════════════════════════════════════════════════════════════════════
```

---

## INTEGRATION POINTS REFERENCE

### Key Files and Line Numbers

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Phase 1: Generation** | `src/agents/rbi_agent_pp_multi.py` | 100-399 | Strategy generation with 9 parallel threads |
| **Phase 2: Deployment Init** | `risk_management/rbi_strategy_deployer.py` | 46-67 | Initialization with database connection |
| **Phase 2: Find Results** | `risk_management/rbi_strategy_deployer.py` | 68-82 | Find latest RBI folder by date |
| **Phase 2: Load CSVs** | `risk_management/rbi_strategy_deployer.py` | 84-115 | Load strategy result CSVs |
| **Phase 2: Filter** | `risk_management/rbi_strategy_deployer.py` | 117-149 | Filter strategies >= min_return |
| **Phase 2: Convert** | `risk_management/rbi_strategy_deployer.py` | 176-203 | Copy to strategies directory |
| **Phase 2: Deploy** | `risk_management/rbi_strategy_deployer.py` | 223-340 | Complete deployment with validation |
| **Phase 2: DB Insert** | `risk_management/trading_database.py` | 327-358 | Insert strategy into database |
| **Phase 2: DB Deploy** | `risk_management/trading_database.py` | 385-394 | Mark strategy as deployed |
| **Phase 2: DB Get Deployed** | `risk_management/trading_database.py` | 402-409 | Get all deployed strategies |
| **Phase 2: Add Tokens** | `risk_management/trading_database.py` | 606-639 | Add strategy token assignments |
| **Phase 3A: Strategy Init** | `src/agents/strategy_agent.py` | 56-91 | Initialize with deployed strategies |
| **Phase 3A: Get Signals** | `src/agents/strategy_agent.py` | 137-204 | Collect and evaluate signals |
| **Phase 3A: LLM Eval** | `src/agents/strategy_agent.py` | 93-135 | Claude evaluation of signals |
| **Phase 3A: Execute** | `src/agents/strategy_agent.py` | 231-305 | Execute approved signals |
| **Phase 3B: Master Agent** | `src/agents/master_trading_agent_two_engine.py` | 128-203 | Orchestrate two engines |
| **Phase 3B: Run Agents** | `src/agents/master_trading_agent_two_engine.py` | 50-90 | Run engines as subprocesses |
| **Phase 3B: Execute Trades** | `src/agents/master_trading_agent_two_engine.py` | 93-126 | Execute fused signals |
| **Phase 3B: Fusion Init** | `src/agents/fusion_layer.py` | 40-72 | Initialize fusion layer |
| **Phase 3B: Collect Signals** | `src/agents/fusion_layer.py` | 95-146 | Collect from both engines |
| **Phase 3B: Calculate Fusion** | `src/agents/fusion_layer.py` | 148-256 | Decision matrix logic |
| **Phase 3B: Fuse All** | `src/agents/fusion_layer.py` | 258-267 | Process multiple symbols |
| **Phase 3B: Display** | `src/agents/fusion_layer.py` | 278-328 | Color-coded output |
| **Base Strategy** | `src/strategies/base_strategy.py` | 6-20 | Strategy interface |

---

## KEY INSIGHTS

### Why Two Separate Systems?

1. **System A (RBI)**:
   - User-defined strategies from research
   - Backtested and validated
   - Can run on any token/timeframe combination
   - Direct database integration

2. **System B (Two-Engine)**:
   - Real-time market intelligence
   - Volume + Funding correlation (~0.35)
   - High-frequency signals (every 15 min)
   - Evidence-based fusion logic

### Database as Central Hub

All systems write to `trading_system.db`:
- RBI strategies stored with validation results
- All trades tracked with strategy attribution
- Performance metrics calculated per strategy
- Risk events logged for analysis

### LLM Integration Points

1. **RBI Agent**: Strategy code generation (xAI Grok-4)
2. **Strategy Agent**: Signal validation (Claude)
3. **Fusion Layer**: No LLM (pure logic-based)

### Execution Control

Single config flag controls everything:
```python
EXECUTE_TRADES = False  # DRY-RUN mode (safe)
EXECUTE_TRADES = True   # LIVE mode (real money)
```

---

**End of Document**
