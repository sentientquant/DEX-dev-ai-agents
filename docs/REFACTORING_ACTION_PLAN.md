# REFACTORING ACTION PLAN
## Stop Fixing Symptoms, Fix the Architecture

**Created**: 2025-11-18
**Status**: PROPOSED - Awaiting Approval
**Estimated Time**: 3-4 weeks
**Expected Bug Reduction**: 60-80%

---

## QUICK START: What to Do Right Now

### Option 1: Full Refactoring (Recommended)
Follow the 5-phase plan below. This is the PERMANENT solution.

### Option 2: Immediate Band-Aid (Quick Fix)
If you need to keep running while planning refactoring:

1. **Pin Library Versions** (5 minutes)
   ```bash
   # Update requirements.txt with exact versions
   pip freeze | grep -E 'pandas_ta|talib' >> requirements.txt
   ```

2. **Add Type Stubs** (15 minutes)
   ```bash
   pip install mypy types-requests
   # Run type checker to find issues
   mypy trading_modes/core/ --ignore-missing-imports
   ```

3. **Standardize Error Returns** (30 minutes)
   Create `trading_modes/core/common.py`:
   ```python
   def error_response(action='NOTHING', confidence=0, reasoning='Error occurred'):
       """Standard error response - use this everywhere"""
       return {
           'action': action,
           'confidence': confidence,
           'reasoning': reasoning,
           'agreement_level': 'error',
           'agrees_with_scanner': False
       }
   ```

---

## PHASE 1: TYPE SAFETY FOUNDATION
**Timeline**: Week 1-2
**Goal**: Eliminate 304 defensive `.get()` calls

### Step 1.1: Create Domain Models (Day 1-2)

**File**: `trading_modes/models/domain.py`

