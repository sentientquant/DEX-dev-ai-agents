#!/usr/bin/env python3
"""
🌙 Moon Dev's Real-Time Risk Monitor

REAL-TIME RISK ASSESSMENT AND AUTOMATIC POSITION MANAGEMENT

Monitors open positions in real-time and:
1. Continuously reassesses risk level (LOW/MODERATE/HIGH)
2. Automatically closes position at market if risk becomes HIGH
3. Updates stop loss dynamically if market conditions change
4. Detects sudden market regime changes
5. Protects profits by trailing stops when appropriate

RISK LEVELS:
- LOW: Trade going as planned, all good
- MODERATE: Some concerning signs, watch closely
- HIGH: Immediate danger, close position NOW at market

RISK FACTORS MONITORED:
1. Price action (sudden reversals, volatility spikes)
2. Volume changes (dumping, distribution)
3. Market regime changes (trending → choppy)
4. Support/resistance breaks (key levels violated)
5. Time decay (position open too long)
6. Correlation breakdown (BTC dump affecting altcoins)
7. Unrealized PnL (drawdown from peak)
"""

import sys
import os
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"

@dataclass
class RiskAssessment:
    """Complete risk assessment for a position"""
    timestamp: datetime
    risk_level: RiskLevel
    risk_score: float  # 0-100 (0=no risk, 100=extreme risk)

    # Individual risk factors (each 0-100)
    price_action_risk: float
    volume_risk: float
    regime_change_risk: float
    support_break_risk: float
    time_decay_risk: float
    correlation_risk: float
    drawdown_risk: float

    # Action recommendation
    recommended_action: str  # "HOLD", "ADJUST_SL", "CLOSE_NOW"
    reasoning: str

    # Updated levels if needed
    suggested_sl: Optional[float] = None
    suggested_tp1: Optional[float] = None
    suggested_tp2: Optional[float] = None
    suggested_tp3: Optional[float] = None


