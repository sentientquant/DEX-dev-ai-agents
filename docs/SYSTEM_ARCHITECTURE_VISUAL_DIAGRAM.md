# SYSTEM ARCHITECTURE - VISUAL DIAGRAM
**Moon Dev AI Trading System - Complete Flow**

---

## HIGH-LEVEL OVERVIEW

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                         MOON DEV AI TRADING SYSTEM                             │
│                      Three-Phase Intelligence Pipeline                         │
└───────────────────────────────────────────────────────────────────────────────┘

              ┌──────────────────────────────────────┐
              │         PHASE 1: CREATION            │
              │      RBI Agent (Strategy Gen)        │
              │   YouTube/PDFs → Trading Code        │
              └────────────────┬─────────────────────┘
                               │
                               ▼
              ┌──────────────────────────────────────┐
              │       PHASE 2: DEPLOYMENT            │
              │   Strategy Validator & Database      │
              │   Filter → Validate → Deploy         │
              └────────────────┬─────────────────────┘
                               │
                               ▼
              ┌──────────────────────────────────────┐
              │      PHASE 3: EXECUTION              │
              │        TWO PARALLEL SYSTEMS          │
              │                                       │
              │  ┌─────────────┐  ┌──────────────┐   │
              │  │  System A   │  │  System B    │   │
              │  │ RBI Strats  │  │ Two-Engine   │   │
              │  │  (Deploy)   │  │   Fusion     │   │
              │  └─────┬───────┘  └──────┬───────┘   │
              │        │                  │           │
              │        └────────┬─────────┘           │
              │                 ▼                     │
              │          ┌──────────────┐             │
              │          │    TRADES    │             │
              │          └──────────────┘             │
              └──────────────────────────────────────┘
```

---

## DETAILED PHASE DIAGRAMS

### PHASE 1: STRATEGY GENERATION (RBI Agent)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RBI AGENT WORKFLOW                               │
│                  (src/agents/rbi_agent_pp_multi.py)                     │
└─────────────────────────────────────────────────────────────────────────┘

INPUT SOURCES
═════════════
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ YouTube URLs │  │   PDF Docs   │  │  Text Ideas  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       └──────────────────┴──────────────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │  Trading Ideas Dir  │
                │ src/data/web_search │
                │ _research/final_    │
                │    strategies/      │
                └──────────┬──────────┘
                           │
                           ▼

PARALLEL PROCESSING (9 THREADS)
════════════════════════════════
┌──────────────────────────────────────────────────────────────────────┐
│  THREAD 1     THREAD 2     THREAD 3     ...     THREAD 9             │
│     │            │            │                     │                 │
│     ▼            ▼            ▼                     ▼                 │
│  ┌─────────────────────────────────────────────────────────┐         │
│  │            xAI Grok-4-Fast-Reasoning                     │         │
│  │                                                           │         │
│  │  STEP 1: Research Phase                                  │         │
│  │    ├─ Analyze trading idea                               │         │
│  │    ├─ Research indicators                                │         │
│  │    └─ Design strategy logic                              │         │
│  │                                                           │         │
│  │  STEP 2: Code Generation                                 │         │
│  │    ├─ Generate backtesting.py code                       │         │
│  │    ├─ Add pandas_ta indicators                           │         │
│  │    └─ Implement entry/exit logic                         │         │
│  │                                                           │         │
│  │  STEP 3: Initial Test (15m data)                         │         │
│  │    ├─ Load BTC-USDT-15m.csv                              │         │
│  │    ├─ Run backtest                                       │         │
│  │    └─ Check for errors                                   │         │
│  │                                                           │         │
│  │  STEP 4: Debug (max 2 iterations)                        │         │
│  │    ├─ If errors: AI auto-fix                             │         │
│  │    ├─ Re-test                                            │         │
│  │    └─ Repeat until working                               │         │
│  │                                                           │         │
│  │  STEP 5: Optimize (max 2 iterations)                     │         │
│  │    ├─ Tune parameters                                    │         │
│  │    ├─ Improve performance                                │         │
│  │    └─ Lock final version                                 │         │
│  │                                                           │         │
│  │  STEP 6: Multi-Data Test (25+ sources)                   │         │
│  │    ├─ Test on BTC, ETH, SOL                              │         │
│  │    ├─ Test on 15m, 1H, 4H                                │         │
│  │    ├─ Generate results CSV                               │         │
│  │    └─ Save if any pair >= 50% return                     │         │
│  └─────────────────────────────────────────────────────────┘         │
│     │            │            │                     │                 │
│     ▼            ▼            ▼                     ▼                 │
└──────────────────────────────────────────────────────────────────────┘
       │            │            │                     │
       └────────────┴────────────┴─────────────────────┘
                                 │
                                 ▼

OUTPUT STRUCTURE
════════════════
src/data/rbi_pp_multi/11_09_2025/
├── backtests_optimized/
│   ├── MeanReversion_OPT_v18.py         ← Strategy code
│   ├── BreakoutStrategy_OPT_v12.py      ← Strategy code
│   ├── TrendFollowing_OPT_v23.py        ← Strategy code
│   └── results/
│       ├── MeanReversion_OPT_v18.csv    ← Performance results
│       │   Symbol,Timeframe,Return_%,Sharpe,Trades,Win_Rate,Max_DD
│       │   BTC,15m,52.4,1.8,45,64.4,-12.3
│       │   ETH,1H,48.2,1.5,38,61.1,-15.8
│       │   SOL,15m,67.8,2.1,52,68.2,-10.2
│       │
│       ├── BreakoutStrategy_OPT_v12.csv
│       └── TrendFollowing_OPT_v23.csv
└── logs/
    └── execution_log.txt

SUCCESS CRITERIA
════════════════
✓ At least ONE token/timeframe combo >= 50% return
✓ No runtime errors in final version
✓ Valid backtesting.py syntax
✓ All indicators correctly implemented
```

---

### PHASE 2: STRATEGY DEPLOYMENT (Deployer + Database)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    STRATEGY DEPLOYMENT PIPELINE                          │
│              (risk_management/rbi_strategy_deployer.py)                 │
└─────────────────────────────────────────────────────────────────────────┘