```python
"""
Type-safe domain models for trading system
Replaces untyped dictionaries with validated dataclasses
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS - All valid states enumerated
# ============================================================================

class TradeStatus(Enum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'

class TradeSide(Enum):
    BUY = 'BUY'
    SELL = 'SELL'

class TradingMode(Enum):
    PAPER = 'PAPER'
    LIVE = 'LIVE'

class SignalAction(Enum):
    BUY = 'BUY'
    SELL = 'SELL'
    NOTHING = 'NOTHING'
    WAIT = 'WAIT'

class AgreementLevel(Enum):
    FULL = 'full'
    MAJORITY = 'majority'
    WEAK = 'weak'
    NONE = 'none'
    ERROR = 'error'
    DISABLED = 'disabled'

# ============================================================================
# DOMAIN MODELS - Replace dictionaries
# ============================================================================

@dataclass
class Trade:
    """
    Represents a single trade (paper or live)

    Replaces untyped dict with 20+ fields
    Database column names match field names EXACTLY
    """
    trade_id: str
    symbol: str  # Format: "BTCUSDT" (never "BTC", never "BTC-USDT")
    side: TradeSide
    entry_price: float
    position_size_usd: float
    stop_loss: float
    mode: TradingMode
    status: TradeStatus
    timestamp: datetime

    # Optional fields
    tp1_price: Optional[float] = None
    tp2_price: Optional[float] = None
    tp3_price: Optional[float] = None
    tp1_pct: Optional[float] = None
    tp2_pct: Optional[float] = None
    tp3_pct: Optional[float] = None
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl_usd: Optional[float] = None
    pnl_pct: Optional[float] = None
    exit_reason: Optional[str] = None
    strategy_name: Optional[str] = None
    confidence: Optional[int] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        """Validate data on creation"""
        if self.entry_price <= 0:
            raise ValueError(f"Entry price must be positive, got {self.entry_price}")
        if self.position_size_usd <= 0:
            raise ValueError(f"Position size must be positive, got {self.position_size_usd}")
        if self.confidence is not None and not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")

    @property
    def base_asset(self) -> str:
        """Extract base asset from symbol: 'BTCUSDT' -> 'BTC'"""
        return self.symbol.replace('USDT', '').replace('PERP', '')

    @property
    def is_open(self) -> bool:
        """Check if trade is currently open"""
        return self.status == TradeStatus.OPEN

    @classmethod
    def from_db_row(cls, row: dict) -> 'Trade':
        """
        Convert database row to Trade object
        SINGLE CONVERSION POINT - no more scattered conversions
        """
        return cls(
            trade_id=row['trade_id'],
            symbol=row['symbol'],
            side=TradeSide(row['side']),
            entry_price=float(row['entry_price']),
            position_size_usd=float(row['position_size_usd']),
            stop_loss=float(row['stop_loss']),
            mode=TradingMode(row['mode']),
            status=TradeStatus(row['status']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            tp1_price=float(row['tp1_price']) if row.get('tp1_price') else None,
            tp2_price=float(row['tp2_price']) if row.get('tp2_price') else None,
            tp3_price=float(row['tp3_price']) if row.get('tp3_price') else None,
            tp1_pct=float(row['tp1_pct']) if row.get('tp1_pct') else None,
            tp2_pct=float(row['tp2_pct']) if row.get('tp2_pct') else None,
            tp3_pct=float(row['tp3_pct']) if row.get('tp3_pct') else None,
            exit_price=float(row['exit_price']) if row.get('exit_price') else None,
            exit_timestamp=datetime.fromisoformat(row['exit_timestamp']) if row.get('exit_timestamp') else None,
            pnl_usd=float(row['pnl_usd']) if row.get('pnl_usd') else None,
            pnl_pct=float(row['pnl_pct']) if row.get('pnl_pct') else None,
            exit_reason=row.get('exit_reason'),
            strategy_name=row.get('strategy_name'),
            confidence=int(row['confidence']) if row.get('confidence') else None,
            metadata=row.get('metadata')
        )


@dataclass
class Verdict:
    """Single AI model verdict on trading signal"""
    model_name: str
    vote: SignalAction
    confidence: int
    reasoning: str

    def __post_init__(self):
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")


@dataclass
class SignalVerificationResult:
    """
    Result from AI swarm signal verification

    Replaces the untyped dict that caused KeyError bugs
    ALL FIELDS ALWAYS PRESENT - no more .get() needed
    """
    agrees_with_scanner: bool
    agreement_level: AgreementLevel
    action: SignalAction
    confidence: int
    reasoning: str
    verdicts: List[Verdict]

    def __post_init__(self):
        """Validate on creation"""
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")
        if not self.verdicts:
            raise ValueError("Verdicts list cannot be empty")

    @classmethod
    def error(cls, error_message: str) -> 'SignalVerificationResult':
        """Factory method for error state - ALWAYS has all required fields"""
        return cls(
            agrees_with_scanner=False,
            agreement_level=AgreementLevel.ERROR,
            action=SignalAction.WAIT,
            confidence=0,
            reasoning=f"Verification failed: {error_message}",
            verdicts=[]
        )


@dataclass
class StrategySignal:
    """Signal generated by a trading strategy"""
    action: SignalAction
    confidence: int
    reasoning: str
    strategy_name: str
    symbol: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")


@dataclass
class AccountStatus:
    """Real-time account status with balance tracking"""
    current_balance: float
    free_usdt: float
    allocated_usdt: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    open_positions: int
    mode: TradingMode

    @property
    def allocation_pct(self) -> float:
        """Percentage of capital allocated to trades"""
        if self.current_balance == 0:
            return 0.0
        return (self.allocated_usdt / self.current_balance) * 100
```

### Step 1.2: Create Result Type (Day 2)

**File**: `trading_modes/models/result.py`

```python
"""
Result type for consistent error handling
Eliminates inconsistent error response shapes
"""

from typing import TypeVar, Generic, Union
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Success(Generic[T]):
    """Successful operation with typed value"""
    value: T

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False


@dataclass
class Failure:
    """Failed operation with error details"""
    error: str
    error_type: str = 'unknown'
    details: dict = None

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True


# Type alias for readability
Result = Union[Success[T], Failure]


# Helper functions
def success(value: T) -> Success[T]:
    """Create success result"""
    return Success(value)


def failure(error: str, error_type: str = 'unknown', **details) -> Failure:
    """Create failure result"""
    return Failure(error=error, error_type=error_type, details=details or None)
```

