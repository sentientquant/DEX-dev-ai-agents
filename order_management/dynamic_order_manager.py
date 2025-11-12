#!/usr/bin/env python3
"""
🌙 Moon Dev's Dynamic Order Management System
Intelligent Stop Loss & Take Profit Placement Based on Market Conditions

PHILOSOPHY:
"One size fits all" stop losses get you stopped out in volatility.
"One size fits all" take profits leave money on the table in trends.
This system adapts SL/TP to token dynamics, regime, and momentum.

FEATURES:
- Dynamic SL/TP calculation (not fixed percentages)
- Multi-level take profits (3 levels with dynamic allocation)
- OCO (One-Cancels-Other) order support
- Token-aware: ATR-based levels for each asset
- Regime-aware: Trending = wider TPs, Choppy = tighter
- Momentum-aware: Strong = trail stops, Weak = fixed
- Support/Resistance integration (optional)

ORDER STRUCTURE:
After BUY at $100:
├── OCO Order #1 (40% position)
│   ├── Stop Loss: $95 (dynamic based on ATR)
│   └── Take Profit 1: $110 (dynamic based on regime)
├── Limit Order #2 (30% position)
│   └── Take Profit 2: $115 (scaled from TP1)
└── Limit Order #3 (30% position)
    └── Take Profit 3: $120 (max target)

DYNAMIC FACTORS:
- Token Volatility (ATR): High ATR = wider levels
- Market Regime: Trending = 3:1 RR, Choppy = 2:1 RR
- Momentum Strength: Strong = trail SL, Weak = fixed SL
- Support/Resistance: Align TPs with resistance, SL below support

DESIGNED BY: Moon Dev + User's Advanced Requirements
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import talib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from enum import Enum
import logging

from risk_management.dynamic_risk_engine import TokenRiskProfile, MarketRegime

# ===========================
# ORDER STRUCTURES
# ===========================

class OrderType(Enum):
    """Order types for execution"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    OCO = "OCO"  # One-Cancels-Other

@dataclass
class TakeProfitLevel:
    """Single take profit level"""
    level_number: int  # 1, 2, or 3
    price: float
    allocation_pct: float  # Percentage of total position
    order_type: OrderType = OrderType.LIMIT
    rationale: str = ""

@dataclass
class StopLossConfig:
    """Stop loss configuration"""
    price: float
    trail: bool = False  # Whether to trail the stop
    trail_distance: Optional[float] = None  # Trail distance if trailing
    rationale: str = ""

@dataclass
class OrderPlan:
    """Complete order execution plan"""
    entry_price: float
    position_size_usd: float
    direction: str  # 'BUY' or 'SELL'

    # Stop loss
    stop_loss: StopLossConfig

    # Take profits (3 levels)
    take_profits: List[TakeProfitLevel]

    # OCO structure
    oco_stop_loss: float  # SL price for OCO order
    oco_take_profit: float  # TP1 price for OCO order
    oco_allocation_pct: float  # % of position in OCO (typically 40%)

    # Metadata
    symbol: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dict for logging/storage"""
        return {
            'symbol': self.symbol,
            'entry_price': self.entry_price,
            'position_size_usd': self.position_size_usd,
            'direction': self.direction,
            'stop_loss': {
                'price': self.stop_loss.price,
                'trail': self.stop_loss.trail,
                'trail_distance': self.stop_loss.trail_distance,
                'rationale': self.stop_loss.rationale
            },
            'take_profits': [
                {
                    'level': tp.level_number,
                    'price': tp.price,
                    'allocation_pct': tp.allocation_pct,
                    'rationale': tp.rationale
                }
                for tp in self.take_profits
            ],
            'oco': {
                'stop_loss': self.oco_stop_loss,
                'take_profit': self.oco_take_profit,
                'allocation_pct': self.oco_allocation_pct
            },
            'timestamp': self.timestamp.isoformat()
        }

# ===========================
# MOMENTUM ANALYZER
# ===========================

class MomentumStrength(Enum):
    """Momentum strength classification"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"

