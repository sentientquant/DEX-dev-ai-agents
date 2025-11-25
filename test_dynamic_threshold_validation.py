#!/usr/bin/env python3
"""
DYNAMIC THRESHOLD VALIDATION - Compare Pine Script vs Python Implementation

Simulates the EXACT scenario from TradingView chart:
- Entry: $86,137.19
- Current: $86,963.27
- Profit: 0.96%
- Regime: FLAT
- ATR: 0.83%

Validates that dynamic threshold calculation matches between:
1. Pine Script (TradingView)
2. Python PAPER mode
"""

import sys
from pathlib import Path
from termcolor import cprint

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def calculate_dynamic_threshold(regime, atr_pct):
    """
    Calculate dynamic activation threshold
    MUST match Pine Script logic exactly
    """
    # Regime-adaptive base thresholds
    regime_thresholds = {
        'TRENDING_UP': 1.5,
        'TRENDING_DOWN': 2.0,
        'CHOPPY': 1.0,
        'CRISIS': 2.5,
        'FLAT': 1.5
    }

    base_threshold = regime_thresholds.get(regime, 1.5)

    # ATR adjustment: Higher volatility = higher threshold
    atr_adjustment = (atr_pct / 0.015) * 0.5

    final_threshold = base_threshold + atr_adjustment

    return base_threshold, atr_adjustment, final_threshold

def simulate_chart_scenario():
    """
    Simulate the exact scenario from TradingView chart
    """
    cprint("\n" + "="*80, "cyan")
    cprint("DYNAMIC THRESHOLD VALIDATION - PINE SCRIPT vs PYTHON", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

    # Chart data (from screenshot)
    entry_price = 86137.19
    current_price = 86963.27
    regime = 'FLAT'
    atr_value = 0.83 / 100  # 0.83% ATR

    # Calculate profit
    profit_pct = ((current_price - entry_price) / entry_price) * 100

    cprint("\nCHART DATA (from TradingView screenshot):", "yellow", attrs=['bold'])
    cprint(f"   Entry Price: ${entry_price:,.2f}", "white")
    cprint(f"   Current Price: ${current_price:,.2f}", "white")
    cprint(f"   Profit: {profit_pct:.2f}%", "green")
    cprint(f"   Regime: {regime}", "white")
    cprint(f"   ATR: {atr_value*100:.2f}%", "white")

    # Calculate dynamic threshold
    base_threshold, atr_adjustment, final_threshold = calculate_dynamic_threshold(regime, atr_value)

    cprint("\nDYNAMIC THRESHOLD CALCULATION:", "cyan", attrs=['bold'])
    cprint(f"   Base Threshold (FLAT regime): {base_threshold:.2f}%", "white")
    cprint(f"   ATR Adjustment: ({atr_value:.4f} / 0.015) x 0.5 = +{atr_adjustment:.2f}%", "white")
    cprint(f"   Final Activation Threshold: {final_threshold:.2f}%", "yellow", attrs=['bold'])

    # Check activation status
    cprint("\nTRAILING ACTIVATION STATUS:", "cyan", attrs=['bold'])
    if profit_pct >= final_threshold:
        cprint(f"   [OK] TRAILING ACTIVATED!", "green", attrs=['bold'])
        cprint(f"   Profit {profit_pct:.2f}% >= Threshold {final_threshold:.2f}%", "green")
    else:
        cprint(f"   [WAIT] TRAILING NOT ACTIVATED (waiting for threshold)", "yellow")
        cprint(f"   Profit {profit_pct:.2f}% < Threshold {final_threshold:.2f}%", "yellow")
        cprint(f"   Need: +{final_threshold - profit_pct:.2f}% more profit to activate", "yellow")

    # Compare with Pine Script
    cprint("\nPINE SCRIPT COMPARISON:", "cyan", attrs=['bold'])
    pine_threshold = 1.78  # From chart screenshot info panel
    python_threshold = final_threshold

    cprint(f"   Pine Script Threshold: {pine_threshold:.2f}%", "white")
    cprint(f"   Python Threshold: {python_threshold:.2f}%", "white")

    if abs(pine_threshold - python_threshold) < 0.01:
        cprint(f"   [OK] PERFECT MATCH! Difference: {abs(pine_threshold - python_threshold):.4f}%", "green", attrs=['bold'])
    else:
        cprint(f"   [WARNING] MISMATCH! Difference: {abs(pine_threshold - python_threshold):.2f}%", "red")

    # Test different regimes
    cprint("\nTHRESHOLD COMPARISON ACROSS ALL REGIMES:", "cyan", attrs=['bold'])
    cprint(f"   (with current ATR: {atr_value*100:.2f}%)\n", "white")

    regimes = ['TRENDING_UP', 'TRENDING_DOWN', 'CHOPPY', 'CRISIS', 'FLAT']
    for test_regime in regimes:
        base, adj, final = calculate_dynamic_threshold(test_regime, atr_value)
        status = "[OK] ACTIVATED" if profit_pct >= final else "[WAIT] WAITING"
        color = "green" if profit_pct >= final else "yellow"
        cprint(f"   {test_regime:15s}: {final:.2f}% (base: {base:.1f}% + ATR: {adj:.2f}%) {status}", color)

    # Show what happens with different ATR values in FLAT regime
    cprint("\nATR SENSITIVITY ANALYSIS (FLAT regime):", "cyan", attrs=['bold'])
    test_atrs = [0.005, 0.010, 0.015, 0.020, 0.030, 0.050]
    for test_atr in test_atrs:
        base, adj, final = calculate_dynamic_threshold('FLAT', test_atr)
        status = "[OK] ACTIVATED" if profit_pct >= final else "[WAIT] WAITING"
        color = "green" if profit_pct >= final else "yellow"
        cprint(f"   ATR {test_atr*100:5.2f}%: Threshold {final:.2f}% (base: {base:.1f}% + adj: {adj:.2f}%) {status}", color)

    cprint("\n" + "="*80, "cyan")
    cprint("VALIDATION COMPLETE", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

if __name__ == "__main__":
    simulate_chart_scenario()