STEP 1: INITIALIZATION
══════════════════════
┌─────────────────────────────┐
│ RBIStrategyDeployer()       │
│                              │
│ Config:                      │
│ ├─ min_return_pct: 50%      │
│ ├─ tolerance: 20%            │
│ └─ auto_debug: True          │
│                              │
│ Connections:                 │
│ ├─ trading_system.db         │
│ └─ StrategyValidator         │
└─────────────┬───────────────┘
              │
              ▼

STEP 2: FIND LATEST RBI RESULTS
════════════════════════════════
┌──────────────────────────────────────┐
│ Scan: src/data/rbi_pp_multi/         │
│                                       │
│ Folders found:                        │
│ ├─ 11_05_2025/                       │
│ ├─ 11_07_2025/                       │
│ └─ 11_09_2025/  ← LATEST             │
└──────────────┬───────────────────────┘
               │
               ▼

STEP 3: LOAD STRATEGY RESULTS
══════════════════════════════
┌──────────────────────────────────────────────────────┐
│ Load all CSV files from:                             │
│ 11_09_2025/backtests_optimized/results/              │
│                                                       │
│ Results Dict:                                         │
│ ┌────────────────────────────────────────────┐       │
│ │ 'MeanReversion_OPT_v18': DataFrame         │       │
│ │   ┌─────┬──────┬─────────┬───────┬────┐    │       │
│ │   │ Sym │  TF  │ Return% │Sharpe │ WR │    │       │
│ │   ├─────┼──────┼─────────┼───────┼────┤    │       │
│ │   │ BTC │ 15m  │  52.4   │  1.8  │64.4│    │       │
│ │   │ ETH │  1H  │  48.2   │  1.5  │61.1│    │       │
│ │   │ SOL │ 15m  │  67.8   │  2.1  │68.2│    │       │
│ │   └─────┴──────┴─────────┴───────┴────┘    │       │
│ └────────────────────────────────────────────┘       │
│                                                       │
│ ┌────────────────────────────────────────────┐       │
│ │ 'BreakoutStrategy_OPT_v12': DataFrame      │       │
│ │   (similar structure)                      │       │
│ └────────────────────────────────────────────┘       │
└──────────────┬───────────────────────────────────────┘
               │
               ▼

STEP 4: FILTER PASSING STRATEGIES
══════════════════════════════════
┌─────────────────────────────────────────┐
│ Filter: Return% >= 50%                  │
│                                          │
│ Passing Strategies:                     │
│ ┌────────────────────────────────────┐  │
│ │ MeanReversion_OPT_v18              │  │
│ │  ├─ Best: BTC-15m (52.4%)          │  │
│ │  ├─ Also: SOL-15m (67.8%)          │  │
│ │  └─ Skip: ETH-1H (48.2% < 50%)     │  │
│ └────────────────────────────────────┘  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ BreakoutStrategy_OPT_v12           │  │
│ │  └─ Best: SOL-15m (72.1%)          │  │
│ └────────────────────────────────────┘  │
└─────────────┬───────────────────────────┘
              │
              ▼

STEP 5: FOR EACH STRATEGY → DEPLOY
═══════════════════════════════════