### Step 1.3: Migrate Core Module (Day 3-5)

**File**: `trading_modes/core/signal_verification_agent.py` (REFACTORED)

```python
from trading_modes.models.domain import (
    SignalVerificationResult,
    Verdict,
    SignalAction,
    AgreementLevel
)
from trading_modes.models.result import Result, success, failure

def verify_signal(
    symbol: str,
    scanner_action: str,
    scanner_confidence: int,
    ohlcv: pd.DataFrame
) -> Result[SignalVerificationResult]:
    """
    Verify signal with 5 AI models

    Returns:
        Success[SignalVerificationResult] - All fields guaranteed present
        Failure - Error details
    """
    try:
        # Calculate indicators (abstraction layer to be added in Phase 3)
        bb = TechnicalIndicators.bollinger_bands(ohlcv['close'], period=20, std_dev=2.0)

        # Get verdicts from all models
        verdicts: List[Verdict] = []
        for provider in ['anthropic', 'openai', 'deepseek', 'gemini', 'groq']:
            try:
                model = model_factory.get_model(provider)
                response = model.generate_response(...)

                # Parse verdict
                verdict = Verdict(
                    model_name=provider,
                    vote=SignalAction.BUY,  # Parsed from response
                    confidence=85,           # Parsed from response
                    reasoning="Model agrees"
                )
                verdicts.append(verdict)

            except Exception as model_error:
                # Add error verdict
                verdicts.append(Verdict(
                    model_name=provider,
                    vote=SignalAction.WAIT,
                    confidence=0,
                    reasoning=f"Error: {model_error}"
                ))

        # Calculate agreement
        agreement_level = self._calculate_agreement(verdicts)

        # Create typed result - IMPOSSIBLE to forget a field
        result = SignalVerificationResult(
            agrees_with_scanner=agreement_level in [AgreementLevel.FULL, AgreementLevel.MAJORITY],
            agreement_level=agreement_level,
            action=SignalAction(scanner_action),
            confidence=scanner_confidence,
            reasoning="AI swarm analysis complete",
            verdicts=verdicts
        )

        return success(result)

    except Exception as e:
        # Error path uses factory method - ALWAYS has all required fields
        return failure(error=str(e), error_type=type(e).__name__)
```

**Caller Code** (CLEAN):

```python
# Old way (FRAGILE):
result = verify_signal(...)
agreement = result.get('agreement_level', 'unknown')  # Defensive
action = result.get('action', 'NOTHING')              # Defensive
confidence = result.get('confidence', 0)              # Defensive

# New way (ROBUST):
result = verify_signal(...)

if result.is_success():
    data = result.value
    print(f"Agreement: {data.agreement_level.value}")  # ✅ IDE autocomplete
    print(f"Action: {data.action.value}")              # ✅ Always exists
    print(f"Confidence: {data.confidence}")            # ✅ Validated 0-100
else:
    print(f"Verification failed: {result.error}")      # ✅ Always exists
```

### Step 1.4: Add Type Checking to CI (Day 5)

**File**: `.github/workflows/type-check.yml` (if using GitHub Actions)

```yaml
name: Type Check

on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install mypy
      - run: mypy trading_modes/core/ --strict --ignore-missing-imports
```

**OR Local Pre-commit Hook**:

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running type check..."
mypy trading_modes/core/ --strict --ignore-missing-imports
if [ $? -ne 0 ]; then
    echo "Type check failed. Fix errors before committing."
    exit 1
