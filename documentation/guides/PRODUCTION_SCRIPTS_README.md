# Production Trading System - Utility Scripts

Complete guide to all utility scripts for managing your live trading system.

---

## 🏥 System Health & Diagnostics

### `check_system_health.py`
**Purpose:** Pre-flight check before starting live trading

**What it checks:**
- ✅ API keys configured (Binance, AI services)
- ✅ Database accessible and tables exist
- ✅ Binance connection working (public + authenticated API)
- ✅ Strategies loadable
- ✅ Python dependencies installed
- ✅ Required files and directories exist

**Usage:**
```bash
python check_system_health.py
```

**When to use:**
- Before starting live trading for the first time
- After system updates
- After changing API keys
- Troubleshooting connection issues

---

### `diagnose_binance_api.py`
**Purpose:** Deep diagnostic of Binance API connection

**What it checks:**
- API key format and validity
- Authenticated request signatures
- Account permissions
- Rate limits
- Current balance fetch
- Market data access

**Usage:**
```bash
python diagnose_binance_api.py
```

---

## 📊 Live Trading Monitoring

### `monitor_live_trading.py`
**Purpose:** Real-time dashboard for active trading

**Features:**
- Real-time balance tracking
- Active positions monitoring
- PnL calculations (total and per-trade)
- Win rate statistics
- Auto-refresh every 30 seconds

**Usage:**
```bash
python monitor_live_trading.py
```

**Display shows:**
```
💰 ACCOUNT BALANCE
  Current Balance:  $487.26 USDT
  Total PnL:        +$12.50 (+2.57%)

📊 TRADE STATISTICS
  Total Trades:     5
  Active Trades:    2
  Winning Trades:   3
  Losing Trades:    1
  Win Rate:         75.0%

🔥 ACTIVE TRADES
  BTC - BUY
    Entry Price:    $84,500.00
    Position Size:  $100.00
    Stop Loss:      $83,000.00
```

---

## 📈 Performance Analytics

### `generate_trade_report.py`
**Purpose:** Comprehensive trading performance analysis

**Features:**
- Daily/Weekly/Monthly reports
- Win rate and profit factor
- Best/worst trades
- Strategy performance breakdown
- Average win/loss analysis
- Export to JSON

**Usage:**
```bash
# Last 30 days (default)
python generate_trade_report.py

# Last 7 days
python generate_trade_report.py --days 7

# Paper trading report
python generate_trade_report.py --mode PAPER --days 30

# Save to JSON file
python generate_trade_report.py --save
```

**Sample output:**
```
📊 SUMMARY STATISTICS
  Total Trades:      15
  Closed Trades:     12
  Open Trades:       3
  Total PnL:         $45.80

📈 WIN/LOSS STATISTICS
  Winning Trades:    9
  Losing Trades:     3
  Win Rate:          75.00%
  Average Win:       +$8.50
  Average Loss:      -$3.20
  Profit Factor:     2.66
```

---

## 🚨 Emergency Controls

### `emergency_stop.py`
**Purpose:** Kill switch - immediately stop all trading

**What it does:**
1. Fetches all open LIVE trades
2. Shows confirmation prompt (requires typing "EMERGENCY STOP")
3. Closes ALL positions at current market price
4. Calculates and logs final PnL
5. Creates emergency stop log entry

**Usage:**
```bash
python emergency_stop.py
```

**⚠️ WARNING:** This is PERMANENT and IRREVERSIBLE. Use only when:
- Market crash occurring
- System malfunction detected
- Need to halt trading immediately
- Unexpected strategy behavior

**Process:**
```
Found 3 open trades

  BTC - BUY
    Entry: $84,500.00 | Size: $100.00

WARNING: This will close ALL open positions immediately!

Type 'EMERGENCY STOP' to confirm: EMERGENCY STOP

🚨 CLOSING ALL POSITIONS...
  ✅ Closed BTC | PnL: -$2.50 (-2.50%)

EMERGENCY STOP COMPLETE
  Trades Closed: 3
  Total PnL: -$5.20
```