┌───────────────────────────────────────────────────────────────────┐
│  STRATEGY: MeanReversion_OPT_v18                                  │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  SUB-STEP 5.1: Find Backtest File                                 │
│  ┌──────────────────────────────────────────────────────┐         │
│  │ Search locations:                                     │         │
│  │ ✓ backtests_optimized/MeanReversion_OPT_v18.py       │         │
│  │   backtests_package/                                 │         │
│  │   backtests_final/                                   │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                    │
│  SUB-STEP 5.2: Convert Strategy                                   │
│  ┌──────────────────────────────────────────────────────┐         │
│  │ Copy to:                                              │         │
│  │ trading_modes/02_STRATEGY_BASED_TRADING/             │         │
│  │   strategies/rbi/                                     │         │
│  │     BTC_15m_MeanReversion_OPT_v18_52pct.py           │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                    │
│  SUB-STEP 5.3: Save to Database                                   │
│  ┌──────────────────────────────────────────────────────┐         │
│  │ INSERT INTO strategies                                │         │
│  │ ┌────────────────────────────────────────────────┐   │         │
│  │ │ strategy_name: 'MeanReversion_OPT_v18'         │   │         │
│  │ │ source_type: 'RBI'                             │   │         │
│  │ │ source_url: 'src/data/rbi_pp_multi/11_09_2025'│   │         │
│  │ │ backtest_return: 52.4                          │   │         │
│  │ │ backtest_sharpe: 1.8                           │   │         │
│  │ │ backtest_max_drawdown: -12.3                   │   │         │
│  │ │ backtest_win_rate: 64.4                        │   │         │
│  │ │ backtest_trades: 45                            │   │         │
│  │ │ code_path: 'trading_modes/.../52pct.py'        │   │         │
│  │ │ deployed: 0  ← Not yet deployed                │   │         │
│  │ │ created_timestamp: '2025-11-13 10:30:00'       │   │         │
│  │ └────────────────────────────────────────────────┘   │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                    │
│  SUB-STEP 5.4: Add Token/Timeframe Assignments                    │
│  ┌──────────────────────────────────────────────────────┐         │
│  │ INSERT INTO strategy_tokens                           │         │
│  │                                                        │         │
│  │ PRIMARY (best performer):                             │         │
│  │ ┌────────────────────────────────────────────────┐   │         │
│  │ │ strategy_name: 'MeanReversion_OPT_v18'         │   │         │
│  │ │ token: 'BTC'                                   │   │         │
│  │ │ timeframe: '15m'                               │   │         │
│  │ │ data_file: 'src/data/ohlcv/BTC-USDT-15m.csv'  │   │         │
│  │ │ backtest_return: 52.4                          │   │         │
│  │ │ is_primary: 1  ← Primary assignment            │   │         │
│  │ └────────────────────────────────────────────────┘   │         │
│  │                                                        │         │
│  │ SECONDARY (also passed):                              │         │
│  │ ┌────────────────────────────────────────────────┐   │         │
│  │ │ token: 'SOL'                                   │   │         │
│  │ │ timeframe: '15m'                               │   │         │
│  │ │ backtest_return: 67.8                          │   │         │
│  │ │ is_primary: 0  ← Secondary                     │   │         │
│  │ └────────────────────────────────────────────────┘   │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                    │
│  SUB-STEP 5.5: Validate Strategy                                  │
│  ┌──────────────────────────────────────────────────────┐         │
│  │ StrategyValidator.validate_with_auto_debug()          │         │
│  │                                                        │         │
│  │ ┌────────────────────────────────────────────────┐   │         │
│  │ │ Load: BTC_15m_MeanReversion_OPT_v18_52pct.py  │   │         │
│  │ │ Data: src/data/ohlcv/BTC-USDT-15m.csv         │   │         │
│  │ │                                                │   │         │
│  │ │ Run Backtest on Out-of-Sample Data             │   │         │
│  │ │ ├─ Original Return: 52.4%                      │   │         │
│  │ │ ├─ Validation Return: 48.6%                    │   │         │
│  │ │ └─ Difference: -7.3% (within 20% tolerance)    │   │         │
│  │ │                                                │   │         │
│  │ │ Metrics Comparison:                            │   │         │
│  │ │ ┌─────────────┬──────────┬────────┬───────┐   │   │         │
│  │ │ │ Metric      │ Original │ Valid  │ Pass? │   │   │         │
│  │ │ ├─────────────┼──────────┼────────┼───────┤   │   │         │
│  │ │ │ Return%     │   52.4   │  48.6  │   ✓   │   │   │         │
│  │ │ │ Sharpe      │   1.8    │  1.7   │   ✓   │   │   │         │
│  │ │ │ Win Rate    │   64.4   │  61.2  │   ✓   │   │   │         │
│  │ │ │ Max DD      │  -12.3   │ -14.1  │   ✓   │   │   │         │
│  │ │ └─────────────┴──────────┴────────┴───────┘   │   │         │
│  │ │                                                │   │         │
│  │ │ VALIDATION: PASSED ✓                           │   │         │
│  │ └────────────────────────────────────────────────┘   │         │
│  │                                                        │         │
│  │ UPDATE strategy_tokens SET:                           │         │
│  │   validation_return = 48.6                            │         │
│  │   validation_passed = 1                               │         │
│  │ WHERE strategy_name='MeanReversion_OPT_v18'           │         │
│  │   AND token='BTC' AND timeframe='15m'                 │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                    │
│  SUB-STEP 5.6: Deploy if Validation Passed                        │
│  ┌──────────────────────────────────────────────────────┐         │
│  │ UPDATE strategies SET                                 │         │
│  │   deployed = 1                                        │         │
│  │   deployed_timestamp = '2025-11-13 10:32:00'          │         │
│  │ WHERE strategy_name = 'MeanReversion_OPT_v18'         │         │
│  │                                                        │         │
│  │ STATUS: ✅ DEPLOYED                                   │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘

                              ▼

FINAL DATABASE STATE
════════════════════

┌───────────────────────────────────────────────────────────────────┐
│  trading_system.db                                                 │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  strategies TABLE:                                                 │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ id │ strategy_name         │ deployed │ return │ path     │    │
│  ├────┼───────────────────────┼──────────┼────────┼─────────┤    │
│  │ 1  │ MeanReversion_OPT_v18 │    1     │  52.4  │ trad... │    │
│  │ 2  │ BreakoutStrat_OPT_v12 │    1     │  72.1  │ trad... │    │
│  └────┴───────────────────────┴──────────┴────────┴─────────┘    │
│                                                                    │
│  strategy_tokens TABLE:                                            │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ id │ strategy_name  │ token │ tf  │ return │ valid │ pri │    │
│  ├────┼────────────────┼───────┼─────┼────────┼───────┼─────┤    │
│  │ 1  │ MeanRev_v18    │ BTC   │ 15m │  52.4  │   1   │  1  │    │
│  │ 2  │ MeanRev_v18    │ SOL   │ 15m │  67.8  │   1   │  0  │    │
│  │ 3  │ Breakout_v12   │ SOL   │ 15m │  72.1  │   1   │  1  │    │
│  └────┴────────────────┴───────┴─────┴────────┴───────┴─────┘    │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

---

### PHASE 3A: RBI STRATEGY SIGNAL GENERATION

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   STRATEGY AGENT - RBI EXECUTION                         │
│                    (src/agents/strategy_agent.py)                       │
└─────────────────────────────────────────────────────────────────────────┘

INITIALIZATION
══════════════
┌──────────────────────────────────────┐
│ StrategyAgent.__init__()             │
│                                       │
│ ┌─────────────────────────────────┐  │
│ │ db = get_trading_db()           │  │
│ │                                 │  │
│ │ deployed = db.get_deployed_    │  │
│ │            strategies()         │  │
│ │ ↓                               │  │
│ │ SQL: SELECT * FROM strategies  │  │
│ │      WHERE deployed = 1         │  │
│ └─────────────────────────────────┘  │
│                                       │
│ Returns:                              │
│ [                                     │
│   {strategy_name: 'MeanRev_v18',     │
│    code_path: 'trading_modes/...'},  │
│   {strategy_name: 'Breakout_v12',    │
│    code_path: 'trading_modes/...'}   │
│ ]                                     │
│                                       │
│ ┌─────────────────────────────────┐  │
│ │ For each deployed strategy:     │  │
│ │   ├─ import code_path           │  │
│ │   ├─ instantiate class          │  │
│ │   └─ add to enabled_strategies  │  │
│ └─────────────────────────────────┘  │
│                                       │
│ self.enabled_strategies = [          │
│   MeanReversionStrategy(),           │
│   BreakoutStrategy()                 │
│ ]                                     │
└───────────────┬───────────────────────┘
                │
                │ agent.get_signals(token='BTC')
                ▼

SIGNAL GENERATION FLOW
══════════════════════