fi
```

---

## PHASE 2: DATA MODEL UNIFICATION
**Timeline**: Week 3 (Days 1-3)
**Goal**: Eliminate 50+ field name fallback chains

### Step 2.1: Database Schema Audit (Day 1)

**Action**: Document ALL field name variations

```bash
# Find all field name variations
grep -r "\.get('direction'" trading_modes/ > field_audit.txt
grep -r "\.get('side'" trading_modes/ >> field_audit.txt
grep -r "target_pair\|symbol\|token_address" trading_modes/ >> field_audit.txt
```

**Output**: `docs/FIELD_NAME_STANDARDIZATION.md`

### Step 2.2: Standardize Database Schema (Day 1-2)

**File**: `risk_management/trading_database.py`

**Changes**:
1. Ensure column names match domain model EXACTLY
2. Remove any legacy columns
3. Add migration for existing data

```python
# BEFORE:
# Some code uses 'direction', database has 'side'

# AFTER:
# Database column: side TEXT NOT NULL
# Domain model: side: TradeSide
# ALL code uses: trade.side
```

### Step 2.3: Remove All Fallback Chains (Day 2-3)

**Before**:
```python
side = trade.get('side') or trade.get('direction', 'BUY')
```

**After**:
```python
side = trade.side  # Type-safe, always exists
```

**Search and destroy**:
```bash
# Find all fallback patterns
grep -r "\.get.*or.*\.get" trading_modes/

# Replace with typed access
# Trade object guarantees field exists
```

---

## PHASE 3: INDICATOR ABSTRACTION
**Timeline**: Week 3 (Days 4-5)
**Goal**: Eliminate version-dependent library calls

### Step 3.1: Create Indicator Module (Day 4)

**File**: `trading_modes/indicators/technical.py`

```python
"""
Version-agnostic technical indicator calculations
No external dependencies - pure pandas operations
"""

import pandas as pd
import numpy as np
from typing import Dict

