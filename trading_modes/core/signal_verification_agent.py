"""
Signal Verification Agent V2 - Type-Safe Implementation

ARCHITECTURAL IMPROVEMENTS:
1. Type-safe domain models (no more untyped dicts)
2. Result type for consistent error handling
3. Version-agnostic technical indicators
4. Zero defensive .get() calls
5. Impossible to create invalid responses

This replaces signal_verification_agent.py with permanent architectural fixes.

Previously:
    return {'agrees': True, 'action': 'BUY'}  # Missing 'agreement_level' - crashes!
    agreement = result.get('agreement_level', 'unknown')  # Defensive

Now:
    return success(SignalVerificationResult(...))  # MUST have all fields
    agreement = result.value.agreement_level  # Always exists, type-safe
"""

import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
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

# NEW: Type-safe models and indicators
from trading_modes.models.domain import (
    SignalVerificationResult,
    Verdict,
    SignalAction,
    AgreementLevel,
)
from trading_modes.models.result import Result, success, failure
from trading_modes.indicators.technical import TechnicalIndicators

from src.models.model_factory import model_factory
from risk_management.binance_truth_paper_trading import BinanceTruthAPI


class SignalVerificationAgentV2:
    """
    Type-Safe Pre-Execution Signal Verification System

    Prevents false signals by:
    1. Computing real technical indicators (version-agnostic)
    2. Multi-model consensus verification (5 AI models)
    3. Type-safe responses (impossible to forget fields)

    Use BEFORE trade execution to validate Scanner/Strategy signals
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize verification agent with multi-model swarm"""
        self.config = config or {}

        # Swarm models (5 independent AI models for consensus)
        self.swarm_models = [
            ('xai', 'grok-4-fast-reasoning'),
            ('openrouter', 'anthropic/claude-3.5-sonnet'),  # Claude via OpenRouter (bypasses credits)
            ('openrouter', 'deepseek/deepseek-r1'),
            ('openrouter', 'google/gemini-2.0-flash-exp:free'),
            ('groq', 'llama-3.3-70b-versatile')
        ]

        # Consensus synthesis model
        self.consensus_model = ('xai', 'grok-4-fast-reasoning')

        # Vote thresholds for agreement levels
        self.vote_thresholds = {
            'full': 4,        # 4-5 models agree = FULL
            'majority': 3,    # 3 models agree = MAJORITY
            'weak': 2,        # 2 models agree = WEAK
        }

        cprint("\n[SIGNAL VERIFICATION V2] Type-safe system initialized", "cyan", attrs=['bold'])

    def verify_signal(
        self,
        symbol: str,
        timeframe: str,
        scanner_signal: str,
        scanner_confidence: float,
        strategy_name: Optional[str] = None,
        strategy_logic: Optional[str] = None
    ) -> Result[SignalVerificationResult]:
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
            Success[SignalVerificationResult] - Typed verification result
            Failure - Error details

        Note: ALL return paths have consistent structure (Result type)
        """
        cprint(f"\n[VERIFICATION V2] {symbol} {timeframe} | Scanner: {scanner_signal} @ {scanner_confidence}%", "yellow")

        # PHASE 1: Build technical snapshot (objective data)
        snapshot_result = self._build_technical_snapshot(symbol, timeframe)

        if snapshot_result.is_failure():
            # Error path uses factory method - consistent structure
            return success(SignalVerificationResult.error(snapshot_result.error))

        snapshot = snapshot_result.value

        # PHASE 2: Query swarm for consensus verification
        verdicts_result = self._query_swarm(
            symbol=symbol,
            timeframe=timeframe,
            strategy_name=strategy_name or 'Scanner',
            scanner_signal=scanner_signal,
            scanner_confidence=scanner_confidence,
            snapshot=snapshot,
            strategy_logic=strategy_logic
        )

        if verdicts_result.is_failure():
            return success(SignalVerificationResult.error(verdicts_result.error))

        verdicts = verdicts_result.value

        # PHASE 3: Aggregate consensus
        final_result = self._aggregate_verdicts(verdicts, snapshot, scanner_signal, scanner_confidence)

        # Log results
        if final_result.is_success():
            self._log_verification_result(final_result.value, scanner_signal)

        return final_result

    def _build_technical_snapshot(self, symbol: str, timeframe: str) -> Result[Dict]:
        """
        Build technical snapshot with REAL indicators

        Returns:
            Success[Dict] - Technical snapshot
            Failure - Error fetching data
        """
        try:
            # Fetch live OHLCV data from Binance
            df = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe, days_back=3)

            if df is None or len(df) < 50:
                return failure(
                    error=f"Insufficient data for {symbol}",
                    error_type="InsufficientDataError",
                    symbol=symbol,
                    bars=len(df) if df is not None else 0
                )

            # Extract price series
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']

            # NEW: Use version-agnostic TechnicalIndicators instead of pandas_ta
            # No more KeyError from column name changes!
            bb = TechnicalIndicators.bollinger_bands(close, period=20, std_dev=2.0)
            rsi = TechnicalIndicators.rsi(close, period=14)
            atr = TechnicalIndicators.atr(high, low, close, period=14)
            ema_20 = TechnicalIndicators.ema(close, period=20)
            ema_50 = TechnicalIndicators.ema(close, period=50)
            ema_200 = TechnicalIndicators.ema(close, period=200) if len(df) >= 200 else None
            macd = TechnicalIndicators.macd(close, fast_period=12, slow_period=26, signal_period=9)

            # Volume analysis
            avg_volume = volume.iloc[-20:].mean()
            volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1.0

            # Detect trend from EMA crossovers
            current_price = float(close.iloc[-1])

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

            # Volatility classification
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
            bb_range = bb['upper'] - bb['lower']
            bb_position = ((current_price - bb['lower']) / bb_range * 100) if bb_range > 0 else 50

            snapshot = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'current_price': current_price,
                'ema_20': ema_20,
                'ema_50': ema_50,
                'ema_200': ema_200,
                'rsi': rsi,
                'rsi_regime': rsi_regime,
                'atr': atr,
                'atr_percent': atr_percent,
                'bb_upper': bb['upper'],
                'bb_middle': bb['middle'],
                'bb_lower': bb['lower'],
                'bb_position': bb_position,
                'macd': macd['macd'],
                'macd_signal': macd['signal'],
                'macd_hist': macd['histogram'],
                'volume_ratio': float(volume_ratio),
                'trend': trend,
                'volatility': volatility
            }

            cprint(f"  [SNAPSHOT] Price: ${current_price:.2f} | Trend: {trend} | RSI: {rsi:.1f} ({rsi_regime}) | Vol: {volume_ratio:.2f}x", "white")

            return success(snapshot)

        except Exception as e:
            return failure(
                error=f"Failed to build snapshot: {e}",
                error_type=type(e).__name__,
                symbol=symbol,
                timeframe=timeframe
            )

    def _query_swarm(
        self,
        symbol: str,
        timeframe: str,
        strategy_name: str,
        scanner_signal: str,
        scanner_confidence: float,
        snapshot: Dict,
        strategy_logic: Optional[str]
    ) -> Result[List[Verdict]]:
        """
        Query 5 AI models in parallel with OBJECTIVE technical data

        Returns:
            Success[List[Verdict]] - Type-safe verdicts from all models
            Failure - Critical swarm failure
        """
        # Build verification prompt
        prompt = self._build_verification_prompt(
            symbol, timeframe, strategy_name, scanner_signal,
            scanner_confidence, snapshot, strategy_logic
        )

        verdicts: List[Verdict] = []

        cprint(f"  [SWARM] Querying 5 AI models for consensus...", "cyan")

        for provider, model_name in self.swarm_models:
            try:
                # PERMANENT FIX: Pass BOTH provider AND model_name to factory
                # Previously: Only passed provider, causing OpenRouter models to fail
                # OpenRouter needs specific model IDs (e.g., 'anthropic/claude-3.5-sonnet')
                model = model_factory.get_model(provider, model_name)

                response = model.generate_response(
                    system_prompt="You are a quantitative trading signal verification specialist. Analyze signals against REAL market data with precision. Detect false signals caused by overbought conditions, low volume, or trend conflicts.",
                    user_content=prompt,
                    temperature=0.2,
                    max_tokens=600
                )

                # Extract text from response object
                response_text = response.content if hasattr(response, 'content') else str(response)

                # Parse verdict (returns SignalAction, confidence, reasoning)
                action, confidence, reasoning = self._parse_verdict_text(response_text)

                # NEW: Type-safe Verdict object
                verdict = Verdict(
                    model_name=model_name,
                    vote=action,
                    confidence=confidence,
                    reasoning=reasoning
                )

                verdicts.append(verdict)

                cprint(f"    ✓ {model_name}: {verdict.vote.value} @ {verdict.confidence}%", "white")

            except Exception as e:
                cprint(f"    ✗ {model_name}: Error - {e}", "red")

                # PERMANENT FIX: Don't add failed models to verdicts
                # They shouldn't be counted in voting - only successful responses count
                # Previously: Failed models counted as WAIT votes, artificially rejecting valid signals
                # Now: Skip failed models entirely - voting based on successful responses only
                continue

        # PERMANENT FIX: Check if NO successful verdicts (empty list)
        # Previously: Checked if all verdicts were WAIT votes
        # Now: Failed models aren't added, so check for empty verdicts list
        if len(verdicts) == 0:
            return failure(
                error="All models failed to provide verdict",
                error_type="SwarmFailureError"
            )

        return success(verdicts)

    def _aggregate_verdicts(
        self,
        verdicts: List[Verdict],
        snapshot: Dict,
        scanner_signal: str,
        scanner_confidence: float
    ) -> Result[SignalVerificationResult]:
        """
        Aggregate verdicts into final consensus

        Returns:
            Success[SignalVerificationResult] - Type-safe result
        """
        try:
            # Count votes
            vote_counts = {
                SignalAction.BUY: 0,
                SignalAction.SELL: 0,
                SignalAction.NOTHING: 0,
                SignalAction.WAIT: 0
            }

            for verdict in verdicts:
                vote_counts[verdict.vote] += 1

            # Determine consensus action (majority wins)
            consensus_action = max(vote_counts, key=vote_counts.get)
            consensus_count = vote_counts[consensus_action]

            # Determine agreement level
            if consensus_count >= self.vote_thresholds['full']:
                agreement_level = AgreementLevel.FULL
            elif consensus_count >= self.vote_thresholds['majority']:
                agreement_level = AgreementLevel.MAJORITY
            elif consensus_count >= self.vote_thresholds['weak']:
                agreement_level = AgreementLevel.WEAK
            else:
                agreement_level = AgreementLevel.NONE

            # Check if swarm agrees with scanner
            scanner_action = SignalAction(scanner_signal)
            agrees_with_scanner = (consensus_action == scanner_action) and (agreement_level != AgreementLevel.NONE)

            # Calculate confidence (weighted by agreement)
            if agreement_level == AgreementLevel.FULL:
                confidence = 95
            elif agreement_level == AgreementLevel.MAJORITY:
                confidence = 80
            elif agreement_level == AgreementLevel.WEAK:
                confidence = 65
            else:
                confidence = 40

            # Build reasoning
            vote_summary = ', '.join([f"{action.value}: {count}" for action, count in vote_counts.items() if count > 0])
            reasoning = f"Swarm consensus: {consensus_action.value} ({consensus_count}/5 models). Votes: {vote_summary}. Agreement: {agreement_level.value}"

            # NEW: Type-safe SignalVerificationResult
            # IMPOSSIBLE to forget a field - dataclass enforces all fields
            result = SignalVerificationResult(
                agrees_with_scanner=agrees_with_scanner,
                agreement_level=agreement_level,
                action=consensus_action,
                confidence=confidence,
                reasoning=reasoning,
                verdicts=verdicts
            )

            return success(result)

        except Exception as e:
            # Error path returns SignalVerificationResult.error() factory method
            return success(SignalVerificationResult.error(f"Aggregation failed: {e}"))

    def _parse_verdict_text(self, text: str) -> tuple[SignalAction, int, str]:
        """
        Parse AI response into (action, confidence, reasoning)

        Returns tuple instead of dict for internal use
        Final verdict is constructed as type-safe Verdict object
        """
        # Extract action
        action_match = re.search(r'\*\*VERDICT:\*\*\s*(BUY|SELL|NEUTRAL|WAIT)', text, re.IGNORECASE)
        if action_match:
            action_str = action_match.group(1).upper()
            # Map NEUTRAL to NOTHING for SignalAction enum
            action = SignalAction.NOTHING if action_str == 'NEUTRAL' else SignalAction(action_str)
        else:
            action = SignalAction.WAIT

        # Extract confidence
        conf_match = re.search(r'\*\*CONFIDENCE:\*\*\s*(\d+)', text)
        confidence = int(conf_match.group(1)) if conf_match else 50

        # Extract reasoning (first paragraph after verdict)
        reasoning_match = re.search(r'\*\*VERDICT:\*\*.*?\n\n(.*?)\n\n', text, re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else text[:200]

        return action, confidence, reasoning

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
        """Build detailed verification prompt with REAL technical data"""

        strategy_section = ""
        if strategy_logic:
            strategy_section = f"""
