#!/usr/bin/env python3
"""
🌙 Moon Dev's Historical Dynamic Level Calculator

FULLY DYNAMIC - NO STATIC RANGES!

Calculates stop loss and take profit levels based on:
1. Token-specific historical volatility (not static ATR%)
2. Historical support/resistance levels (price action memory)
3. Fibonacci retracement levels (natural price targets)
4. Historical bounce-back patterns (where price actually reversed)
5. Token-specific movement capacity (some tokens move 2%, others 50%)

NO MORE STATIC RANGES like "1.5% to 8%"!
Each token gets its own levels based on its actual history.
"""

import sys
import os
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# ===========================
# HISTORICAL ANALYSIS
# ===========================

@dataclass
class TokenHistoricalProfile:
    """Historical characteristics of a token"""
    symbol: str

    # Volatility metrics
    avg_daily_move_pct: float  # Average daily price movement
    max_daily_move_pct: float  # Maximum daily movement seen
    typical_pullback_pct: float  # Typical retracement size

    # Support/Resistance
    resistance_levels: List[float]  # Historical resistance prices
    support_levels: List[float]     # Historical support prices

    # Fibonacci levels
    fib_levels: Dict[str, float]   # Key fib levels from recent swing

    # Bounce patterns
    avg_bounce_pct: float  # Average bounce size from support
    max_bounce_pct: float  # Maximum bounce seen

    # Stop loss patterns
    typical_stop_distance_pct: float  # Where stops should be
    safe_stop_distance_pct: float     # Conservative stop distance


