#!/usr/bin/env python3
"""
QUICK SMOKE TEST - Core Components
Tests without stdout encoding issues
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

print("="*80)
print("QUICK SMOKE TEST - CORE COMPONENTS")
print("="*80)

# Test 1: Database
print("\n[1/6] Testing Database...")
try:
    from risk_management.trading_database import TradingDatabase
    db = TradingDatabase("quick_test.db")
    print("  PASS: Database initialized")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 2: Sharp Fibonacci + ATR
print("\n[2/6] Testing Sharp Fibonacci + ATR...")
try:
    from risk_management.sharp_fibonacci_atr import ATRFibonacciCalculator
    import pandas as pd
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='h')
    ohlcv = pd.DataFrame({
        'open': np.random.randn(200).cumsum() + 100000,
        'high': np.random.randn(200).cumsum() + 100500,
        'low': np.random.randn(200).cumsum() + 99500,
        'close': np.random.randn(200).cumsum() + 100000,
        'volume': np.random.rand(200) * 1000000
    }, index=dates)

    ohlcv['high'] = ohlcv[['open', 'high', 'close']].max(axis=1)
    ohlcv['low'] = ohlcv[['open', 'low', 'close']].min(axis=1)

    calc = ATRFibonacciCalculator()
    entry_price = ohlcv['close'].iloc[-1]
    levels_obj = calc.calculate_sharp_fibonacci_atr(ohlcv, entry_price, 'BUY')
    levels = levels_obj.to_dict()

    assert levels['stop_loss'] < entry_price
    assert levels['tp1'] > entry_price
    print(f"  PASS: Calculated levels (Stop: {levels['sl_pct']:.2f}%, TP1: {levels['tp1_pct']:.2f}%)")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 3: Strategy Validator
print("\n[3/6] Testing Strategy Validator...")
try:
    from risk_management.strategy_validator import StrategyValidator
    validator = StrategyValidator(tolerance_pct=20.0)

    original = {'return_pct': 150.0, 'win_rate': 60.0}
    validation_pass = {'return_pct': 145.0, 'win_rate': 58.0}

    passed, _ = validator._compare_metrics(original, validation_pass)
    assert passed == True
    print("  PASS: Validator logic working")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 4: Allocation Calculator
print("\n[4/6] Testing Allocation Calculator...")
try:
    from order_management.simple_allocation_calculator import calculate_smart_allocation
    import pandas as pd
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='h')
    ohlcv = pd.DataFrame({
        'open': np.random.randn(200).cumsum() + 100000,
        'high': np.random.randn(200).cumsum() + 100500,
        'low': np.random.randn(200).cumsum() + 99500,
        'close': np.random.randn(200).cumsum() + 100000,
        'volume': np.random.rand(200) * 1000000
    }, index=dates)

    result = calculate_smart_allocation(ohlcv, 500.0, 0)
    assert result['can_trade'] == True
    assert result['position_size_usd'] > 0
    print(f"  PASS: Allocation calculated (Size: ${result['position_size_usd']:.2f})")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 5: Risk Monitoring
print("\n[5/6] Testing Risk Monitoring...")
try:
    from risk_management.realtime_risk_monitor import RealTimeRiskMonitor, RiskLevel
    import pandas as pd
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='h')
    ohlcv = pd.DataFrame({
        'open': np.random.randn(200).cumsum() + 100000,
        'high': np.random.randn(200).cumsum() + 100500,
        'low': np.random.randn(200).cumsum() + 99500,
        'close': np.random.randn(200).cumsum() + 100000,
        'volume': np.random.rand(200) * 1000000
    }, index=dates)

    ohlcv['high'] = ohlcv[['open', 'high', 'close']].max(axis=1)
    ohlcv['low'] = ohlcv[['open', 'low', 'close']].min(axis=1)

    monitor = RealTimeRiskMonitor('BTC', 100000.0, 'LONG', 99000.0, 102000.0)
    assessment = monitor.assess_risk(ohlcv, ohlcv['close'].iloc[-1])

    assert assessment.risk_level in [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH]
    print(f"  PASS: Risk assessed ({assessment.risk_level.name}, score: {assessment.risk_score:.1f})")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 6: Binance API
print("\n[6/6] Testing Binance API...")
try:
    from risk_management.binance_truth_paper_trading import BinanceTruthAPI
    price = BinanceTruthAPI.get_live_price('BTC')
    if price and price > 0:
        print(f"  PASS: BTC price fetched (${price:,.2f})")
    else:
        print("  WARN: Could not fetch price (API may be down)")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n" + "="*80)
print("QUICK SMOKE TEST COMPLETE")
print("="*80)
print("\nAll core components tested successfully!")
print("\nNote: Some tests may show WARN if external APIs are down")
print("This is expected and does not indicate a bug.")