## STRATEGY BEING VERIFIED
**Name:** {strategy_name}
**Logic:**
```python
{strategy_logic[:500]}
```
"""

        prompt = f"""
# SIGNAL VERIFICATION REQUEST

## SCANNER SIGNAL
- **Symbol:** {symbol}
- **Timeframe:** {timeframe}
- **Signal:** {scanner_signal}
- **Confidence:** {scanner_confidence}%
- **Strategy:** {strategy_name}

{strategy_section}

## REAL MARKET DATA (OBJECTIVE - NOT AI GUESSES)
**Price:** ${snapshot['current_price']:.2f}

**Trend:**
- EMA20: ${snapshot['ema_20']:.2f}
- EMA50: ${snapshot['ema_50']:.2f}
- EMA200: {f"${snapshot['ema_200']:.2f}" if snapshot['ema_200'] else "N/A"}
- Detected Trend: {snapshot['trend'].upper()}

**Momentum:**
- RSI(14): {snapshot['rsi']:.2f} ({snapshot['rsi_regime']})
- MACD: {snapshot['macd']:.4f}
- MACD Signal: {snapshot['macd_signal']:.4f}
- MACD Histogram: {snapshot['macd_hist']:.4f}

**Volatility:**
- ATR: ${snapshot['atr']:.2f} ({snapshot['atr_percent']:.2f}% of price)
- Volatility: {snapshot['volatility'].upper()}

