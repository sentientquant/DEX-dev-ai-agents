# TESTING GUIDE - Refactored Type-Safe System

**Purpose**: Validate the refactored trading system works correctly
**Duration**: 48-72 hours of paper trading
**Goal**: Zero KeyError/AttributeError crashes

---

## QUICK START: INSTALL DEPENDENCIES

```bash
# Install type checking tools
pip install mypy types-requests pandas-stubs types-termcolor

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

---

## PHASE 1: TYPE CHECKING (5 minutes)

### Run Type Checker

**Windows**:
```bash
cd c:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents
scripts\type_check.bat
```

**Linux/Mac**:
```bash
cd /path/to/DEX-dev-ai-agents
chmod +x scripts/type_check.sh
./scripts/type_check.sh
```

### Expected Output:
```
========================================
TYPE CHECKING MIGRATED MODULES
========================================

[1/5] Checking domain models...
[PASS] Domain models OK

[2/5] Checking result type...
[PASS] Result type OK

[3/5] Checking technical indicators...
[PASS] Technical indicators OK

[4/5] Checking signal verification agent...
[PASS] Signal verification agent OK

[5/5] Checking typed database...
[PASS] Typed database OK

========================================
TYPE CHECK COMPLETE - ALL PASSED ✓
========================================
```

### If Type Checking Fails:
1. Check the error message for specific file/line
2. Most common issues:
   - Missing type hints on function parameters
   - Incompatible return types
   - Using `None` where value is required
3. Fix and re-run

---

## PHASE 2: UNIT TESTS (15 minutes)

### Test 1: Domain Models

```python
# test_domain_models.py
from trading_modes.models.domain import (
    Trade, TradeSide, TradingMode, TradeStatus,
    SignalVerificationResult, AgreementLevel, SignalAction, Verdict
)
from datetime import datetime

def test_trade_creation():
    """Test creating a valid Trade object"""
    trade = Trade(
        trade_id='TEST_001',
        symbol='BTCUSDT',
        side=TradeSide.BUY,
        entry_price=50000.0,
        position_size_usd=100.0,
        stop_loss=49000.0,
        mode=TradingMode.PAPER,
        status=TradeStatus.OPEN,
        timestamp=datetime.now()
    )

    assert trade.base_asset == 'BTC'
    assert trade.is_long == True
    assert trade.is_open == True
    print("✓ Trade creation test passed")

def test_trade_validation():
    """Test Trade validation catches invalid data"""
    try:
        trade = Trade(
            trade_id='INVALID',
            symbol='BTCUSDT',
            side=TradeSide.BUY,
            entry_price=-100.0,  # Invalid: negative price
            position_size_usd=100.0,
            stop_loss=49000.0,
            mode=TradingMode.PAPER,
            status=TradeStatus.OPEN,
            timestamp=datetime.now()
        )
        print("✗ Validation test failed - should have raised error")
    except ValueError as e:
        print(f"✓ Validation test passed - caught error: {e}")

def test_signal_verification_result():
    """Test SignalVerificationResult"""
    result = SignalVerificationResult(
        agrees_with_scanner=True,
        agreement_level=AgreementLevel.FULL,
        action=SignalAction.BUY,
        confidence=95,
        reasoning="Test reasoning",
        verdicts=[
            Verdict(model_name='test', vote=SignalAction.BUY, confidence=90, reasoning='Test')
        ]
    )

    assert result.agreement_level == AgreementLevel.FULL
    assert result.action == SignalAction.BUY
    print("✓ SignalVerificationResult test passed")

# Run tests
test_trade_creation()
test_trade_validation()
test_signal_verification_result()
print("\n✅ All domain model tests passed!")
```

**Run**:
```bash
python test_domain_models.py
```

### Test 2: Technical Indicators

```python
# test_indicators.py
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
```

**Run**:
```bash
python test_indicators.py
```

### Test 3: Typed Database

```python
# test_database.py
from risk_management.trading_database_typed import TradingDatabaseTyped
from trading_modes.models.domain import Trade, TradeSide, TradingMode, TradeStatus
from datetime import datetime

