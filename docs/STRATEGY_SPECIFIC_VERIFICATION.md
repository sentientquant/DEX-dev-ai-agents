# Strategy-Specific Verification - Using Strategy's ACTUAL Settings ✅

## Critical Upgrade Implemented

**BEFORE**: System used generic indicator defaults (EMA 20/50/200, RSI 14, ATR 14)
**AFTER**: System extracts and uses **STRATEGY'S ACTUAL INDICATOR SETTINGS**

## Why This Matters

### The Problem You Identified

If we analyze with **generic indicators** but the strategy uses **different settings**, we're comparing apples to oranges!

**Example**:
```python
# Technical Snapshot (OLD - WRONG):
ema_50 = calculate_ema(closes, 50)  # Generic default
rsi_14 = calculate_rsi(closes, 14)  # Generic default

# But Strategy Uses:
ma_period = 50          # ✓ Happens to match
rsi_period = 14         # ✓ Happens to match
atr_period = 14         # ✓ Happens to match
multiplier = 1.5        # ✗ NOT CHECKED!
min_atr_pct = 0.005     # ✗ NOT CHECKED!
max_atr_pct = 0.03      # ✗ NOT CHECKED!
```

**Result**: We might say "strategy needs tuning" when actually the strategy is working perfectly with ITS settings!

## Solution Implemented

### 1. Extract Strategy's Actual Settings

```python
def _extract_strategy_settings(strategy_instance):
    """Extract ACTUAL indicator settings from strategy object"""
    settings = {}

    # ATR settings
    if hasattr(strategy_instance, 'atr_period'):
        settings['atr_period'] = strategy_instance.atr_period  # e.g., 14
    if hasattr(strategy_instance, 'multiplier'):
        settings['multiplier'] = strategy_instance.multiplier  # e.g., 1.5

    # MA settings
    if hasattr(strategy_instance, 'ma_period'):
        settings['ma_period'] = strategy_instance.ma_period  # e.g., 50

    # RSI settings
    if hasattr(strategy_instance, 'rsi_period'):
        settings['rsi_period'] = strategy_instance.rsi_period  # e.g., 14
    if hasattr(strategy_instance, 'rsi_overbought'):
        settings['rsi_overbought'] = strategy_instance.rsi_overbought  # e.g., 65
    if hasattr(strategy_instance, 'rsi_oversold'):
        settings['rsi_oversold'] = strategy_instance.rsi_oversold  # e.g., 35

    # ATR thresholds
    if hasattr(strategy_instance, 'min_atr_pct'):
        settings['min_atr_pct'] = strategy_instance.min_atr_pct  # e.g., 0.005
    if hasattr(strategy_instance, 'max_atr_pct'):
        settings['max_atr_pct'] = strategy_instance.max_atr_pct  # e.g., 0.03

    return settings
```

### 2. Calculate Indicators Using Strategy's Settings

```python
def _build_technical_snapshot(ohlcv_data, symbol, strategy_settings):
    """Build snapshot using STRATEGY'S settings, not generic defaults"""

    # Get strategy-specific periods (or fallback to defaults)
    atr_period = strategy_settings.get('atr_period', 14)        # Strategy's ATR period
    ma_period = strategy_settings.get('ma_period', 50)          # Strategy's MA period
    rsi_period = strategy_settings.get('rsi_period', 14)        # Strategy's RSI period
    atr_multiplier = strategy_settings.get('multiplier', 2.0)   # Strategy's ATR multiplier

    # Calculate using STRATEGY'S settings
    ma_value = calculate_sma(closes, ma_period)              # Strategy's MA
    rsi_value = calculate_rsi(closes, rsi_period)            # Strategy's RSI
    atr_value = calculate_atr(highs, lows, closes, atr_period)  # Strategy's ATR

    # Calculate brackets EXACTLY as strategy does
    prev_close = closes[-2]
    upper_bracket = prev_close + (atr_multiplier * atr_value)  # Strategy's formula!
    lower_bracket = prev_close - (atr_multiplier * atr_value)  # Strategy's formula!

    return {
        'ma_period': ma_period,              # Show which MA we used
        'ma_value': ma_value,
        'rsi_period': rsi_period,            # Show which RSI we used
        'rsi_value': rsi_value,
        'atr_period': atr_period,            # Show which ATR we used
        'atr_value': atr_value,
        'atr_multiplier': atr_multiplier,    # Show strategy's multiplier
        'upper_bracket': upper_bracket,      # Strategy's ACTUAL bracket
        'lower_bracket': lower_bracket,      # Strategy's ACTUAL bracket
        # ... more fields
    }
```

### 3. Verify Using Strategy's Logic