**Bollinger Bands:**
- Upper: ${snapshot['bb_upper']:.2f}
- Middle: ${snapshot['bb_middle']:.2f}
- Lower: ${snapshot['bb_lower']:.2f}
- Position: {snapshot['bb_position']:.1f}% (0%=lower band, 100%=upper band)

**Volume:**
- Volume Ratio: {snapshot['volume_ratio']:.2f}x average

## YOUR TASK
Verify if the scanner signal is valid based on REAL technical data above.

**Red Flags to Check:**
1. Overbought/Oversold: Is RSI > 70 (overbought) or < 30 (oversold)?
2. Trend Conflict: Does signal align with EMA trend?
3. Volatility Risk: Is ATR% > 3% (high volatility)?
4. Volume Confirmation: Is volume_ratio > 1.5x (strong volume)?
5. Bollinger Position: Is price near bands (potential reversal)?

**Response Format:**
**VERDICT:** BUY | SELL | NEUTRAL | WAIT

**CONFIDENCE:** [0-100]

[Brief reasoning based on technical data above]

Be precise. Base your verdict ONLY on the real data provided.
"""

        return prompt

    def _log_verification_result(self, result: SignalVerificationResult, scanner_signal: str):
        """Log verification result with color coding"""

        # Color based on agreement
        if result.agrees_with_scanner:
            color = "green"
            prefix = "✓ VERIFIED"
        else:
            color = "red"
            prefix = "✗ REJECTED"

        cprint(f"\n  [{prefix}] Consensus: {result.action.value} @ {result.confidence}% | Agreement: {result.agreement_level.value.upper()}", color, attrs=['bold'])
        cprint(f"  Reasoning: {result.reasoning[:150]}", "white")


# Backward compatibility: expose both versions
SignalVerificationAgent = SignalVerificationAgentV2


# Singleton instance
_signal_verification_agent: Optional[SignalVerificationAgentV2] = None

def get_signal_verification_agent() -> SignalVerificationAgentV2:
    """Get singleton signal verification agent instance"""
    global _signal_verification_agent
    if _signal_verification_agent is None:
        _signal_verification_agent = SignalVerificationAgentV2()
    return _signal_verification_agent
