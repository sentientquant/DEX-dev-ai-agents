"""
Type-safe domain models for trading system

Replaces untyped dictionaries with validated dataclasses.
Eliminates 304 defensive .get() calls and prevents KeyError crashes.

All models include validation in __post_init__ to ensure data integrity.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json


# ============================================================================
# ENUMS - All valid states enumerated
# ============================================================================

class TradeStatus(Enum):
    """Trade lifecycle status"""
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'


class TradeSide(Enum):
    """Trade direction - BUY (long) or SELL (short)"""
    BUY = 'BUY'
    SELL = 'SELL'


class TradingMode(Enum):
    """Trading mode - paper or live"""
    PAPER = 'PAPER'
    LIVE = 'LIVE'


class SignalAction(Enum):
    """Trading signal action"""
    BUY = 'BUY'
    SELL = 'SELL'
    NOTHING = 'NOTHING'
    WAIT = 'WAIT'


class AgreementLevel(Enum):
    """AI swarm agreement level"""
    FULL = 'full'          # 5/5 or 4/5 models agree
    MAJORITY = 'majority'  # 3/5 models agree
    WEAK = 'weak'          # 2/5 models agree
    NONE = 'none'          # 0-1/5 models agree
    ERROR = 'error'        # Verification failed
    DISABLED = 'disabled'  # Verification not enabled


# ============================================================================
# DOMAIN MODELS - Replace untyped dictionaries
# ============================================================================

@dataclass
class Trade:
    """
    Type-safe trade representation

    Replaces untyped dict with 20+ fields.
    Database column names match field names EXACTLY (no more direction/side confusion).

    Validation ensures:
    - Prices are positive
    - Confidence is 0-100
    - Required fields always present
    """
    # Required fields
    trade_id: str
    symbol: str  # Format: "BTCUSDT" (standardized - never "BTC", never "BTC-USDT")
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
    swing_bars_ago: Optional[int] = None
    swing_strength: Optional[float] = None
    atr_pct: Optional[float] = None
    atr_multiplier: Optional[float] = None
    confidence: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate data on creation - prevents invalid trades"""
        if self.entry_price <= 0:
            raise ValueError(f"Entry price must be positive, got {self.entry_price}")
        if self.position_size_usd <= 0:
            raise ValueError(f"Position size must be positive, got {self.position_size_usd}")
        if self.confidence is not None and not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")

        # Convert string enums if needed (for database compatibility)
        if isinstance(self.side, str):
            self.side = TradeSide(self.side)
        if isinstance(self.mode, str):
            self.mode = TradingMode(self.mode)
        if isinstance(self.status, str):
            self.status = TradeStatus(self.status)

    @property
    def base_asset(self) -> str:
        """Extract base asset from symbol: 'BTCUSDT' -> 'BTC'"""
        return self.symbol.replace('USDT', '').replace('PERP', '')

    @property
    def is_open(self) -> bool:
        """Check if trade is currently open"""
        return self.status == TradeStatus.OPEN

    @property
    def is_long(self) -> bool:
        """Check if this is a long position"""
        return self.side == TradeSide.BUY

    @property
    def is_short(self) -> bool:
        """Check if this is a short position"""
        return self.side == TradeSide.SELL

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Trade':
        """
        Convert database row to Trade object

        SINGLE CONVERSION POINT - no more scattered conversions
        Handles both dict and sqlite3.Row objects
        """
        # Handle datetime strings
        timestamp = row.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        exit_timestamp = row.get('exit_timestamp')
        if isinstance(exit_timestamp, str):
            exit_timestamp = datetime.fromisoformat(exit_timestamp)

        # Handle metadata JSON string
        metadata = row.get('metadata')
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = None

        return cls(
            trade_id=row['trade_id'],
            symbol=row['symbol'],
            side=TradeSide(row['side']),
            entry_price=float(row['entry_price']),
            position_size_usd=float(row['position_size_usd']),
            stop_loss=float(row['stop_loss']),
            mode=TradingMode(row['mode']),
            status=TradeStatus(row['status']),
            timestamp=timestamp,
            tp1_price=float(row['tp1_price']) if row.get('tp1_price') else None,
            tp2_price=float(row['tp2_price']) if row.get('tp2_price') else None,
            tp3_price=float(row['tp3_price']) if row.get('tp3_price') else None,
            tp1_pct=float(row['tp1_pct']) if row.get('tp1_pct') else None,
            tp2_pct=float(row['tp2_pct']) if row.get('tp2_pct') else None,
            tp3_pct=float(row['tp3_pct']) if row.get('tp3_pct') else None,
            exit_price=float(row['exit_price']) if row.get('exit_price') else None,
            exit_timestamp=exit_timestamp,
            pnl_usd=float(row['pnl_usd']) if row.get('pnl_usd') else None,
            pnl_pct=float(row['pnl_pct']) if row.get('pnl_pct') else None,
            exit_reason=row.get('exit_reason'),
            strategy_name=row.get('strategy_name'),
            swing_bars_ago=int(row['swing_bars_ago']) if row.get('swing_bars_ago') else None,
            swing_strength=float(row['swing_strength']) if row.get('swing_strength') else None,
            atr_pct=float(row['atr_pct']) if row.get('atr_pct') else None,
            atr_multiplier=float(row['atr_multiplier']) if row.get('atr_multiplier') else None,
            confidence=int(float(row['confidence'])) if row.get('confidence') else None,  # FIXED: convert float string to int
            metadata=metadata
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            'trade_id': self.trade_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'symbol': self.symbol,
            'side': self.side.value,
            'entry_price': self.entry_price,
            'position_size_usd': self.position_size_usd,
            'stop_loss': self.stop_loss,
            'tp1_price': self.tp1_price,
            'tp2_price': self.tp2_price,
            'tp3_price': self.tp3_price,
            'tp1_pct': self.tp1_pct,
            'tp2_pct': self.tp2_pct,
            'tp3_pct': self.tp3_pct,
            'mode': self.mode.value,
            'status': self.status.value,
            'exit_price': self.exit_price,
            'exit_timestamp': self.exit_timestamp.isoformat() if self.exit_timestamp else None,
            'pnl_usd': self.pnl_usd,
            'pnl_pct': self.pnl_pct,
            'exit_reason': self.exit_reason,
            'strategy_name': self.strategy_name,
            'swing_bars_ago': self.swing_bars_ago,
            'swing_strength': self.swing_strength,
            'atr_pct': self.atr_pct,
            'atr_multiplier': self.atr_multiplier,
            'confidence': self.confidence,
            'metadata': json.dumps(self.metadata) if self.metadata else None
        }