class MomentumAnalyzer:
    """Analyzes momentum strength for dynamic SL/TP"""

    def analyze_momentum(self, ohlcv_data: pd.DataFrame) -> Tuple[MomentumStrength, float]:
        """
        Analyze momentum strength

        Args:
            ohlcv_data: OHLCV data for analysis

        Returns:
            (MomentumStrength, momentum_score)
        """
        close = ohlcv_data['close'].values
        high = ohlcv_data['high'].values
        low = ohlcv_data['low'].values
        volume = ohlcv_data['volume'].values if 'volume' in ohlcv_data else None

        # 1. RSI (Relative Strength Index)
        rsi = talib.RSI(close, timeperiod=14)[-1]

        # 2. MACD
        macd, signal, hist = talib.MACD(close)
        macd_hist = hist[-1]

        # 3. ADX (Trend Strength)
        adx = talib.ADX(high, low, close, timeperiod=14)[-1]

        # 4. Rate of Change
        roc = talib.ROC(close, timeperiod=10)[-1]

        # 5. Volume trend (if available)
        volume_trend = 1.0
        if volume is not None:
            recent_vol = np.mean(volume[-5:])
            avg_vol = np.mean(volume[-20:])
            volume_trend = recent_vol / avg_vol if avg_vol > 0 else 1.0

        # COMPOSITE MOMENTUM SCORE
        momentum_score = 0.0

        # RSI component (0-100 scale)
        if rsi > 70:
            momentum_score += 30  # Overbought = strong bullish momentum
        elif rsi > 60:
            momentum_score += 20
        elif rsi > 50:
            momentum_score += 10
        elif rsi < 30:
            momentum_score -= 30  # Oversold = strong bearish momentum
        elif rsi < 40:
            momentum_score -= 20

        # MACD component
        if macd_hist > 0:
            momentum_score += min(abs(macd_hist) * 10, 20)
        else:
            momentum_score -= min(abs(macd_hist) * 10, 20)

        # ADX component (trend strength)
        if adx > 40:
            momentum_score += 25  # Very strong trend
        elif adx > 25:
            momentum_score += 15  # Strong trend
        elif adx > 20:
            momentum_score += 5

        # ROC component
        if abs(roc) > 5:
            momentum_score += 15 if roc > 0 else -15
        elif abs(roc) > 2:
            momentum_score += 10 if roc > 0 else -10

        # Volume component
        if volume_trend > 1.5:
            momentum_score += 10  # Strong volume confirmation
        elif volume_trend > 1.2:
            momentum_score += 5

        # Normalize to 0-100 scale
        momentum_score = max(min(momentum_score, 100), -100)

        # CLASSIFY MOMENTUM
        if momentum_score > 60:
            strength = MomentumStrength.VERY_STRONG
        elif momentum_score > 30:
            strength = MomentumStrength.STRONG
        elif momentum_score > -30:
            strength = MomentumStrength.MODERATE
        elif momentum_score > -60:
            strength = MomentumStrength.WEAK
        else:
            strength = MomentumStrength.VERY_WEAK

        return strength, momentum_score

# ===========================
# SUPPORT/RESISTANCE DETECTOR
# ===========================

class SupportResistanceDetector:
    """Detects support and resistance levels"""

    def find_levels(
        self,
        ohlcv_data: pd.DataFrame,
        current_price: float,
        num_levels: int = 3
    ) -> Tuple[List[float], List[float]]:
        """
        Find support and resistance levels

        Args:
            ohlcv_data: OHLCV data
            current_price: Current price
            num_levels: Number of levels to find (default: 3)

        Returns:
            (support_levels, resistance_levels)
        """
        close = ohlcv_data['close'].values
        high = ohlcv_data['high'].values
        low = ohlcv_data['low'].values

        # Find pivot points (local maxima/minima)
        pivots_high = self._find_pivots(high, order=5)
        pivots_low = self._find_pivots(low, order=5, maximize=False)

        # Get resistance levels (above current price)
        resistance_levels = [high[i] for i in pivots_high if high[i] > current_price]
        resistance_levels = sorted(resistance_levels)[:num_levels]

        # Get support levels (below current price)
        support_levels = [low[i] for i in pivots_low if low[i] < current_price]
        support_levels = sorted(support_levels, reverse=True)[:num_levels]

        # If not enough levels, use percentages
        if len(resistance_levels) < num_levels:
            for i in range(len(resistance_levels), num_levels):
                resistance_levels.append(current_price * (1 + 0.05 * (i + 1)))

        if len(support_levels) < num_levels:
            for i in range(len(support_levels), num_levels):
                support_levels.append(current_price * (1 - 0.05 * (i + 1)))

        return support_levels, resistance_levels

    def _find_pivots(self, data: np.ndarray, order: int = 5, maximize: bool = True) -> List[int]:
        """Find local maxima or minima"""
        from scipy.signal import argrelextrema

        if maximize:
            pivots = argrelextrema(data, np.greater, order=order)[0]
        else:
            pivots = argrelextrema(data, np.less, order=order)[0]

        return pivots.tolist()