class HistoricalAnalyzer:
    """Analyzes token history to determine dynamic levels"""

    @staticmethod
    def analyze_volatility(ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze historical volatility patterns

        Returns actual movement characteristics, not static %
        """
        close = ohlcv['close'].values
        high = ohlcv['high'].values
        low = ohlcv['low'].values

        # Calculate daily movements
        daily_moves = []
        for i in range(1, len(close)):
            move_pct = abs(close[i] - close[i-1]) / close[i-1] * 100
            daily_moves.append(move_pct)

        # Calculate intraday ranges
        intraday_ranges = []
        for i in range(len(high)):
            range_pct = (high[i] - low[i]) / close[i] * 100
            intraday_ranges.append(range_pct)

        return {
            'avg_daily_move': np.mean(daily_moves),
            'max_daily_move': np.max(daily_moves),
            'avg_intraday_range': np.mean(intraday_ranges),
            'max_intraday_range': np.max(intraday_ranges),
            'volatility_75th_percentile': np.percentile(daily_moves, 75),
            'volatility_90th_percentile': np.percentile(daily_moves, 90)
        }

    @staticmethod
    def find_support_resistance(ohlcv: pd.DataFrame, current_price: float) -> Tuple[List[float], List[float]]:
        """
        Find historical support and resistance levels

        Uses price clustering and swing high/low detection
        """
        close = ohlcv['close'].values
        high = ohlcv['high'].values
        low = ohlcv['low'].values

        # Find swing highs (resistance)
        swing_highs = []
        for i in range(2, len(high) - 2):
            if high[i] > high[i-1] and high[i] > high[i-2] and \
               high[i] > high[i+1] and high[i] > high[i+2]:
                swing_highs.append(high[i])

        # Find swing lows (support)
        swing_lows = []
        for i in range(2, len(low) - 2):
            if low[i] < low[i-1] and low[i] < low[i-2] and \
               low[i] < low[i+1] and low[i] < low[i+2]:
                swing_lows.append(low[i])

        # Cluster nearby levels (within 1% of each other)
        def cluster_levels(levels, tolerance=0.01):
            if not levels:
                return []

            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]

            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                    current_cluster.append(level)
                else:
                    clusters.append(np.mean(current_cluster))
                    current_cluster = [level]

            if current_cluster:
                clusters.append(np.mean(current_cluster))

            return clusters

        resistance_levels = cluster_levels(swing_highs)
        support_levels = cluster_levels(swing_lows)

        # Filter to levels near current price (within 20%)
        nearby_resistance = [r for r in resistance_levels if r > current_price and r < current_price * 1.2]
        nearby_support = [s for s in support_levels if s < current_price and s > current_price * 0.8]

        return nearby_resistance[:5], nearby_support[:5]  # Top 5 each

    @staticmethod
    def calculate_fibonacci_levels(ohlcv: pd.DataFrame, lookback: int = 100) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels from recent swing

        Finds the most recent significant swing (high to low or low to high)
        and calculates Fib levels
        """
        high = ohlcv['high'].values[-lookback:]
        low = ohlcv['low'].values[-lookback:]
        close = ohlcv['close'].values[-lookback:]

        # Find recent swing high and low
        swing_high = np.max(high)
        swing_low = np.min(low)
        swing_range = swing_high - swing_low

        # Determine if we're in uptrend or downtrend
        current_price = close[-1]
        is_uptrend = current_price > (swing_high + swing_low) / 2

        if is_uptrend:
            # Calculate retracement levels from swing high
            fib_levels = {
                '0.0': swing_high,
                '0.236': swing_high - (swing_range * 0.236),
                '0.382': swing_high - (swing_range * 0.382),
                '0.5': swing_high - (swing_range * 0.5),
                '0.618': swing_high - (swing_range * 0.618),
                '0.786': swing_high - (swing_range * 0.786),
                '1.0': swing_low
            }
            # Extension levels (targets)
            fib_levels['1.272'] = swing_high + (swing_range * 0.272)
            fib_levels['1.618'] = swing_high + (swing_range * 0.618)
            fib_levels['2.618'] = swing_high + (swing_range * 1.618)
        else:
            # Calculate extension levels from swing low
            fib_levels = {
                '0.0': swing_low,
                '0.236': swing_low + (swing_range * 0.236),
                '0.382': swing_low + (swing_range * 0.382),
                '0.5': swing_low + (swing_range * 0.5),
                '0.618': swing_low + (swing_range * 0.618),
                '0.786': swing_low + (swing_range * 0.786),
                '1.0': swing_high
            }
            # Extension levels (targets)
            fib_levels['1.272'] = swing_low - (swing_range * 0.272)
            fib_levels['1.618'] = swing_low - (swing_range * 0.618)
            fib_levels['2.618'] = swing_low - (swing_range * 1.618)

        return fib_levels

    @staticmethod
    def analyze_bounce_patterns(ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze historical bounce-back patterns

        Finds where price reversed and bounced back,
        calculates typical bounce size
        """
        close = ohlcv['close'].values
        high = ohlcv['high'].values
        low = ohlcv['low'].values

        bounces = []

        # Look for V-shaped reversals
        for i in range(5, len(close) - 5):
            # Check if this is a local low
            if low[i] == np.min(low[i-5:i+6]):
                # Measure the bounce
                low_price = low[i]

                # Find the high within next 10 bars
                next_high = np.max(high[i:min(i+10, len(high))])
                bounce_pct = (next_high - low_price) / low_price * 100

                if bounce_pct > 0.5:  # Only count meaningful bounces
                    bounces.append(bounce_pct)

        if not bounces:
            return {
                'avg_bounce': 3.0,  # Default
                'max_bounce': 10.0,
                'typical_bounce': 5.0
            }

        return {
            'avg_bounce': np.mean(bounces),
            'max_bounce': np.max(bounces),
            'typical_bounce': np.percentile(bounces, 75)  # 75th percentile
        }

    @staticmethod
    def analyze_stop_patterns(ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze where stops should be placed

        Finds typical pullback distances before continuation
        """
        close = ohlcv['close'].values
        high = ohlcv['high'].values
        low = ohlcv['low'].values

        pullbacks = []

        # Find uptrends that had pullbacks but continued
        for i in range(10, len(close) - 10):
            # Check if we're in an uptrend
            if close[i] > close[i-10]:
                # Find maximum pullback in next 10 bars
                entry_price = close[i]
                lowest_low = np.min(low[i:min(i+10, len(low))])
                pullback_pct = (entry_price - lowest_low) / entry_price * 100

                # Check if trend continued after pullback
                final_price = close[min(i+10, len(close)-1)]
                if final_price > entry_price:  # Trend continued
                    pullbacks.append(pullback_pct)

        if not pullbacks:
            return {
                'typical_pullback': 2.0,
                'safe_stop_distance': 5.0
            }

        return {
            'typical_pullback': np.mean(pullbacks),
            'safe_stop_distance': np.percentile(pullbacks, 90)  # 90th percentile (conservative)
        }

    @staticmethod
    def create_profile(ohlcv: pd.DataFrame, symbol: str) -> TokenHistoricalProfile:
        """Create complete historical profile for token"""

        current_price = ohlcv['close'].values[-1]

        # Analyze all aspects
        volatility = HistoricalAnalyzer.analyze_volatility(ohlcv)
        resistance, support = HistoricalAnalyzer.find_support_resistance(ohlcv, current_price)
        fib_levels = HistoricalAnalyzer.calculate_fibonacci_levels(ohlcv)
        bounces = HistoricalAnalyzer.analyze_bounce_patterns(ohlcv)
        stops = HistoricalAnalyzer.analyze_stop_patterns(ohlcv)

        return TokenHistoricalProfile(
            symbol=symbol,
            avg_daily_move_pct=volatility['avg_daily_move'],
            max_daily_move_pct=volatility['max_daily_move'],
            typical_pullback_pct=stops['typical_pullback'],
            resistance_levels=resistance,
            support_levels=support,
            fib_levels=fib_levels,
            avg_bounce_pct=bounces['avg_bounce'],
            max_bounce_pct=bounces['max_bounce'],
            typical_stop_distance_pct=stops['typical_pullback'],
            safe_stop_distance_pct=stops['safe_stop_distance']
        )


# ===========================
# DYNAMIC LEVEL CALCULATOR
# ===========================

class HistoricalDynamicLevelCalculator:
    """
    Calculate FULLY DYNAMIC stop loss and take profit levels

    NO STATIC RANGES!
    Everything based on token's actual historical behavior
    """

    @staticmethod
    def calculate_levels(
        ohlcv: pd.DataFrame,
        entry_price: float,
        side: str = 'BUY',
        symbol: str = 'UNKNOWN'
    ) -> Dict:
        """
        Calculate dynamic SL and TP levels based on token history

        Args:
            ohlcv: Historical OHLCV data (at least 200 bars recommended)
            entry_price: Entry price
            side: 'BUY' or 'SELL'
            symbol: Token symbol for profile

        Returns:
            {
                'stop_loss': float,
                'tp1': float,
                'tp2': float,
                'tp3': float,
                'tp1_pct': float,
                'tp2_pct': float,
                'tp3_pct': float,
                'sl_pct': float,
                'reasoning': str,
                'profile': TokenHistoricalProfile
            }
        """

        # Create historical profile
        profile = HistoricalAnalyzer.create_profile(ohlcv, symbol)

        close = ohlcv['close'].values
        high = ohlcv['high'].values
        low = ohlcv['low'].values

        # Calculate regime
        adx = talib.ADX(high, low, close, timeperiod=14)[-1]
        rsi = talib.RSI(close, timeperiod=14)[-1]

        if side == 'BUY':
            # ========================================
            # STOP LOSS (based on token history)
            # ========================================

            # Option 1: Use nearest support level
            if profile.support_levels:
                nearest_support = max([s for s in profile.support_levels if s < entry_price], default=None)
                if nearest_support:
                    support_distance_pct = (entry_price - nearest_support) / entry_price * 100

                    # If support is within reasonable range, use it
                    if support_distance_pct < profile.safe_stop_distance_pct:
                        stop_loss = nearest_support * 0.99  # Slightly below support
                        sl_method = f"Support level at ${nearest_support:.2f}"
                    else:
                        # Support too far, use safe distance
                        stop_loss = entry_price * (1 - profile.safe_stop_distance_pct / 100)
                        sl_method = f"Safe stop distance ({profile.safe_stop_distance_pct:.1f}% typical pullback)"
                else:
                    stop_loss = entry_price * (1 - profile.safe_stop_distance_pct / 100)
                    sl_method = f"No nearby support, using {profile.safe_stop_distance_pct:.1f}% historical pullback"
            else:
                stop_loss = entry_price * (1 - profile.safe_stop_distance_pct / 100)
                sl_method = f"Historical pullback distance ({profile.safe_stop_distance_pct:.1f}%)"

            sl_pct = (entry_price - stop_loss) / entry_price * 100

            # ========================================
            # TAKE PROFITS (based on token capacity)
            # ========================================

            # Get relevant Fibonacci extension levels for uptrend
            fib_targets = []
            for fib_name, fib_price in profile.fib_levels.items():
                if fib_price > entry_price and fib_name in ['0.618', '1.0', '1.272', '1.618', '2.618']:
                    fib_pct = (fib_price - entry_price) / entry_price * 100
                    fib_targets.append((fib_name, fib_price, fib_pct))

            # Get resistance levels
            resistance_targets = []
            for resistance in profile.resistance_levels:
                if resistance > entry_price:
                    r_pct = (resistance - entry_price) / entry_price * 100
                    resistance_targets.append(('resistance', resistance, r_pct))

            # Combine all targets
            all_targets = sorted(fib_targets + resistance_targets, key=lambda x: x[2])  # Sort by %

            if len(all_targets) >= 3:
                # Use historical levels
                tp1 = all_targets[0][1]
                tp2 = all_targets[1][1]
                tp3 = all_targets[2][1]
                tp_method = f"Historical levels: {all_targets[0][0]}, {all_targets[1][0]}, {all_targets[2][0]}"

            elif len(all_targets) > 0:
                # Mix historical levels with calculated targets
                tp1 = all_targets[0][1]
                tp2 = entry_price * (1 + profile.avg_bounce_pct / 100 / 2)
                tp3 = entry_price * (1 + profile.avg_bounce_pct / 100)
                tp_method = f"Mix: Historical {all_targets[0][0]} + {profile.avg_bounce_pct:.1f}% avg bounce"

            else:
                # No historical levels, use token's typical movement
                # TP1: Conservative (50% of typical bounce)
                tp1 = entry_price * (1 + profile.avg_bounce_pct / 100 / 2)
                # TP2: Typical bounce
                tp2 = entry_price * (1 + profile.avg_bounce_pct / 100)
                # TP3: Extended (75th percentile bounce)
                tp3 = entry_price * (1 + profile.max_bounce_pct / 100 * 0.75)
                tp_method = f"Token typical: {profile.avg_bounce_pct:.1f}% avg, {profile.max_bounce_pct:.1f}% max bounce"

            # Calculate percentages
            tp1_pct = (tp1 - entry_price) / entry_price * 100
            tp2_pct = (tp2 - entry_price) / entry_price * 100
            tp3_pct = (tp3 - entry_price) / entry_price * 100

        else:  # SELL
            # Similar logic but inverted for shorts
            if profile.resistance_levels:
                nearest_resistance = min([r for r in profile.resistance_levels if r > entry_price], default=None)
                if nearest_resistance:
                    resistance_distance_pct = (nearest_resistance - entry_price) / entry_price * 100
                    if resistance_distance_pct < profile.safe_stop_distance_pct:
                        stop_loss = nearest_resistance * 1.01
                        sl_method = f"Resistance level at ${nearest_resistance:.2f}"
                    else:
                        stop_loss = entry_price * (1 + profile.safe_stop_distance_pct / 100)
                        sl_method = f"Safe stop distance ({profile.safe_stop_distance_pct:.1f}%)"
                else:
                    stop_loss = entry_price * (1 + profile.safe_stop_distance_pct / 100)
                    sl_method = f"No nearby resistance, using {profile.safe_stop_distance_pct:.1f}% historical"
            else:
                stop_loss = entry_price * (1 + profile.safe_stop_distance_pct / 100)
                sl_method = f"Historical distance ({profile.safe_stop_distance_pct:.1f}%)"

            sl_pct = (stop_loss - entry_price) / entry_price * 100

            # TPs for shorts (downside targets)
            tp1 = entry_price * (1 - profile.avg_bounce_pct / 100 / 2)
            tp2 = entry_price * (1 - profile.avg_bounce_pct / 100)
            tp3 = entry_price * (1 - profile.max_bounce_pct / 100 * 0.75)
            tp_method = f"Short targets: {profile.avg_bounce_pct:.1f}% avg move"

            tp1_pct = (entry_price - tp1) / entry_price * 100
            tp2_pct = (entry_price - tp2) / entry_price * 100
            tp3_pct = (entry_price - tp3) / entry_price * 100

        # Build reasoning
        reasoning = f"""
TOKEN PROFILE: {symbol}
• Avg daily move: {profile.avg_daily_move_pct:.1f}% | Max seen: {profile.max_daily_move_pct:.1f}%
• Typical bounce: {profile.avg_bounce_pct:.1f}% | Max bounce: {profile.max_bounce_pct:.1f}%
• Historical pullback: {profile.typical_pullback_pct:.1f}% | Safe stop: {profile.safe_stop_distance_pct:.1f}%

STOP LOSS: {sl_method}
TAKE PROFITS: {tp_method}

REGIME: {'Trending' if adx > 25 else 'Choppy' if adx < 15 else 'Neutral'} (ADX {adx:.0f})
MOMENTUM: {'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'} (RSI {rsi:.0f})
""".strip()

        return {
            'stop_loss': stop_loss,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'tp1_pct': tp1_pct,
            'tp2_pct': tp2_pct,
            'tp3_pct': tp3_pct,
            'sl_pct': sl_pct,
            'reasoning': reasoning,
            'profile': profile
        }


# ===========================
# TEST / DEMO
# ===========================

if __name__ == "__main__":
    # Fix encoding for Windows
    if os.name == 'nt' and hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Moon Dev's Historical Dynamic Level Calculator - TEST\n")

    # Fetch real BTC data for testing
    try:
        import requests

        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'BTCUSDT',
            'interval': '1h',
            'limit': 500  # 500 bars for good historical analysis
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        ohlcv = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        current_price = ohlcv['close'].iloc[-1]

        print(f"Analyzing BTC/USDT")
        print(f"Current price: ${current_price:,.2f}")
        print(f"Historical data: {len(ohlcv)} bars (1H timeframe)")
        print("\n" + "="*60)
        print("CALCULATING DYNAMIC LEVELS...")
        print("="*60 + "\n")

        # Calculate dynamic levels
        result = HistoricalDynamicLevelCalculator.calculate_levels(
            ohlcv,
            current_price,
            side='BUY',
            symbol='BTC'
        )

        print(result['reasoning'])
        print("\n" + "="*60)
        print("LEVELS CALCULATED")
        print("="*60)
        print(f"\nEntry: ${current_price:,.2f}")
        print(f"\nStop Loss: ${result['stop_loss']:,.2f} ({result['sl_pct']:.2f}%)")
        print(f"TP1: ${result['tp1']:,.2f} (+{result['tp1_pct']:.2f}%)")
        print(f"TP2: ${result['tp2']:,.2f} (+{result['tp2_pct']:.2f}%)")
        print(f"TP3: ${result['tp3']:,.2f} (+{result['tp3_pct']:.2f}%)")

        print(f"\nRisk/Reward Ratios:")
        print(f"  TP1 R:R = 1:{result['tp1_pct']/result['sl_pct']:.2f}")
        print(f"  TP2 R:R = 1:{result['tp2_pct']/result['sl_pct']:.2f}")
        print(f"  TP3 R:R = 1:{result['tp3_pct']/result['sl_pct']:.2f}")

        print("\nNO STATIC RANGES - All levels based on BTC's actual history!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
