#!/usr/bin/env python3
"""
AI Market Analysis Agent - ENHANCED WITH MULTI-MODEL VERIFICATION

Uses comprehensive strategy verification combining:
1. Technical Snapshot: Real market indicators (EMA, RSI, ATR, Bollinger)
2. Swarm Consensus: 5 AI models analyze strategy logic vs market reality
3. Logic Verification: Checkmate strategy parameters against actual conditions

Upgraded from single-model quick analysis to production-grade multi-agent verification.
Based on Moon Dev's BTC Signal Agent + Swarm Agent patterns.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
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

from trading_modes.core.strategy_verification_agent import get_strategy_verification_agent


class MarketAnalysisAgent:
    """
    ENHANCED AI-powered market analysis agent using multi-model verification

    Now uses StrategyVerificationAgent for production-grade analysis:
    - Technical snapshot of actual market conditions
    - Multi-model consensus (5 AI models in parallel)
    - Logic verification (strategy parameters vs market reality)
    """

    def __init__(self, model_provider: str = 'openrouter'):
        """
        Initialize with enhanced verification system

        Args:
            model_provider: Kept for backwards compatibility, but now uses multi-model swarm
        """
        # Get the enhanced verification agent (uses Swarm)
        self.verification_agent = get_strategy_verification_agent()
        self.analysis_cache = {}

        cprint("\n[UPGRADED] Market Analysis Agent initialized with MULTI-MODEL VERIFICATION", "green", attrs=['bold'])
        cprint("   → Technical Snapshot: ENABLED", "green")
        cprint("   → Swarm Consensus (5 models): ENABLED", "green")
        cprint("   → Logic Verification: ENABLED", "green")

    def analyze_strategy_performance(
        self,
        strategy_name: str,
        symbol: str,
        cycles: int,
        signal_count: int,
        ohlcv_data: pd.DataFrame,
        recent_reasoning: List[str],
        bracket_info: Dict = None,
        strategy_instance: Any = None  # NEW: Strategy instance for extracting settings
    ) -> Dict:
        """
        ENHANCED: Use multi-model verification to analyze strategy health

        Now uses StrategyVerificationAgent for production-grade analysis:
        - Builds technical snapshot of actual market conditions
        - Queries 5 AI models in parallel for consensus
        - Verifies strategy logic against market reality

        Args:
            strategy_name: Name of strategy
            symbol: Trading symbol
            cycles: Number of cycles run
            signal_count: Signals generated
            ohlcv_data: Recent OHLCV data
            recent_reasoning: List of recent strategy reasoning messages
            bracket_info: Optional bracket information (upper, lower, current price)

        Returns:
            {
                'verdict': 'STRATEGY_WORKING' | 'STRATEGY_BROKEN' | 'NEEDS_TUNING',
                'confidence': 0-100,
                'reasoning': 'Multi-model consensus explanation',
                'market_state': 'CONSOLIDATION' | 'TRENDING' | 'VOLATILE',
                'action_required': 'NONE' | 'FIX_LOGIC' | 'ADJUST_PARAMS',
                'technical_snapshot': {...},  # NEW: Real market indicators
                'swarm_consensus': {...}       # NEW: Multi-model responses
            }
        """
        try:
            # Use enhanced verification agent (multi-model + technical analysis)
            result = self.verification_agent.verify_strategy(
                strategy_name=strategy_name,
                symbol=symbol,
                cycles_run=cycles,
                signals_generated=signal_count,
                ohlcv_data=ohlcv_data,
                recent_reasoning=recent_reasoning,
                strategy_params=bracket_info,  # Pass bracket info as strategy params
                strategy_instance=strategy_instance  # ✅ Pass strategy instance for settings extraction
            )

            return result

        except Exception as e:
            # Fallback to simple rule-based analysis if enhanced verification fails
            cprint(f"⚠️  Enhanced verification failed: {e}", "yellow")
            cprint(f"   Falling back to simple analysis...", "yellow")

            # Simple fallback based on basic metrics
            close_prices = ohlcv_data['close'].values[-50:]
            price_mean = np.mean(close_prices)
            price_std = np.std(close_prices)
            price_cv = (price_std / price_mean * 100) if price_mean != 0 else 0

            highs = ohlcv_data['high'].values[-50:]
            lows = ohlcv_data['low'].values[-50:]
            true_ranges = highs - lows
            avg_true_range = np.mean(true_ranges)
            atr_pct = (avg_true_range / price_mean * 100) if price_mean != 0 else 0

            return self._fallback_analysis(price_cv, atr_pct, signal_count, cycles)

    def _parse_ai_response(self, response) -> Dict:
        """Parse structured AI response from ModelResponse object"""
        # Extract text content from ModelResponse object
        response_text = response.content if hasattr(response, 'content') else str(response)
        lines = response_text.strip().split('\n')
        result = {
            'verdict': 'UNKNOWN',
            'confidence': 50,
            'reasoning': 'AI analysis failed to parse',
            'market_state': 'UNKNOWN',
            'action_required': 'NONE'
        }

        for line in lines:
            if line.startswith('VERDICT:'):
                result['verdict'] = line.split(':', 1)[1].strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    result['confidence'] = int(line.split(':', 1)[1].strip())
                except:
                    pass
            elif line.startswith('MARKET_STATE:'):
                result['market_state'] = line.split(':', 1)[1].strip()
            elif line.startswith('REASONING:'):
                result['reasoning'] = line.split(':', 1)[1].strip()
            elif line.startswith('ACTION_REQUIRED:'):
                result['action_required'] = line.split(':', 1)[1].strip()

        return result

    def _fallback_analysis(self, price_cv: float, atr_pct: float, signal_count: int, cycles: int) -> Dict:
        """Rule-based fallback if AI fails"""
        if price_cv < 0.2 and atr_pct < 1.0:
            return {
                'verdict': 'STRATEGY_WORKING',
                'confidence': 80,
                'reasoning': 'Low volatility consolidation - strategy correctly waiting for breakout',
                'market_state': 'CONSOLIDATION',
                'action_required': 'NONE'
            }
        elif price_cv > 1.0 and signal_count == 0 and cycles > 20:
            return {
                'verdict': 'NEEDS_TUNING',
                'confidence': 70,
                'reasoning': 'High volatility but no signals - parameters may be too conservative',
                'market_state': 'VOLATILE',
                'action_required': 'ADJUST_PARAMS'
            }
        else:
            return {
                'verdict': 'STRATEGY_WORKING',
                'confidence': 60,
                'reasoning': 'Normal market conditions - waiting for entry criteria',
                'market_state': 'TRENDING',
                'action_required': 'NONE'
            }

    def display_analysis(self, analysis: Dict, strategy_name: str, symbol: str):
        """Display ENHANCED AI analysis with multi-model consensus"""
        # Use the verification agent's display method for comprehensive output
        self.verification_agent.display_verification_result(analysis)


# Singleton instance
_analysis_agent_instance = None

def get_market_analysis_agent(model_provider: str = 'deepseek') -> MarketAnalysisAgent:
    """Get global market analysis agent instance"""
    global _analysis_agent_instance
    if _analysis_agent_instance is None:
        _analysis_agent_instance = MarketAnalysisAgent(model_provider)
    return _analysis_agent_instance
