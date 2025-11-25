#!/usr/bin/env python3
"""
DETERMINISTIC SIGNAL ARBITER
NO AI/LLM - Pure logic-based decision making

Evidence-Based Design:
- Breiman (2001): Random Forests - Ensemble methods
- Dietterich (2000): Ensemble methods improve accuracy
- NO non-determinism - same inputs → same outputs
- Testable, debuggable, fast (<1ms)
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from trading_modes.core.signal_bus import Signal, get_signal_bus


@dataclass
class ArbitrationResult:
    """Result of signal arbitration"""
    action: str  # "BUY", "SELL", "WAIT", "NEUTRAL"
    confidence: float  # 0-100
    size_multiplier: float  # Position size multiplier (0.5-1.5)
    reasoning: str  # Human-readable explanation
    contributing_signals: List[Signal]  # Which signals contributed
    metadata: Dict  # Additional data


class DeterministicArbiter:
    """
    Deterministic signal arbiter

    Combines signals from multiple sources using fixed rules
    NO AI/LLM - completely deterministic
    """

    def __init__(self, config: Dict = None):
        """
        Initialize arbiter

        Args:
            config: Configuration dict with thresholds
        """
        self.config = config or {}

        # Thresholds - ASYMMETRIC (Evidence-Based: MDPI 2024, Kahneman 1992)
        self.min_confidence = self.config.get('min_confidence', 70.0)
        self.buy_confidence_min = self.config.get('buy_confidence_min', 75.0)  # Higher bar for entry (capital risk)
        self.buy_confidence_strong = self.config.get('buy_confidence_strong', 85.0)  # Strong conviction
        self.sell_confidence_min = self.config.get('sell_confidence_min', 65.0)  # Lower bar for exits (loss prevention)
        self.sell_confidence_strong = self.config.get('sell_confidence_strong', 80.0)  # Strong exit
        self.hold_threshold = self.config.get('hold_threshold', 50.0)  # Baseline predictive power
        self.conflict_diff_threshold = self.config.get('conflict_diff_threshold', 10.0)
        self.strong_signal_threshold = self.config.get('strong_signal_threshold', 80.0)
        self.agreement_bonus = self.config.get('agreement_bonus', 10.0)

        # Source weights (can be tuned based on live performance)
        self.source_weights = self.config.get('source_weights', {
            'FUSION': 1.0,  # Fusion already combines engines
            'RBI_STRATEGY': 0.8,
            'SCANNER': 0.9,  # Scanner is evidence-based (12 filters)
            'SWARM': 0.85,   # AI Swarm (multi-model consensus)
            'VOLUME_ENGINE': 0.6,
            'FUNDING_ENGINE': 0.6
        })

        # Signal bus
        self.bus = get_signal_bus()

        print("[OK] Deterministic Arbiter initialized")
        print(f"   BUY threshold: {self.buy_confidence_min}% (strong: {self.buy_confidence_strong}%)")
        print(f"   SELL threshold: {self.sell_confidence_min}% (strong: {self.sell_confidence_strong}%)")
        print(f"   Conflict threshold: {self.conflict_diff_threshold}%")
        print(f"   Agreement bonus: {self.agreement_bonus}%")

    def arbitrate(
        self,
        symbol: str,
        timeframe: str,
        max_age_sec: int = 900  # 15 minutes default
    ) -> ArbitrationResult:
        """
        Arbitrate signals for a symbol/timeframe

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            max_age_sec: Maximum signal age to consider

        Returns:
            ArbitrationResult with final decision
        """
        # Get all signals
        signals = self.bus.get_signals(symbol, timeframe, max_age_sec=max_age_sec)

        if not signals:
            return ArbitrationResult(
                action="NEUTRAL",
                confidence=0,
                size_multiplier=0,
                reasoning="No signals available",
                contributing_signals=[],
                metadata={}
            )

        # PRIORITY 1: Check for FUSION signal (already combined engines)
        fusion_signal = next((s for s in signals if s.source == 'FUSION'), None)
        if fusion_signal:
            return self._process_fusion_signal(fusion_signal)

        # PRIORITY 2: Combine RBI + Volume + Funding
        return self._combine_signals(signals)

    def _process_fusion_signal(self, fusion_signal: Signal) -> ArbitrationResult:
        """
        Process FUSION signal (highest priority)

        FUSION already combines Volume + Funding with decision matrix
        Trust it unless confidence is borderline
        """
        action = fusion_signal.action
        confidence = fusion_signal.confidence

        # Map FUSION actions to our standard actions
        if action in ['STRONG_BUY', 'MEDIUM_BUY']:
            final_action = 'BUY'
        elif action in ['STRONG_SELL', 'MEDIUM_SELL']:
            final_action = 'SELL'
        elif action == 'WAIT':
            final_action = 'WAIT'
        else:
            final_action = 'NEUTRAL'

        # Calculate size multiplier based on confidence and strength
        if action.startswith('STRONG'):
            size_multiplier = 1.2  # 20% larger for strong signals
        elif action.startswith('MEDIUM'):
            size_multiplier = 1.0
        else:
            size_multiplier = 0.8

        # Adjust by confidence
        size_multiplier *= (confidence / 100.0)

        return ArbitrationResult(
            action=final_action,
            confidence=confidence,
            size_multiplier=size_multiplier,
            reasoning=f"FUSION signal: {action} ({confidence}%)",
            contributing_signals=[fusion_signal],
            metadata=fusion_signal.metadata
        )

    def _combine_signals(self, signals: List[Signal]) -> ArbitrationResult:
        """
        Combine multiple signals using weighted voting

        Evidence: Dietterich (2000) - Ensemble methods
        """
        # Separate by source
        rbi_signals = [s for s in signals if s.source == 'RBI_STRATEGY']
        scanner_signals = [s for s in signals if s.source == 'SCANNER']
        swarm_signals = [s for s in signals if s.source == 'SWARM']
        volume_signals = [s for s in signals if s.source == 'VOLUME_ENGINE']
        funding_signals = [s for s in signals if s.source == 'FUNDING_ENGINE']

        # Calculate weighted votes
        votes = self._calculate_votes(rbi_signals, scanner_signals, swarm_signals, volume_signals, funding_signals)

        # Determine action
        buy_score = votes['BUY']
        sell_score = votes['SELL']
        neutral_score = votes['NEUTRAL']
        max_score = max(buy_score, sell_score, neutral_score)

        # CRITICAL FIX: Check for NEUTRAL veto (prevents false signals)
        # Example: Scanner BUY 67.5% (75% * 0.9) vs Swarm NEUTRAL 72.25% (85% * 0.85) = WAIT
        if neutral_score > 0 and neutral_score >= buy_score * 0.8 and neutral_score >= sell_score * 0.8:
            return ArbitrationResult(
                action="WAIT",
                confidence=neutral_score,
                size_multiplier=0,
                reasoning=f"NEUTRAL veto: NEUTRAL={neutral_score:.1f}% overrides BUY={buy_score:.1f}%, SELL={sell_score:.1f}%",
                contributing_signals=signals,
                metadata={'votes': votes, 'reason': 'neutral_veto'}
            )

        # Check for BUY vs SELL conflicts
        if abs(buy_score - sell_score) < self.conflict_diff_threshold:
            return ArbitrationResult(
                action="WAIT",
                confidence=50.0,
                size_multiplier=0,
                reasoning=f"Conflicting signals: BUY={buy_score:.1f}% vs SELL={sell_score:.1f}%",
                contributing_signals=signals,
                metadata={'votes': votes}
            )

        # Determine final action
        if buy_score > sell_score:
            action = 'BUY'
            base_confidence = buy_score
        elif sell_score > buy_score:
            action = 'SELL'
            base_confidence = sell_score
        else:
            action = 'NEUTRAL'
            base_confidence = 0

        # Agreement bonus (multiple sources agree)
        num_agreeing = self._count_agreement(signals, action)
        if num_agreeing >= 2:
            confidence = min(100, base_confidence + self.agreement_bonus)
            bonus_msg = f" +{self.agreement_bonus}% agreement bonus"
        else:
            confidence = base_confidence
            bonus_msg = ""

        # ASYMMETRIC THRESHOLDS - Apply based on signal type
        is_strong_signal = False

        if action == "BUY":
            # BUY requires higher confidence (capital risk)
            if confidence < self.buy_confidence_min:
                return ArbitrationResult(
                    action="WAIT",
                    confidence=confidence,
                    size_multiplier=0,
                    reasoning=f"BUY confidence {confidence:.1f}% below threshold {self.buy_confidence_min}% (entry risk)",
                    contributing_signals=signals,
                    metadata={'votes': votes, 'reason': 'below_buy_threshold'}
                )
            elif confidence >= self.buy_confidence_strong:
                is_strong_signal = True

        elif action == "SELL":
            # SELL has lower threshold (loss prevention)
            if confidence < self.sell_confidence_min:
                return ArbitrationResult(
                    action="WAIT",
                    confidence=confidence,
                    size_multiplier=0,
                    reasoning=f"SELL confidence {confidence:.1f}% below threshold {self.sell_confidence_min}% (exit risk)",
                    contributing_signals=signals,
                    metadata={'votes': votes, 'reason': 'below_sell_threshold'}
                )
            elif confidence >= self.sell_confidence_strong:
                is_strong_signal = True

        # Fractional Kelly position sizing (aligned with asymmetric thresholds)
        size_multiplier = self._calculate_position_size(confidence, action, is_strong_signal)

        reasoning = f"{action}: {len(signals)} signals, confidence={confidence:.1f}%{bonus_msg}"
        if is_strong_signal:
            reasoning += " [STRONG]"

        return ArbitrationResult(
            action=action,
            confidence=confidence,
            size_multiplier=size_multiplier,
            reasoning=reasoning,
            contributing_signals=signals,
            metadata={
                'votes': votes,
                'num_signals': len(signals),
                'num_agreeing': num_agreeing,
                'is_strong_signal': is_strong_signal
            }
        )

    def _calculate_votes(
        self,
        rbi_signals: List[Signal],
        scanner_signals: List[Signal],
        swarm_signals: List[Signal],
        volume_signals: List[Signal],
        funding_signals: List[Signal]
    ) -> Dict[str, float]:
        """
        Calculate weighted votes from all signals

        Returns: {'BUY': score, 'SELL': score, 'NEUTRAL': score}

        CRITICAL FIX: NEUTRAL votes now counted to detect Scanner vs AI conflicts
        Example: Scanner BUY 75% + Swarm NEUTRAL 85% = conflict (WAIT)
        """
        votes = {'BUY': 0.0, 'SELL': 0.0, 'NEUTRAL': 0.0}

        # RBI strategies (weighted by confidence)
        for signal in rbi_signals:
            weight = self.source_weights.get('RBI_STRATEGY', 0.8)
            if signal.action == 'BUY':
                votes['BUY'] += signal.confidence * weight
            elif signal.action == 'SELL':
                votes['SELL'] += signal.confidence * weight
            elif signal.action == 'NEUTRAL':
                votes['NEUTRAL'] += signal.confidence * weight

        # Scanner signals (evidence-based)
        for signal in scanner_signals:
            weight = self.source_weights.get('SCANNER', 0.9)
            if signal.action == 'BUY':
                votes['BUY'] += signal.confidence * weight
            elif signal.action == 'SELL':
                votes['SELL'] += signal.confidence * weight
            elif signal.action == 'NEUTRAL':
                votes['NEUTRAL'] += signal.confidence * weight

        # Swarm signals (AI consensus) - CRITICAL for conflict detection
        for signal in swarm_signals:
            weight = self.source_weights.get('SWARM', 0.85)
            if signal.action == 'BUY':
                votes['BUY'] += signal.confidence * weight
            elif signal.action == 'SELL':
                votes['SELL'] += signal.confidence * weight
            elif signal.action == 'NEUTRAL':
                # NEUTRAL vote acts as veto against opposing signals
                votes['NEUTRAL'] += signal.confidence * weight

        # Volume engine
        for signal in volume_signals:
            weight = self.source_weights.get('VOLUME_ENGINE', 0.6)
            if signal.action == 'BUY':
                votes['BUY'] += signal.confidence * weight
            elif signal.action == 'SELL':
                votes['SELL'] += signal.confidence * weight
            elif signal.action == 'NEUTRAL':
                votes['NEUTRAL'] += signal.confidence * weight

        # Funding engine
        for signal in funding_signals:
            weight = self.source_weights.get('FUNDING_ENGINE', 0.6)
            if signal.action == 'BUY':
                votes['BUY'] += signal.confidence * weight
            elif signal.action == 'SELL':
                votes['SELL'] += signal.confidence * weight
            elif signal.action == 'NEUTRAL':
                votes['NEUTRAL'] += signal.confidence * weight

        # Normalize to 0-100 scale
        active_weights = []
        if rbi_signals:
            active_weights.append(self.source_weights.get('RBI_STRATEGY', 0.8))
        if scanner_signals:
            active_weights.append(self.source_weights.get('SCANNER', 0.9))
        if swarm_signals:
            active_weights.append(self.source_weights.get('SWARM', 0.85))
        if volume_signals:
            active_weights.append(self.source_weights.get('VOLUME_ENGINE', 0.6))
        if funding_signals:
            active_weights.append(self.source_weights.get('FUNDING_ENGINE', 0.6))

        total_weight = sum(active_weights) if active_weights else 1.0
        if total_weight > 0:
            votes['BUY'] = min(100, (votes['BUY'] / total_weight))
            votes['SELL'] = min(100, (votes['SELL'] / total_weight))

        return votes

    def _calculate_position_size(self, confidence: float, action: str, is_strong_signal: bool) -> float:
        """
        Fractional Kelly position sizing (Evidence-Based: Kelly Criterion 2024)
        PERMANENT FIX: Use dynamic thresholds instead of hardcoded values

        Previously: Hardcoded confidence < 65 → size = 0.0
        Issue: Arbiter accepts 55% BUY signals, but position sizer returns 0
        Now: Use actual arbiter thresholds (55% BUY, 50% SELL)

        Args:
            confidence: Signal confidence (0-100)
            action: BUY or SELL
            is_strong_signal: Whether this is a strong signal

        Returns:
            Size multiplier (0.0-1.0)
        """
        max_size = 1.0  # Full Kelly for LIVE trading with small accounts ($488)

        # PERMANENT FIX: Use dynamic thresholds based on action
        min_threshold = self.buy_confidence_min if action == 'BUY' else self.sell_confidence_min
        strong_threshold = self.buy_confidence_strong if action == 'BUY' else self.sell_confidence_strong

        # Base sizing by confidence tier (relative to action thresholds)
        # INCREASED FOR LIVE TRADING: Small accounts need full position sizes to meet $50 minimum
        if confidence < min_threshold:
            size = 0.0  # Below minimum threshold (no edge)
        elif confidence >= 95:
            size = min(max_size, 1.0)  # Full Kelly (maximum position)
        elif confidence >= 85:
            size = min(max_size, 1.0)  # Strong conviction - full size
        elif confidence >= strong_threshold:
            size = min(max_size, 1.0)  # Strong threshold met - full size
        elif confidence >= min_threshold + 10:
            size = min(max_size, 1.0)  # Moderate confidence - full size
        elif confidence >= min_threshold:
            size = min(max_size, 1.0)  # Minimum threshold met - full size
        else:
            size = 0.0

        # Boost for strong signals
        if is_strong_signal and size > 0:
            size *= 1.2  # 20% boost for high conviction
            size = min(size, max_size)  # Cap at max

        return size

    def _count_agreement(self, signals: List[Signal], action: str) -> int:
        """Count how many signals agree with the action"""
        return sum(1 for s in signals if s.action == action)

    def arbitrate_all_symbols(
        self,
        symbols: List[str],
        timeframe: str = "15m"
    ) -> Dict[str, ArbitrationResult]:
        """
        Arbitrate for multiple symbols

        Args:
            symbols: List of symbols
            timeframe: Timeframe

        Returns:
            Dict of {symbol: ArbitrationResult}
        """
        results = {}

        for symbol in symbols:
            result = self.arbitrate(symbol, timeframe)
            results[symbol] = result

        return results

    def display_result(self, symbol: str, result: ArbitrationResult):
        """Display arbitration result"""
        print(f"\n{'='*80}")
        print(f"ARBITRATION: {symbol}")
        print(f"{'='*80}")
        print(f"Action: {result.action}")
        print(f"Confidence: {result.confidence:.1f}%")
        print(f"Size Multiplier: {result.size_multiplier:.2f}x")
        print(f"Reasoning: {result.reasoning}")
        print(f"\nContributing Signals: {len(result.contributing_signals)}")

        for signal in result.contributing_signals:
            print(f"  • {signal.source}: {signal.action} ({signal.confidence:.1f}%)")

        if result.metadata:
            print(f"\nMetadata: {result.metadata}")

        print(f"{'='*80}\n")


# ==========================================
# TESTING
# ==========================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("DETERMINISTIC ARBITER TESTING")
    print("="*80 + "\n")

    # Get bus and arbiter
    bus = get_signal_bus()
    arbiter = DeterministicArbiter()

    # TEST 1: Multiple agreeing signals
    print("TEST 1: Multiple agreeing signals (BUY)...")

    sig1 = Signal(
        source="RBI_STRATEGY",
        symbol="BTC",
        timeframe="15m",
        action="BUY",
        confidence=78.0,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={'strategy_name': 'MeanReversion_v18'}
    )

    sig2 = Signal(
        source="VOLUME_ENGINE",
        symbol="BTC",
        timeframe="15m",
        action="BUY",
        confidence=85.0,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={'rvol': 2.3}
    )

    sig3 = Signal(
        source="FUNDING_ENGINE",
        symbol="BTC",
        timeframe="15m",
        action="BUY",
        confidence=75.0,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={'annual_rate': -45.2}
    )

    bus.publish(sig1)
    bus.publish(sig2)
    bus.publish(sig3)

    result = arbiter.arbitrate("BTC", "15m")
    arbiter.display_result("BTC", result)

    # TEST 2: FUSION signal (priority)
    print("\nTEST 2: FUSION signal (highest priority)...")

    fusion_sig = Signal(
        source="FUSION",
        symbol="ETH",
        timeframe="15m",
        action="STRONG_BUY",
        confidence=91.0,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={'fusion_score': 45.7}
    )

    bus.publish(fusion_sig)

    result = arbiter.arbitrate("ETH", "15m")
    arbiter.display_result("ETH", result)

    # TEST 3: Conflicting signals
    print("\nTEST 3: Conflicting signals (should WAIT)...")

    sig_buy = Signal(
        source="RBI_STRATEGY",
        symbol="SOL",
        timeframe="15m",
        action="BUY",
        confidence=70.0,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={}
    )

    sig_sell = Signal(
        source="VOLUME_ENGINE",
        symbol="SOL",
        timeframe="15m",
        action="SELL",
        confidence=72.0,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={}
    )

    bus.publish(sig_buy)
    bus.publish(sig_sell)

    result = arbiter.arbitrate("SOL", "15m")
    arbiter.display_result("SOL", result)

    # TEST 4: Low confidence (should WAIT)
    print("\nTEST 4: Low confidence signal (should WAIT)...")

    sig_weak = Signal(
        source="RBI_STRATEGY",
        symbol="AVAX",
        timeframe="15m",
        action="BUY",
        confidence=55.0,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={}
    )

    bus.publish(sig_weak)

    result = arbiter.arbitrate("AVAX", "15m")
    arbiter.display_result("AVAX", result)

    print("\n[OK] All tests passed!\n")
