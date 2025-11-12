#!/usr/bin/env python3
"""
🌙 Moon Dev's SIMPLIFIED Allocation Calculator
PRAGMATIC, FAST, PRODUCTION-READY

PHILOSOPHY:
Less code = less bugs = more reliable
Focus on what actually moves the needle in crypto trading

KEY FACTORS (5 essentials, not 15):
1. Momentum (RSI + MACD)
2. Volatility (ATR)
3. Regime (trending/choppy/flat)
4. Portfolio state (winning/losing streak)
5. Balance constraints (minimum $100 for 3 tokens)

STRATEGIES:
- Trending + Strong = Let winners run (25/30/45)
- Choppy + Weak = Take early (60/25/15)
- Balanced = Standard (40/30/30)

LOW BALANCE AWARE:
- $100 total = One token only, 100/0/0 allocation
- $300 total = Three tokens max, balanced allocation
- $1000+ = Full flexibility
"""

import numpy as np
import pandas as pd
import talib
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

# ===========================
# SIMPLIFIED DATA STRUCTURES
# ===========================

class Strategy(Enum):
    """Simple strategy types"""
    LET_WINNERS_RUN = "let_winners_run"  # 25/30/45
    TAKE_EARLY = "take_early"  # 60/25/15
    BALANCED = "balanced"  # 40/30/30

@dataclass
class SimpleFactors:
    """Only what matters"""
    rsi: float  # 0-100
    macd_histogram: float  # Positive = bullish
    atr_pct: float  # ATR as % of price
    regime: str  # 'trending', 'choppy', 'flat'
    recent_wins: int  # Last 5 trades: how many won?
    balance_usd: float  # Available balance
    num_positions: int  # Current open positions

# ===========================
# SIMPLIFIED CALCULATOR
# ===========================

class SimpleAllocationCalculator:
    """
    KISS (Keep It Simple Stupid) allocation calculator
    """

    def calculate(
        self,
        ohlcv: pd.DataFrame,
        balance_usd: float,
        num_positions: int = 0,
        recent_wins: int = 3
    ) -> Tuple[List[float], str]:
        """
        Calculate allocation in ONE function

        Args:
            ohlcv: OHLCV DataFrame
            balance_usd: Available balance
            num_positions: Current open positions (0-3)
            recent_wins: Number of wins in last 5 trades

        Returns:
            ([tp1_pct, tp2_pct, tp3_pct], reasoning)
        """
        # Extract data
        close = ohlcv['close'].values
        high = ohlcv['high'].values
        low = ohlcv['low'].values

        # Calculate essentials
        rsi = talib.RSI(close, timeperiod=14)[-1]
        macd, signal, hist = talib.MACD(close)
        macd_hist = hist[-1]
        atr = talib.ATR(high, low, close, timeperiod=14)[-1]
        atr_pct = atr / close[-1] * 100

        # Detect regime (simple)
        adx = talib.ADX(high, low, close, timeperiod=14)[-1]
        if adx > 25:
            regime = 'trending'
        elif adx < 15:
            regime = 'flat'
        else:
            regime = 'choppy'

        # LOW BALANCE LOGIC
        if balance_usd < 100:
            return [100, 0, 0], "Balance < $100: Exit 100% at TP1 (cannot split)"

        if balance_usd < 300:
            if num_positions >= 1:
                return [100, 0, 0], "Low balance + position open: Exit 100% at TP1"
            else:
                return [60, 25, 15], "Low balance: Take profits early"

        # DECISION TREE (simple)

        # Strong trend + momentum
        if regime == 'trending' and rsi > 60 and macd_hist > 0:
            if recent_wins >= 3:
                return [25, 30, 45], "Strong trend + winning streak: Let winners run"
            else:
                return [40, 30, 30], "Strong trend but cautious: Balanced"

        # Choppy market
        if regime == 'choppy' or atr_pct > 3.0:  # High volatility
            return [60, 25, 15], "Choppy/volatile: Take profits early"

        # Weak momentum
        if rsi < 40 or macd_hist < 0:
            return [55, 30, 15], "Weak momentum: Secure early"

        # Default balanced
        return [40, 30, 30], "Balanced conditions: Standard allocation"


# ===========================
# BALANCE-AWARE POSITION SIZER
# ===========================

