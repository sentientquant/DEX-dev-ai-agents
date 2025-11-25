# HOW TO RUN: Enhanced Volume Agent
## Complete Step-by-Step Guide

**Date**: 2025-01-13
**File**: [src/agents/volume_agent_enhanced.py](../src/agents/volume_agent_enhanced.py)

---

## 🚀 QUICK START (30 Seconds)

### Single Test Run
```bash
cd C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents
python src/agents/volume_agent_enhanced.py --once
```

### Continuous Mode (4H Intervals)
```bash
cd C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents
python src/agents/volume_agent_enhanced.py
```

---

## 📋 PREREQUISITES

### 1. Python Environment
```bash
# Use existing conda environment
conda activate tflow
```

### 2. Required Packages (Already Installed)
- ✅ `requests` - API calls
- ✅ `pandas` - Data processing
- ✅ `numpy` - Statistical calculations
- ✅ `termcolor` - Colored output
- ✅ `python-dotenv` - Environment variables (if needed)

**No new packages needed!**

### 3. API Keys Required
- ✅ **Hyperliquid API** - Public, no key needed
- ✅ **AI Models** - At least one of:
  - Anthropic (Claude)
  - OpenAI (GPT)
  - xAI (Grok)
  - DeepSeek
  - OpenRouter

Keys should be in `.env` file (already configured).

---

## 🎯 RUNNING OPTIONS

### Option 1: Test Mode (Recommended First)
**Purpose**: Run once, see results, exit

```bash
# Navigate to project root
cd C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents

# Run single check
python src/agents/volume_agent_enhanced.py --once
```

**What happens**:
1. Fetches top 15 Hyperliquid tokens
2. Calculates intelligence metrics (RVOL, Z-Score, Persistence)
3. Pre-filters top 5 signals
4. Queries AI swarm
5. Displays intelligent summary
6. Saves data to CSV files
7. Exits

**Expected runtime**: 30-60 seconds (depends on AI response time)

---

### Option 2: Continuous Mode (Production)
**Purpose**: Run every 4 hours automatically

```bash
# Navigate to project root
cd C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents

# Start continuous monitoring
python src/agents/volume_agent_enhanced.py
```

**What happens**:
1. Runs check every 4 hours (configurable)
2. Builds baseline statistics over time
3. Learns AI performance patterns
4. Runs until Ctrl+C

**To stop**: Press `Ctrl+C`

---

### Option 3: Custom Interval
**Purpose**: Change check frequency

Edit line 40 in `volume_agent_enhanced.py`:
```python
# Change from 4 hours to 1 hour
CHECK_INTERVAL = 1 * 60 * 60  # 1 hour
```

Or run with environment variable:
```bash
# Not yet implemented, but can add this feature if needed
```

---

## 📊 EXPECTED OUTPUT

### Startup Output
```
🚀 HYPERLIQUID VOLUME AGENT - ENHANCED INTELLIGENCE EDITION 🚀
════════════════════════════════════════════════════════════════

📊 ENHANCEMENTS:
   Phase 1: RVOL, Z-Score, Persistence, Vol-Price Correlation
   Phase 2: AI Pre-Filtering, Confidence Voting, Learning Memory
   Phase 3: Signal Categories, OI/Funding Health, Smart Display

💾 Data saved to: C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\volume_agent/
⏰ Running every 4 hours
```

### Processing Steps
```
🔄 ENHANCED VOLUME AGENT CHECK - 2025-01-13 10:00:00
════════════════════════════════════════════════════════════════

📡 Fetching Hyperliquid data...
✅ Got top 15 altcoins

📊 Loading historical context...
✅ Loaded baselines for 15 tokens

🧠 Calculating intelligence metrics (RVOL, Z-Score, Persistence)...
✅ Intelligence calculated for 15 tokens

🔄 Updating persistence tracker...
✅ Persistence updated

🎯 Pre-filtering top 5 signals for AI swarm...
✅ Filtered to top 5 signals (70% token reduction)

🤖 Querying AI swarm with pre-processed intelligence...
```

