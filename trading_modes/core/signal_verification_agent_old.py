"""
Signal Verification Agent - Hybrid Multi-Model Technical Analysis

PRE-EXECUTION VERIFICATION: Prevents false signals before trade execution

Combines:
1. Technical Snapshot Builder (BTC Signal Agent approach)
   - Computes REAL indicators from actual price data (EMA, RSI, ATR, Bollinger, MACD)
   - Objective market state detection (trend, volatility, volume)

2. Swarm Consensus Verification (Swarm Agent approach)
   - 5 AI models verify signal against real data
   - Multi-model consensus prevents bias/hallucination
   - Cross-checks Scanner signal vs technical reality

This agent prevents false signals like NIL and WCT trades by
cross-checking scanner signals against actual technical indicators
and multi-AI consensus BEFORE execution.

Author: Moon Dev Trading System
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import pandas_ta as ta
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

from src.models.model_factory import model_factory
from risk_management.binance_truth_paper_trading import BinanceTruthAPI


class SignalVerificationAgent:
    """
    Pre-Execution Signal Verification System

    Prevents false signals by:
    1. Computing real technical indicators (no AI guessing)
    2. Multi-model consensus verification (5 AI models)
    3. Cross-checking signal conditions against actual data

    Use BEFORE trade execution to validate Scanner/Strategy signals
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize verification agent with multi-model swarm

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}

        # Swarm models (5 independent AI models for consensus)
        self.swarm_models = [
            ('xai', 'grok-4-fast-reasoning'),          # Fast reasoning
            ('claude', 'claude-sonnet-4-5'),           # Balanced analysis
            ('openrouter', 'deepseek/deepseek-r1'),    # Deep reasoning
            ('openrouter', 'google/gemini-2.0-flash-exp:free'),  # Fast inference
            ('groq', 'llama-3.3-70b-versatile')        # Fast, versatile
        ]

        # Consensus synthesis model
        self.consensus_model = ('xai', 'grok-4-fast-reasoning')

        # Confidence thresholds
        self.unanimous_confidence = 95.0  # All 5 models agree
        self.strong_majority_confidence = 85.0  # 4/5 models agree
        self.majority_confidence = 75.0  # 3/5 models agree

        cprint("\n[SIGNAL VERIFICATION AGENT] Initialized with 5-model swarm", "cyan", attrs=['bold'])

    def verify_signal(
        self,
        symbol: str,
        timeframe: str,
        scanner_signal: str,
        scanner_confidence: float,
        strategy_name: Optional[str] = None,
        strategy_logic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main verification pipeline - validates signal BEFORE execution

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '15m', '1h')
            scanner_signal: Signal from scanner (BUY/SELL/NEUTRAL)
            scanner_confidence: Scanner confidence %
            strategy_name: Optional strategy name being verified
            strategy_logic: Optional strategy code/description

        Returns:
            {
                'action': 'BUY|SELL|NEUTRAL|WAIT',
                'confidence': float,
                'model_votes': {'BUY': int, 'SELL': int, 'NEUTRAL': int},
                'reasoning': str,
                'technical_snapshot': dict,
                'individual_verdicts': list,
                'agrees_with_scanner': bool
            }
        """
        cprint(f"\n[VERIFICATION] {symbol} {timeframe} | Scanner: {scanner_signal} @ {scanner_confidence}%", "yellow")

        # PHASE 1: Build technical snapshot (objective data)
        snapshot = self._build_technical_snapshot(symbol, timeframe)

        if not snapshot:
            return {
                'action': 'WAIT',
                'confidence': 0.0,
                'reasoning': 'Failed to fetch market data',
                'technical_snapshot': {},
                'model_votes': {'BUY': 0, 'SELL': 0, 'NEUTRAL': 0, 'WAIT': 5},
                'agreement_level': 'error',  # CRITICAL FIX: Add missing key
                'agrees_with_scanner': False
            }

        # PHASE 2: Query swarm for consensus verification
        verdicts = self._query_swarm(
            symbol=symbol,
            timeframe=timeframe,
            strategy_name=strategy_name or 'Scanner',
            scanner_signal=scanner_signal,
            scanner_confidence=scanner_confidence,
            snapshot=snapshot,
            strategy_logic=strategy_logic
        )

        # PHASE 3: Aggregate consensus
        final_verdict = self._aggregate_verdicts(verdicts, snapshot, scanner_signal)

        # Log results
        self._log_verification_result(final_verdict, scanner_signal)

        return final_verdict

    def _build_technical_snapshot(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        Build technical snapshot with REAL indicators computed from actual price data

        This prevents AI hallucination by providing objective ground truth.
        """
        try:
            # Fetch live OHLCV data from Binance
            df = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe, days_back=3)

            if df is None or len(df) < 50:
                cprint(f"  [ERROR] Insufficient data for {symbol}", "red")
                return None

            # Extract price series
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']

            # Compute REAL technical indicators (NOT AI guesses)
            ema_20 = ta.ema(close, length=20).iloc[-1]
            ema_50 = ta.ema(close, length=50).iloc[-1]
            ema_200 = ta.ema(close, length=200).iloc[-1] if len(df) >= 200 else None

            rsi = ta.rsi(close, length=14).iloc[-1]
            atr = ta.atr(high, low, close, length=14).iloc[-1]

            # Bollinger Bands - Use manual calculation for reliability
            # pandas_ta has version-specific column naming issues, manual calc is safer
            try:
                # Manual Bollinger Bands calculation (most reliable)
                sma_20 = close.rolling(window=20).mean()
                std_20 = close.rolling(window=20).std()
                bb_upper_series = sma_20 + (2 * std_20)
                bb_middle_series = sma_20
                bb_lower_series = sma_20 - (2 * std_20)

                # Get last values
                bb_upper = float(bb_upper_series.iloc[-1])
                bb_middle = float(bb_middle_series.iloc[-1])
                bb_lower = float(bb_lower_series.iloc[-1])

                # Validate values are not NaN
                if any(pd.isna([bb_upper, bb_middle, bb_lower])):
                    cprint(f"  [ERROR] Bollinger Bands contain NaN values for {symbol}", "red")
                    return None

            except Exception as bb_error:
                cprint(f"  [ERROR] Bollinger Bands calculation failed for {symbol}: {bb_error}", "red")
                import traceback
                cprint(f"  {traceback.format_exc()[:200]}", "red")
                return None

            macd = ta.macd(close)
            macd_value = macd['MACD_12_26_9'].iloc[-1]
            macd_signal = macd['MACDs_12_26_9'].iloc[-1]
            macd_hist = macd['MACDh_12_26_9'].iloc[-1]

            # Volume analysis
            avg_volume = volume.iloc[-20:].mean()
            volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1.0

            # Detect trend from actual EMA crossovers
            current_price = close.iloc[-1]
            if ema_200:
                if ema_20 > ema_50 > ema_200:
                    trend = 'strong_uptrend'
                elif ema_20 > ema_50:
                    trend = 'uptrend'
                elif ema_20 < ema_50 < ema_200:
                    trend = 'strong_downtrend'
                elif ema_20 < ema_50:
                    trend = 'downtrend'
                else:
                    trend = 'consolidation'
            else:
                if ema_20 > ema_50:
                    trend = 'uptrend'
                elif ema_20 < ema_50:
                    trend = 'downtrend'
                else:
                    trend = 'consolidation'

            # Measure actual volatility from ATR
            atr_percent = (atr / current_price) * 100

            if atr_percent > 3.0:
                volatility = 'high'
            elif atr_percent > 1.5:
                volatility = 'medium'
            else:
                volatility = 'low'

            # RSI regime
            if rsi > 70:
                rsi_regime = 'overbought'
            elif rsi > 60:
                rsi_regime = 'bullish'
            elif rsi > 40:
                rsi_regime = 'neutral'
            elif rsi > 30:
                rsi_regime = 'bearish'
            else:
                rsi_regime = 'oversold'

            # Bollinger position (0-100%)
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) * 100 if (bb_upper - bb_lower) > 0 else 50

            snapshot = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'current_price': float(current_price),
                'ema_20': float(ema_20),
                'ema_50': float(ema_50),
                'ema_200': float(ema_200) if ema_200 else None,
                'rsi': float(rsi),
                'rsi_regime': rsi_regime,
                'atr': float(atr),
                'atr_percent': float(atr_percent),
                'bb_upper': float(bb_upper),
                'bb_middle': float(bb_middle),
                'bb_lower': float(bb_lower),
                'bb_position': float(bb_position),
                'macd': float(macd_value),
                'macd_signal': float(macd_signal),
                'macd_hist': float(macd_hist),
                'volume_ratio': float(volume_ratio),
                'trend': trend,
                'volatility': volatility
            }

            cprint(f"  [SNAPSHOT] Price: ${current_price:.2f} | Trend: {trend} | RSI: {rsi:.1f} ({rsi_regime}) | Vol: {volume_ratio:.2f}x", "white")

            return snapshot

        except Exception as e:
            cprint(f"  [ERROR] Failed to build snapshot: {e}", "red")
            return None

    def _query_swarm(
        self,
        symbol: str,
        timeframe: str,
        strategy_name: str,
        scanner_signal: str,
        scanner_confidence: float,
        snapshot: Dict,
        strategy_logic: Optional[str]
    ) -> List[Dict]:
        """
        Query 5 AI models in parallel with OBJECTIVE technical data

        Each model receives:
        - Scanner signal + confidence
        - REAL technical indicators (not guesses)
        - Strategy name/logic
        - Market conditions

        Returns list of model verdicts
        """
        # Build verification prompt with REAL data
        prompt = self._build_verification_prompt(
            symbol, timeframe, strategy_name, scanner_signal,
            scanner_confidence, snapshot, strategy_logic
        )

        verdicts = []

        cprint(f"  [SWARM] Querying 5 AI models for consensus...", "cyan")

        for provider, model_name in self.swarm_models:
            try:
                # FIX: Use get_model() instead of create_model()
                model = model_factory.get_model(provider)

                response = model.generate_response(
                    system_prompt="You are a quantitative trading signal verification specialist. Analyze signals against REAL market data with precision. Detect false signals caused by overbought conditions, low volume, or trend conflicts.",
                    user_content=prompt,
                    temperature=0.2,  # Very low temp for objective analysis
                    max_tokens=600
                )

                # CRITICAL FIX: Convert ModelResponse object to string before parsing
                response_text = response.content if hasattr(response, 'content') else str(response)

                # Parse verdict from response
                verdict = self._parse_verdict(response_text, model_name)

                verdicts.append({
                    'model': model_name,
                    'provider': provider,
                    'verdict': verdict,
                    'raw_response': response
                })

                cprint(f"    ✓ {model_name}: {verdict['action']} @ {verdict['confidence']}%", "white")

            except Exception as e:
                cprint(f"    ✗ {model_name}: Error - {e}", "red")
                # Add error verdict (counts as WAIT) - CRITICAL FIX: Include all required keys
                verdicts.append({
                    'model': model_name,
                    'provider': provider,
                    'verdict': {
                        'action': 'WAIT',
                        'confidence': 0,
                        'reasoning': f'Model error: {e}',
                        'risk_level': 'high',
                        'agrees_with_scanner': False  # CRITICAL: Add missing key
                    },
                    'raw_response': ''
                })

        return verdicts

    def _build_verification_prompt(
        self,
        symbol: str,
        timeframe: str,
        strategy_name: str,
        scanner_signal: str,
        scanner_confidence: float,
        snapshot: Dict,
        strategy_logic: Optional[str]
    ) -> str:
        """
        Build verification prompt with REAL technical data
        """
        ema_200_str = f"${snapshot['ema_200']:.2f}" if snapshot['ema_200'] else "N/A (insufficient data)"

        prompt = f"""
SIGNAL VERIFICATION REQUEST (Pre-Execution Check)

Symbol: {symbol}
Timeframe: {timeframe}
Strategy/Scanner: {strategy_name}
Scanner Signal: {scanner_signal} @ {scanner_confidence}% confidence

REAL TECHNICAL SNAPSHOT (computed from actual price data, NOT estimates):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Price & Trend:
  - Current Price: ${snapshot['current_price']:.2f}
  - EMA 20: ${snapshot['ema_20']:.2f}
  - EMA 50: ${snapshot['ema_50']:.2f}
  - EMA 200: {ema_200_str}
  - Detected Trend: {snapshot['trend']}

Momentum & Oscillators:
  - RSI: {snapshot['rsi']:.1f} ({snapshot['rsi_regime']})
  - MACD: {snapshot['macd']:.4f}
  - MACD Signal: {snapshot['macd_signal']:.4f}
  - MACD Histogram: {snapshot['macd_hist']:.4f}

Volatility & Bands:
  - ATR: ${snapshot['atr']:.2f} ({snapshot['atr_percent']:.2f}% of price)
  - Volatility: {snapshot['volatility']}
  - Bollinger Upper: ${snapshot['bb_upper']:.2f}
  - Bollinger Middle: ${snapshot['bb_middle']:.2f}
  - Bollinger Lower: ${snapshot['bb_lower']:.2f}
  - BB Position: {snapshot['bb_position']:.1f}% (0=lower band, 100=upper band)

Volume:
  - Volume Ratio: {snapshot['volume_ratio']:.2f}x average (20-period)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{"STRATEGY LOGIC:\n" + strategy_logic if strategy_logic else ""}

YOUR TASK: Verify if Scanner {scanner_signal} signal is valid or FALSE SIGNAL

CRITICAL RULES (False Signal Detection):
1. RSI Overbought Check:
   - If RSI > 70 and Scanner says BUY → likely FALSE SIGNAL
   - If RSI < 30 and Scanner says SELL → likely FALSE SIGNAL

2. Volume Validation:
   - If volume < 0.8x average and Scanner says BUY → RISKY (low conviction)
   - If volume < 0.5x average → VETO (manipulation risk)

3. Trend Alignment:
   - If trend is 'downtrend' or 'consolidation' and Scanner says BUY → WEAK SETUP
   - Check if EMA 20 > EMA 50 for BUY signals (uptrend confirmation)

4. MACD Confirmation:
   - If MACD histogram < 0 and Scanner says BUY → CONFLICTING SIGNAL
   - Negative MACD = bearish momentum

5. Bollinger Extremes:
   - If BB Position > 90% and Scanner says BUY → EXTENDED (overbought)
   - If BB Position < 10% and Scanner says SELL → EXTENDED (oversold)

VERIFICATION CHECKLIST:
□ Does Scanner {scanner_signal} align with current trend ({snapshot['trend']})?
□ Is RSI in appropriate regime for {scanner_signal}?
□ Does MACD confirm or conflict with {scanner_signal}?
□ Is volume sufficient (>0.8x recommended)?
□ Is price position in Bollinger Bands reasonable?

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "action": "BUY|SELL|NEUTRAL|WAIT",
  "confidence": 0-100,
  "reasoning": "Brief explanation referencing SPECIFIC data (e.g., 'RSI 69 approaching overbought, volume 0.71x below threshold')",
  "risk_level": "low|medium|high",
  "agrees_with_scanner": true/false
}}

IMPORTANT: If you detect FALSE SIGNAL conditions, vote NEUTRAL or WAIT with high confidence.
"""
        return prompt

    def _parse_verdict(self, response: str, model_name: str) -> Dict[str, Any]:
        """
        Parse AI model verdict from response text

        Expects JSON format:
        {
          "action": "BUY|SELL|NEUTRAL|WAIT",
          "confidence": 0-100,
          "reasoning": "...",
          "risk_level": "low|medium|high",
          "agrees_with_scanner": true/false
        }
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response, re.DOTALL)

            if json_match:
                verdict_json = json.loads(json_match.group(0))

                return {
                    'action': verdict_json.get('action', 'WAIT').upper(),
                    'confidence': int(verdict_json.get('confidence', 50)),
                    'reasoning': verdict_json.get('reasoning', 'No reasoning provided'),
                    'risk_level': verdict_json.get('risk_level', 'medium'),
                    'agrees_with_scanner': verdict_json.get('agrees_with_scanner', False)
                }
            else:
                # Fallback: Extract action and confidence from text
                action = 'WAIT'
                confidence = 50

                response_upper = response.upper()
                if 'BUY' in response_upper and 'NOT' not in response_upper and 'DON\'T' not in response_upper:
                    action = 'BUY'
                elif 'SELL' in response_upper and 'NOT' not in response_upper and 'DON\'T' not in response_upper:
                    action = 'SELL'
                elif 'NEUTRAL' in response_upper:
                    action = 'NEUTRAL'
                elif 'WAIT' in response_upper:
                    action = 'WAIT'

                conf_match = re.search(r'(\d{1,3})\s*%', response)
                if conf_match:
                    confidence = int(conf_match.group(1))

                return {
                    'action': action,
                    'confidence': confidence,
                    'reasoning': response[:200],
                    'risk_level': 'medium',
                    'agrees_with_scanner': False
                }

        except Exception as e:
            cprint(f"    [PARSE ERROR] {model_name}: {e}", "red")
            return {
                'action': 'WAIT',
                'confidence': 0,
                'reasoning': f'Parse error: {e}',
                'risk_level': 'high',
                'agrees_with_scanner': False
            }

    def _aggregate_verdicts(self, verdicts: List[Dict], snapshot: Dict, scanner_signal: str) -> Dict[str, Any]:
        """
        Aggregate 5 model verdicts using weighted voting

        Returns final consensus with confidence based on agreement level
        """
        actions = [v['verdict']['action'] for v in verdicts]
        confidences = [v['verdict']['confidence'] for v in verdicts]
        agreements = [v['verdict']['agrees_with_scanner'] for v in verdicts]

        # Count votes
        buy_count = actions.count('BUY')
        sell_count = actions.count('SELL')
        neutral_count = actions.count('NEUTRAL')
        wait_count = actions.count('WAIT')

        # Determine final action by majority vote
        if buy_count >= 3:
            final_action = 'BUY'
        elif sell_count >= 3:
            final_action = 'SELL'
        elif neutral_count >= 3:
            final_action = 'NEUTRAL'
        else:
            final_action = 'WAIT'  # No consensus

        # Calculate confidence based on agreement level
        total_models = len(verdicts)
        max_votes = max(buy_count, sell_count, neutral_count, wait_count)

        if max_votes == total_models:
            # Unanimous (5/5)
            final_confidence = self.unanimous_confidence
            agreement_level = 'unanimous'
        elif max_votes == total_models - 1:
            # Strong majority (4/5)
            final_confidence = self.strong_majority_confidence
            agreement_level = 'strong_majority'
        elif max_votes >= 3:
            # Majority (3/5)
            final_confidence = self.majority_confidence
            agreement_level = 'majority'
        else:
            # No consensus
            final_confidence = sum(confidences) / len(confidences) if confidences else 50
            agreement_level = 'no_consensus'

        # Check if AI agrees with scanner
        agreement_count = sum(1 for agree in agreements if agree)
        agrees_with_scanner = (agreement_count >= 3) or (final_action == scanner_signal)

        # Build reasoning summary
        reasoning_parts = []
        for v in verdicts:
            reasoning_parts.append(f"{v['model']}: {v['verdict']['reasoning'][:80]}")

        reasoning_summary = f"{agreement_level.upper()} ({max_votes}/{total_models} models) - " + "; ".join(reasoning_parts[:2])

        return {
            'action': final_action,
            'confidence': final_confidence,
            'model_votes': {
                'BUY': buy_count,
                'SELL': sell_count,
                'NEUTRAL': neutral_count,
                'WAIT': wait_count
            },
            'agreement_level': agreement_level,
            'reasoning': reasoning_summary,
            'technical_snapshot': snapshot,
            'individual_verdicts': verdicts,
            'agrees_with_scanner': agrees_with_scanner
        }

    def _log_verification_result(self, verdict: Dict, scanner_signal: str):
        """Log verification result to console"""
        action = verdict['action']
        confidence = verdict['confidence']
        votes = verdict['model_votes']
        agrees = verdict['agrees_with_scanner']

        if action in ['BUY', 'SELL']:
            color = 'green' if action == 'BUY' else 'red'
        elif action == 'NEUTRAL':
            color = 'yellow'
        else:
            color = 'white'

        cprint(f"\n  [FINAL VERDICT] {action} @ {confidence:.0f}% confidence", color, attrs=['bold'])
        cprint(f"  [VOTES] BUY: {votes['BUY']}, SELL: {votes['SELL']}, NEUTRAL: {votes['NEUTRAL']}, WAIT: {votes['WAIT']}", "white")
        cprint(f"  [AGREEMENT] {verdict['agreement_level']}", "white")

        if not agrees:
            cprint(f"  [CONFLICT] AI verdict {action} DISAGREES with Scanner {scanner_signal} - potential false signal!", "red", attrs=['bold'])
        else:
            cprint(f"  [ALIGNED] AI verdict {action} agrees with Scanner {scanner_signal}", "green")


# Singleton instance
_signal_verification_agent = None

def get_signal_verification_agent(config: Optional[Dict] = None) -> SignalVerificationAgent:
    """Get singleton signal verification agent instance"""
    global _signal_verification_agent
    if _signal_verification_agent is None:
        _signal_verification_agent = SignalVerificationAgent(config)
    return _signal_verification_agent