class LowBalancePositionSizer:
    """
    Handles low balance scenarios ($100-$1000)
    """

    def calculate_position_size(
        self,
        balance_usd: float,
        num_open_positions: int,
        max_positions: int = 3,
        min_position_usd: float = 100.0
    ) -> Tuple[float, int, str]:
        """
        Calculate how much to allocate per trade

        Args:
            balance_usd: Available balance
            num_open_positions: Currently open positions
            max_positions: Max allowed (default: 3)
            min_position_usd: Minimum per position (Binance: $100)

        Returns:
            (position_size_usd, max_new_positions, reasoning)
        """
        # Can't trade if balance below minimum
        if balance_usd < min_position_usd:
            return 0.0, 0, f"Balance ${balance_usd:.0f} < ${min_position_usd:.0f} minimum"

        # Calculate available for new positions
        positions_left = max_positions - num_open_positions

        if positions_left <= 0:
            return 0.0, 0, f"Max positions ({max_positions}) already open"

        # Divide balance among remaining position slots
        per_position = balance_usd / positions_left

        if per_position < min_position_usd:
            # Can only open fewer positions
            can_open = int(balance_usd / min_position_usd)
            if can_open < 1:
                return 0.0, 0, f"Balance only allows ${balance_usd:.0f}, need ${min_position_usd:.0f}"

            position_size = min_position_usd
            return position_size, can_open, f"Low balance: ${min_position_usd:.0f} per position, max {can_open} positions"

        # Normal case
        position_size = per_position
        return position_size, positions_left, f"${position_size:.0f} per position, {positions_left} slots available"


# ===========================
# COMBINED CALCULATOR
# ===========================

def calculate_smart_allocation(
    ohlcv: pd.DataFrame,
    balance_usd: float,
    num_positions: int = 0,
    recent_wins: int = 3
) -> dict:
    """
    One-shot calculation: position size + allocation

    Returns:
        {
            'can_trade': bool,
            'position_size_usd': float,
            'max_new_positions': int,
            'tp1_pct': float,
            'tp2_pct': float,
            'tp3_pct': float,
            'reasoning': str
        }
    """
    # Step 1: Check if can trade
    sizer = LowBalancePositionSizer()
    position_size, max_new, size_reason = sizer.calculate_position_size(
        balance_usd, num_positions
    )

    if position_size == 0:
        return {
            'can_trade': False,
            'position_size_usd': 0,
            'max_new_positions': 0,
            'tp1_pct': 0,
            'tp2_pct': 0,
            'tp3_pct': 0,
            'reasoning': size_reason
        }

    # Step 2: Calculate allocation
    calc = SimpleAllocationCalculator()
    allocations, alloc_reason = calc.calculate(
        ohlcv, balance_usd, num_positions, recent_wins
    )

    return {
        'can_trade': True,
        'position_size_usd': position_size,
        'max_new_positions': max_new,
        'tp1_pct': allocations[0],
        'tp2_pct': allocations[1],
        'tp3_pct': allocations[2],
        'reasoning': f"{size_reason} | {alloc_reason}"
    }


if __name__ == "__main__":
    import sys
    import io
    if __name__ == '__main__' and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("🌙 Simplified Allocation Calculator - Test\n")

    # Create sample data
    dates = pd.date_range('2024-01-01', periods=200, freq='1H')
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(200) * 0.5)

    ohlcv = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices - 0.5,
        'high': close_prices + np.random.rand(200) * 2,
        'low': close_prices - np.random.rand(200) * 2,
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 200)
    })

    # Test scenarios
    scenarios = [
        ("High balance, no positions", 10000, 0, 4),
        ("Medium balance, 1 position", 1000, 1, 3),
        ("Low balance, no positions", 300, 0, 2),
        ("Very low balance", 100, 0, 2),
        ("Below minimum", 50, 0, 1),
    ]

    for name, balance, positions, wins in scenarios:
        print(f"Scenario: {name}")
        print(f"  Balance: ${balance:.0f} | Positions: {positions} | Recent wins: {wins}")

        result = calculate_smart_allocation(ohlcv, balance, positions, wins)

        print(f"  Can trade: {result['can_trade']}")
        if result['can_trade']:
            print(f"  Position size: ${result['position_size_usd']:.0f}")
            print(f"  Allocation: TP1={result['tp1_pct']:.0f}% | "
                  f"TP2={result['tp2_pct']:.0f}% | TP3={result['tp3_pct']:.0f}%")
        print(f"  Reasoning: {result['reasoning']}")
        print()

    print("✅ Simple, fast, production-ready!")
