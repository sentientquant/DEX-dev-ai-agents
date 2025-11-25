# Risk Management System

## Overview
3-layer risk management system with AI override capability. Runs FIRST before any trading decisions.

## Risk Philosophy
**User requirement**: "explain the risk managemnt we have currently"

The system implements a **defense-in-depth** approach with multiple fallback layers:

## 3-Layer Risk System

### Layer 1: Position-Level Risk (Continuous)
**Monitors**: Individual position performance
**Frequency**: Every 5 seconds
**Limits**:
- **Stop Loss**: 5% per position (configurable)
- **Take Profit**: Configurable per strategy
- **Max Position Size**: 30% of portfolio

**Action**: Close individual position if limits breached

### Layer 2: Portfolio-Level Risk (12-hour window)
**Monitors**: Total portfolio P&L over 12 hours
**Frequency**: Every 15 minutes
**Limits**:
- **Max Loss**: $50 USD in 12 hours (default)
- **Max Gain**: $100 USD in 12 hours (default)
- **Min Balance**: $100 USD (emergency threshold)

**Action**: Close ALL positions if limits breached

**Configuration**:
```python
RISK_LIMITS = {
    'max_loss_usd': 50,
    'max_gain_usd': 100,
    'max_loss_gain_check_hours': 12,
    'minimum_balance_usd': 100
}
```

### Layer 3: AI Override System
**Purpose**: Prevent false-positive closures during volatile markets
**Requirement**: AI must have 90%+ confidence to override risk limits

**How it works**:
1. Risk limit breached (e.g., -$50 loss in 12h)
2. System asks AI: "Should we really close all positions?"
3. AI analyzes:
   - Market conditions (volatility, trend)
   - Correlation of losses (all positions down = market crash)
   - Recovery potential
   - News/events
4. If AI confidence ≥ 90%: Override limit, keep positions
5. If AI confidence < 90%: Close all positions immediately

**Configuration**:
```python
RISK_LIMITS = {
    'use_ai_confirmation': True,  # Enable AI override
    'ai_override_confidence_threshold': 90  # % required
}
```

**Example Scenario**:
```
Portfolio: -$55 in 12 hours (breached -$50 limit)
AI Analysis: "Market is down 8% due to Fed news.
              Your positions are correlated to market.
              Recovery likely in 24-48h based on historical data.
              Confidence: 92%"
Result: Override engaged, positions kept open
```

## Risk Agent File
**Location**: `risk_management/risk_agent.py`

**Key Methods**:
- `check_pnl_limits()`: Monitor 12-hour P&L
- `should_override_limit()`: Ask AI for override decision
- `close_all_positions()`: Emergency position closure
- `get_portfolio_pnl()`: Calculate total P&L

## Running Risk Agent

### Standalone
```bash
python risk_management/risk_agent.py
```

### With Main Orchestrator (Automatic)
```bash
# Risk agent runs FIRST, before any trading
python src/main.py
```

## Risk Limit Examples

### Conservative (Default)
```python
RISK_LIMITS = {
    'max_loss_usd': 50,
    'max_gain_usd': 100,
    'minimum_balance_usd': 100,
    'use_ai_confirmation': True
}
```

### Aggressive
```python
RISK_LIMITS = {
    'max_loss_usd': 100,
    'max_gain_usd': 200,
    'minimum_balance_usd': 50,
    'use_ai_confirmation': False  # No AI override
}
```

### Ultra-Conservative
```python
RISK_LIMITS = {
    'max_loss_usd': 25,
    'max_gain_usd': 50,
    'minimum_balance_usd': 200,
    'use_ai_confirmation': False  # Hard stop
}
```

## Percentage-Based Limits (Alternative)
Instead of USD amounts, use percentage of portfolio:

```python
RISK_LIMITS = {
    'use_percentage': True,  # Switch to percentage mode
    'max_loss_percent': 5,   # 5% portfolio loss
    'max_gain_percent': 10   # 10% portfolio gain
}
```

## Circuit Breakers

### Minimum Balance Breach
If balance < `MINIMUM_BALANCE_USD`:
1. Stop all trading immediately
2. Close all positions (with AI confirmation if enabled)
3. Send alert to user
4. Require manual restart

### Max Loss Breach
If loss > `MAX_LOSS_USD` in 12 hours:
1. Pause trading for SLEEP_AFTER_CLOSE seconds (default: 600)
2. Close positions (with AI confirmation if enabled)
3. Reset 12-hour window

### Max Gain Breach
If gain > `MAX_GAIN_USD` in 12 hours:
1. Take profits by closing positions
2. Lock in gains
3. Reset 12-hour window
4. Optional: Reduce position sizes for next trades

## Integration with Trading Modes

### AI Swarm Mode
Risk agent provides context to 6 AI models:
- Current portfolio risk
- Position sizes
- Recent P&L

### Strategy-Based Mode
Strategies must respect risk limits:
- Position size capped at MAX_POSITION_PERCENTAGE
- Stop loss mandatory

### CopyBot Mode
Risk agent filters whale trades:
- Reject if would breach position size limits
- Scale down if too large

### RBI Research Mode
Backtest strategies must include:
- Max drawdown limits
- Position sizing rules

## AI Models Used
- **Default**: claude-3-sonnet-20240229 (balanced reasoning)
- **Override**: Requires 90%+ confidence
- **Fallback**: If AI fails, default to closing positions

## Logging
Risk agent logs all decisions:
- Risk limit checks
- AI override decisions
- Position closures
- P&L updates

Log location: Console output (color-coded)

## Alerts
Risk agent can send alerts via:
- Console output
- Discord webhook (optional)
- Telegram bot (optional)
- Email (optional)

## Testing Risk Limits
```python
# Simulate loss scenario
python risk_management/risk_agent.py --test-loss -60

# Simulate gain scenario
python risk_management/risk_agent.py --test-gain 120

# Test AI override
python risk_management/risk_agent.py --test-override
```

## Emergency Override
Manual override via config:
```python
RISK_LIMITS = {
    'emergency_override': True,  # Bypass all limits
    'emergency_duration_minutes': 60  # Auto-restore after 60 min
}
```

**WARNING**: Only use in extreme circumstances!

## Risk Metrics Dashboard
View current risk status:
```bash
python risk_management/risk_agent.py --dashboard
```

Output:
```
==== RISK DASHBOARD ====
Portfolio Value: $647.45
12h P&L: -$22.30 (-3.4%)
Open Positions: 2
Max Loss Remaining: $27.70
Max Gain Remaining: $77.70
AI Override: ENABLED
========================
```

## Best Practices
1. **Start Conservative**: Use default limits first
2. **Monitor Daily**: Check risk dashboard daily
3. **Respect Stops**: Never disable AI override in production
4. **Test First**: Paper trade with risk limits enabled
5. **Gradual Increase**: Only increase limits after consistent profitability

## Support
Risk management is the most critical component. Don't modify without understanding implications.