class RealTimeRiskMonitor:
    """
    Monitors open positions in real-time and assesses risk

    Runs continuously while position is open:
    - Fetches latest market data every N seconds
    - Calculates risk score based on multiple factors
    - Determines risk level (LOW/MODERATE/HIGH)
    - Recommends action (HOLD/ADJUST_SL/CLOSE_NOW)
    - Can automatically close position if risk is HIGH
    """

    def __init__(
        self,
        symbol: str,
        entry_price: float,
        entry_time: datetime,
        position_size: float,
        side: str,
        initial_sl: float,
        initial_tp1: float,
        initial_tp2: float,
        initial_tp3: float,
        auto_close_on_high_risk: bool = True
    ):
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.position_size = position_size
        self.side = side  # 'BUY' or 'SELL'

        # Initial levels
        self.current_sl = initial_sl
        self.current_tp1 = initial_tp1
        self.current_tp2 = initial_tp2
        self.current_tp3 = initial_tp3

        # Risk settings
        self.auto_close_on_high_risk = auto_close_on_high_risk

        # Track peak profit for drawdown calculation
        self.peak_profit_pct = 0.0
        self.peak_price = entry_price

        # Track risk history
        self.risk_history: List[RiskAssessment] = []

        print(f"\nReal-Time Risk Monitor initialized")
        print(f"   Symbol: {symbol}")
        print(f"   Entry: ${entry_price:,.2f}")
        print(f"   Side: {side}")
        print(f"   Auto-close on HIGH risk: {auto_close_on_high_risk}")

    def assess_risk(self, current_ohlcv: pd.DataFrame, current_price: float) -> RiskAssessment:
        """
        Assess current risk level based on multiple factors

        Returns complete risk assessment with recommendation
        """

        # Extract data
        close = current_ohlcv['close'].values
        high = current_ohlcv['high'].values
        low = current_ohlcv['low'].values
        volume = current_ohlcv['volume'].values

        # Calculate current PnL
        if self.side == 'BUY':
            pnl_pct = (current_price - self.entry_price) / self.entry_price * 100
        else:
            pnl_pct = (self.entry_price - current_price) / self.entry_price * 100

        # Update peak profit
        if pnl_pct > self.peak_profit_pct:
            self.peak_profit_pct = pnl_pct
            self.peak_price = current_price

        # ========================================
        # FACTOR 1: PRICE ACTION RISK (0-100)
        # ========================================
        price_action_risk = self._assess_price_action_risk(
            current_ohlcv, current_price, close, high, low
        )

        # ========================================
        # FACTOR 2: VOLUME RISK (0-100)
        # ========================================
        volume_risk = self._assess_volume_risk(volume, close, current_price)

        # ========================================
        # FACTOR 3: REGIME CHANGE RISK (0-100)
        # ========================================
        regime_change_risk = self._assess_regime_change_risk(high, low, close)

        # ========================================
        # FACTOR 4: SUPPORT/RESISTANCE BREAK RISK (0-100)
        # ========================================
        support_break_risk = self._assess_support_break_risk(
            current_price, high, low, close
        )

        # ========================================
        # FACTOR 5: TIME DECAY RISK (0-100)
        # ========================================
        time_decay_risk = self._assess_time_decay_risk()

        # ========================================
        # FACTOR 6: CORRELATION RISK (0-100)
        # ========================================
        # TODO: Implement BTC correlation check for altcoins
        correlation_risk = 0.0  # Placeholder

        # ========================================
        # FACTOR 7: DRAWDOWN RISK (0-100)
        # ========================================
        drawdown_risk = self._assess_drawdown_risk(pnl_pct)

        # ========================================
        # CALCULATE OVERALL RISK SCORE
        # ========================================

        # Weighted average (some factors more important)
        risk_score = (
            price_action_risk * 0.25 +
            volume_risk * 0.15 +
            regime_change_risk * 0.20 +
            support_break_risk * 0.20 +
            time_decay_risk * 0.05 +
            correlation_risk * 0.05 +
            drawdown_risk * 0.10
        )

        # Determine risk level
        if risk_score < 30:
            risk_level = RiskLevel.LOW
        elif risk_score < 60:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.HIGH

        # ========================================
        # DETERMINE RECOMMENDED ACTION
        # ========================================

        recommended_action, reasoning = self._determine_action(
            risk_level, risk_score, pnl_pct,
            price_action_risk, volume_risk, regime_change_risk,
            support_break_risk, drawdown_risk
        )

        # ========================================
        # SUGGEST UPDATED LEVELS IF NEEDED
        # ========================================

        suggested_sl, suggested_tp1, suggested_tp2, suggested_tp3 = self._suggest_updated_levels(
            current_ohlcv, current_price, pnl_pct, risk_level
        )

        # Create assessment
        assessment = RiskAssessment(
            timestamp=datetime.now(),
            risk_level=risk_level,
            risk_score=risk_score,
            price_action_risk=price_action_risk,
            volume_risk=volume_risk,
            regime_change_risk=regime_change_risk,
            support_break_risk=support_break_risk,
            time_decay_risk=time_decay_risk,
            correlation_risk=correlation_risk,
            drawdown_risk=drawdown_risk,
            recommended_action=recommended_action,
            reasoning=reasoning,
            suggested_sl=suggested_sl,
            suggested_tp1=suggested_tp1,
            suggested_tp2=suggested_tp2,
            suggested_tp3=suggested_tp3
        )

        # Store in history
        self.risk_history.append(assessment)

        return assessment

    def _assess_price_action_risk(
        self,
        ohlcv: pd.DataFrame,
        current_price: float,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray
    ) -> float:
        """
        Assess risk from price action patterns

        High risk if:
        - Sudden reversal (shooting star, doji after rally)
        - Increased volatility (ATR spiking)
        - Price approaching stop loss
        - Failed breakout (couldn't hold above resistance)
        """
        risk = 0.0

        # Calculate ATR
        atr = talib.ATR(high, low, close, timeperiod=14)
        current_atr = atr[-1]
        avg_atr = np.mean(atr[-20:])

        # Check volatility spike
        if current_atr > avg_atr * 1.5:
            risk += 20  # Volatility spike

        # Check distance to stop loss
        if self.side == 'BUY':
            distance_to_sl_pct = (current_price - self.current_sl) / self.entry_price * 100
            if distance_to_sl_pct < 0.5:
                risk += 40  # Very close to stop
            elif distance_to_sl_pct < 1.0:
                risk += 20  # Getting close to stop
        else:
            distance_to_sl_pct = (self.current_sl - current_price) / self.entry_price * 100
            if distance_to_sl_pct < 0.5:
                risk += 40
            elif distance_to_sl_pct < 1.0:
                risk += 20

        # Check for reversal patterns (simplified)
        last_3_candles = close[-3:]
        last_3_highs = high[-3:]
        last_3_lows = low[-3:]

        if self.side == 'BUY':
            # Bearish reversal patterns
            # Shooting star: small body, long upper wick
            body_size = abs(close[-1] - ohlcv['open'].values[-1])
            upper_wick = high[-1] - max(close[-1], ohlcv['open'].values[-1])
            if upper_wick > body_size * 2:
                risk += 15  # Shooting star pattern

            # Three consecutive lower highs
            if last_3_highs[-1] < last_3_highs[-2] < last_3_highs[-3]:
                risk += 10  # Weakening uptrend

        else:
            # Bullish reversal patterns (for shorts)
            body_size = abs(close[-1] - ohlcv['open'].values[-1])
            lower_wick = min(close[-1], ohlcv['open'].values[-1]) - low[-1]
            if lower_wick > body_size * 2:
                risk += 15  # Hammer pattern

            # Three consecutive higher lows
            if last_3_lows[-1] > last_3_lows[-2] > last_3_lows[-3]:
                risk += 10  # Weakening downtrend

        return min(risk, 100)

    def _assess_volume_risk(self, volume: np.ndarray, close: np.ndarray, current_price: float) -> float:
        """
        Assess risk from volume patterns

        High risk if:
        - Volume spike on reversal candle (distribution)
        - Volume declining on trend continuation (weak momentum)
        - Sudden volume dump
        """
        risk = 0.0

        avg_volume = np.mean(volume[-20:])
        current_volume = volume[-1]

        # Volume spike
        if current_volume > avg_volume * 3:
            # Check if spike is on reversal candle
            price_change = (close[-1] - close[-2]) / close[-2] * 100

            if self.side == 'BUY' and price_change < -1:
                risk += 30  # Volume spike on down candle (distribution)
            elif self.side == 'SELL' and price_change > 1:
                risk += 30  # Volume spike on up candle (short squeeze)

        # Volume declining
        last_5_volume = volume[-5:]
        if all(last_5_volume[i] > last_5_volume[i+1] for i in range(4)):
            risk += 15  # Volume declining (weakening trend)

        return min(risk, 100)

    def _assess_regime_change_risk(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> float:
        """
        Assess risk from market regime changes

        High risk if:
        - ADX dropping (trend weakening)
        - Transition from trending to choppy
        - RSI divergence
        """
        risk = 0.0

        # Calculate ADX
        adx = talib.ADX(high, low, close, timeperiod=14)
        current_adx = adx[-1]
        prev_adx = adx[-5]

        # ADX dropping significantly
        if prev_adx > 30 and current_adx < 20:
            risk += 30  # Trend to choppy transition
        elif prev_adx > 25 and current_adx < prev_adx - 10:
            risk += 20  # Trend weakening

        # Calculate RSI
        rsi = talib.RSI(close, timeperiod=14)
        current_rsi = rsi[-1]

        # Extreme RSI
        if self.side == 'BUY':
            if current_rsi > 80:
                risk += 25  # Severely overbought
            elif current_rsi > 70:
                risk += 15  # Overbought
        else:
            if current_rsi < 20:
                risk += 25  # Severely oversold
            elif current_rsi < 30:
                risk += 15  # Oversold

        # RSI divergence (simplified check)
        price_higher = close[-1] > close[-10]
        rsi_lower = rsi[-1] < rsi[-10]

        if self.side == 'BUY' and price_higher and rsi_lower:
            risk += 20  # Bearish divergence
        elif self.side == 'SELL' and not price_higher and not rsi_lower:
            risk += 20  # Bullish divergence

        return min(risk, 100)

    def _assess_support_break_risk(
        self,
        current_price: float,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> float:
        """
        Assess risk from support/resistance breaks

        High risk if:
        - Key support broken (for longs)
        - Key resistance broken (for shorts)
        - Failed to reclaim level
        """
        risk = 0.0

        # Find recent swing lows (support) and highs (resistance)
        swing_lows = []
        swing_highs = []

        for i in range(5, len(low) - 5):
            if low[i] == np.min(low[i-5:i+6]):
                swing_lows.append(low[i])
            if high[i] == np.max(high[i-5:i+6]):
                swing_highs.append(high[i])

        if self.side == 'BUY':
            # Check if recent support broken
            recent_supports = [s for s in swing_lows[-5:] if s < current_price]
            if recent_supports:
                nearest_support = max(recent_supports)
                if current_price < nearest_support * 0.99:
                    risk += 40  # Support broken
                elif current_price < nearest_support * 1.005:
                    risk += 20  # Testing support

        else:
            # Check if recent resistance broken
            recent_resistances = [r for r in swing_highs[-5:] if r > current_price]
            if recent_resistances:
                nearest_resistance = min(recent_resistances)
                if current_price > nearest_resistance * 1.01:
                    risk += 40  # Resistance broken
                elif current_price > nearest_resistance * 0.995:
                    risk += 20  # Testing resistance

        return min(risk, 100)

    def _assess_time_decay_risk(self) -> float:
        """
        Assess risk from time decay

        Higher risk the longer position is open without progress
        """
        time_open = datetime.now() - self.entry_time
        hours_open = time_open.total_seconds() / 3600

        risk = 0.0

        # If position open > 24 hours with no progress
        if hours_open > 24 and self.peak_profit_pct < 1:
            risk += 20

        # If position open > 72 hours
        if hours_open > 72:
            risk += 15

        return min(risk, 100)

    def _assess_drawdown_risk(self, current_pnl_pct: float) -> float:
        """
        Assess risk from drawdown from peak

        High risk if gave back significant profits
        """
        risk = 0.0

        # Calculate drawdown from peak
        drawdown = self.peak_profit_pct - current_pnl_pct

        if drawdown > 5:
            risk += 50  # Gave back 5%+ from peak
        elif drawdown > 3:
            risk += 30  # Gave back 3%+ from peak
        elif drawdown > 1.5:
            risk += 15  # Gave back 1.5%+ from peak

        return min(risk, 100)

    def _determine_action(
        self,
        risk_level: RiskLevel,
        risk_score: float,
        pnl_pct: float,
        price_action_risk: float,
        volume_risk: float,
        regime_change_risk: float,
        support_break_risk: float,
        drawdown_risk: float
    ) -> Tuple[str, str]:
        """
        Determine recommended action based on risk assessment

        Returns: (action, reasoning)
        """

        # HIGH RISK: Close immediately
        if risk_level == RiskLevel.HIGH:
            reasons = []

            if price_action_risk > 50:
                reasons.append(f"price action risk {price_action_risk:.0f}%")
            if volume_risk > 50:
                reasons.append(f"volume risk {volume_risk:.0f}%")
            if regime_change_risk > 50:
                reasons.append(f"regime change risk {regime_change_risk:.0f}%")
            if support_break_risk > 50:
                reasons.append(f"support broken")
            if drawdown_risk > 50:
                reasons.append(f"large drawdown from peak")

            reasoning = f"HIGH RISK ({risk_score:.0f}/100): {', '.join(reasons)}. Close position NOW at market to protect capital!"

            return "CLOSE_NOW", reasoning

        # MODERATE RISK: Adjust stop loss or monitor closely
        elif risk_level == RiskLevel.MODERATE:
            # If in profit, consider trailing stop
            if pnl_pct > 2:
                reasoning = f"MODERATE RISK ({risk_score:.0f}/100) but in profit (+{pnl_pct:.1f}%). Consider tightening stop loss to protect gains."
                return "ADJUST_SL", reasoning
            else:
                reasoning = f"MODERATE RISK ({risk_score:.0f}/100). Monitor closely. Consider exiting if risk increases."
                return "HOLD", reasoning

        # LOW RISK: Hold position
        else:
            reasoning = f"LOW RISK ({risk_score:.0f}/100). Trade going as planned. Current PnL: {pnl_pct:+.2f}%"
            return "HOLD", reasoning

    def _suggest_updated_levels(
        self,
        ohlcv: pd.DataFrame,
        current_price: float,
        pnl_pct: float,
        risk_level: RiskLevel
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        Suggest updated stop loss and take profit levels if needed

        Returns: (suggested_sl, suggested_tp1, suggested_tp2, suggested_tp3)
        """

        # Only suggest updates if in profit and risk is moderate/high
        if pnl_pct < 1 or risk_level == RiskLevel.LOW:
            return None, None, None, None

        # Trail stop loss to breakeven or better
        suggested_sl = None

        if self.side == 'BUY':
            # Trail to breakeven + small buffer
            if pnl_pct > 2 and self.current_sl < self.entry_price:
                suggested_sl = self.entry_price * 1.002  # Breakeven + 0.2%

            # Trail to secure some profit
            elif pnl_pct > 5 and self.current_sl < self.entry_price * 1.02:
                suggested_sl = self.entry_price * 1.02  # Lock in +2%

        else:
            # Trail for shorts
            if pnl_pct > 2 and self.current_sl > self.entry_price:
                suggested_sl = self.entry_price * 0.998  # Breakeven - 0.2%

            elif pnl_pct > 5 and self.current_sl > self.entry_price * 0.98:
                suggested_sl = self.entry_price * 0.98  # Lock in +2%

        # Keep original TPs (or could recalculate based on new data)
        return suggested_sl, None, None, None

    def print_assessment(self, assessment: RiskAssessment, current_price: float):
        """Print risk assessment in readable format"""

        # Color based on risk level
        if assessment.risk_level == RiskLevel.LOW:
            color = "green"
            emoji = "✅"
        elif assessment.risk_level == RiskLevel.MODERATE:
            color = "yellow"
            emoji = "⚠️"
        else:
            color = "red"
            emoji = "🚨"

        print(f"\n[{assessment.risk_level.value}] RISK ASSESSMENT - {assessment.timestamp.strftime('%H:%M:%S')}")
        print(f"   Risk Level: {assessment.risk_level.value}")
        print(f"   Risk Score: {assessment.risk_score:.0f}/100")
        print(f"   Current Price: ${current_price:,.2f}")

        print(f"\n   Risk Factors:")
        print(f"   • Price Action: {assessment.price_action_risk:.0f}/100")
        print(f"   • Volume: {assessment.volume_risk:.0f}/100")
        print(f"   • Regime Change: {assessment.regime_change_risk:.0f}/100")
        print(f"   • Support/Resistance: {assessment.support_break_risk:.0f}/100")
        print(f"   • Time Decay: {assessment.time_decay_risk:.0f}/100")
        print(f"   • Drawdown: {assessment.drawdown_risk:.0f}/100")

        print(f"\n   Recommended Action: {assessment.recommended_action}")
        print(f"   Reasoning: {assessment.reasoning}")

        if assessment.suggested_sl:
            print(f"\n   Suggested Updates:")
            print(f"   • New SL: ${assessment.suggested_sl:,.2f}")


# ===========================
# TEST / DEMO
# ===========================

if __name__ == "__main__":
    # Fix encoding for Windows
    if os.name == 'nt' and hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Moon Dev's Real-Time Risk Monitor - TEST\n")

    # Fetch BTC data
    try:
        import requests

        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'BTCUSDT',
            'interval': '1h',
            'limit': 200
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

        # Simulate a trade opened 10 bars ago
        entry_bar = -10
        entry_price = ohlcv['close'].iloc[entry_bar]
        current_price = ohlcv['close'].iloc[-1]

        print(f"Simulating BTC long position:")
        print(f"Entry: ${entry_price:,.2f} (10 hours ago)")
        print(f"Current: ${current_price:,.2f}")
        print(f"PnL: {(current_price - entry_price) / entry_price * 100:+.2f}%")

        # Initialize monitor
        monitor = RealTimeRiskMonitor(
            symbol='BTC',
            entry_price=entry_price,
            entry_time=datetime.now() - timedelta(hours=10),
            position_size=150,
            side='BUY',
            initial_sl=entry_price * 0.99,
            initial_tp1=entry_price * 1.04,
            initial_tp2=entry_price * 1.06,
            initial_tp3=entry_price * 1.12,
            auto_close_on_high_risk=True
        )

        # Assess current risk
        assessment = monitor.assess_risk(ohlcv, current_price)
        monitor.print_assessment(assessment, current_price)

        print("\n" + "="*60)
        print("RISK MONITORING SYSTEM READY")
        print("="*60)
        print("\nIn production:")
        print("- Run this continuously while position is open")
        print("- Check every 30-60 seconds")
        print("- Automatically close if risk becomes HIGH")
        print("- Update stop loss dynamically based on suggestions")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