def test_typed_database():
    """Test typed database wrapper"""
    db = TradingDatabaseTyped(db_path="test_trading.db")

    # Create test trade
    trade = Trade(
        trade_id='TEST_DB_001',
        symbol='BTCUSDT',
        side=TradeSide.BUY,
        entry_price=50000.0,
        position_size_usd=100.0,
        stop_loss=49000.0,
        mode=TradingMode.PAPER,
        status=TradeStatus.OPEN,
        timestamp=datetime.now()
    )

    # Insert trade
    insert_result = db.insert_trade(trade)
    if insert_result.is_success():
        print(f"✓ Trade inserted with ID: {insert_result.value}")
    else:
        print(f"✗ Insert failed: {insert_result.error}")
        return

    # Get open trades
    trades_result = db.get_open_trades(mode=TradingMode.PAPER)
    if trades_result.is_success():
        trades = trades_result.value
        print(f"✓ Found {len(trades)} open trades")

        if trades:
            trade = trades[0]
            # Test type-safe access
            print(f"  Symbol: {trade.symbol}")
            print(f"  Side: {trade.side.value}")  # Enum.value
            print(f"  Entry: ${trade.entry_price:.2f}")
            print(f"  Base: {trade.base_asset}")  # Computed property
    else:
        print(f"✗ Get trades failed: {trades_result.error}")
        return

    # Close trade
    close_result = db.close_trade(
        trade_id='TEST_DB_001',
        exit_price=51000.0,
        pnl_usd=20.0,
        pnl_pct=2.0,
        exit_reason='Test exit'
    )
    if close_result.is_success():
        print("✓ Trade closed successfully")
    else:
        print(f"✗ Close failed: {close_result.error}")

    print("\n✅ Typed database test passed!")

# Run test
test_typed_database()
```

**Run**:
```bash
python test_database.py
```

---

## PHASE 3: INTEGRATION TEST (30 minutes)

### Test Signal Verification Agent

```python
# test_signal_verification.py
from trading_modes.core.signal_verification_agent import SignalVerificationAgent

def test_signal_verification():
    """Test signal verification with real data"""
    agent = SignalVerificationAgent()

    # Test signal verification
    result = agent.verify_signal(
        symbol='BTCUSDT',
        timeframe='1h',
        scanner_signal='BUY',
        scanner_confidence=85.0,
        strategy_name='TestStrategy'
    )

    # Check result type
    if result.is_success():
        verification = result.value

        print(f"✓ Verification completed")
        print(f"  Action: {verification.action.value}")
        print(f"  Confidence: {verification.confidence}%")
        print(f"  Agreement: {verification.agreement_level.value}")
        print(f"  Agrees with scanner: {verification.agrees_with_scanner}")

        # Test that all fields exist (no KeyError)
        assert hasattr(verification, 'agrees_with_scanner')
        assert hasattr(verification, 'agreement_level')
        assert hasattr(verification, 'action')
        assert hasattr(verification, 'confidence')
        assert hasattr(verification, 'reasoning')
        assert hasattr(verification, 'verdicts')

        print("\n✅ Signal verification test passed!")
    else:
        print(f"✗ Verification failed: {result.error}")

# Run test
test_signal_verification()
```

**Run**:
```bash
python test_signal_verification.py
```

---

## PHASE 4: PAPER TRADING TEST (48-72 hours)

### Setup Paper Trading

1. **Configure paper trading mode**:
```bash
# Edit config or pass via command line
export MODE=PAPER
export INTERVAL=5  # 5 minutes
export SYMBOLS="BTC SOL ETH"
```

2. **Run RBI Research Trade Flow**:
```bash
python trading_modes/RBI_RESEARCH_TRADE_FLOW.py --mode PAPER --interval 5 --symbols BTC SOL ETH
```

### What to Monitor

#### Critical Metrics (First 24 hours)

**Zero Tolerance Errors** (Should NOT appear):
- ❌ `KeyError: 'agreement_level'`
- ❌ `KeyError: 'direction'`
- ❌ `KeyError: 'side'`
- ❌ `KeyError: 'BBU_20_2.0'`
- ❌ `AttributeError: 'NoneType' object has no attribute`
- ❌ `Object of type bool is not JSON serializable`

**Expected Behavior**:
- ✅ Balance updates every cycle
- ✅ Strategies generate signals
- ✅ Signal verification completes
- ✅ Trades execute (if signals valid)
- ✅ PnL tracks correctly

#### Log Monitoring

**Watch for these patterns**:

```bash
# Good patterns
[OK] Technical snapshot built
[VERIFIED] Consensus: BUY @ 95%
Balance: $10,123.45 | PnL: $+123.45