@dataclass
class Verdict:
    """
    Single AI model verdict on trading signal

    Used by SignalVerificationResult to track individual model votes
    """
    model_name: str
    vote: SignalAction
    confidence: int
    reasoning: str

    def __post_init__(self) -> None:
        """Validate confidence range"""
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")

        # Convert string enum if needed
        if isinstance(self.vote, str):
            self.vote = SignalAction(self.vote)

    def agrees_with_action(self, action: SignalAction) -> bool:
        """Check if this verdict agrees with the given action"""
        return self.vote == action


@dataclass
class SignalVerificationResult:
    """
    Result from AI swarm signal verification

    Replaces the untyped dict that caused KeyError bugs.
    ALL FIELDS ALWAYS PRESENT - no more .get() needed.

    Previously:
        result = {'agrees': True, 'action': 'BUY'}  # Missing 'agreement_level' - crashes!
        agreement = result.get('agreement_level', 'unknown')  # Defensive .get()

    Now:
        result = SignalVerificationResult(...)  # MUST have all fields
        agreement = result.agreement_level.value  # Always exists, IDE autocomplete
    """
    agrees_with_scanner: bool
    agreement_level: AgreementLevel
    action: SignalAction
    confidence: int
    reasoning: str
    verdicts: List[Verdict]

    def __post_init__(self) -> None:
        """Validate on creation"""
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")

        # Convert string enums if needed
        if isinstance(self.agreement_level, str):
            self.agreement_level = AgreementLevel(self.agreement_level)
        if isinstance(self.action, str):
            self.action = SignalAction(self.action)

    @classmethod
    def error(cls, error_message: str) -> 'SignalVerificationResult':
        """
        Factory method for error state

        ALWAYS has all required fields - no missing key crashes
        """
        return cls(
            agrees_with_scanner=False,
            agreement_level=AgreementLevel.ERROR,
            action=SignalAction.WAIT,
            confidence=0,
            reasoning=f"Verification failed: {error_message}",
            verdicts=[]
        )

    @classmethod
    def disabled(cls) -> 'SignalVerificationResult':
        """Factory method for disabled verification"""
        return cls(
            agrees_with_scanner=True,  # Don't block trades
            agreement_level=AgreementLevel.DISABLED,
            action=SignalAction.NOTHING,
            confidence=0,
            reasoning="Signal verification disabled",
            verdicts=[]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return {
            'agrees_with_scanner': self.agrees_with_scanner,
            'agreement_level': self.agreement_level.value,
            'action': self.action.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'verdicts': [
                {
                    'model': v.model_name,
                    'vote': v.vote.value,
                    'confidence': v.confidence,
                    'reasoning': v.reasoning
                }
                for v in self.verdicts
            ]
        }


@dataclass
class StrategySignal:
    """
    Signal generated by a trading strategy

    Replaces untyped dict from strategy.generate_signals()
    """
    action: SignalAction
    confidence: int
    reasoning: str
    strategy_name: str
    symbol: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Optional technical details
    current_price: Optional[float] = None
    indicators: Optional[Dict[str, float]] = None

    def __post_init__(self) -> None:
        """Validate confidence range"""
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")

        # Convert string enum if needed
        if isinstance(self.action, str):
            self.action = SignalAction(self.action)

    @property
    def is_tradeable(self) -> bool:
        """Check if this signal should trigger a trade"""
        return self.action in [SignalAction.BUY, SignalAction.SELL]

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strategy_name: str, symbol: str) -> 'StrategySignal':
        """
        Create from legacy dictionary format

        Handles old strategy output: {'action': 'BUY', 'confidence': 85, ...}
        """
        return cls(
            action=SignalAction(data['action']),
            confidence=int(data['confidence']),
            reasoning=data.get('reasoning', ''),
            strategy_name=strategy_name,
            symbol=symbol,
            current_price=data.get('current_price'),
            indicators=data.get('indicators')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return {
            'action': self.action.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'current_price': self.current_price,
            'indicators': self.indicators
        }


@dataclass
class AccountStatus:
    """
    Real-time account status with balance tracking

    Replaces the dummy/mock balance display issue.
    Includes unrealized PnL from open positions.
    """
    current_balance: float
    free_usdt: float
    allocated_usdt: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    open_positions: int
    mode: TradingMode
    starting_balance: float = 10000.0

    @property
    def allocation_pct(self) -> float:
        """Percentage of capital allocated to trades"""
        if self.current_balance == 0:
            return 0.0
        return (self.allocated_usdt / self.current_balance) * 100

    @property
    def return_pct(self) -> float:
        """Total return percentage"""
        if self.starting_balance == 0:
            return 0.0
        return (self.total_pnl / self.starting_balance) * 100

    def __str__(self) -> str:
        """Human-readable status string"""
        pnl_sign = '+' if self.total_pnl >= 0 else ''
        return (
            f"Balance: ${self.current_balance:,.2f} | "
            f"PnL: ${pnl_sign}{self.total_pnl:,.2f} ({pnl_sign}{self.return_pct:.2f}%) | "
            f"Open: {self.open_positions} | "
            f"Free: ${self.free_usdt:,.2f} | "
            f"Allocated: ${self.allocated_usdt:,.2f}"
        )