STEP 1: Collect Raw Signals from Each Strategy
───────────────────────────────────────────────
┌──────────────────────────────────────────────────────────┐
│ for strategy in enabled_strategies:                      │
│     signal = strategy.generate_signals()                 │
│                                                           │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ MeanReversionStrategy.generate_signals()             │ │
│ │ ┌──────────────────────────────────────────────────┐ │ │
│ │ │ # Get market data                                │ │ │
│ │ │ df = get_ohlcv_data('BTC', '15m')                │ │ │
│ │ │                                                  │ │ │
│ │ │ # Calculate indicators                           │ │ │
│ │ │ rsi = ta.rsi(df['close'], 14)                    │ │ │
│ │ │ bb = ta.bbands(df['close'], 20)                  │ │ │
│ │ │ sma50 = ta.sma(df['close'], 50)                  │ │ │
│ │ │                                                  │ │ │
│ │ │ # Current values                                 │ │ │
│ │ │ rsi_now = 28.5  (OVERSOLD)                       │ │ │
│ │ │ price = 43,250                                   │ │ │
│ │ │ bb_lower = 43,450 (price BELOW lower band)      │ │ │
│ │ │                                                  │ │ │
│ │ │ # Generate signal                                │ │ │
│ │ │ if rsi_now < 30 and price < bb_lower:            │ │ │
│ │ │     confidence = 0.78  (78%)                     │ │ │
│ │ │     direction = 'BUY'                            │ │ │
│ │ │                                                  │ │ │
│ │ │ return {                                         │ │ │
│ │ │     'token': 'BTC',                              │ │ │
│ │ │     'signal': 0.78,                              │ │ │
│ │ │     'direction': 'BUY',                          │ │ │
│ │ │     'metadata': {                                │ │ │
│ │ │         'rsi': 28.5,                             │ │ │
│ │ │         'bb_position': 'below_lower',            │ │ │
│ │ │         'entry_reason': 'Mean reversion setup'   │ │ │
│ │ │     }                                            │ │ │
│ │ │ }                                                │ │ │
│ │ └──────────────────────────────────────────────────┘ │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                           │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ BreakoutStrategy.generate_signals()                  │ │
│ │ ┌──────────────────────────────────────────────────┐ │ │
│ │ │ # Detect breakout                                │ │ │
│ │ │ volume_spike = 2.3x  (HIGH)                      │ │ │
│ │ │ resistance_break = True                          │ │ │
│ │ │ momentum = +2.3%                                 │ │ │
│ │ │                                                  │ │ │
│ │ │ return {                                         │ │ │
│ │ │     'token': 'BTC',                              │ │ │
│ │ │     'signal': 0.65,                              │ │ │
│ │ │     'direction': 'BUY',                          │ │ │
│ │ │     'metadata': {                                │ │ │
│ │ │         'volume_spike': 2.3,                     │ │ │
│ │ │         'resistance_break': True                 │ │ │
│ │ │     }                                            │ │ │
│ │ │ }                                                │ │ │
│ │ └──────────────────────────────────────────────────┘ │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                           │
│ signals = [                                               │
│     {token:'BTC', direction:'BUY', signal:0.78, ...},    │
│     {token:'BTC', direction:'BUY', signal:0.65, ...}     │
│ ]                                                         │
└──────────────────────────┬────────────────────────────────┘
                           │
                           ▼

STEP 2: Get Market Context
───────────────────────────
┌──────────────────────────────────────┐
│ collect_token_data('BTC')            │
│                                       │
│ Returns:                              │
│ {                                     │
│   'price': 43250.00,                 │
│   'volume_24h': 28500000000,         │
│   'price_change_24h': 2.3,           │
│   'volatility': 0.023,               │
│   'trend': 'BULLISH',                │
│   'support': 42800,                  │
│   'resistance': 43800                │
│ }                                     │
└──────────────┬───────────────────────┘
               │
               ▼

STEP 3: LLM Evaluation (Claude)
────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│ self.evaluate_signals(signals, market_data)                     │
│                                                                  │
│ PROMPT TO CLAUDE:                                               │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ "You are Moon Dev's Strategy Validation Assistant        │  │
│ │                                                           │  │
│ │ Analyze these signals:                                    │  │
│ │                                                           │  │
│ │ Strategy Signals:                                         │  │
│ │ [                                                         │  │
│ │   {                                                       │  │
│ │     "strategy": "MeanReversion_OPT_v18",                  │  │
│ │     "direction": "BUY",                                   │  │
│ │     "signal": 0.78,                                       │  │
│ │     "metadata": {                                         │  │
│ │       "rsi": 28.5,                                        │  │
│ │       "bb_position": "below_lower"                        │  │
│ │     }                                                     │  │
│ │   },                                                      │  │
│ │   {                                                       │  │
│ │     "strategy": "BreakoutStrategy_OPT_v12",               │  │
│ │     "direction": "BUY",                                   │  │
│ │     "signal": 0.65,                                       │  │
│ │     "metadata": {                                         │  │
│ │       "volume_spike": 2.3,                                │  │
│ │       "resistance_break": true                            │  │
│ │     }                                                     │  │
│ │   }                                                       │  │
│ │ ]                                                         │  │
│ │                                                           │  │
│ │ Market Context:                                           │  │
│ │ {                                                         │  │
│ │   "price": 43250,                                         │  │
│ │   "trend": "BULLISH",                                     │  │
│ │   "volume_24h": 28500000000                               │  │
│ │ }                                                         │  │
│ │                                                           │  │
│ │ Validate each signal and respond with:                    │  │
│ │ 1. First line: EXECUTE or REJECT for each                │  │
│ │ 2. Then explain reasoning..."                             │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│ CLAUDE RESPONSE:                                                │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ EXECUTE signal_1, EXECUTE signal_2                        │  │
│ │                                                           │  │
│ │ ANALYSIS:                                                 │  │
│ │                                                           │  │
│ │ Signal 1 (MeanReversion - BUY):                           │  │
│ │ ✓ RSI 28.5 = oversold conditions                          │  │
│ │ ✓ Price below BB lower = mean reversion setup             │  │
│ │ ✓ High confidence (78%)                                   │  │
│ │ ✓ Risk minimal in bullish trend                           │  │
│ │ Verdict: EXECUTE with 85% confidence                      │  │
│ │                                                           │  │
│ │ Signal 2 (Breakout - BUY):                                │  │
│ │ ✓ Volume spike 2.3x confirms strength                     │  │
│ │ ✓ Resistance break + bullish context                      │  │
│ │ ✓ Price momentum +2.3%                                    │  │
│ │ ✓ Both signals agree (BUY+BUY) = high conviction          │  │
│ │ Verdict: EXECUTE with 80% confidence                      │  │
│ │                                                           │  │
│ │ OVERALL:                                                  │  │
│ │ - Both signals align (confirmation)                       │  │
│ │ - Market supports bullish position                        │  │
│ │ - Risk/reward favorable                                   │  │
│ │ → RECOMMEND EXECUTION                                     │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│ evaluation = {                                                  │
│     'decisions': ['EXECUTE signal_1', 'EXECUTE signal_2'],     │
│     'reasoning': '...(full analysis)...'                        │
│ }                                                                │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼

STEP 4: Filter Approved Signals
────────────────────────────────
┌──────────────────────────────────────┐
│ approved_signals = []                │
│                                       │
│ for signal, decision in zip(...):    │
│     if "EXECUTE" in decision:        │
│         approved_signals.append()    │
│                                       │
│ Results:                              │
│   ✅ MeanReversion_OPT_v18 approved  │
│   ✅ BreakoutStrategy_OPT_v12 approved│
│                                       │
│ approved_signals = [                 │
│   {token:'BTC', direction:'BUY',     │
│    signal:0.78, ...},                │
│   {token:'BTC', direction:'BUY',     │
│    signal:0.65, ...}                 │
│ ]                                     │
└──────────────┬───────────────────────┘
               │
               ▼

STEP 5: Execute Approved Signals
─────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│ execute_strategy_signals(approved_signals)                      │
│                                                                  │
│ FOR EACH SIGNAL:                                                │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Signal: MeanReversion_OPT_v18 (BUY, 0.78)                 │  │
│ │                                                           │  │
│ │ Calculate Position Size:                                  │  │
│ │ ┌─────────────────────────────────────────────────────┐   │  │
│ │ │ usd_size = 10,000                                   │   │  │
│ │ │ MAX_POSITION_PERCENTAGE = 10                        │   │  │
│ │ │                                                     │   │  │
│ │ │ max_position = 10,000 * 0.10 = 1,000 USD           │   │  │
│ │ │ target_size = 1,000 * 0.78 = 780 USD               │   │  │
│ │ └─────────────────────────────────────────────────────┘   │  │
│ │                                                           │  │
│ │ Get Current Position:                                     │  │
│ │ ┌─────────────────────────────────────────────────────┐   │  │
│ │ │ em.get_token_balance_usd('BTC')                     │   │  │
│ │ │ → Returns: 250 USD                                  │   │  │
│ │ └─────────────────────────────────────────────────────┘   │  │
│ │                                                           │  │
│ │ Execute Trade:                                            │  │
│ │ ┌─────────────────────────────────────────────────────┐   │  │
│ │ │ if direction == 'BUY' and 250 < 780:                │   │  │
│ │ │     em.ai_entry('BTC', 780)                         │   │  │
│ │ │                                                     │   │  │
│ │ │ Trade Execution:                                    │   │  │
│ │ │   Buy Amount: 780 - 250 = 530 USD of BTC           │   │  │
│ │ │   Entry Price: $43,250                             │   │  │
│ │ │   Quantity: 530 / 43,250 = 0.01226 BTC             │   │  │
│ │ │                                                     │   │  │
│ │ │ INSERT INTO trades (                               │   │  │
│ │ │   symbol='BTC',                                    │   │  │
│ │ │   side='BUY',                                      │   │  │
│ │ │   entry_price=43250,                               │   │  │
│ │ │   position_size_usd=780,                           │   │  │
│ │ │   strategy_name='MeanReversion_OPT_v18',           │   │  │
│ │ │   mode='LIVE',                                     │   │  │
│ │ │   status='OPEN'                                    │   │  │
│ │ │ )                                                  │   │  │
│ │ └─────────────────────────────────────────────────────┘   │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│ OUTPUT:                                                          │
│   🎯 Processing signal for BTC...                               │
│   📊 Signal strength: 0.78                                       │
│   🎯 Target position: $780.00 USD                               │
│   📈 Current position: $250.00 USD                              │
│   ✨ Executing BUY for BTC                                      │
│   ✅ Entry complete for BTC                                     │
└──────────────────────────────────────────────────────────────────┘
```

---

### PHASE 3B: TWO-ENGINE FUSION SIGNAL GENERATION

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   TWO-ENGINE FUSION SYSTEM                               │
│             (master_trading_agent_two_engine.py + fusion_layer.py)      │
└─────────────────────────────────────────────────────────────────────────┘

MASTER AGENT ORCHESTRATION (Every 15 minutes)
══════════════════════════════════════════════

┌──────────────────────────────────────┐
│ run_trading_cycle()                  │
└──────────────┬───────────────────────┘
               │
               ▼

STEP 1: Run Both Engines (Parallel Subprocesses)
─────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│ ENGINE 1: Volume Intelligence                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ subprocess.run('volume_agent_enhanced.py')                  │ │
│ │                                                             │ │
│ │ Process:                                                    │ │
│ │ ├─ Fetch 24h volume data for BTC, ETH, SOL                 │ │
│ │ ├─ Calculate RVOL (relative volume)                        │ │
│ │ ├─ Calculate Z-Score (statistical significance)            │ │
│ │ ├─ Detect persistence (sustained vs spike)                 │ │
│ │ ├─ Classify signal quality                                 │ │
│ │ └─ Generate action (BUY/SELL/NOTHING)                      │ │
│ │                                                             │ │
│ │ Example Analysis (BTC):                                     │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ Current Volume: $28.5B                                  │ │ │
│ │ │ 30-day Average: $12.4B                                  │ │ │
│ │ │ RVOL: 28.5 / 12.4 = 2.3x                                │ │ │
│ │ │                                                         │ │ │
│ │ │ Volume Std Dev: $4.2B                                   │ │ │
│ │ │ Z-Score: (28.5 - 12.4) / 4.2 = 3.2σ                     │ │ │
│ │ │ (3.2 = HIGH statistical significance)                   │ │ │
│ │ │                                                         │ │ │
│ │ │ Persistence: 3 consecutive 15m bars above 2x            │ │ │
│ │ │ Classification: HIGH persistence                        │ │ │
│ │ │                                                         │ │ │
│ │ │ Signal Quality: EXCELLENT                               │ │ │
│ │ │ (RVOL > 2.0 + Z-Score > 3.0 + High persistence)         │ │ │
│ │ │                                                         │ │ │
│ │ │ Decision: BUY (confidence: 85%)                         │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ Output: src/data/signals/volume_signals.json                │ │
│ │ {                                                           │ │
│ │   "BTC": {                                                  │ │
│ │     "action": "BUY",                                        │ │
│ │     "confidence": 85,                                       │ │
│ │     "timestamp": "2025-11-13T10:30:00Z",                    │ │
│ │     "data": {                                               │ │
│ │       "rvol": 2.3,                                          │ │
│ │       "z_score": 3.2,                                       │ │
│ │       "persistence_class": "HIGH",                          │ │
│ │       "signal_quality": "EXCELLENT"                         │ │
│ │     }                                                       │ │
│ │   }                                                         │ │
│ │ }                                                           │ │
│ │                                                             │ │
│ │ Runtime: 12.3 seconds                                       │ │
│ │ Status: ✅ SUCCESS                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ENGINE 2: Funding Rate Intelligence                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ subprocess.run('funding_agent.py')                          │ │
│ │                                                             │ │
│ │ Process:                                                    │ │
│ │ ├─ Fetch funding rates from exchanges                      │ │
│ │ ├─ Convert to annualized %                                 │ │
│ │ ├─ Analyze positioning (long/short crowded)                │ │
│ │ ├─ Calculate squeeze risk                                  │ │
│ │ └─ Generate action (BUY/SELL/NOTHING)                      │ │
│ │                                                             │ │
│ │ Example Analysis (BTC):                                     │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ 8-hour Funding Rate: -0.15%                             │ │ │
│ │ │ Daily Rate: -0.15% * 3 = -0.45%                         │ │ │
│ │ │ Annual Rate: -0.45% * 365 = -45.2%                      │ │ │
│ │ │                                                         │ │ │
│ │ │ Interpretation:                                         │ │ │
│ │ │ ├─ Negative rate = Shorts pay Longs                     │ │ │
│ │ │ ├─ -45% APR = VERY negative                             │ │ │
│ │ │ └─ Positioning: SHORTS CROWDED                          │ │ │
│ │ │                                                         │ │ │
│ │ │ Squeeze Risk Analysis:                                  │ │ │
│ │ │ ├─ Rate < -20% APR = HIGH squeeze potential             │ │ │
│ │ │ ├─ Historical: -45% often precedes short squeezes       │ │ │
│ │ │ └─ Risk Level: HIGH                                     │ │ │
│ │ │                                                         │ │ │
│ │ │ Decision: BUY (confidence: 78%)                         │ │ │
│ │ │ Reasoning: "Short squeeze setup - funding -45% APR"     │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ Output: src/data/signals/funding_signals.json               │ │
│ │ {                                                           │ │
│ │   "BTC": {                                                  │ │
│ │     "action": "BUY",                                        │ │
│ │     "confidence": 78,                                       │ │
│ │     "timestamp": "2025-11-13T10:30:00Z",                    │ │
│ │     "data": {                                               │ │
│ │       "annual_rate": -45.2,                                 │ │
│ │       "positioning": "SHORTS_CROWDED",                      │ │
│ │       "squeeze_risk": "HIGH"                                │ │
│ │     },                                                      │ │
│ │     "reasoning": "Funding -45% APR indicates short squeeze" │ │
│ │   }                                                         │ │
│ │ }                                                           │ │
│ │                                                             │ │
│ │ Runtime: 8.7 seconds                                        │ │
│ │ Status: ✅ SUCCESS                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

                         ▼

STEP 2: Fuse Signals (fusion_layer.py)
───────────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│ fusion = TwoEngineFusion()                                      │
│ fused = fusion.fuse_all_symbols(['BTC', 'ETH', 'SOL'])          │
│                                                                  │
│ FOR SYMBOL 'BTC':                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ collect_signals('BTC', max_age_minutes=30)                  │ │
│ │                                                             │ │
│ │ Load Volume Signal:                                         │ │
│ │ ├─ Read: volume_signals.json                                │ │
│ │ ├─ Extract: BTC section                                     │ │
│ │ ├─ Validate age: 2.3 min (< 30 min ✓)                      │ │
│ │ └─ Status: VALID                                            │ │
│ │                                                             │ │
│ │ Load Funding Signal:                                        │ │
│ │ ├─ Read: funding_signals.json                               │ │
│ │ ├─ Extract: BTC section                                     │ │
│ │ ├─ Validate age: 1.8 min (< 30 min ✓)                      │ │
│ │ └─ Status: VALID                                            │ │
│ │                                                             │ │
│ │ signals = {                                                 │ │
│ │     'volume': {                                             │ │
│ │         'action': 'BUY',                                    │ │
│ │         'confidence': 85,                                   │ │
│ │         'data': {...},                                      │ │
│ │         'age_minutes': 2.3                                  │ │
│ │     },                                                      │ │
│ │     'funding': {                                            │ │
│ │         'action': 'BUY',                                    │ │
│ │         'confidence': 78,                                   │ │
│ │         'data': {...},                                      │ │
│ │         'age_minutes': 1.8                                  │ │
│ │     }                                                       │ │
│ │ }                                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ calculate_fusion(signals)                                   │ │
│ │                                                             │ │
│ │ DECISION MATRIX CHECK:                                      │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ Volume Action: BUY (85%)                                │ │ │
│ │ │ Funding Action: BUY (78%)                               │ │ │
│ │ │                                                         │ │ │
│ │ │ Matrix Lookup:                                          │ │ │
│ │ │ ┌────────┬─────────┬──────────────┬──────┐             │ │ │
│ │ │ │ Volume │ Funding │ Result       │ Conf │             │ │ │
│ │ │ ├────────┼─────────┼──────────────┼──────┤             │ │ │
│ │ │ │ BUY    │ BUY     │ STRONG_BUY   │ 95%  │ ← MATCH    │ │ │
│ │ │ │ BUY    │ NEUTRAL │ MEDIUM_BUY   │ 75%  │             │ │ │
│ │ │ │ BUY    │ SELL    │ WAIT         │ 50%  │             │ │ │
│ │ │ └────────┴─────────┴──────────────┴──────┘             │ │ │
│ │ │                                                         │ │ │
│ │ │ MATCH: BUY + BUY = STRONG_BUY                           │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ Calculate Confidence:                                       │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ confidence = (85 + 78) / 2 + 10                         │ │ │
│ │ │            = 81.5 + 10                                  │ │ │
│ │ │            = 91.5                                       │ │ │
│ │ │            = min(100, 91.5)                             │ │ │
│ │ │            = 91%                                        │ │ │
│ │ │                                                         │ │ │
│ │ │ (Agreement bonus: +10% for both engines agreeing)       │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ Generate Reasoning:                                         │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ "Volume spike + Short squeeze setup = High conviction"  │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ fusion_result = {                                           │ │
│ │     'action': 'STRONG_BUY',                                 │ │
│ │     'confidence': 91,                                       │ │
│ │     'fusion_score': 45.7,                                   │ │
│ │     'reasoning': 'Volume spike + Short squeeze = High conv',│ │
│ │     'engines': {                                            │ │
│ │         'volume': {action:'BUY', conf:85, rvol:2.3, ...},   │ │
│ │         'funding': {action:'BUY', conf:78, rate:-45.2, ...} │ │
│ │     },                                                      │ │
│ │     'timestamp': '2025-11-13T10:32:00Z'                     │ │
│ │ }                                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼

STEP 3: Save Fused Signals
───────────────────────────
┌──────────────────────────────────────┐
│ fusion.save_fused_signals()          │
│                                       │
│ Write to:                             │
│ src/data/signals/fused_signals.json  │
│                                       │
│ {                                     │
│   "BTC": {                            │
│     "action": "STRONG_BUY",           │
│     "confidence": 91,                 │
│     "reasoning": "...",               │
│     "engines": {...}                  │
│   },                                  │
│   "ETH": {...},                       │
│   "SOL": {...}                        │
│ }                                     │
└──────────────┬───────────────────────┘
               │
               ▼

STEP 4: Analyze & Display
──────────────────────────
┌──────────────────────────────────────┐
│ Filter Strong Signals:               │
│ ├─ confidence >= 80%                 │
│ ├─ action in [STRONG_BUY,STRONG_SELL]│
│ └─ found: 1 (BTC)                    │
│                                       │
│ Display Output:                       │
│ ════════════════════════════════════ │
│ BTC: STRONG_BUY                      │
│   Confidence: 91%                    │
│   Reasoning: Volume spike + Short... │
│                                       │
│   ENGINE 1 (Volume):                 │
│     Action: BUY (85%)                │
│     RVOL: 2.30x | Z: 3.20            │
│     Persistence: HIGH                │
│     Quality: EXCELLENT               │
│                                       │
│   ENGINE 2 (Funding):                │
│     Action: BUY (78%)                │
│     Rate: -45.20% APR                │
│     Positioning: SHORTS_CROWDED      │
│     Squeeze Risk: HIGH               │
│ ════════════════════════════════════ │
└──────────────┬───────────────────────┘
               │
               ▼

STEP 5: Execute Trades
──────────────────────
┌──────────────────────────────────────┐
│ execute_trade(                       │
│     symbol='BTC',                    │
│     action='STRONG_BUY',             │
│     confidence=91,                   │
│     reasoning='...'                  │
│ )                                     │
│                                       │
│ If EXECUTE_TRADES = True:            │
│ ┌────────────────────────────────┐   │
│ │ from nice_funcs_hl import *    │   │
│ │                                │   │
│ │ size = calc_position(91%)      │   │
│ │ market_buy('BTC', size)        │   │
│ │                                │   │
│ │ Trade Executed:                │   │
│ │ ├─ Symbol: BTC                 │   │
│ │ ├─ Side: BUY                   │   │
│ │ ├─ Size: 0.0462 BTC            │   │
│ │ ├─ Entry: $43,250              │   │
│ │ └─ USD: $2,000                 │   │
│ │                                │   │
│ │ INSERT INTO trades (...)       │   │
│ └────────────────────────────────┘   │
│                                       │
│ Output:                               │
│   [TRADE] BTC: STRONG_BUY (91%)      │
│   [EXEC] Bought 0.0462 BTC           │
└──────────────┬───────────────────────┘
               │
               │ Sleep 15 minutes
               ▼
    ┌──────────────────────┐
    │  CYCLE REPEATS       │
    └──────────────────────┘
```