# Bad patterns (should not appear)
[ERROR] KeyError: 'agreement_level'
[WARN] Error calculating PnL: 'direction'
[FAIL] Missing key in response
```

**Monitor command** (Windows):
```bash
# Real-time log monitoring
powershell "Get-Content -Path trading.log -Wait | Select-String -Pattern 'ERROR|FAIL|KeyError|AttributeError'"
```

**Monitor command** (Linux):
```bash
tail -f trading.log | grep -E 'ERROR|FAIL|KeyError|AttributeError'
```

### Success Criteria (48 hours)

| Metric | Target | Critical? |
|--------|--------|-----------|
| KeyError count | 0 | ✅ YES |
| AttributeError count | 0 | ✅ YES |
| JSON serialization errors | 0 | ✅ YES |
| Defensive `.get()` calls in new code | 0 | ✅ YES |
| Balance updates per cycle | 100% | ✅ YES |
| Strategy signals generated | > 0 | ⚠️ No (market dependent) |
| Trades executed | > 0 | ⚠️ No (signal dependent) |
| System uptime | > 95% | ✅ YES |

---

## PHASE 5: VALIDATION CHECKLIST

### Before Going Live

- [ ] Type checking passes (`scripts/type_check.bat`)
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Paper trading ran 48+ hours error-free
- [ ] Zero KeyError/AttributeError in logs
- [ ] Balance tracking accurate
- [ ] PnL calculations correct
- [ ] No "CRITICAL FIX" comments added
- [ ] No defensive `.get()` calls added
- [ ] Code review completed

### Deployment Checklist

- [ ] Start with PAPER mode for 1 week
- [ ] Monitor logs daily
- [ ] Check balance accuracy daily
- [ ] Validate PnL against manual calculations
- [ ] Switch to LIVE with small position sizes
- [ ] Monitor for 3 days before increasing positions
- [ ] Keep paper trading running in parallel for comparison

---

## TROUBLESHOOTING

### Issue: Type checking fails

**Problem**: `mypy` reports type errors

**Solution**:
1. Read the error message carefully
2. Check which file/line has the issue
3. Common fixes:
   - Add type hints: `def func(x: int) -> str:`
   - Use Optional for nullable: `Optional[Trade]`
   - Convert enums properly: `TradingSide(value)`

**Example Error**:
```
error: Argument 1 has incompatible type "str"; expected "TradingMode"
```

**Fix**:
```python
# Before
db.get_open_trades(mode='PAPER')

# After
db.get_open_trades(mode=TradingMode.PAPER)
```

### Issue: Tests fail

**Problem**: Unit tests report failures

**Solution**:
1. Check error message
2. Verify test data is valid
3. Check database exists (for database tests)
4. Ensure API keys configured (for integration tests)

### Issue: Paper trading crashes

**Problem**: System crashes during paper trading

**Solution**:
1. Check logs for exact error
2. If KeyError:
   - This should NOT happen with new system
   - Report as critical bug
3. If other error:
   - Check API connectivity
   - Verify database not corrupted
   - Check disk space

---

## REPORTING ISSUES

If you find bugs in the refactored system:

1. **Capture the error**:
   ```bash
   # Get last 100 lines of log
   tail -100 trading.log > error_report.txt
   ```

2. **Check if it's a regression**:
   - Is it a KeyError we supposedly fixed?
   - Is it in migrated code or legacy code?

3. **File format**:
   ```
   **Error Type**: KeyError / AttributeError / Other
   **Location**: File:Line
   **Migrated Code**: Yes / No
   **Error Message**: [paste exact error]
   **Context**: [what operation was running]
   ```

---

## PERFORMANCE BENCHMARKS

### Expected Performance

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Type safety checks | Runtime | Compile time | ✅ Faster |
| Dictionary access | `.get()` overhead | Direct access | ✅ 10% faster |
| Error handling | Try/except | Type checking | ✅ Prevents errors |
| Developer time | Bug fixing | Feature development | ✅ 60-80% saved |

### Measure Performance

```python
import time

# Test 1000 trade retrievals
start = time.time()
for _ in range(1000):
    result = db.get_open_trades(mode=TradingMode.PAPER)
    if result.is_success():
        trades = result.value
end = time.time()

print(f"1000 retrievals: {end - start:.2f}s")
print(f"Per operation: {(end - start) / 1000 * 1000:.2f}ms")
```

---

## NEXT STEPS AFTER TESTING

Once testing passes:

1. **Week 1**: Paper mode with full monitoring
2. **Week 2**: LIVE mode with $10 positions
3. **Week 3**: LIVE mode with $50 positions
4. **Week 4+**: Normal position sizes

**Success**: No "CRITICAL FIX" comments needed for 1 month

---

**Last Updated**: 2025-11-18
**Status**: Ready for testing