# ===========================
# DYNAMIC ORDER MANAGER
# ===========================

class DynamicOrderManager:
    """
    Main order management system with dynamic SL/TP calculation
    """

    def __init__(self):
        self.momentum_analyzer = MomentumAnalyzer()
        self.sr_detector = SupportResistanceDetector()

        logging.info("🌙 Dynamic Order Manager initialized")

    def calculate_order_plan(
        self,
        symbol: str,
        entry_price: float,
        position_size_usd: float,
        direction: str,
        token_profile: TokenRiskProfile,
        regime: MarketRegime,
        ohlcv_data: pd.DataFrame,
        use_support_resistance: bool = True
    ) -> OrderPlan:
        """
        Calculate complete order plan with dynamic SL/TP levels

        Args:
            symbol: Token symbol
            entry_price: Entry price for the trade
            position_size_usd: Position size in USD
            direction: 'BUY' or 'SELL'
            token_profile: Token risk profile from risk engine
            regime: Current market regime
            ohlcv_data: OHLCV data for analysis
            use_support_resistance: Whether to use S/R levels

        Returns:
            OrderPlan with complete execution plan
        """
        # Analyze momentum
        momentum_strength, momentum_score = self.momentum_analyzer.analyze_momentum(ohlcv_data)

        # Get support/resistance levels
        support_levels, resistance_levels = [], []
        if use_support_resistance:
            try:
                support_levels, resistance_levels = self.sr_detector.find_levels(
                    ohlcv_data, entry_price, num_levels=3
                )
            except:
                logging.warning("Could not detect S/R levels, using ATR-based levels")

        # Calculate ATR for dynamic spacing
        close = ohlcv_data['close'].values
        high = ohlcv_data['high'].values
        low = ohlcv_data['low'].values
        atr = talib.ATR(high, low, close, timeperiod=14)[-1]
        atr_pct = atr / entry_price

        # STEP 1: Calculate Stop Loss
        stop_loss_config = self._calculate_stop_loss(
            entry_price=entry_price,
            direction=direction,
            atr=atr,
            atr_pct=atr_pct,
            token_profile=token_profile,
            regime=regime,
            momentum_strength=momentum_strength,
            support_levels=support_levels
        )

        # STEP 2: Calculate Take Profit Levels
        take_profit_levels = self._calculate_take_profits(
            entry_price=entry_price,
            direction=direction,
            atr=atr,
            atr_pct=atr_pct,
            stop_loss_distance=abs(entry_price - stop_loss_config.price),
            regime=regime,
            momentum_strength=momentum_strength,
            momentum_score=momentum_score,
            resistance_levels=resistance_levels
        )

        # STEP 3: Configure OCO Order (40% allocation at TP1)
        oco_allocation_pct = self._calculate_oco_allocation(
            momentum_strength=momentum_strength,
            regime=regime
        )

        # Create order plan
        order_plan = OrderPlan(
            symbol=symbol,
            entry_price=entry_price,
            position_size_usd=position_size_usd,
            direction=direction,
            stop_loss=stop_loss_config,
            take_profits=take_profit_levels,
            oco_stop_loss=stop_loss_config.price,
            oco_take_profit=take_profit_levels[0].price,
            oco_allocation_pct=oco_allocation_pct
        )

        # Log plan
        logging.info(
            f"📋 Order Plan Created: {symbol} {direction}\n"
            f"   Entry: ${entry_price:.6f}\n"
            f"   SL: ${stop_loss_config.price:.6f} ({stop_loss_config.rationale})\n"
            f"   TP1: ${take_profit_levels[0].price:.6f} ({take_profit_levels[0].allocation_pct:.0f}%)\n"
            f"   TP2: ${take_profit_levels[1].price:.6f} ({take_profit_levels[1].allocation_pct:.0f}%)\n"
            f"   TP3: ${take_profit_levels[2].price:.6f} ({take_profit_levels[2].allocation_pct:.0f}%)\n"
            f"   Momentum: {momentum_strength.value} ({momentum_score:.0f})\n"
            f"   Regime: {regime.value}"
        )

        return order_plan

    def _calculate_stop_loss(
        self,
        entry_price: float,
        direction: str,
        atr: float,
        atr_pct: float,
        token_profile: TokenRiskProfile,
        regime: MarketRegime,
        momentum_strength: MomentumStrength,
        support_levels: List[float]
    ) -> StopLossConfig:
        """Calculate dynamic stop loss"""

        # Base SL distance from token profile
        base_sl_multiplier = token_profile.sl_multiplier  # e.g., 1.5-2.5x ATR

        # Adjust for regime
        regime_multiplier = {
            MarketRegime.CRISIS: 0.8,  # Tighter stops in crisis
            MarketRegime.TRENDING_UP: 1.2 if direction == 'BUY' else 0.9,
            MarketRegime.TRENDING_DOWN: 0.9 if direction == 'BUY' else 1.2,
            MarketRegime.CHOPPY: 0.85,  # Tighter in choppy
            MarketRegime.FLAT: 1.0
        }.get(regime, 1.0)

        # Calculate SL distance
        sl_distance = base_sl_multiplier * atr * regime_multiplier

        # Calculate SL price
        if direction == 'BUY':
            sl_price = entry_price - sl_distance
        else:
            sl_price = entry_price + sl_distance

        # Align with support (if available and close)
        if support_levels and direction == 'BUY':
            nearest_support = support_levels[0]
            # If support is within 20% of calculated SL, use it
            if abs(nearest_support - sl_price) / sl_price < 0.20:
                sl_price = nearest_support * 0.99  # Slightly below support
                rationale = f"Aligned with support at ${nearest_support:.6f}"
            else:
                rationale = f"{base_sl_multiplier:.1f}x ATR, {regime.value}"
        else:
            rationale = f"{base_sl_multiplier:.1f}x ATR, {regime.value}"

        # Trailing stop for strong momentum
        trail = momentum_strength in [MomentumStrength.VERY_STRONG, MomentumStrength.STRONG]
        trail_distance = atr * 1.5 if trail else None

        if trail:
            rationale += " (trailing)"

        return StopLossConfig(
            price=sl_price,
            trail=trail,
            trail_distance=trail_distance,
            rationale=rationale
        )

    def _calculate_take_profits(
        self,
        entry_price: float,
        direction: str,
        atr: float,
        atr_pct: float,
        stop_loss_distance: float,
        regime: MarketRegime,
        momentum_strength: MomentumStrength,
        momentum_score: float,
        resistance_levels: List[float]
    ) -> List[TakeProfitLevel]:
        """Calculate 3 dynamic take profit levels"""

        # RISK/REWARD RATIO (regime-dependent)
        rr_ratios = {
            MarketRegime.TRENDING_UP: [2.5, 4.0, 6.0],  # Aggressive TPs
            MarketRegime.TRENDING_DOWN: [2.0, 3.0, 4.5],
            MarketRegime.CHOPPY: [1.5, 2.5, 3.5],  # Conservative
            MarketRegime.FLAT: [2.0, 3.0, 4.0],
            MarketRegime.CRISIS: [1.5, 2.0, 3.0]  # Very conservative
        }

        base_rr = rr_ratios.get(regime, [2.0, 3.0, 4.0])

        # Adjust RR for momentum
        if momentum_strength == MomentumStrength.VERY_STRONG:
            rr_multiplier = 1.3
        elif momentum_strength == MomentumStrength.STRONG:
            rr_multiplier = 1.15
        elif momentum_strength == MomentumStrength.WEAK:
            rr_multiplier = 0.85
        elif momentum_strength == MomentumStrength.VERY_WEAK:
            rr_multiplier = 0.7
        else:
            rr_multiplier = 1.0

        # Calculate TP prices
        tp_levels = []

        for i, rr in enumerate(base_rr):
            adjusted_rr = rr * rr_multiplier
            tp_distance = stop_loss_distance * adjusted_rr

            if direction == 'BUY':
                tp_price = entry_price + tp_distance
            else:
                tp_price = entry_price - tp_distance

            # Align with resistance (if available)
            rationale = f"{adjusted_rr:.1f}:1 RR"
            if resistance_levels and direction == 'BUY' and i < len(resistance_levels):
                nearest_resistance = resistance_levels[i]
                # If resistance is within 15% of calculated TP, use it
                if abs(nearest_resistance - tp_price) / tp_price < 0.15:
                    tp_price = nearest_resistance * 0.995  # Slightly below resistance
                    rationale = f"Resistance at ${nearest_resistance:.6f}"

            tp_levels.append(TakeProfitLevel(
                level_number=i + 1,
                price=tp_price,
                allocation_pct=0.0,  # Will be set below
                rationale=rationale
            ))

        # DYNAMIC ALLOCATION (momentum-dependent)
        if momentum_strength in [MomentumStrength.VERY_STRONG, MomentumStrength.STRONG]:
            # Let winners run
            allocations = [30, 30, 40]
        elif momentum_strength == MomentumStrength.MODERATE:
            # Balanced
            allocations = [40, 30, 30]
        else:
            # Take profits early
            allocations = [50, 30, 20]

        for tp, alloc in zip(tp_levels, allocations):
            tp.allocation_pct = alloc

        return tp_levels

    def _calculate_oco_allocation(
        self,
        momentum_strength: MomentumStrength,
        regime: MarketRegime
    ) -> float:
        """Calculate what % of position to put in OCO order"""

        # Default: 40% in OCO (TP1)
        base_allocation = 40.0

        # Adjust for momentum
        if momentum_strength in [MomentumStrength.VERY_STRONG, MomentumStrength.STRONG]:
            # Less in OCO, more for TP2/TP3
            return base_allocation - 10
        elif momentum_strength in [MomentumStrength.WEAK, MomentumStrength.VERY_WEAK]:
            # More in OCO, secure profits early
            return base_allocation + 10

        return base_allocation