class TechnicalIndicators:
    """
    All technical indicators in one place
    Returns consistent dict format regardless of library version
    """

    @staticmethod
    def bollinger_bands(
        close: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate Bollinger Bands

        Returns:
            {'upper': float, 'middle': float, 'lower': float}
        """
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        upper = sma.iloc[-1] + (std_dev * std.iloc[-1])
        middle = sma.iloc[-1]
        lower = sma.iloc[-1] - (std_dev * std.iloc[-1])

        # Validate
        if pd.isna(upper) or pd.isna(middle) or pd.isna(lower):
            raise ValueError(f"BB calculation failed - insufficient data (need {period}+ bars)")

        return {
            'upper': float(upper),
            'middle': float(middle),
            'lower': float(lower)
        }

    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index

        Returns:
            RSI value (0-100)
        """
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()

        rs = gain / loss
        rsi_value = 100 - (100 / (1 + rs.iloc[-1]))

        if pd.isna(rsi_value):
            raise ValueError(f"RSI calculation failed - insufficient data (need {period + 1}+ bars)")

        return float(rsi_value)

    @staticmethod
    def sma(close: pd.Series, period: int) -> float:
        """Simple Moving Average"""
        sma_value = close.rolling(window=period).mean().iloc[-1]

        if pd.isna(sma_value):
            raise ValueError(f"SMA calculation failed - insufficient data (need {period}+ bars)")

        return float(sma_value)

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """
        Average True Range

        Returns:
            ATR value
        """
        high_low = high - low
        high_close = (high - close.shift()).abs()
        low_close = (low - close.shift()).abs()

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr_value = true_range.rolling(window=period).mean().iloc[-1]

        if pd.isna(atr_value):
            raise ValueError(f"ATR calculation failed - insufficient data (need {period + 1}+ bars)")

        return float(atr_value)
```

### Step 3.2: Replace Library Calls (Day 5)

**Before**:
```python
# Issue: Version-dependent column names
bb_result = pandas_ta.bbands(close, length=20, std=2.0)
bb_upper = bb_result['BBU_20_2.0']  # Breaks on library update
```

**After**:
```python
from trading_modes.indicators.technical import TechnicalIndicators

# Always works - consistent output
bb = TechnicalIndicators.bollinger_bands(close, period=20, std_dev=2.0)
bb_upper = bb['upper']  # Always 'upper', never 'BBU_20_2.0'
```

**Files to update**: All 23 files using pandas_ta/talib

---

## PHASE 4: ERROR HANDLING STANDARDIZATION
**Timeline**: Week 4 (Days 1-3)
**Goal**: Eliminate missing error keys

### Step 4.1: Migrate Verification Agent (Day 1)

Already done in Phase 1.3 - uses Result type

### Step 4.2: Migrate Database Operations (Day 2)

**File**: `risk_management/trading_database.py`

**Before**:
```python
def get_open_trades(self, mode: str = None) -> List[Dict]:
    """Returns list of dicts - caller doesn't know what keys exist"""
    ...
```

**After**:
```python
from trading_modes.models.domain import Trade
from trading_modes.models.result import Result, success, failure

def get_open_trades(self, mode: str = None) -> Result[List[Trade]]:
    """Returns typed Trade objects - caller knows exact structure"""
    try:
        if mode:
            self.cursor.execute("""
                SELECT * FROM trades WHERE status = 'OPEN' AND UPPER(mode) = UPPER(?)
                ORDER BY timestamp DESC
            """, (mode,))
        else:
            self.cursor.execute("""
                SELECT * FROM trades WHERE status = 'OPEN'
                ORDER BY timestamp DESC
            """)

        rows = self.cursor.fetchall()
        trades = [Trade.from_db_row(dict(row)) for row in rows]

        return success(trades)

    except Exception as e:
        return failure(
            error=f"Failed to get open trades: {e}",
            error_type=type(e).__name__
        )
```

### Step 4.3: Update All Callers (Day 3)

**Before**:
```python
trades = db.get_open_trades(mode='PAPER')
for trade in trades:
    side = trade.get('side') or trade.get('direction', 'BUY')  # Defensive
    entry_price = trade.get('entry_price', 0.0)                 # Defensive
```

**After**:
```python
result = db.get_open_trades(mode=TradingMode.PAPER)

if result.is_success():
    for trade in result.value:
        side = trade.side              # ✅ Always exists
        entry_price = trade.entry_price  # ✅ Always exists, validated > 0
else:
    cprint(f"Database error: {result.error}", "red")
```

---

## PHASE 5: STATE MANAGEMENT
**Timeline**: Week 4 (Days 4-5)
**Goal**: Eliminate outer-scope variable declarations

### Step 5.1: Create Context Objects (Day 4)

**File**: `trading_modes/models/context.py`

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from trading_modes.models.domain import (
    SignalVerificationResult,
    StrategySignal,
    Trade
)

@dataclass
class TradingCycleContext:
    """
    All state for one trading cycle
    Replaces scattered outer-scope variables
    """
    cycle_number: int
    mode: str
    symbols: list[str]
    interval_minutes: int
    start_time: datetime = field(default_factory=datetime.now)

    # Signal processing state
    strategy_signal: Optional[StrategySignal] = None
    verification_result: Optional[SignalVerificationResult] = None
    final_action: str = 'NOTHING'
    final_confidence: int = 0

    # Trade execution state
    trade_executed: bool = False
    trade: Optional[Trade] = None

    def has_signal(self) -> bool:
        """Check if strategy generated a signal"""
        return self.strategy_signal is not None

    def is_verified(self) -> bool:
        """Check if signal has been verified"""
        return self.verification_result is not None

    def should_execute_trade(self) -> bool:
        """Check if all conditions met for trade execution"""
        return (
            self.has_signal() and
            self.is_verified() and
            self.verification_result.agrees_with_scanner and
            self.final_action in ['BUY', 'SELL']
        )
```

### Step 5.2: Refactor Main Loop (Day 5)

**Before** (Scattered Variables):
```python
verification_agreement = 'none'  # Outer scope to avoid UnboundLocalError

if enable_verification:
    try:
        verification_result = verify_signal(...)
        verification_agreement = verification_result.get('agreement_level', 'unknown')
    except:
        verification_agreement = 'error'

# ... 100 lines later ...
metadata = {'verification': verification_agreement}  # Where did this come from?
```

**After** (Explicit Context):
```python
from trading_modes.models.context import TradingCycleContext

ctx = TradingCycleContext(
    cycle_number=1,
    mode='PAPER',
    symbols=['BTC', 'ETH', 'SOL'],
    interval_minutes=5
)

# Generate signal
signal_result = strategy.generate_signals(...)
if signal_result.is_success():
    ctx.strategy_signal = signal_result.value

# Verify signal
if ctx.has_signal():
    verify_result = verify_signal(...)
    if verify_result.is_success():
        ctx.verification_result = verify_result.value
        ctx.final_action = verify_result.value.action.value
        ctx.final_confidence = verify_result.value.confidence

# Execute trade
if ctx.should_execute_trade():
    trade_result = execute_trade(...)
    if trade_result.is_success():
        ctx.trade = trade_result.value
        ctx.trade_executed = True

# Clear state for next cycle
print(f"Cycle {ctx.cycle_number} complete: {ctx.final_action} @ {ctx.final_confidence}% confidence")
```

---

## ROLLOUT STRATEGY

### Option A: Big Bang (Fast but Risky)
1. Complete all 5 phases in 3-4 weeks
2. Test extensively in paper mode
3. Deploy to live trading

**Pros**: Clean break, no mixed code
**Cons**: High risk, long testing period

### Option B: Incremental (Slow but Safe)
1. Phase 1-2: Core module only (Week 1-2)
2. Test in paper mode for 1 week
3. Phase 3-4: Expand to other modules (Week 3-4)
4. Test in paper mode for 1 week
5. Phase 5: Polish (Week 5)
6. Deploy to live trading

**Pros**: Lower risk, continuous validation
**Cons**: Temporary mixed code (typed + untyped)

### Option C: Parallel Development (Recommended)
1. Create new `trading_modes_v2/` directory
2. Implement all phases clean in v2
3. Run both systems in paper mode for 2 weeks
4. Compare results
5. Switch to v2 when validated

**Pros**: No disruption to current system, side-by-side validation
**Cons**: Extra work maintaining two codebases temporarily

---

## SUCCESS METRICS

### Week 1 (After Phase 1-2)
- [ ] Domain models defined
- [ ] Result type implemented
- [ ] Core verification agent migrated
- [ ] Type checker passing on core/
- [ ] Zero `.get()` calls in migrated code

### Week 2 (After Phase 2)
- [ ] All field names standardized
- [ ] Database schema matches domain models
- [ ] Zero fallback chains (`or trade.get(...)`)
- [ ] Paper trading runs error-free for 48 hours

### Week 3 (After Phase 3-4)
- [ ] Indicator abstraction layer complete
- [ ] No direct pandas_ta/talib calls
- [ ] All database operations return Result types
- [ ] Error handling consistent across modules

### Week 4 (After Phase 5)
- [ ] Context objects implemented
- [ ] No outer-scope variable declarations
- [ ] Full type coverage >90%
- [ ] Paper trading runs error-free for 1 week

### Production Ready
- [ ] Live trading tested with small position sizes
- [ ] Zero KeyError/AttributeError for 2 weeks
- [ ] New developer can onboard in <3 days
- [ ] Code review speed increased 50%

---

## DECISION POINT

**You need to choose**:

1. **Do nothing** - Keep patching symptoms as they appear
   - Pro: No upfront work
   - Con: Perpetual bug-fix cycle

2. **Quick fixes only** - Pin versions, add error_response helper
   - Pro: 1 hour of work
   - Con: Doesn't solve root causes

3. **Full refactoring** - Follow this 5-phase plan
   - Pro: Permanent solution, 60-80% fewer bugs
   - Con: 3-4 weeks of focused work

**Recommendation**: Option 3 (Full Refactoring)

The current rate of "CRITICAL FIX" additions (70+ in codebase) suggests technical debt is compounding. Each patch makes the next patch harder. A clean refactoring will pay for itself within 2-3 months.
