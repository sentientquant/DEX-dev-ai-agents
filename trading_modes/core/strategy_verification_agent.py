#!/usr/bin/env python3
"""
STRATEGY VERIFICATION AGENT V2 - Type-Safe Implementation

PERMANENT FIX:
✅ Numpy bool serialization properly handled (np.bool_ before bool check)
✅ Type hints added for all methods
✅ Ready for Result type integration (Phase 4)

Verifies trading strategy behavior using:
1. Technical Snapshot: Real market indicators (EMA, RSI, ATR, Bollinger, Volume)
2. Swarm Consensus: 5 AI models analyze strategy logic vs actual market conditions
3. Logic Checkmate: Verify strategy parameters match market reality

Built for RBI Research-Based Trading Flow
Based on Moon Dev's BTC Signal Agent + Swarm Agent patterns
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text
from pathlib import Path
import sys

# Add project root
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.agents.swarm_agent import SwarmAgent


class StrategyVerificationAgent:
    """
    Verifies if trading strategies are working correctly or broken
    using technical analysis + multi-model AI consensus
    """

    def __init__(self):
        """Initialize with Swarm Agent for multi-model consensus"""
        self.swarm = SwarmAgent()
        cprint("\n[INIT] Strategy Verification Agent initialized", "cyan")
        cprint("   → Technical Snapshot Builder: READY", "green")
        cprint("   → Swarm Consensus (5 AI models): READY", "green")

    def verify_strategy(
        self,
        strategy_name: str,
        symbol: str,
        cycles_run: int,
        signals_generated: int,
        ohlcv_data: pd.DataFrame,
        recent_reasoning: List[str],
        strategy_params: Dict = None,
        strategy_instance: Any = None  # NEW: Pass actual strategy object
    ) -> Dict[str, Any]:
        """
        Comprehensive strategy verification

        Args:
            strategy_name: Name of strategy
            symbol: Trading symbol
            cycles_run: Number of cycles executed
            signals_generated: Signals produced
            ohlcv_data: Recent OHLCV data
            recent_reasoning: List of strategy reasoning messages
            strategy_params: Strategy parameters (brackets, thresholds, etc.)

        Returns:
            {
                'verdict': 'STRATEGY_WORKING' | 'STRATEGY_BROKEN' | 'NEEDS_TUNING',
                'confidence': 0-100,
                'reasoning': 'Multi-model consensus explanation',
                'market_state': 'CONSOLIDATION' | 'TRENDING' | 'VOLATILE',
                'action_required': 'NONE' | 'FIX_LOGIC' | 'ADJUST_PARAMS',
                'technical_snapshot': {...},
                'swarm_consensus': {...}
            }
        """
        cprint(f"\n[VERIFY] Starting comprehensive strategy verification...", "cyan", attrs=['bold'])
        cprint(f"   Strategy: {strategy_name}", "white")
        cprint(f"   Symbol: {symbol}", "white")
        cprint(f"   Cycles: {cycles_run} | Signals: {signals_generated}", "white")

        # Step 0: Extract strategy's actual indicator settings
        cprint("\n[STEP 0/3] Extracting strategy indicator settings...", "yellow")
        strategy_settings = self._extract_strategy_settings(strategy_instance, strategy_name)
        if strategy_settings:
            cprint(f"   [OK] Using strategy's actual indicator settings:", "green")
            cprint(f"       ATR Period: {strategy_settings.get('atr_period', 'N/A')}", "white")
            cprint(f"       MA Period: {strategy_settings.get('ma_period', 'N/A')}", "white")
            cprint(f"       RSI Period: {strategy_settings.get('rsi_period', 'N/A')}", "white")
            cprint(f"       ATR Multiplier: {strategy_settings.get('multiplier', 'N/A')}", "white")
        else:
            cprint(f"   [WARN] Could not extract strategy settings, using generic defaults", "yellow")

        # Step 1: Build technical snapshot using STRATEGY'S settings
        cprint("\n[STEP 1/3] Building technical snapshot with strategy's indicators...", "yellow")
        tech_snapshot = self._build_technical_snapshot(
            ohlcv_data,
            symbol,
            strategy_settings  # Use strategy's actual settings!
        )

        # Step 2: Verify strategy logic against market reality
        cprint("\n[STEP 2/3] Verifying strategy logic vs market conditions...", "yellow")
        logic_check = self._verify_strategy_logic(
            strategy_name,
            strategy_params,
            tech_snapshot,
            recent_reasoning
        )

        # Step 3: Get multi-model consensus verdict
        cprint("\n[STEP 3/3] Querying AI Swarm for consensus verdict...", "yellow")
        swarm_verdict = self._get_swarm_consensus(
            strategy_name,
            symbol,
            cycles_run,
            signals_generated,
            tech_snapshot,
            recent_reasoning,
            strategy_params,
            logic_check
        )

        # Combine results
        final_verdict = self._synthesize_verdict(tech_snapshot, logic_check, swarm_verdict)

        cprint(f"\n[COMPLETE] Verification complete!", "green", attrs=['bold'])
        return final_verdict

    def _extract_strategy_settings(self, strategy_instance: Any, strategy_name: str) -> Dict[str, Any]:
        """
        Extract indicator settings from strategy instance

        This allows us to analyze using the STRATEGY'S actual settings,
        not generic defaults!
        """
        settings = {}

        if strategy_instance is None:
            return settings

        try:
            # Try to extract common strategy parameters
            if hasattr(strategy_instance, 'atr_period'):
                settings['atr_period'] = strategy_instance.atr_period
            if hasattr(strategy_instance, 'ma_period'):
                settings['ma_period'] = strategy_instance.ma_period
            if hasattr(strategy_instance, 'rsi_period'):
                settings['rsi_period'] = strategy_instance.rsi_period
            if hasattr(strategy_instance, 'multiplier'):
                settings['multiplier'] = strategy_instance.multiplier
            if hasattr(strategy_instance, 'min_atr_pct'):
                settings['min_atr_pct'] = strategy_instance.min_atr_pct
            if hasattr(strategy_instance, 'max_atr_pct'):
                settings['max_atr_pct'] = strategy_instance.max_atr_pct

            # For EMA-based strategies
            if hasattr(strategy_instance, 'ema_fast'):
                settings['ema_fast'] = strategy_instance.ema_fast
            if hasattr(strategy_instance, 'ema_slow'):
                settings['ema_slow'] = strategy_instance.ema_slow

            # For RSI thresholds
            if hasattr(strategy_instance, 'rsi_overbought'):
                settings['rsi_overbought'] = strategy_instance.rsi_overbought
            if hasattr(strategy_instance, 'rsi_oversold'):
                settings['rsi_oversold'] = strategy_instance.rsi_oversold

        except Exception as e:
            cprint(f"   [WARN] Error extracting strategy settings: {e}", "yellow")

        return settings

    def _build_technical_snapshot(
        self,
        ohlcv_data: pd.DataFrame,
        symbol: str,
        strategy_settings: Dict = None
    ) -> Dict[str, Any]:
        """Build comprehensive technical snapshot using STRATEGY'S indicator settings"""
        closes = ohlcv_data['close'].values[-100:]  # Last 100 candles
        highs = ohlcv_data['high'].values[-100:]
        lows = ohlcv_data['low'].values[-100:]
        volumes = ohlcv_data['volume'].values[-100:] if 'volume' in ohlcv_data.columns else None

        current_price = closes[-1]

        # Use strategy's settings or fallback to defaults
        if strategy_settings is None:
            strategy_settings = {}

        # Get strategy-specific periods (or use defaults)
        atr_period = strategy_settings.get('atr_period', 14)
        ma_period = strategy_settings.get('ma_period', 50)
        rsi_period = strategy_settings.get('rsi_period', 14)
        atr_multiplier = strategy_settings.get('multiplier', 2.0)

        # Calculate MA (strategy's MA period)
        ma_value = self._sma(closes, ma_period)[-1]

        # Calculate secondary MA for trend detection (if using SMA, add longer period)
        ma_long_period = ma_period * 4  # e.g., if strategy uses MA(50), use MA(200) for trend
        ma_long = self._sma(closes, ma_long_period)[-1] if len(closes) >= ma_long_period else ma_value

        # RSI (strategy's RSI period)
        rsi_value = self._rsi(closes, rsi_period)[-1]

        # ATR (strategy's ATR period)
        atr_value = self._atr(highs, lows, closes, atr_period)[-1]
        atr_pct = (atr_value / current_price * 100) if current_price != 0 else 0

        # Calculate brackets using STRATEGY'S multiplier (THIS IS CRITICAL!)
        prev_close = closes[-2]  # Use previous close as bracket reference (matches strategy logic)
        upper_bracket = prev_close + (atr_multiplier * atr_value)
        lower_bracket = prev_close - (atr_multiplier * atr_value)

        # Bollinger Bands (use generic 20-period for reference)
        bb_mid = self._sma(closes, 20)[-1]
        bb_std = self._stddev(closes, 20)[-1]
        bb_upper = bb_mid + (2 * bb_std)
        bb_lower = bb_mid - (2 * bb_std)

        # Trend detection using strategy's MA
        trend = self._detect_trend(closes, ma_value, ma_long)

        # Volatility
        price_std = np.std(closes[-20:])
        price_mean = np.mean(closes[-20:])
        volatility_cv = (price_std / price_mean * 100) if price_mean != 0 else 0

        # Price movement
        price_change_20_candles = ((closes[-1] - closes[-20]) / closes[-20] * 100)

        # Volume (if available)
        vol_ratio = None
        if volumes is not None and len(volumes) > 20:
            avg_volume = np.mean(volumes[-20:])
            vol_ratio = volumes[-1] / avg_volume if avg_volume != 0 else 1.0

        # Get strategy-specific RSI thresholds for interpretation
        rsi_overbought = strategy_settings.get('rsi_overbought', 70)
        rsi_oversold = strategy_settings.get('rsi_oversold', 30)

        snapshot = {
            'symbol': symbol,
            'current_price': current_price,
            'trend': trend,
            # STRATEGY-SPECIFIC INDICATORS (not generic!)
            'ma_period': ma_period,
            'ma_value': ma_value,
            'price_vs_ma': 'ABOVE' if current_price > ma_value else 'BELOW',
            'rsi_period': rsi_period,
            'rsi_value': rsi_value,
            'rsi_state': self._interpret_rsi_custom(rsi_value, rsi_overbought, rsi_oversold),
            'rsi_overbought_threshold': rsi_overbought,
            'rsi_oversold_threshold': rsi_oversold,
            'atr_period': atr_period,
            'atr_value': atr_value,
            'atr_pct': atr_pct,
            'atr_multiplier': atr_multiplier,
            # STRATEGY'S ACTUAL BRACKETS (critical!)
            'upper_bracket': upper_bracket,
            'lower_bracket': lower_bracket,
            'bracket_width_pct': ((upper_bracket - lower_bracket) / current_price * 100),
            'price_to_upper_pct': ((upper_bracket - current_price) / current_price * 100),
            'price_to_lower_pct': ((current_price - lower_bracket) / current_price * 100),
            'price_in_brackets': lower_bracket <= current_price <= upper_bracket,
            # Reference indicators (Bollinger Bands for comparison)
            'bb_upper': bb_upper,
            'bb_mid': bb_mid,
            'bb_lower': bb_lower,
            'bb_position': self._bollinger_position(current_price, bb_mid, bb_upper, bb_lower),
            'volatility_cv': volatility_cv,
            'volatility_state': 'HIGH' if volatility_cv > 2.0 else 'LOW' if volatility_cv < 0.5 else 'NORMAL',
            'price_change_20c': price_change_20_candles,
            'volume_ratio': vol_ratio,
            'volume_state': self._interpret_volume(vol_ratio) if vol_ratio else 'UNKNOWN',
            # Strategy settings used (for verification)
            'strategy_settings': strategy_settings
        }

        cprint(f"   [OK] Technical snapshot built using STRATEGY'S settings:", "green")
        cprint(f"       Price: ${current_price:.2f} | Trend: {trend}", "white")
        cprint(f"       MA({ma_period}): ${ma_value:.2f} | RSI({rsi_period}): {rsi_value:.1f}", "white")
        cprint(f"       ATR({atr_period}): {atr_pct:.2f}% | Brackets: [{lower_bracket:.2f}, {upper_bracket:.2f}]", "white")
        cprint(f"       Volatility: {volatility_cv:.2f}% ({snapshot['volatility_state']})", "white")

        return snapshot

    def _verify_strategy_logic(
        self,
        strategy_name: str,
        strategy_params: Dict,
        tech_snapshot: Dict,
        recent_reasoning: List[str]
    ) -> Dict[str, Any]:
        """Verify strategy logic against actual market conditions using STRATEGY'S indicators"""
        issues = []
        warnings = []
        optimizations = []  # NEW: Track potential optimizations

        # For VolatilityBracket strategies - use brackets from snapshot (calculated with strategy's settings!)
        if 'VolatilityBracket' in strategy_name:
            current_price = tech_snapshot['current_price']
            upper_bracket = tech_snapshot['upper_bracket']
            lower_bracket = tech_snapshot['lower_bracket']
            bracket_width_pct = tech_snapshot['bracket_width_pct']
            atr_pct = tech_snapshot['atr_pct']
            atr_multiplier = tech_snapshot['atr_multiplier']
            price_in_brackets = tech_snapshot['price_in_brackets']

            # Verify bracket calculations match strategy logic
            cprint(f"   [CHECK] Verifying VolatilityBracket logic...", "cyan")
            cprint(f"       Brackets: ${lower_bracket:.2f} - ${upper_bracket:.2f} (width: {bracket_width_pct:.2f}%)", "white")
            cprint(f"       ATR: {atr_pct:.2f}% | Multiplier: {atr_multiplier}x", "white")
            cprint(f"       Price in brackets: {price_in_brackets}", "white")

            # Check if brackets are reasonable given current volatility
            # Bracket width should be ~2x to 5x the ATR%
            expected_bracket_width = atr_pct * 2 * atr_multiplier  # 2 * ATR * multiplier (upper + lower)

            if bracket_width_pct > (atr_pct * 15):
                # Brackets extremely wide - price unlikely to ever reach
                issues.append(f"Brackets critically too wide ({bracket_width_pct:.1f}%) vs ATR ({atr_pct:.2f}% * {atr_multiplier}x = {atr_pct*atr_multiplier:.2f}%) - price will never reach brackets")
                optimizations.append(f"REDUCE atr_multiplier from {atr_multiplier}x to {atr_multiplier * 0.6:.1f}x")
            elif bracket_width_pct > (atr_pct * 8):
                # Brackets too wide for current volatility
                warnings.append(f"Brackets too wide ({bracket_width_pct:.1f}%) for current ATR ({atr_pct:.2f}%) - may generate few signals")
                optimizations.append(f"Consider reducing atr_multiplier from {atr_multiplier}x to {atr_multiplier * 0.75:.1f}x")
            elif bracket_width_pct < (atr_pct * 0.8):
                # Brackets too narrow - will generate excessive signals
                warnings.append(f"Brackets too narrow ({bracket_width_pct:.1f}%) vs ATR ({atr_pct:.2f}%) - may generate excessive whipsaw signals")
                optimizations.append(f"Consider increasing atr_multiplier from {atr_multiplier}x to {atr_multiplier * 1.3:.1f}x")

            # Check if low volatility + wide brackets = no signals expected
            if tech_snapshot['volatility_state'] == 'LOW' and bracket_width_pct > 3.0:
                warnings.append(f"Low volatility ({tech_snapshot['volatility_cv']:.2f}%) + wide brackets ({bracket_width_pct:.1f}%) = strategy correctly waiting")

            # Check ATR thresholds if available
            if 'min_atr_pct' in tech_snapshot['strategy_settings'] and 'max_atr_pct' in tech_snapshot['strategy_settings']:
                min_atr = tech_snapshot['strategy_settings']['min_atr_pct'] * 100
                max_atr = tech_snapshot['strategy_settings']['max_atr_pct'] * 100

                if atr_pct < min_atr:
                    warnings.append(f"ATR {atr_pct:.2f}% below minimum threshold {min_atr:.2f}% - strategy filtering out signals")
                elif atr_pct > max_atr:
                    warnings.append(f"ATR {atr_pct:.2f}% above maximum threshold {max_atr:.2f}% - strategy filtering out signals (too volatile)")

        # Check RSI logic using STRATEGY'S thresholds
        rsi_value = tech_snapshot['rsi_value']
        rsi_overbought = tech_snapshot.get('rsi_overbought_threshold', 70)
        rsi_oversold = tech_snapshot.get('rsi_oversold_threshold', 30)

        if 'RSI' in ' '.join(recent_reasoning):
            if rsi_value > rsi_overbought and 'LONG' in ' '.join(recent_reasoning):
                warnings.append(f"RSI overbought (>{rsi_overbought}) but strategy considering LONG")
            if rsi_value < rsi_oversold and 'SHORT' in ' '.join(recent_reasoning):
                warnings.append(f"RSI oversold (<{rsi_oversold}) but strategy considering SHORT")

        logic_check = {
            'has_issues': len(issues) > 0,
            'issues': issues,
            'warnings': warnings,
            'optimizations': optimizations,  # NEW: Suggested parameter changes
            'logic_verdict': 'BROKEN' if issues else 'WORKING'
        }

        if issues:
            cprint(f"   [!] Logic issues detected: {len(issues)}", "red")
            for issue in issues:
                cprint(f"       - {issue}", "red")
        elif warnings:
            cprint(f"   [!] Logic warnings: {len(warnings)}", "yellow")
            for warning in warnings:
                cprint(f"       - {warning}", "yellow")
        else:
            cprint(f"   [OK] Logic verification passed", "green")

        if optimizations:
            cprint(f"   [💡] Optimization suggestions: {len(optimizations)}", "cyan")
            for opt in optimizations:
                cprint(f"       → {opt}", "cyan")

        return logic_check

    def _get_swarm_consensus(
        self,
        strategy_name: str,
        symbol: str,
        cycles: int,
        signals: int,
        tech_snapshot: Dict,
        recent_reasoning: List[str],
        strategy_params: Dict,
        logic_check: Dict
    ) -> Dict[str, Any]:
        """Get multi-model consensus on strategy health"""
        import json
        import numpy as np

        # Convert numpy types and booleans to native Python types for JSON serialization
        def convert_to_serializable(obj):
            """Recursively convert numpy types and booleans to native Python types"""
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, np.bool_):
                # CRITICAL: Handle numpy bool BEFORE regular bool check
                # numpy.bool_ doesn't serialize to JSON properly
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (bool, np.bool_)):
                # Handle both Python bool and numpy bool (fallback)
                return bool(obj)
            elif obj is None:
                return None
            else:
                return obj

        # Convert all data to serializable format
        tech_snapshot_serializable = convert_to_serializable(tech_snapshot)
        strategy_params_serializable = convert_to_serializable(strategy_params) if strategy_params else None
        logic_check_serializable = convert_to_serializable(logic_check)

        # Build comprehensive prompt for swarm
        system_prompt = """You are an expert quantitative trading strategy auditor.

Your job is to determine if a trading strategy is:
1. **STRATEGY_WORKING**: Logic is correct, market just doesn't meet entry criteria (wait patiently)
2. **STRATEGY_BROKEN**: Logic has bugs or impossible conditions (needs fixing)
3. **NEEDS_TUNING**: Logic correct but parameters too conservative/aggressive (adjust settings)

Analyze the technical data objectively. Consider if the strategy's behavior matches market reality."""

        user_prompt = f"""Analyze this trading strategy performance:

**STRATEGY**: {strategy_name}
**SYMBOL**: {symbol}
**PERFORMANCE**:
- Cycles Run: {cycles}
- Signals Generated: {signals}
- Signal Rate: {(signals/cycles*100) if cycles > 0 else 0:.1f}%

**ACTUAL MARKET CONDITIONS** (Real Technical Data):
{json.dumps(tech_snapshot_serializable, indent=2)}

**STRATEGY REASONING** (Last 5 decisions):
{chr(10).join(f"  - {r}" for r in recent_reasoning[-5:])}

**STRATEGY PARAMETERS**:
{json.dumps(strategy_params_serializable, indent=2) if strategy_params_serializable else "Not provided"}

**LOGIC VERIFICATION**:
{json.dumps(logic_check_serializable, indent=2)}

**YOUR TASK**:
Provide a verdict in this EXACT format:

VERDICT: [STRATEGY_WORKING | STRATEGY_BROKEN | NEEDS_TUNING]
CONFIDENCE: [0-100]
MARKET_STATE: [CONSOLIDATION | TRENDING | VOLATILE]
REASONING: [2-3 sentence explanation linking technical data to strategy behavior]
ACTION_REQUIRED: [NONE | FIX_LOGIC | ADJUST_PARAMS]

Be objective. If market is low volatility and strategy is correctly waiting, say STRATEGY_WORKING.
If brackets are impossible to reach or logic has bugs, say STRATEGY_BROKEN.
If parameters are too conservative for current market, say NEEDS_TUNING."""

        # Query swarm
        result = self.swarm.query(user_prompt, system_prompt)

        cprint(f"   [OK] Swarm consensus generated", "green")
        cprint(f"       Models queried: {result['metadata']['total_models']}", "white")
        cprint(f"       Successful responses: {result['metadata']['successful_responses']}", "white")

        return {
            'consensus_summary': result.get('consensus_summary', ''),
            'individual_responses': result.get('responses', {}),
            'model_mapping': result.get('model_mapping', {}),
            'metadata': result.get('metadata', {})
        }

    def _synthesize_verdict(
        self,
        tech_snapshot: Dict,
        logic_check: Dict,
        swarm_verdict: Dict
    ) -> Dict[str, Any]:
        """Synthesize final verdict from all verification sources"""
        # Parse consensus summary to extract verdict
        consensus = swarm_verdict['consensus_summary']

        # Default verdict structure
        final = {
            'verdict': 'STRATEGY_WORKING',
            'confidence': 70,
            'reasoning': consensus,
            'market_state': tech_snapshot.get('trend', 'UNKNOWN'),
            'action_required': 'NONE',
            'technical_snapshot': tech_snapshot,
            'swarm_consensus': swarm_verdict,
            'logic_check': logic_check
        }

        # Override based on logic check
        if logic_check['has_issues']:
            final['verdict'] = 'STRATEGY_BROKEN'
            final['action_required'] = 'FIX_LOGIC'
            final['confidence'] = 90
            final['reasoning'] = f"Logic issues detected: {'; '.join(logic_check['issues'])}"
        elif logic_check['warnings']:
            final['verdict'] = 'NEEDS_TUNING'
            final['action_required'] = 'ADJUST_PARAMS'
            final['confidence'] = 75
            final['reasoning'] = f"Logic warnings: {'; '.join(logic_check['warnings'])}. {consensus}"

        # Parse swarm consensus for verdict keywords
        if 'STRATEGY_BROKEN' in consensus.upper():
            final['verdict'] = 'STRATEGY_BROKEN'
            final['action_required'] = 'FIX_LOGIC'
        elif 'NEEDS_TUNING' in consensus.upper() or 'TOO CONSERVATIVE' in consensus.upper():
            final['verdict'] = 'NEEDS_TUNING'
            final['action_required'] = 'ADJUST_PARAMS'

        # Map market state from technical snapshot
        if tech_snapshot['volatility_state'] == 'LOW' and abs(tech_snapshot['price_change_20c']) < 1.0:
            final['market_state'] = 'CONSOLIDATION'
        elif tech_snapshot['volatility_state'] == 'HIGH':
            final['market_state'] = 'VOLATILE'
        elif tech_snapshot['trend'] in ['UPTREND', 'DOWNTREND']:
            final['market_state'] = 'TRENDING'

        return final

    # ============================================================================
    # TECHNICAL INDICATOR UTILITIES (from BTC Signal Agent)
    # ============================================================================

    def _ema(self, values: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if not values or len(values) < period:
            return [values[-1]] if values else [0.0]
        ema_values = []
        k = 2 / (period + 1)
        for i, price in enumerate(values):
            if i == 0:
                ema_values.append(price)
            else:
                ema_values.append(price * k + ema_values[-1] * (1 - k))
        return ema_values

    def _rsi(self, values: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index"""
        if len(values) < period + 1:
            return [50.0] * len(values)

        deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
        gains = [max(d, 0) for d in deltas]
        losses = [abs(min(d, 0)) for d in deltas]

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        rsis = [50.0] * period

        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            if avg_loss == 0:
                rsi_val = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi_val = 100 - (100 / (1 + rs))
            rsis.append(rsi_val)

        return [50.0] + rsis

    def _atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
        """Average True Range"""
        if len(closes) < period + 1:
            return [0.0] * len(closes)

        trs = []
        for i in range(len(closes)):
            if i == 0:
                tr = highs[i] - lows[i]
            else:
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1])
                )
            trs.append(tr)

        atrs = [0.0] * period
        first_atr = sum(trs[1:period + 1]) / period
        atrs.append(first_atr)

        for i in range(period + 1, len(trs)):
            prev_atr = atrs[-1]
            curr_atr = (prev_atr * (period - 1) + trs[i]) / period
            atrs.append(curr_atr)

        while len(atrs) < len(closes):
            atrs.insert(0, 0.0)

        return atrs

    def _sma(self, values: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(values) < period:
            return [sum(values) / len(values)] * len(values) if values else [0.0]
        out = []
        for i in range(len(values)):
            if i < period - 1:
                out.append(sum(values[:i + 1]) / (i + 1))
            else:
                window = values[i - period + 1:i + 1]
                out.append(sum(window) / period)
        return out

    def _stddev(self, values: List[float], period: int) -> List[float]:
        """Rolling Standard Deviation"""
        import math
        if len(values) < period:
            mean = sum(values) / len(values) if values else 0.0
            return [math.sqrt(sum((v - mean) ** 2 for v in values) / len(values)) if values else 0.0] * len(values)
        out = []
        for i in range(len(values)):
            if i < period - 1:
                window = values[:i + 1]
            else:
                window = values[i - period + 1:i + 1]
            m = sum(window) / len(window)
            var = sum((v - m) ** 2 for v in window) / len(window)
            out.append(math.sqrt(var))
        return out

    def _detect_trend(self, closes: List[float], ema_50: float, ema_200: float) -> str:
        """Detect trend based on EMAs and price action"""
        if len(closes) < 5:
            return "UNKNOWN"

        price = closes[-1]
        recent_slope = closes[-1] - closes[-5]

        if price > ema_200 and ema_50 > ema_200 and recent_slope > 0:
            return "UPTREND"
        elif price < ema_200 and ema_50 < ema_200 and recent_slope < 0:
            return "DOWNTREND"
        else:
            return "CONSOLIDATION"

    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value using generic thresholds"""
        if rsi >= 70:
            return "OVERBOUGHT"
        elif rsi <= 30:
            return "OVERSOLD"
        elif rsi >= 60:
            return "BULLISH"
        elif rsi <= 40:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _interpret_rsi_custom(self, rsi: float, overbought: float, oversold: float) -> str:
        """Interpret RSI value using STRATEGY'S thresholds"""
        if rsi >= overbought:
            return "OVERBOUGHT"
        elif rsi <= oversold:
            return "OVERSOLD"
        elif rsi >= 55:
            return "BULLISH"
        elif rsi <= 45:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _bollinger_position(self, price: float, mid: float, upper: float, lower: float) -> str:
        """Determine price position relative to Bollinger Bands"""
        if upper == lower:
            return "MIDDLE"
        if price >= upper:
            return "UPPER_BAND"
        if price <= lower:
            return "LOWER_BAND"
        if price > mid:
            return "UPPER_HALF"
        return "LOWER_HALF"

    def _interpret_volume(self, vol_ratio: float) -> str:
        """Interpret volume ratio"""
        if vol_ratio >= 1.5:
            return "HIGH"
        elif vol_ratio <= 0.7:
            return "LOW"
        else:
            return "NORMAL"

    def display_verification_result(self, result: Dict):
        """Display verification result with color coding"""
        verdict = result['verdict']
        confidence = result['confidence']
        reasoning = result['reasoning']
        market_state = result['market_state']
        action = result['action_required']

        cprint("\n" + "="*80, "cyan", attrs=['bold'])
        cprint("🔍 STRATEGY VERIFICATION RESULT (MULTI-MODEL CONSENSUS)", "cyan", attrs=['bold'])
        cprint("="*80, "cyan", attrs=['bold'])

        # Verdict with color
        if verdict == 'STRATEGY_WORKING':
            verdict_color = "green"
            verdict_icon = "✅"
        elif verdict == 'STRATEGY_BROKEN':
            verdict_color = "red"
            verdict_icon = "🔴"
        else:
            verdict_color = "yellow"
            verdict_icon = "⚠️"

        cprint(f"\n{verdict_icon} VERDICT: {verdict} (Confidence: {confidence}%)", verdict_color, attrs=['bold'])
        cprint(f"📊 Market State: {market_state}", "cyan")
        cprint(f"💡 Consensus Reasoning:\n   {reasoning}", "white")

        # Technical snapshot summary
        tech = result['technical_snapshot']
        cprint(f"\n📈 Technical Snapshot (Using Strategy's Settings):", "yellow")
        cprint(f"   Price: ${tech['current_price']:.2f} | Trend: {tech['trend']}", "white")
        cprint(f"   MA({tech['ma_period']}): ${tech['ma_value']:.2f} | RSI({tech['rsi_period']}): {tech['rsi_value']:.1f} ({tech['rsi_state']})", "white")
        cprint(f"   ATR({tech['atr_period']}): {tech['atr_pct']:.2f}% (Multiplier: {tech['atr_multiplier']}x)", "white")
        cprint(f"   Brackets: [${tech['lower_bracket']:.2f}, ${tech['upper_bracket']:.2f}] | Width: {tech['bracket_width_pct']:.2f}%", "white")
        cprint(f"   Volatility: {tech['volatility_cv']:.2f}% ({tech['volatility_state']})", "white")

        # Logic check
        if result['logic_check']['has_issues']:
            cprint(f"\n🔴 Logic Issues Detected:", "red", attrs=['bold'])
            for issue in result['logic_check']['issues']:
                cprint(f"   - {issue}", "red")
        elif result['logic_check']['warnings']:
            cprint(f"\n⚠️  Logic Warnings:", "yellow")
            for warning in result['logic_check']['warnings']:
                cprint(f"   - {warning}", "yellow")

        # Optimization suggestions
        if result['logic_check'].get('optimizations'):
            cprint(f"\n💡 Optimization Suggestions (Based on Strategy's Settings):", "cyan", attrs=['bold'])
            for opt in result['logic_check']['optimizations']:
                cprint(f"   → {opt}", "cyan")

        # Action required
        if action == 'NONE':
            cprint(f"\n✅ Action Required: {action} - Continue monitoring", "green")
        elif action == 'FIX_LOGIC':
            cprint(f"\n🔴 Action Required: {action} - Strategy needs debugging", "red", attrs=['bold'])
        else:
            cprint(f"\n⚠️  Action Required: {action} - Consider parameter optimization", "yellow")

        # Swarm details
        swarm_meta = result['swarm_consensus']['metadata']
        cprint(f"\n🤖 Swarm Consensus:", "magenta")
        cprint(f"   Models Queried: {swarm_meta['total_models']}", "white")
        cprint(f"   Successful Responses: {swarm_meta['successful_responses']}", "white")
        cprint(f"   Analysis Time: {swarm_meta['total_time']}s", "white")

        cprint("\n" + "="*80 + "\n", "cyan", attrs=['bold'])


# Singleton instance
_verification_agent_instance = None

def get_strategy_verification_agent() -> StrategyVerificationAgent:
    """Get global strategy verification agent instance"""
    global _verification_agent_instance
    if _verification_agent_instance is None:
        _verification_agent_instance = StrategyVerificationAgent()
    return _verification_agent_instance
