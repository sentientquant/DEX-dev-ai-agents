# test_indicators.py
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from trading_modes.indicators.technical import TechnicalIndicators
import pandas as pd
import numpy as np

def test_bollinger_bands():
    """Test Bollinger Bands calculation"""
    # Create sample price data
    close = pd.Series([100 + i + np.sin(i/10)*5 for i in range(50)])

    bb = TechnicalIndicators.bollinger_bands(close, period=20, std_dev=2.0)

    # Validate keys exist
    assert 'upper' in bb
    assert 'middle' in bb
    assert 'lower' in bb

    # Validate values are reasonable
    assert bb['upper'] > bb['middle'] > bb['lower']

    print(f"✓ Bollinger Bands: Upper={bb['upper']:.2f}, Mid={bb['middle']:.2f}, Lower={bb['lower']:.2f}")

def test_rsi():
    """Test RSI calculation"""
    # Create uptrending data
    close = pd.Series([100 + i*0.5 for i in range(50)])

    rsi = TechnicalIndicators.rsi(close, period=14)

    # RSI should be > 50 for uptrend
    assert 0 <= rsi <= 100
    assert rsi > 50  # Uptrending

    print(f"✓ RSI: {rsi:.2f}")

def test_version_agnostic():
    """Test that indicators don't break on pandas updates"""
    close = pd.Series(np.random.randn(100) + 100)

    # These should all work regardless of pandas_ta version
    bb = TechnicalIndicators.bollinger_bands(close)
    rsi = TechnicalIndicators.rsi(close)
    sma = TechnicalIndicators.sma(close, period=20)
    ema = TechnicalIndicators.ema(close, period=20)

    # All should return float or dict with predictable keys
    assert isinstance(bb, dict)
    assert isinstance(rsi, float)
    assert isinstance(sma, float)
    assert isinstance(ema, float)

    print("✓ Version-agnostic test passed")

# Run tests
test_bollinger_bands()
test_rsi()
test_version_agnostic()
print("\n✅ All indicator tests passed!")