### Intelligence Summary Output
```
🎯 MARKET INTELLIGENCE SUMMARY
════════════════════════════════════════════════════════════════

✅ TOP CONFIRMED TREND CONTINUATIONS (2)
   1. HYPE     [HIGH]   RVOL 2.1x, ESTABLISHED trend (4 cycles), STRONG_BUY
   2. DOGE     [HIGH]   RVOL 3.2x, EMERGING trend (2 cycles), STRONG_BUY

⚠️  NEW HYPE ENTRIES (Likely to Fade) (1)
   1. SHIB     [FADE RISK 70%]   First cycle, funding 0.05%

🔍 QUIET ACCUMULATION (Low Crowd Exposure) (1)
   1. ARB      [STEALTH]   OI +25%, price flat, funding 0.005%

🚨 DISTRIBUTION TRAPS (Avoid These) (1)
   1. PEPE     [DANGER]   Volume +45%, price -2%, OI -8%

📊 CROWDED TRADES (Reversal Risk) (0)
   None detected this cycle

════════════════════════════════════════════════════════════════

🧠 AI SWARM CONSENSUS:
   🏆 TOP PICK: HYPE
      Consensus Score: 75% (weighted by AI accuracy + confidence)
      Lead AI: DEEPSEEK (Accuracy: 90%, Confidence: 85%)

   🥈 RUNNER-UP: DOGE (58%)

════════════════════════════════════════════════════════════════
```

---

## 📁 DATA FILES CREATED

All files saved to: `C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\volume_agent/`

### 1. volume_history.csv
**Purpose**: Raw volume snapshots every 4H
```csv
timestamp,datetime,rank,symbol,volume_24h,price,change_24h_pct,funding_rate_pct,open_interest
1705147200,2025-01-13 08:00:00,1,DOGE,125500000,0.0875,8.2,0.01,45000000
```

### 2. baseline_stats.csv (NEW)
**Purpose**: Rolling 10-day baselines for RVOL calculation
```csv
symbol,mean_4h_volume,std_4h_volume,mean_rank,last_updated,sample_count
DOGE,39250000,8500000,8.5,2025-01-13 12:00:00,24
```

### 3. persistence_tracker.csv (NEW)
**Purpose**: Track consecutive cycles in Top-15
```csv
timestamp,symbol,consecutive_cycles_top15,consecutive_cycles_high_rvol,classification,fade_risk_pct
1705147200,DOGE,2,1,EMERGING,50
```

### 4. ai_performance.csv (NEW)
**Purpose**: AI historical accuracy tracking
```csv
ai_name,total_predictions,correct_predictions,accuracy,last_updated
deepseek,20,18,0.90,2025-01-13 12:00:00
claude,20,15,0.75,2025-01-13 12:00:00
```

### 5. swarm_memory.csv (NEW)
**Purpose**: Record all swarm decisions + outcomes
```csv
timestamp,datetime,top_pick,consensus_score,price_entry,price_4h_later,outcome,profit_pct,winning_ai,ai_confidence
1705147200,2025-01-13 08:00:00,DOGE,75.2,0.0875,0.0895,WIN,2.3,deepseek,85
```

### 6. agent_analysis.jsonl
**Purpose**: Full analysis logs in JSON format
```json
{"timestamp": 1705147200, "datetime": "2025-01-13 08:00:00", "changes": [...], "swarm_result": {...}}
```

---

## 🔧 TROUBLESHOOTING

### Issue 1: Windows Encoding Error (Emojis)
**Error**: `UnicodeEncodeError: 'charmap' codec can't encode character`

**Solution**: Already handled in code with UTF-8 fallback. If still occurs:
```bash
# Set console to UTF-8
chcp 65001

# Then run
python src/agents/volume_agent_enhanced.py --once
```

### Issue 2: No Baseline Stats on First Run
**Expected**: First run won't have RVOL/Z-Score (needs history)

**Solution**:
- Run for 3+ cycles (12 hours) to build baseline
- After 3 cycles, all intelligence features activate

### Issue 3: AI Models Failing
**Error**: Some AI models may fail to initialize

**Solution**: System continues with working models
- Needs at least 1 AI model to work
- Best results with 3+ models
- Check `.env` for API keys

### Issue 4: Hyperliquid API Down
**Error**: `❌ API Error: 503`

**Solution**:
- Wait and retry (API may be temporarily down)
- Check Hyperliquid status: https://status.hyperliquid.xyz/

---

## ⚙️ CONFIGURATION OPTIONS

### Change Check Interval
Edit line 40:
```python
CHECK_INTERVAL = 4 * 60 * 60  # 4 hours (default)
# Change to:
CHECK_INTERVAL = 1 * 60 * 60  # 1 hour
CHECK_INTERVAL = 24 * 60 * 60  # 24 hours
```

### Change Top N Tokens
Edit line 44:
```python
TOP_N = 15  # Default
# Change to:
TOP_N = 20  # Track top 20
```