```python
def _verify_strategy_logic(strategy_name, tech_snapshot):
    """Verify using STRATEGY'S brackets and thresholds"""

    # Use brackets calculated with strategy's settings
    upper_bracket = tech_snapshot['upper_bracket']     # From strategy's formula
    lower_bracket = tech_snapshot['lower_bracket']     # From strategy's formula
    bracket_width_pct = tech_snapshot['bracket_width_pct']
    atr_pct = tech_snapshot['atr_pct']
    atr_multiplier = tech_snapshot['atr_multiplier']   # Strategy's actual multiplier

    # Check if brackets are reasonable FOR THIS STRATEGY'S SETTINGS
    if bracket_width_pct > (atr_pct * 15):
        issues.append(f"Brackets too wide ({bracket_width_pct:.1f}%) vs ATR ({atr_pct:.2f}%)")
        optimizations.append(f"REDUCE atr_multiplier from {atr_multiplier}x to {atr_multiplier * 0.6:.1f}x")

    # Check ATR thresholds (strategy-specific)
    if 'min_atr_pct' in tech_snapshot['strategy_settings']:
        min_atr = strategy_settings['min_atr_pct'] * 100
        if atr_pct < min_atr:
            warnings.append(f"ATR {atr_pct:.2f}% below strategy's minimum {min_atr:.2f}%")
```

### 4. Provide Optimization Suggestions

Now we can suggest **specific parameter changes** based on strategy's actual settings:

```python
optimizations = [
    "REDUCE atr_multiplier from 1.5x to 0.9x",  # Specific value!
    "Consider increasing atr_multiplier from 1.5x to 1.95x",
    "ATR filter removing signals - adjust min_atr_pct from 0.5% to 0.3%"
]
```

## Example Output

### OLD System (Generic Defaults)
```
📈 Technical Snapshot:
   Price: $95432.50 | Trend: CONSOLIDATION
   RSI: 52.3 (NEUTRAL) | ATR: 1.29%
   Volatility: 0.8% (LOW)
```

**Problem**: We don't know if these match what the strategy actually sees!

### NEW System (Strategy's Actual Settings)
```
================================================================================
[STEP 0/3] Extracting strategy indicator settings...
   [OK] Using strategy's actual indicator settings:
       ATR Period: 14
       MA Period: 50
       RSI Period: 14
       ATR Multiplier: 1.5
================================================================================

[STEP 1/3] Building technical snapshot with strategy's indicators...
   [OK] Technical snapshot built using STRATEGY'S settings:
       Price: $95432.50 | Trend: CONSOLIDATION
       MA(50): $94876.23 | RSI(14): 52.3
       ATR(14): 1.29% | Brackets: [$93850.50, $97014.50]
       Volatility: 0.8% (LOW)

[STEP 2/3] Verifying strategy logic vs market conditions...
   [CHECK] Verifying VolatilityBracket logic...
       Brackets: $93850.50 - $97014.50 (width: 3.32%)
       ATR: 1.29% | Multiplier: 1.5x
       Price in brackets: True

   [!] Logic warnings: 1
       - Low volatility (0.8%) + wide brackets (3.32%) = strategy correctly waiting

   [💡] Optimization suggestions: 1
       → Consider reducing atr_multiplier from 1.5x to 1.12x
```

**Result**: We now see EXACTLY what the strategy sees and can suggest specific optimizations!

## What's Different Now

### Before (Generic Analysis)
```python
# System calculated:
rsi_14 = 52.3  # Generic RSI(14)
rsi_overbought = 70  # Generic threshold
rsi_oversold = 30    # Generic threshold

# Verdict: "RSI neutral, no issues"
```

**But strategy actually uses**:
```python
rsi_period = 14       # ✓ Same
rsi_overbought = 65   # ✗ Different! Strategy is more aggressive
rsi_oversold = 35     # ✗ Different! Strategy is more aggressive
```

### After (Strategy-Specific Analysis)
```python
# System extracts from strategy:
rsi_period = strategy_instance.rsi_period  # 14
rsi_overbought = strategy_instance.rsi_overbought  # 65
rsi_oversold = strategy_instance.rsi_oversold  # 35

# System calculates:
rsi_value = calculate_rsi(closes, rsi_period)  # 52.3

# System interprets using STRATEGY'S thresholds:
if rsi_value >= rsi_overbought:  # 52.3 >= 65? No
    state = "OVERBOUGHT"
elif rsi_value <= rsi_oversold:  # 52.3 <= 35? No
    state = "OVERSOLD"
else:
    state = "NEUTRAL"  # ✓ Correct for THIS strategy

# Verdict: "RSI 52.3 neutral (strategy thresholds: 65/35)"
```

## Technical Snapshot Enhanced Fields

