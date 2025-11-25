#!/usr/bin/env python3
"""
Trading Modes Core Package

Contains shared components for all trading flows:
- signal_bus: Unified messaging for trading signals
- arbiter: Deterministic signal arbitration
- signal_verification_agent: AI swarm signal verification
- strategy_validator: Strategy validation
- market_analysis_agent: Market analysis
"""

from trading_modes.core.signal_bus import Signal, get_signal_bus
from trading_modes.core.arbiter import DeterministicArbiter, ArbitrationResult

__all__ = [
    'Signal',
    'get_signal_bus',
    'DeterministicArbiter',
    'ArbitrationResult',
]