# ===========================
# BINANCE ORDER EXECUTOR
# ===========================

class BinanceOrderExecutor:
    """
    Executes order plans on Binance exchange
    (Placeholder - needs actual Binance API integration)
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        # TODO: Initialize Binance client
        logging.info("🔄 Binance Order Executor initialized (placeholder)")

    def execute_order_plan(self, order_plan: OrderPlan) -> Dict:
        """
        Execute complete order plan on Binance

        Steps:
        1. Market buy/sell (entry)
        2. Place OCO order (SL + TP1, 40% of position)
        3. Place limit order for TP2 (30%)
        4. Place limit order for TP3 (30%)

        Returns:
            Dict with order IDs and status
        """
        logging.info(f"📤 Executing order plan for {order_plan.symbol}...")

        # TODO: Implement actual Binance API calls
        # Example structure:
        # 1. client.create_order(symbol, side='BUY', type='MARKET', quantity=...)
        # 2. client.create_oco_order(symbol, side='SELL', stopPrice=..., price=..., quantity=...)
        # 3. client.create_order(symbol, side='SELL', type='LIMIT', price=TP2, quantity=...)
        # 4. client.create_order(symbol, side='SELL', type='LIMIT', price=TP3, quantity=...)

        return {
            'status': 'placeholder',
            'order_plan': order_plan.to_dict()
        }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    print("🌙 Moon Dev's Dynamic Order Manager - Example\n")

    # This would be integrated with your trading system
    # See integration examples in the documentation