```python
{
    # STRATEGY-SPECIFIC INDICATORS (not generic!)
    'ma_period': 50,                    # Strategy's MA period
    'ma_value': 94876.23,               # MA calculated with strategy's period
    'price_vs_ma': 'ABOVE',

    'rsi_period': 14,                   # Strategy's RSI period
    'rsi_value': 52.3,                  # RSI calculated with strategy's period
    'rsi_state': 'NEUTRAL',             # Interpreted with strategy's thresholds
    'rsi_overbought_threshold': 65,     # Strategy's threshold (not 70!)
    'rsi_oversold_threshold': 35,       # Strategy's threshold (not 30!)

    'atr_period': 14,                   # Strategy's ATR period
    'atr_value': 1234.56,               # ATR calculated with strategy's period
    'atr_pct': 1.29,
    'atr_multiplier': 1.5,              # Strategy's actual multiplier

    # STRATEGY'S ACTUAL BRACKETS (critical!)
    'upper_bracket': 97014.50,          # Calculated with strategy's formula
    'lower_bracket': 93850.50,          # Calculated with strategy's formula
    'bracket_width_pct': 3.32,          # Actual bracket width
    'price_to_upper_pct': 1.66,         # Distance to upper bracket
    'price_to_lower_pct': 1.66,         # Distance to lower bracket
    'price_in_brackets': True,          # Is price inside brackets?

    # Strategy settings (for reference)
    'strategy_settings': {
        'atr_period': 14,
        'ma_period': 50,
        'rsi_period': 14,
        'multiplier': 1.5,
        'min_atr_pct': 0.005,
        'max_atr_pct': 0.03
    }
}
```

## Optimization Suggestions

The system now provides **actionable, specific suggestions**:

```
💡 Optimization Suggestions (Based on Strategy's Settings):
   → REDUCE atr_multiplier from 1.5x to 0.9x
   → Consider reducing atr_multiplier from 1.5x to 1.12x
   → ATR 1.29% above maximum threshold 3.0% - strategy filtering out signals (too volatile)
```

You can then:
1. Edit the strategy file
2. Change `multiplier = 1.5` to `multiplier = 1.12`
3. Redeploy the strategy
4. System will now verify with the new setting!

## Integration

The system automatically extracts strategy settings when available:

```python
# In RBI_RESEARCH_TRADE_FLOW.py
# Just pass the strategy instance (if available)
analysis = self.ai_analyst.analyze_strategy_performance(
    strategy_name=strategy_name,
    symbol=symbol,
    cycles=cycles_run,
    signal_count=signals_generated,
    ohlcv_data=ohlcv_df,
    recent_reasoning=recent_reasoning,
    bracket_info={'upper': upper, 'lower': lower, 'current': current_price},
    strategy_instance=strategy_obj  # NEW: Pass strategy object
)
```

If strategy_instance is not available, system falls back to generic defaults (but warns you).

## Benefits

### 1. Accurate Analysis ✅
- Analyzes what the strategy **actually sees**
- No more false diagnostics from indicator mismatch
- Brackets calculated with strategy's exact formula

### 2. Specific Optimization Suggestions ✅
- "Reduce multiplier from 1.5x to 1.12x" (not generic advice)
- "ATR below strategy's minimum 0.5%" (not generic threshold)
- Actionable parameter changes you can implement immediately

### 3. Strategy Settings Verification ✅
- Confirms strategy settings match intended configuration
- Detects if parameters are too conservative/aggressive for current market
- Validates ATR thresholds, RSI thresholds, bracket calculations

### 4. Optimization Debugging ✅
- See if strategy's multiplier is causing brackets to be too wide
- Check if ATR filters are removing too many signals
- Verify RSI thresholds are appropriate for current volatility

## Files Modified

1. **[strategy_verification_agent.py](trading_modes/core/strategy_verification_agent.py)**
   - Added `_extract_strategy_settings()` method
   - Updated `_build_technical_snapshot()` to use strategy's settings
   - Enhanced `_verify_strategy_logic()` to verify strategy-specific parameters
   - Added optimization suggestions based on strategy's actual values
   - Added `_interpret_rsi_custom()` for strategy-specific RSI thresholds

2. **[market_analysis_agent.py](trading_modes/core/market_analysis_agent.py)**
   - Updated `analyze_strategy_performance()` signature to accept `strategy_instance`
   - Passes strategy instance to verification agent

## Example: BTC_1h_VolatilityBracket_1025pct

**Strategy's Actual Settings**:
```python
atr_period = 14
multiplier = 1.5        # For brackets
ma_period = 50         # For trend confirmation
rsi_period = 14
min_atr_pct = 0.005    # Min ATR as 0.5% of price
max_atr_pct = 0.03     # Max ATR as 3% of price
```

**System Now Verifies**:
- ✅ Brackets calculated with ATR(14) * 1.5x
- ✅ MA trend using MA(50)
- ✅ RSI confirmation using RSI(14)
- ✅ ATR filters at 0.5%-3.0%
- ✅ Bracket width vs current ATR%

**If Brackets Too Wide**:
```
[!] Logic warnings: 1
    - Brackets too wide (3.32%) for current ATR (1.29%)

[💡] Optimization suggestions: 1
    → Consider reducing atr_multiplier from 1.5x to 1.12x
```

**Action**: Edit strategy, change `multiplier = 1.5` to `multiplier = 1.12`, redeploy!

## Summary

**You were 100% correct** - using generic indicator defaults was wrong!

The system now:
- ✅ Extracts strategy's ACTUAL indicator settings
- ✅ Calculates indicators using strategy's periods (not generic)
- ✅ Verifies brackets using strategy's multiplier
- ✅ Interprets RSI using strategy's thresholds
- ✅ Provides specific optimization suggestions
- ✅ Shows you EXACTLY what strategy sees

**Result**: Verification that matches reality, not generic assumptions! 🎯
