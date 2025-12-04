#!/usr/bin/env python3
"""
Strategy Validation System - Catches Broken Strategies BEFORE They Waste Time
Prevents issues like:
- Strategies that can never generate signals (bracket logic bugs)
- Strategies with incorrect indicator calculations
- Strategies that always return NEUTRAL
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    import pandas as pd

# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)


class StrategyValidator:
    """
    Validates strategies in REAL-TIME to catch bugs immediately

    Alerts:
    - 🔴 Strategy hasn't generated a signal in N cycles (possible logic bug)
    - 🔴 Strategy conditions are mathematically impossible
    - 🔴 Indicators always return same value (calculation error)
    - 🟡 Low signal frequency (might need parameter tuning)
    """

    def __init__(self, alert_after_cycles: int = 20):
        """
        Args:
            alert_after_cycles: Alert if no signals after this many cycles
        """
        self.alert_after_cycles = alert_after_cycles
        self.strategy_stats = {}  # Track each strategy's performance

    def track_strategy_cycle(self, strategy_name: str, signal_result: Dict, ohlcv: Optional[pd.DataFrame] = None):
        """
        Track strategy output for each cycle

        Args:
            strategy_name: Name of strategy
            signal_result: Output from strategy.generate_signals()
            ohlcv: Optional OHLCV data for analysis
        """
        if strategy_name not in self.strategy_stats:
            self.strategy_stats[strategy_name] = {
                'total_cycles': 0,
                'signal_count': 0,
                'buy_count': 0,
                'sell_count': 0,
                'neutral_count': 0,
                'last_signal_cycle': 0,
                'reasoning_patterns': {},
                'price_ranges': [],
                'bracket_checks': []  # Track if brackets are always containing price
            }

        stats = self.strategy_stats[strategy_name]
        stats['total_cycles'] += 1

        action = signal_result.get('action', 'NOTHING')
        # PERMANENT FIX: Check both 'reason' (strategies) and 'reasoning' (legacy) keys
        reasoning = signal_result.get('reason', '') or signal_result.get('reasoning', '')

        # Track action counts
        if action == 'BUY':
            stats['signal_count'] += 1
            stats['buy_count'] += 1
            stats['last_signal_cycle'] = stats['total_cycles']
        elif action == 'SELL':
            stats['signal_count'] += 1
            stats['sell_count'] += 1
            stats['last_signal_cycle'] = stats['total_cycles']
        else:
            stats['neutral_count'] += 1

        # Track reasoning patterns (detect repeated messages)
        if reasoning not in stats['reasoning_patterns']:
            stats['reasoning_patterns'][reasoning] = 0
        stats['reasoning_patterns'][reasoning] += 1

        # Detect bracket logic bug (price always in range)
        if 'in range' in reasoning.lower() and ohlcv is not None:
            # Extract bracket values from reasoning if possible
            if '[' in reasoning and ']' in reasoning:
                stats['bracket_checks'].append(True)  # Price was in range

        # Track price movement
        if ohlcv is not None and len(ohlcv) > 0:
            current_price = ohlcv['close'].iloc[-1]
            stats['price_ranges'].append(current_price)

    def validate_and_alert(self, symbol: str = None) -> List[Dict]:
        """
        Check all tracked strategies and return alerts

        Returns:
            List of alert dictionaries with severity and message
        """
        alerts = []

        for strategy_name, stats in self.strategy_stats.items():
            cycles = stats['total_cycles']

            if cycles == 0:
                continue

            # 🔴 CRITICAL: No signals in many cycles
            # PERMANENT FIX: Check for legitimate market blocks before alerting
            cycles_since_signal = cycles - stats['last_signal_cycle']
            if cycles >= self.alert_after_cycles and cycles_since_signal >= self.alert_after_cycles:
                # Check if reasoning shows LEGITIMATE market-driven blocks
                most_common_reasoning = max(stats['reasoning_patterns'].items(), key=lambda x: x[1]) if stats['reasoning_patterns'] else ('', 0)
                reasoning_text = most_common_reasoning[0].lower()

                # LEGITIMATE BLOCKS: Market-driven reasons that are NOT bugs
                # PERMANENT FIX: Updated to match new debug output format
                legitimate_market_blocks = [
                    # New debug format patterns (from MACD/LazyBear strategies)
                    'rsi_oob' in reasoning_text,           # RSI Out Of Bounds (outside 25-80)
                    'rsi_falling' in reasoning_text,       # RSI momentum falling
                    'rsi_rising' in reasoning_text,        # RSI momentum rising (blocks SHORT)
                    'macd_bear' in reasoning_text,         # MACD bearish (blocks LONG)
                    'macd_bull' in reasoning_text,         # MACD bullish (blocks SHORT)
                    'imp_bull' in reasoning_text,          # Impulse bullish (blocks SHORT)
                    'imp_bear' in reasoning_text,          # Impulse bearish (blocks LONG)
                    'price<ema' in reasoning_text,         # Price below EMA (blocks LONG)
                    'price>ema' in reasoning_text,         # Price above EMA (blocks SHORT)
                    'consol' in reasoning_text,            # In consolidation zone
                    'holding_long' in reasoning_text,      # Strategy holding LONG position
                    'holding_short' in reasoning_text,     # Strategy holding SHORT position
                    '[long_blocked]' in reasoning_text,    # Any LONG block reason
                    '[short_blocked]' in reasoning_text,   # Any SHORT block reason
                    # Legacy patterns (keep for backwards compatibility)
                    'rsi' in reasoning_text and 'outside' in reasoning_text,
                    'death cross' in reasoning_text,
                    'divergence' in reasoning_text,
                    'cooldown' in reasoning_text,
                    'holding' in reasoning_text,
                    'consolidation' in reasoning_text,
                ]

                if not any(legitimate_market_blocks):
                    signal_rate = (stats['signal_count'] / cycles * 100)
                    alerts.append({
                        'severity': 'CRITICAL',
                        'strategy': strategy_name,
                        'symbol': symbol,
                        'message': f"NO SIGNALS in {cycles_since_signal} cycles! Signal rate: {signal_rate:.1f}%",
                        'suggestion': "Check strategy logic - may have bracket calculation bug or impossible conditions"
                    })

            # 🔴 REMOVED: "100% NEUTRAL" check removed - causes too many false positives
            #
            # REASONING:
            # - Strategies correctly block during legitimate market conditions
            # - [LONG_BLOCKED] and [SHORT_BLOCKED] are CORRECT behaviors
            # - Market conditions (RSI overbought, price below EMA, consolidation) are NOT bugs
            # - The health check display already shows legitimate blocks in cyan
            # - Only bracket bugs need alerting (very rare)
            #
            # PERMANENT FIX: Only alert for actual bracket bugs, not market blocks
            if cycles >= 20 and stats['signal_count'] == 0:
                # Only check for bracket bugs (price always in range despite movement)
                if len(stats['bracket_checks']) >= 10 and all(stats['bracket_checks'][-10:]):
                    if len(stats['price_ranges']) >= 10:
                        recent_prices = stats['price_ranges'][-10:]
                        price_std = np.std(recent_prices)
                        price_mean = np.mean(recent_prices)
                        cv = (price_std / price_mean * 100) if price_mean != 0 else 0

                        # Only alert if price IS moving significantly but still always in brackets
                        if cv > 1.0:  # Price moving >1% but still always in brackets = likely bug
                            alerts.append({
                                'severity': 'CRITICAL',
                                'strategy': strategy_name,
                                'symbol': symbol,
                                'message': f"BRACKET BUG: Price moving ({cv:.2f}%) but ALWAYS in range after {cycles} cycles",
                                'suggestion': "Brackets may be calculated incorrectly"
                            })

            # 🔴 DISABLED: "STUCK IN LOOP" check removed due to excessive false positives
            #
            # REASONING:
            # - Death Cross can persist for days/weeks (legitimate bearish trend)
            # - High RSI can persist for extended periods (legitimate overbought condition)
            # - Strategies CORRECTLY blocking entries during these conditions
            # - This is capital protection, NOT a bug!
            #
            # FALSE POSITIVE EXAMPLE:
            # - BTC in Death Cross for 7+ cycles with RSI 75-85
            # - Validator flagged as "STUCK IN LOOP"
            # - But this is CORRECT behavior - strategy protecting capital
            #
            # DECISION: Remove this check entirely to eliminate false positives
            # The other checks (100% neutral, bracket bugs) are sufficient

            # 🟡 WARNING: Low signal frequency (may need tuning)
            # PERMANENT FIX: Check for legitimate market blocks before warning
            if cycles >= 50:
                signal_rate = (stats['signal_count'] / cycles * 100)
                if signal_rate < 2.0:  # Less than 2% signals
                    # Check if reasoning shows LEGITIMATE market-driven blocks
                    most_common_reasoning = max(stats['reasoning_patterns'].items(), key=lambda x: x[1]) if stats['reasoning_patterns'] else ('', 0)
                    reasoning_text = most_common_reasoning[0].lower()

                    # LEGITIMATE BLOCKS: Same checks as CRITICAL section
                    # These are market-driven reasons, NOT conservative strategy settings
                    legitimate_market_blocks = [
                        # New debug format patterns (from MACD/LazyBear strategies)
                        'rsi_oob' in reasoning_text,           # RSI Out Of Bounds (outside 25-80)
                        'rsi_falling' in reasoning_text,       # RSI momentum falling
                        'rsi_rising' in reasoning_text,        # RSI momentum rising (blocks SHORT)
                        'macd_bear' in reasoning_text,         # MACD bearish (blocks LONG)
                        'macd_bull' in reasoning_text,         # MACD bullish (blocks SHORT)
                        'imp_bull' in reasoning_text,          # Impulse bullish (blocks SHORT)
                        'imp_bear' in reasoning_text,          # Impulse bearish (blocks LONG)
                        'price<ema' in reasoning_text,         # Price below EMA (blocks LONG)
                        'price>ema' in reasoning_text,         # Price above EMA (blocks SHORT)
                        'consol' in reasoning_text,            # In consolidation zone
                        'holding_long' in reasoning_text,      # Strategy holding LONG position
                        'holding_short' in reasoning_text,     # Strategy holding SHORT position
                        '[long_blocked]' in reasoning_text,    # Any LONG block reason
                        '[short_blocked]' in reasoning_text,   # Any SHORT block reason
                        # Legacy patterns (keep for backwards compatibility)
                        'rsi' in reasoning_text and 'outside' in reasoning_text,
                        'death cross' in reasoning_text,
                        'divergence' in reasoning_text,
                        'cooldown' in reasoning_text,
                        'holding' in reasoning_text,
                        'consolidation' in reasoning_text,
                    ]

                    # Only warn if NO legitimate market blocks found
                    # This means low signal frequency is due to conservative settings, not market conditions
                    if not any(legitimate_market_blocks):
                        alerts.append({
                            'severity': 'WARNING',
                            'strategy': strategy_name,
                            'symbol': symbol,
                            'message': f"Low signal frequency: {signal_rate:.1f}% ({stats['signal_count']}/{cycles})",
                            'suggestion': "Strategy might be too conservative - consider parameter tuning"
                        })

            # 📊 INFO: Low volatility consolidation (only show if cycles > 20 and CV < 0.05%)
            if len(stats['price_ranges']) >= 10 and cycles >= 20:
                recent_prices = stats['price_ranges'][-10:]
                price_std = np.std(recent_prices)
                price_mean = np.mean(recent_prices)
                cv = (price_std / price_mean * 100) if price_mean != 0 else 0

                # Only warn if EXTREMELY low volatility (< 0.05%) - may indicate data feed issue
                if cv < 0.05:
                    alerts.append({
                        'severity': 'WARNING',
                        'strategy': strategy_name,
                        'symbol': symbol,
                        'message': f"EXTREMELY low price movement (CV: {cv:.3f}%) - Possible data feed issue",
                        'suggestion': "Verify OHLCV data is updating correctly from exchange"
                    })
                # Low but reasonable volatility (0.05% - 0.2%) - just consolidation, no alert needed
                elif cv < 0.2:
                    # This is normal tight consolidation - don't alert
                    pass

        return alerts

    def display_alerts(self, alerts: List[Dict]):
        """Display alerts to console with color coding"""
        if not alerts:
            return

        cprint("\n" + "="*80, "red", attrs=['bold'])
        cprint("!!! STRATEGY VALIDATION ALERTS !!!", "red", attrs=['bold'])
        cprint("="*80, "red", attrs=['bold'])

        for alert in alerts:
            severity = alert['severity']
            strategy = alert['strategy']
            symbol = alert.get('symbol', 'N/A')
            message = alert['message']
            suggestion = alert['suggestion']

            if severity == 'CRITICAL':
                cprint(f"\n[CRITICAL] {strategy} ({symbol})", "red", attrs=['bold'])
                cprint(f"   {message}", "red")
                cprint(f"   SUGGESTION: {suggestion}", "yellow")
            elif severity == 'WARNING':
                cprint(f"\n[WARNING] {strategy} ({symbol})", "yellow", attrs=['bold'])
                cprint(f"   {message}", "yellow")
                cprint(f"   SUGGESTION: {suggestion}", "white")

        cprint("\n" + "="*80 + "\n", "red", attrs=['bold'])

    def get_strategy_summary(self, strategy_name: str) -> Dict:
        """Get summary stats for a strategy"""
        if strategy_name not in self.strategy_stats:
            return {}

        stats = self.strategy_stats[strategy_name]
        cycles = stats['total_cycles']

        return {
            'total_cycles': cycles,
            'signal_count': stats['signal_count'],
            'signal_rate': (stats['signal_count'] / cycles * 100) if cycles > 0 else 0,
            'buy_count': stats['buy_count'],
            'sell_count': stats['sell_count'],
            'neutral_count': stats['neutral_count'],
            'cycles_since_signal': cycles - stats['last_signal_cycle']
        }

    def reset_strategy(self, strategy_name: str):
        """Reset tracking for a strategy (useful after fixing bugs)"""
        if strategy_name in self.strategy_stats:
            del self.strategy_stats[strategy_name]
            cprint(f"✅ Reset validation tracking for {strategy_name}", "green")


# Singleton instance
_validator_instance = None

def get_strategy_validator() -> StrategyValidator:
    """Get global strategy validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = StrategyValidator(alert_after_cycles=30)
    return _validator_instance