### Change Intelligence Thresholds
Edit lines 46-54:
```python
RVOL_HIGH_THRESHOLD = 2.0      # Default: 2.0x
Z_SCORE_HIGH = 2.0             # Default: 2σ (95th percentile)
CORRELATION_STRONG = 0.7       # Default: 0.7 correlation
FUNDING_CROWDED = 0.05         # Default: 0.05% (crowded)
BASELINE_DAYS = 10             # Default: 10-day baseline
```

### Change AI Pre-Filter Count
Edit line 438:
```python
top_signals = filter_top_signals(intelligence_data, top_n=5)
# Change to:
top_signals = filter_top_signals(intelligence_data, top_n=3)  # Top 3 only
```

---

## 📈 MONITORING PROGRESS

### Check Data Directory
```bash
cd C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\volume_agent
dir
```

**Should see**:
- `volume_history.csv` (growing each cycle)
- `baseline_stats.csv` (updates each cycle)
- `persistence_tracker.csv` (grows each cycle)
- `ai_performance.csv` (updates when manually tracked)
- `swarm_memory.csv` (grows each cycle)

### View Latest Baseline Stats
```bash
type baseline_stats.csv
```

### Count Historical Samples
```bash
# PowerShell
(Get-Content volume_history.csv | Measure-Object -Line).Lines

# Should grow by 15 entries per cycle
```

---

## 🎯 TESTING CHECKLIST

### Day 1: First Run
- [ ] Run `--once` mode successfully
- [ ] Verify 6 CSV files created
- [ ] Check baseline_stats.csv has entries
- [ ] Confirm persistence_tracker.csv created
- [ ] See intelligent summary output

### Day 2-3: Building Baseline
- [ ] Run 3+ times (12+ hours apart)
- [ ] Verify RVOL calculations appear
- [ ] Check Z-Score values showing
- [ ] Confirm persistence classifications working

### Week 1: Full Intelligence
- [ ] All 5 signal categories populating
- [ ] AI consensus showing weighted scores
- [ ] Baseline stats have 10+ samples
- [ ] Persistence tracking showing ESTABLISHED trends

### Month 1: Validation
- [ ] Track performance vs original agent
- [ ] Calculate actual win rate
- [ ] Measure false positive reduction
- [ ] Validate academic projections

---

## 🚨 IMPORTANT NOTES

### What This Does
- ✅ Analyzes volume patterns with intelligence
- ✅ Provides trading signals (not execution)
- ✅ Learns baselines over time
- ✅ Tracks AI performance

### What This Does NOT Do
- ❌ Does NOT execute trades automatically
- ❌ Does NOT guarantee profits
- ❌ Does NOT work without historical data (first 3 cycles)
- ❌ Does NOT require new packages

### Risk Warning
- This is an **experimental educational tool**
- All trading involves **substantial risk of loss**
- Validate on paper trading first
- Never risk more than you can afford to lose

---

## 🆘 GETTING HELP

### Check Logs
All errors printed to console with colors:
- 🔴 Red = Error
- 🟡 Yellow = Warning
- 🟢 Green = Success
- 🔵 Blue/Cyan = Info

### Common Issues
1. **No output**: Check Python environment (`conda activate tflow`)
2. **API errors**: Check internet connection + Hyperliquid API status
3. **No baselines**: Normal on first 3 runs, wait for history
4. **AI failures**: At least 1 AI must work, check `.env` keys

### Still Stuck?
- Check error messages carefully
- Verify all prerequisites installed
- Test with original `volume_agent.py` first
- Check Hyperliquid API status

---

## ✅ SUCCESS CRITERIA

You know it's working when you see:
1. ✅ All 6 CSV files created in `src/data/volume_agent/`
2. ✅ RVOL values showing (after 3+ cycles)
3. ✅ Z-Score calculations appearing
4. ✅ Persistence classifications (SPIKE/EMERGING/ESTABLISHED)
5. ✅ 5 signal categories populating
6. ✅ AI consensus with weighted scores

---

## 📞 QUICK REFERENCE

```bash
# TEST MODE (run once)
python src/agents/volume_agent_enhanced.py --once

# PRODUCTION MODE (continuous)
python src/agents/volume_agent_enhanced.py

# STOP RUNNING
Ctrl+C

# CHECK DATA
cd src/data/volume_agent
dir

# VIEW BASELINE STATS
type baseline_stats.csv

# VIEW PERSISTENCE
type persistence_tracker.csv
```

---

**Ready to run!** Start with `--once` mode to test, then switch to continuous mode for production monitoring.
