"""
Trading System Domain Models
Type-safe data structures replacing untyped dictionaries
"""

from .domain import (
    # Enums
    TradeStatus,
    TradeSide,
    TradingMode,
    SignalAction,
    AgreementLevel,
    # Domain Models
    Trade,
    Verdict,
    SignalVerificationResult,
    StrategySignal,
    AccountStatus,
)

from .result import (
    Result,
    Success,
    Failure,
    success,
    failure,
)

__all__ = [
    # Enums
    'TradeStatus',
    'TradeSide',
    'TradingMode',
    'SignalAction',
    'AgreementLevel',
    # Domain Models
    'Trade',
    'Verdict',
    'SignalVerificationResult',
    'StrategySignal',
    'AccountStatus',
    # Result Types
    'Result',
    'Success',
    'Failure',
    'success',
    'failure',
]