---

### `close_open_trades.py`
**Purpose:** Gracefully close specific trades (non-emergency)

**Usage:**
```bash
python close_open_trades.py
```

---

## 🔍 Testing & Verification

### `verify_indicators.py`
**Purpose:** Independent verification of technical indicators

**Tests:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- ATR (Average True Range)
- EMA trends

**Usage:**
```bash
python verify_indicators.py
```

---

### `test_volatility_bracket_fix.py`
**Purpose:** Verify Keltner Channel bracket calculations

**Usage:**
```bash
python test_volatility_bracket_fix.py
```

---

### `test_database.py`
**Purpose:** Test database operations

**Usage:**
```bash
python test_database.py
```

---

### `test_domain_models.py`
**Purpose:** Test type-safe domain models

**Usage:**
```bash
python test_domain_models.py
```

---

## 🛠️ Maintenance Scripts

### `fix_all_termcolor.py`
**Purpose:** Fix termcolor imports across entire project

**What it does:**
- Scans all Python files
- Makes termcolor imports optional
- Adds fallback for missing package

**Usage:**
```bash
python fix_all_termcolor.py
```

---

## 🎮 Main Trading System

### `trading_modes/RBI_RESEARCH_TRADE_FLOW.py`
**Purpose:** Main trading system (live and paper trading)

**Modes:**
- **LIVE:** Real trading with actual Binance account
- **PAPER:** Simulated trading with paper money

**Usage:**
```bash
# Live trading (REAL MONEY)
python -u trading_modes/RBI_RESEARCH_TRADE_FLOW.py --mode LIVE --interval 15 --symbols BTC SOL ETH

# Paper trading (SIMULATION)
python -u trading_modes/RBI_RESEARCH_TRADE_FLOW.py --mode PAPER --interval 15 --symbols BTC SOL ETH
```

**Parameters:**
- `--mode`: LIVE or PAPER
- `--interval`: Check interval in seconds (default: 15)
- `--symbols`: Space-separated list of symbols (e.g., BTC SOL ETH)

---

## 📋 Recommended Workflow

### Before Starting Live Trading

1. **System Health Check:**
   ```bash
   python check_system_health.py
   ```

2. **Test with Paper Trading:**
   ```bash
   python -u trading_modes/RBI_RESEARCH_TRADE_FLOW.py --mode PAPER --interval 15 --symbols BTC
   ```

3. **Monitor Paper Results:**
   ```bash
   python monitor_live_trading.py
   python generate_trade_report.py --mode PAPER --days 7
   ```

### Starting Live Trading

1. **Final Health Check:**
   ```bash
   python check_system_health.py
   ```

2. **Start Live Trading:**
   ```bash
   python -u trading_modes/RBI_RESEARCH_TRADE_FLOW.py --mode LIVE --interval 15 --symbols BTC SOL ETH
   ```

3. **Monitor in Separate Terminal:**
   ```bash
   python monitor_live_trading.py
   ```

### Daily Operations

1. **Morning Check:**
   ```bash
   python generate_trade_report.py --days 1
   ```

2. **Monitor Throughout Day:**
   ```bash
   python monitor_live_trading.py
   ```

3. **Emergency Stop (if needed):**
   ```bash
   python emergency_stop.py
   ```

---

## 🔐 Security Reminders

- **NEVER** commit `.env` file to git
- **NEVER** share API keys
- **ALWAYS** use paper trading first
- **ALWAYS** run `check_system_health.py` before live trading
- Keep `emergency_stop.py` accessible at all times

---

## 📞 Support

For issues or questions:
1. Check [FIXES_APPLIED_SUMMARY.md](FIXES_APPLIED_SUMMARY.md) for recent fixes
2. Run `check_system_health.py` for diagnostics
3. Review logs in `trading_system.db`

---

**Last Updated:** November 23, 2025
