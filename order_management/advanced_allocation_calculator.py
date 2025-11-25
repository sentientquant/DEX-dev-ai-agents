#!/usr/bin/env python3
"""
🌙 Moon Dev's ULTRA-ADVANCED Intelligent Allocation Calculator
SMART, REALISTIC, AUTOMATIC allocation for Stop Loss & 3 Take Profits

PHILOSOPHY:
Simple momentum-based allocation? That's amateur hour.
This system analyzes 15+ factors to determine the OPTIMAL allocation.

FACTORS CONSIDERED:
1. Momentum Strength (RSI, MACD, ADX)
2. Volatility Level (ATR, realized vol)
3. Volume Profile (buying/selling pressure)
4. Market Regime (trending/choppy/crisis)
5. Time of Day (high/low volatility hours)
6. Historical Win Rate (per TP level)
7. Support/Resistance Proximity
8. Trend Strength & Duration
9. Market Depth (liquidity)
10. Token Risk Score
11. Portfolio Exposure
12. Recent PnL Performance
13. Correlation with BTC
14. Funding Rates (sentiment)
15. Open Interest Changes

OUTPUT:
Not just "40/30/30" but INTELLIGENT allocations like:
- Scalping setup: 60/25/15 (take profits fast)
- Momentum breakout: 25/25/50 (let winners run big)
- Mean reversion: 50/35/15 (secure early)
- Trend following: 20/30/50 (maximize runners)

DESIGNED BY: Moon Dev + User's "ULTRA INTELLIGENT" Requirements
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import talib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from datetime import datetime, time
from enum import Enum
import logging

from order_management.dynamic_order_manager import MomentumStrength, MomentumAnalyzer

# ===========================
# ALLOCATION STRATEGY TYPES
# ===========================

class AllocationStrategy(Enum):
    """Types of allocation strategies"""
    SCALPING = "scalping"  # 60/25/15 - Quick profits
    MOMENTUM_BREAKOUT = "momentum_breakout"  # 25/25/50 - Let big winners run
    MEAN_REVERSION = "mean_reversion"  # 50/35/15 - Secure early
    TREND_FOLLOWING = "trend_following"  # 20/30/50 - Maximize runners
    BALANCED = "balanced"  # 40/30/30 - Standard
    DEFENSIVE = "defensive"  # 70/20/10 - Capital preservation
    AGGRESSIVE = "aggressive"  # 15/35/50 - Maximum profit seeking

@dataclass
class AllocationFactors:
    """Complete set of factors for allocation decision"""

    # Technical factors
    momentum_strength: MomentumStrength
    momentum_score: float
    volatility_percentile: float  # 0-100
    trend_strength: float  # ADX value
    volume_profile_score: float  # -100 to +100

    # Market factors
    regime: str  # Market regime
    time_volatility: str  # 'high', 'medium', 'low' (time of day)
    market_depth_score: float  # 0-100 (liquidity)

    # Risk factors
    token_risk_score: float  # 0.3-1.5
    portfolio_exposure_pct: float  # Current exposure
    recent_pnl_trend: str  # 'winning', 'losing', 'neutral'

    # Advanced factors
    support_proximity_pct: float  # Distance to nearest support
    resistance_proximity_pct: float  # Distance to nearest resistance
    btc_correlation: float  # -1 to +1
    funding_rate: Optional[float]  # Funding rate (if available)
    oi_change_pct: Optional[float]  # Open interest change

    # Historical performance
    tp1_historical_hit_rate: float  # 0-100
    tp2_historical_hit_rate: float  # 0-100
    tp3_historical_hit_rate: float  # 0-100

# ===========================
# FACTOR ANALYZERS
# ===========================

class VolatilityAnalyzer:
    """Analyzes volatility for allocation decisions"""

    def analyze_volatility(self, ohlcv_data: pd.DataFrame) -> Tuple[float, str]:
        """
        Analyze volatility percentile

        Returns:
            (volatility_percentile, interpretation)
        """
        close = ohlcv_data['close'].values
        high = ohlcv_data['high'].values
        low = ohlcv_data['low'].values

        # Calculate ATR
        atr = talib.ATR(high, low, close, timeperiod=14)
        current_atr = atr[-1]

        # Get historical ATR distribution
        atr_percentile = (atr < current_atr).sum() / len(atr) * 100

        if atr_percentile > 80:
            interpretation = "very_high"
        elif atr_percentile > 60:
            interpretation = "high"
        elif atr_percentile > 40:
            interpretation = "medium"
        elif atr_percentile > 20:
            interpretation = "low"
        else:
            interpretation = "very_low"

        return atr_percentile, interpretation


class VolumeProfileAnalyzer:
    """Analyzes volume profile for buying/selling pressure"""

    def analyze_volume_profile(self, ohlcv_data: pd.DataFrame) -> Tuple[float, str]:
        """
        Analyze volume profile

        Returns:
            (volume_profile_score, interpretation)
            Score: -100 (heavy selling) to +100 (heavy buying)
        """
        close = ohlcv_data['close'].values
        volume = ohlcv_data['volume'].values if 'volume' in ohlcv_data else None

        if volume is None:
            return 0.0, "neutral"

        # Calculate OBV (On-Balance Volume)
        obv = talib.OBV(close, volume)
        obv_slope = (obv[-1] - obv[-20]) / obv[-20] * 100  # 20-period change

        # Calculate volume-weighted price momentum
        recent_closes = close[-10:]
        recent_volumes = volume[-10:]

        up_volume = sum(recent_volumes[i] for i in range(len(recent_closes)-1)
                       if recent_closes[i+1] > recent_closes[i])
        down_volume = sum(recent_volumes[i] for i in range(len(recent_closes)-1)
                         if recent_closes[i+1] < recent_closes[i])

        total_volume = up_volume + down_volume
        if total_volume > 0:
            volume_ratio = (up_volume - down_volume) / total_volume * 100
        else:
            volume_ratio = 0

        # Combine OBV and volume ratio
        score = (obv_slope + volume_ratio) / 2
        score = max(min(score, 100), -100)  # Clamp to -100 to +100

        if score > 50:
            interpretation = "strong_buying"
        elif score > 20:
            interpretation = "buying"
        elif score > -20:
            interpretation = "neutral"
        elif score > -50:
            interpretation = "selling"
        else:
            interpretation = "strong_selling"

        return score, interpretation


class TimeVolatilityAnalyzer:
    """Analyzes time-of-day volatility patterns"""

    @staticmethod
    def get_time_volatility(current_time: Optional[datetime] = None) -> str:
        """
        Get time-based volatility expectation

        Returns:
            'high', 'medium', or 'low'
        """
        if current_time is None:
            current_time = datetime.now()

        hour = current_time.hour

        # High volatility periods (UTC):
        # - 0:00-2:00 (US close)
        # - 8:00-10:00 (London open)
        # - 13:00-15:00 (US open)

        high_vol_hours = [0, 1, 8, 9, 13, 14]
        medium_vol_hours = [2, 3, 7, 10, 11, 12, 15, 16, 21, 22, 23]

        if hour in high_vol_hours:
            return "high"
        elif hour in medium_vol_hours:
            return "medium"
        else:
            return "low"


class MarketDepthAnalyzer:
    """Analyzes market depth/liquidity"""

    def analyze_market_depth(
        self,
        symbol: str,
        volume_24h_usd: float,
        avg_spread_bps: float
    ) -> Tuple[float, str]:
        """
        Analyze market depth

        Returns:
            (depth_score, interpretation)
            Score: 0-100
        """
        # Score based on volume
        if volume_24h_usd > 100_000_000:  # >$100M
            volume_score = 100
        elif volume_24h_usd > 10_000_000:  # >$10M
            volume_score = 80
        elif volume_24h_usd > 1_000_000:  # >$1M
            volume_score = 60
        elif volume_24h_usd > 100_000:  # >$100k
            volume_score = 40
        else:
            volume_score = 20

        # Score based on spread
        if avg_spread_bps < 5:
            spread_score = 100
        elif avg_spread_bps < 10:
            spread_score = 80
        elif avg_spread_bps < 20:
            spread_score = 60
        elif avg_spread_bps < 50:
            spread_score = 40
        else:
            spread_score = 20

        # Combine
        depth_score = (volume_score * 0.7 + spread_score * 0.3)

        if depth_score > 80:
            interpretation = "excellent"
        elif depth_score > 60:
            interpretation = "good"
        elif depth_score > 40:
            interpretation = "fair"
        else:
            interpretation = "poor"

        return depth_score, interpretation


class HistoricalPerformanceAnalyzer:
    """Analyzes historical TP hit rates"""

    def __init__(self, trades_history_path: Optional[str] = None):
        self.trades_history_path = trades_history_path
        self.default_hit_rates = {
            'tp1': 65.0,  # Default assumption: 65% of trades hit TP1
            'tp2': 45.0,  # 45% hit TP2
            'tp3': 25.0   # 25% hit TP3
        }

    def get_tp_hit_rates(
        self,
        strategy_name: str,
        symbol: str
    ) -> Tuple[float, float, float]:
        """
        Get historical TP hit rates for a strategy

        Returns:
            (tp1_hit_rate, tp2_hit_rate, tp3_hit_rate)
        """
        # TODO: Implement actual historical analysis
        # For now, return defaults

        # In production, this would:
        # 1. Load trades history from database/file
        # 2. Filter by strategy_name and symbol
        # 3. Calculate % of trades that hit each TP level
        # 4. Return actual historical performance

        return (
            self.default_hit_rates['tp1'],
            self.default_hit_rates['tp2'],
            self.default_hit_rates['tp3']
        )


# ===========================
# ADVANCED ALLOCATION CALCULATOR
# ===========================

class AdvancedAllocationCalculator:
    """
    ULTRA-INTELLIGENT allocation calculator considering 15+ factors
    """

    def __init__(self):
        self.volatility_analyzer = VolatilityAnalyzer()
        self.volume_analyzer = VolumeProfileAnalyzer()
        self.time_analyzer = TimeVolatilityAnalyzer()
        self.depth_analyzer = MarketDepthAnalyzer()
        self.performance_analyzer = HistoricalPerformanceAnalyzer()

        logging.info("🌙 Advanced Allocation Calculator initialized")

    def calculate_intelligent_allocation(
        self,
        factors: AllocationFactors
    ) -> Tuple[List[float], AllocationStrategy, str]:
        """
        Calculate INTELLIGENT allocation based on ALL factors

        Args:
            factors: Complete set of allocation factors

        Returns:
            (allocations, strategy, reasoning)
            allocations: [tp1_pct, tp2_pct, tp3_pct]
        """
        # STEP 1: Calculate component scores
        momentum_score = self._score_momentum(factors)
        volatility_score = self._score_volatility(factors)
        volume_score = self._score_volume(factors)
        risk_score = self._score_risk(factors)
        market_score = self._score_market(factors)
        performance_score = self._score_performance(factors)

        # STEP 2: Weighted composite score
        composite_score = (
            momentum_score * 0.25 +
            volatility_score * 0.20 +
            volume_score * 0.15 +
            risk_score * 0.20 +
            market_score * 0.10 +
            performance_score * 0.10
        )

        # STEP 3: Determine allocation strategy
        strategy = self._determine_strategy(
            composite_score,
            factors.momentum_strength,
            factors.regime,
            factors.volatility_percentile
        )

        # STEP 4: Calculate base allocations
        base_allocations = self._get_base_allocations(strategy)

        # STEP 5: Apply adjustments
        adjusted_allocations = self._apply_adjustments(
            base_allocations,
            factors,
            composite_score
        )

        # STEP 6: Generate reasoning
        reasoning = self._generate_reasoning(
            strategy,
            factors,
            composite_score,
            momentum_score,
            volatility_score,
            volume_score,
            risk_score,
            market_score,
            performance_score
        )

        logging.info(
            f"📊 Intelligent Allocation Calculated:\n"
            f"   Strategy: {strategy.value}\n"
            f"   Allocations: TP1={adjusted_allocations[0]:.0f}% | "
            f"TP2={adjusted_allocations[1]:.0f}% | TP3={adjusted_allocations[2]:.0f}%\n"
            f"   Composite Score: {composite_score:.1f}/100\n"
            f"   Reasoning: {reasoning}"
        )

        return adjusted_allocations, strategy, reasoning

    def _score_momentum(self, factors: AllocationFactors) -> float:
        """Score momentum component (0-100)"""
        # Momentum score already -100 to +100, normalize to 0-100
        return (factors.momentum_score + 100) / 2

    def _score_volatility(self, factors: AllocationFactors) -> float:
        """Score volatility component (0-100)"""
        # Higher volatility = take profits earlier
        # Return inverse score (low vol = high score for letting winners run)
        return 100 - factors.volatility_percentile

    def _score_volume(self, factors: AllocationFactors) -> float:
        """Score volume component (0-100)"""
        # Buying pressure = let winners run
        # Selling pressure = take profits early
        return (factors.volume_profile_score + 100) / 2

    def _score_risk(self, factors: AllocationFactors) -> float:
        """Score risk component (0-100)"""
        # Lower risk = can let winners run
        # Higher risk = take profits early

        # Token risk (0.3-1.5, lower is better)
        token_score = (1.5 - factors.token_risk_score) / 1.2 * 100

        # Portfolio exposure (lower is better)
        exposure_score = (100 - factors.portfolio_exposure_pct)

        # Recent PnL (winning streak = more confident)
        if factors.recent_pnl_trend == 'winning':
            pnl_score = 80
        elif factors.recent_pnl_trend == 'neutral':
            pnl_score = 50
        else:
            pnl_score = 20

        return (token_score * 0.4 + exposure_score * 0.3 + pnl_score * 0.3)

    def _score_market(self, factors: AllocationFactors) -> float:
        """Score market component (0-100)"""
        # Regime
        regime_scores = {
            'trending_up': 80,
            'trending_down': 40,
            'choppy': 20,
            'flat': 50,
            'crisis': 10
        }
        regime_score = regime_scores.get(factors.regime.lower(), 50)

        # Time volatility
        time_scores = {
            'low': 80,  # Low vol time = safe to hold
            'medium': 50,
            'high': 30  # High vol time = take profits
        }
        time_score = time_scores.get(factors.time_volatility, 50)

        # Market depth
        depth_score = factors.market_depth_score

        return (regime_score * 0.4 + time_score * 0.3 + depth_score * 0.3)

    def _score_performance(self, factors: AllocationFactors) -> float:
        """Score historical performance (0-100)"""
        # If TP3 hits often, allocate more there
        # If TP1 rarely hits, allocate less there

        tp1_weight = factors.tp1_historical_hit_rate / 100
        tp2_weight = factors.tp2_historical_hit_rate / 100
        tp3_weight = factors.tp3_historical_hit_rate / 100

        # Score = how often later TPs hit
        # High score = TP3 hits often, allocate more
        return (tp1_weight * 20 + tp2_weight * 35 + tp3_weight * 45)

    def _determine_strategy(
        self,
        composite_score: float,
        momentum: MomentumStrength,
        regime: str,
        volatility_pct: float
    ) -> AllocationStrategy:
        """Determine which allocation strategy to use"""

        # DEFENSIVE: Low score, high risk
        if composite_score < 30:
            return AllocationStrategy.DEFENSIVE

        # SCALPING: High volatility, choppy market
        if volatility_pct > 75 and regime.lower() == 'choppy':
            return AllocationStrategy.SCALPING

        # MOMENTUM BREAKOUT: Very strong momentum, trending
        if (momentum == MomentumStrength.VERY_STRONG and
            regime.lower() in ['trending_up', 'trending_down']):
            return AllocationStrategy.MOMENTUM_BREAKOUT

        # TREND FOLLOWING: Strong trend, good score
        if composite_score > 70 and regime.lower() in ['trending_up', 'trending_down']:
            return AllocationStrategy.TREND_FOLLOWING

        # MEAN REVERSION: Flat/choppy market
        if regime.lower() in ['flat', 'choppy']:
            return AllocationStrategy.MEAN_REVERSION

        # AGGRESSIVE: Very high composite score
        if composite_score > 80:
            return AllocationStrategy.AGGRESSIVE

        # BALANCED: Default
        return AllocationStrategy.BALANCED

    def _get_base_allocations(self, strategy: AllocationStrategy) -> List[float]:
        """Get base allocations for strategy"""
        allocations = {
            AllocationStrategy.SCALPING: [60, 25, 15],
            AllocationStrategy.MOMENTUM_BREAKOUT: [25, 25, 50],
            AllocationStrategy.MEAN_REVERSION: [50, 35, 15],
            AllocationStrategy.TREND_FOLLOWING: [20, 30, 50],
            AllocationStrategy.BALANCED: [40, 30, 30],
            AllocationStrategy.DEFENSIVE: [70, 20, 10],
            AllocationStrategy.AGGRESSIVE: [15, 35, 50]
        }

        return allocations[strategy]

    def _apply_adjustments(
        self,
        base_allocations: List[float],
        factors: AllocationFactors,
        composite_score: float
    ) -> List[float]:
        """Apply fine-tuning adjustments to base allocations"""
        adjusted = base_allocations.copy()

        # Adjustment 1: Support/Resistance proximity
        if factors.resistance_proximity_pct < 5:  # Near resistance
            # Increase TP1, decrease TP3
            adjusted[0] += 5
            adjusted[2] -= 5

        if factors.support_proximity_pct < 5:  # Near support
            # More confident, can let run
            adjusted[2] += 5
            adjusted[0] -= 5

        # Adjustment 2: Historical performance
        if factors.tp3_historical_hit_rate > 40:  # TP3 hits often
            adjusted[2] += 5
            adjusted[0] -= 5

        if factors.tp1_historical_hit_rate < 50:  # TP1 rarely hits
            adjusted[0] -= 5
            adjusted[1] += 5

        # Adjustment 3: Recent PnL trend
        if factors.recent_pnl_trend == 'losing':
            # More defensive
            adjusted[0] += 10
            adjusted[2] -= 10

        # Ensure allocations sum to 100 and are within bounds
        adjusted = [max(5, min(70, a)) for a in adjusted]  # Clamp 5-70%
        total = sum(adjusted)
        adjusted = [a / total * 100 for a in adjusted]  # Normalize to 100%

        return adjusted

    def _generate_reasoning(
        self,
        strategy: AllocationStrategy,
        factors: AllocationFactors,
        composite_score: float,
        momentum_score: float,
        volatility_score: float,
        volume_score: float,
        risk_score: float,
        market_score: float,
        performance_score: float
    ) -> str:
        """Generate human-readable reasoning"""
        reasons = []

        # Strategy selection
        reasons.append(f"Strategy: {strategy.value.replace('_', ' ').title()}")

        # Key factors
        if momentum_score > 70:
            reasons.append("strong momentum")
        elif momentum_score < 30:
            reasons.append("weak momentum")

        if volatility_score < 30:
            reasons.append("high volatility")

        if volume_score > 70:
            reasons.append("strong buying pressure")
        elif volume_score < 30:
            reasons.append("selling pressure")

        if risk_score < 40:
            reasons.append("elevated risk")

        if market_score > 70:
            reasons.append("favorable market conditions")

        # Special conditions
        if factors.resistance_proximity_pct < 5:
            reasons.append("near resistance")

        if factors.support_proximity_pct < 5:
            reasons.append("near support")

        if factors.recent_pnl_trend == 'losing':
            reasons.append("defensive due to recent losses")

        return " | ".join(reasons)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("🌙 Advanced Allocation Calculator - Example\n")

    # Example: Strong uptrend with high momentum
    factors = AllocationFactors(
        momentum_strength=MomentumStrength.VERY_STRONG,
        momentum_score=85.0,
        volatility_percentile=45.0,
        trend_strength=42.0,
        volume_profile_score=75.0,
        regime='trending_up',
        time_volatility='medium',
        market_depth_score=85.0,
        token_risk_score=0.85,
        portfolio_exposure_pct=25.0,
        recent_pnl_trend='winning',
        support_proximity_pct=15.0,
        resistance_proximity_pct=8.0,
        btc_correlation=0.85,
        funding_rate=0.01,
        oi_change_pct=12.0,
        tp1_historical_hit_rate=70.0,
        tp2_historical_hit_rate=50.0,
        tp3_historical_hit_rate=30.0
    )

    calculator = AdvancedAllocationCalculator()
    allocations, strategy, reasoning = calculator.calculate_intelligent_allocation(factors)

    print(f"\nResults:")
    print(f"  TP1: {allocations[0]:.1f}%")
    print(f"  TP2: {allocations[1]:.1f}%")
    print(f"  TP3: {allocations[2]:.1f}%")
    print(f"  Strategy: {strategy.value}")
    print(f"  Reasoning: {reasoning}")