---

## DATABASE SCHEMA

```
┌───────────────────────────────────────────────────────────────────────┐
│                          trading_system.db                             │
│                           SQLite Database                              │
└───────────────────────────────────────────────────────────────────────┘

TABLE: strategies
══════════════════
┌─────────────────────────────────────────────────────────────────┐
│ id                      INTEGER PRIMARY KEY AUTOINCREMENT       │
│ strategy_name           TEXT UNIQUE NOT NULL                    │
│ created_timestamp       DATETIME NOT NULL                       │
│ source_type             TEXT NOT NULL (RBI, MANUAL, etc.)       │
│ source_url              TEXT (YouTube, PDF, etc.)               │
│ backtest_return         REAL                                    │
│ backtest_sharpe         REAL                                    │
│ backtest_max_drawdown   REAL                                    │
│ backtest_win_rate       REAL                                    │
│ backtest_trades         INTEGER                                 │
│ converted_timestamp     DATETIME                                │
│ validation_timestamp    DATETIME                                │
│ validation_return       REAL                                    │
│ validation_passed       INTEGER (0 or 1)                        │
│ validation_reason       TEXT                                    │
│ deployed                INTEGER DEFAULT 0 (0=no, 1=yes)         │
│ deployed_timestamp      DATETIME                                │
│ code_path               TEXT (path to .py file)                 │
│ metadata                TEXT (JSON)                             │
└─────────────────────────────────────────────────────────────────┘

TABLE: strategy_tokens
═══════════════════════
┌─────────────────────────────────────────────────────────────────────┐
│ id                      INTEGER PRIMARY KEY AUTOINCREMENT           │
│ strategy_name           TEXT NOT NULL (FK → strategies)             │
│ token                   TEXT NOT NULL (BTC, ETH, SOL, etc.)         │
│ timeframe               TEXT NOT NULL (15m, 1H, 4H, etc.)           │
│ data_file               TEXT NOT NULL (path to OHLCV CSV)           │
│ backtest_return         REAL                                        │
│ backtest_sharpe         REAL                                        │
│ backtest_trades         INTEGER                                     │
│ validation_return       REAL                                        │
│ validation_passed       INTEGER DEFAULT 0 (0=no, 1=yes)             │
│ is_primary              INTEGER DEFAULT 0 (1=best, 0=secondary)     │
│ created_timestamp       DATETIME NOT NULL                           │
│                                                                      │
│ UNIQUE(strategy_name, token, timeframe)                             │
└─────────────────────────────────────────────────────────────────────┘

TABLE: trades
══════════════
┌─────────────────────────────────────────────────────────────────────┐
│ id                      INTEGER PRIMARY KEY AUTOINCREMENT           │
│ trade_id                TEXT UNIQUE NOT NULL                        │
│ timestamp               DATETIME NOT NULL                           │
│ symbol                  TEXT NOT NULL (BTC, ETH, etc.)              │
│ side                    TEXT NOT NULL (BUY, SELL)                   │
│ entry_price             REAL NOT NULL                               │
│ position_size_usd       REAL NOT NULL                               │
│ stop_loss               REAL NOT NULL                               │
│ tp1_price, tp2_price, tp3_price  REAL                              │
│ tp1_pct, tp2_pct, tp3_pct        REAL                              │
│ mode                    TEXT NOT NULL (PAPER, LIVE)                 │
│ status                  TEXT NOT NULL (OPEN, CLOSED)                │
│ exit_price              REAL                                        │
│ exit_timestamp          DATETIME                                    │
│ pnl_usd                 REAL                                        │
│ pnl_pct                 REAL                                        │
│ exit_reason             TEXT                                        │
│ strategy_name           TEXT (FK → strategies)                      │
│ swing_bars_ago          INTEGER                                     │
│ swing_strength          REAL                                        │
│ atr_pct                 REAL                                        │
│ atr_multiplier          REAL                                        │
│ confidence              TEXT                                        │
│ metadata                TEXT (JSON)                                 │
└─────────────────────────────────────────────────────────────────────┘

TABLE: strategy_performance
═════════════════════════════
┌─────────────────────────────────────────────────────────────────────┐
│ id                      INTEGER PRIMARY KEY AUTOINCREMENT           │
│ strategy_name           TEXT NOT NULL (FK → strategies)             │
│ timestamp               DATETIME NOT NULL                           │
│ trades_count            INTEGER                                     │
│ win_rate                REAL                                        │
│ avg_pnl_pct             REAL                                        │
│ total_pnl_usd           REAL                                        │
│ sharpe_ratio            REAL                                        │
│ max_drawdown            REAL                                        │
│ status                  TEXT                                        │
└─────────────────────────────────────────────────────────────────────┘

TABLE: risk_events
═══════════════════
┌─────────────────────────────────────────────────────────────────────┐
│ id                      INTEGER PRIMARY KEY AUTOINCREMENT           │
│ timestamp               DATETIME NOT NULL                           │
│ trade_id                TEXT (FK → trades)                          │
│ event_type              TEXT NOT NULL                               │
│ risk_level              TEXT NOT NULL (LOW, MEDIUM, HIGH)           │
│ risk_score              REAL                                        │
│ action_taken            TEXT                                        │
│ reasoning               TEXT                                        │
│ metadata                TEXT (JSON)                                 │
└─────────────────────────────────────────────────────────────────────┘

TABLE: system_events
═════════════════════
┌─────────────────────────────────────────────────────────────────────┐
│ id                      INTEGER PRIMARY KEY AUTOINCREMENT           │
│ timestamp               DATETIME NOT NULL                           │
│ event_type              TEXT NOT NULL                               │
│ component               TEXT NOT NULL                               │
│ status                  TEXT NOT NULL (SUCCESS, ERROR, WARNING)     │
│ message                 TEXT                                        │
│ metadata                TEXT (JSON)                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## KEY SQL QUERIES

```sql
-- Get all deployed strategies
SELECT * FROM strategies WHERE deployed = 1;

-- Get strategies for specific token
SELECT st.strategy_name, st.timeframe, st.backtest_return, s.code_path
FROM strategy_tokens st
JOIN strategies s ON st.strategy_name = s.strategy_name
WHERE st.token = 'BTC'
  AND st.validation_passed = 1
  AND s.deployed = 1
ORDER BY st.backtest_return DESC;

-- Get open trades
SELECT * FROM trades WHERE status = 'OPEN';

-- Get strategy performance
SELECT
    s.strategy_name,
    s.backtest_return,
    COUNT(t.id) as live_trades,
    AVG(t.pnl_pct) as avg_pnl,
    SUM(CASE WHEN t.pnl_usd > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(t.id) as win_rate
FROM strategies s
LEFT JOIN trades t ON s.strategy_name = t.strategy_name AND t.status = 'CLOSED'
WHERE s.deployed = 1
GROUP BY s.strategy_name;
```

---

**End of Visual Diagram**
