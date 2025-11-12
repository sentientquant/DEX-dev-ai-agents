#!/usr/bin/env python3
"""
🌙 Moon Dev's ULTRA-INTELLIGENT DYNAMIC RISK MANAGEMENT ENGINE
Built for crypto trading with adaptive limits based on market conditions

PHILOSOPHY:
Static risk limits in crypto are like using the same brake distance for a bicycle and a Ferrari.
This system treats risk as a FUNCTION, not a constant.

CORE CAPABILITIES:
1. Per-Token Risk Scoring (volatility, liquidity, market cap, spread)
2. Volatility-Based Position Sizing (ATR-adaptive)
3. Market Regime Detection (trending/choppy/flat/crisis)
4. Dynamic Portfolio Limits (based on recent PnL volatility)
5. Timeframe-Aware Risk (5m vs 4h behave differently)
6. Real-Time Monitoring & Alerts

INTEGRATION:
- All Trading Modes (AI Swarm, Strategy-Based, CopyBot, RBI)
- Binance SPOT ($100 minimum)
- Paper Trading with 4-hour evaluation
- AI as Advisor (NOT override mechanism)

DESIGNED BY: Moon Dev + User's Deep Thinking
"""

import numpy as np
import pandas as pd
import talib
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging
import os

# ===========================
# RISK SCORE DATA STRUCTURES
# ===========================

class MarketRegime(Enum):
    """Market regime classification"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    CHOPPY = "choppy"
    FLAT = "flat"
    CRISIS = "crisis"  # Extreme volatility spike

@dataclass
class TokenRiskProfile:
    """Complete risk profile for a token"""
    symbol: str
    risk_score: float  # 0.3-1.5 (higher = riskier)

    # Components
    volatility_score: float  # Based on ATR/realized vol
    liquidity_score: float   # Based on volume/spread
    market_cap_score: float  # Large cap vs microcap

    # Market data
    current_vol: float       # Current realized volatility
    atr: float               # Average True Range
    volume_24h_usd: float    # 24h dollar volume
    avg_spread_bps: float    # Average spread in basis points

    # Risk limits for this token
    max_position_pct: float  # Max % of portfolio
    sl_multiplier: float     # Stop loss distance (x ATR)
    trade_risk_pct: float    # Risk per trade (% of equity)

    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class RegimeConfig:
    """Risk configuration for a market regime"""
    name: str
    trade_risk_pct: float  # Risk per trade
    max_daily_loss_pct: float  # Max portfolio loss per day
    max_exposure_pct: float  # Max total exposure
    sl_tightness: float  # Multiplier for SL distance (1.0 = normal)
    confidence_threshold: float  # Min confidence for entry

@dataclass
class DynamicLimits:
    """Dynamic portfolio-level limits"""
    max_loss_usd: float
    max_gain_usd: float
    max_daily_loss_usd: float
    max_position_pct: float
    max_total_exposure_pct: float
    min_balance_usd: float

    # Rationale
    based_on_equity: float
    based_on_pnl_vol: float
    current_regime: str
    last_calculated: datetime = field(default_factory=datetime.now)

# ===========================
# TOKEN RISK SCORER
# ===========================

class TokenRiskScorer:
    """Computes comprehensive risk scores for each token"""

    def __init__(self):
        # Thresholds for scoring (calibrated for crypto)
        self.HIGH_VOL_THRESHOLD = 0.05  # 5% daily volatility
        self.LOW_LIQUIDITY_THRESHOLD = 1_000_000  # $1M daily volume
        self.LARGE_CAP_THRESHOLD = 1_000_000_000  # $1B market cap
        self.TIGHT_SPREAD_THRESHOLD = 10  # 10 bps

    def compute_risk_score(
        self,
        symbol: str,
        ohlcv_data: pd.DataFrame,
        volume_24h_usd: float,
        market_cap_usd: float,
        avg_spread_bps: float
    ) -> TokenRiskProfile:
        """
        Compute complete risk profile for a token

        Args:
            symbol: Token symbol (e.g., 'BTC', 'SOL')
            ohlcv_data: DataFrame with OHLCV data
            volume_24h_usd: 24-hour dollar volume
            market_cap_usd: Market capitalization in USD
            avg_spread_bps: Average spread in basis points

        Returns:
            TokenRiskProfile with all risk metrics
        """
        # 1. VOLATILITY SCORE
        close = ohlcv_data['close'].values
        high = ohlcv_data['high'].values
        low = ohlcv_data['low'].values

        # Realized volatility (14-period std of returns)
        returns = pd.Series(close).pct_change()
        realized_vol = returns.rolling(14).std().iloc[-1]

        # ATR (14-period)
        atr = talib.ATR(high, low, close, timeperiod=14)[-1]
        atr_pct = atr / close[-1]  # ATR as % of price

        # Volatility score: higher vol = higher score
        vol_score = min(realized_vol / self.HIGH_VOL_THRESHOLD, 2.0)

        # 2. LIQUIDITY SCORE
        if volume_24h_usd > self.LOW_LIQUIDITY_THRESHOLD * 10:
            liq_score = 0.8  # Very liquid
        elif volume_24h_usd > self.LOW_LIQUIDITY_THRESHOLD:
            liq_score = 1.0  # Liquid
        else:
            liq_score = 1.5  # Illiquid (higher risk)

        # 3. MARKET CAP SCORE
        if market_cap_usd > self.LARGE_CAP_THRESHOLD * 10:
            cap_score = 0.8  # Large cap (lower risk)
        elif market_cap_usd > self.LARGE_CAP_THRESHOLD:
            cap_score = 1.0  # Mid cap
        else:
            cap_score = 1.3  # Small/micro cap (higher risk)

        # 4. SPREAD SCORE
        spread_score = 1.0 if avg_spread_bps < self.TIGHT_SPREAD_THRESHOLD else 1.2

        # COMPOSITE RISK SCORE
        raw_score = vol_score * liq_score * cap_score * spread_score
        risk_score = min(max(raw_score / 2.5, 0.3), 1.5)  # Clamp to 0.3-1.5

        # COMPUTE TOKEN-SPECIFIC LIMITS
        base_max_pos_pct = 0.30  # 30% max for low-risk tokens
        max_position_pct = min(base_max_pos_pct / risk_score, base_max_pos_pct)

        # Stop loss: tighter for high-vol tokens
        sl_multiplier = 1.5 + (risk_score - 1.0) * 0.5  # 1.5-2.5x ATR

        # Trade risk: lower for risky tokens
        trade_risk_pct = (0.005 / risk_score)  # 0.5% base / risk_score

        return TokenRiskProfile(
            symbol=symbol,
            risk_score=risk_score,
            volatility_score=vol_score,
            liquidity_score=liq_score,
            market_cap_score=cap_score,
            current_vol=realized_vol,
            atr=atr,
            volume_24h_usd=volume_24h_usd,
            avg_spread_bps=avg_spread_bps,
            max_position_pct=max_position_pct,
            sl_multiplier=sl_multiplier,
            trade_risk_pct=trade_risk_pct
        )

# ===========================
# VOLATILITY POSITION SIZER
# ===========================

class VolatilityPositionSizer:
    """ATR-based position sizing that adapts to volatility"""

    def compute_position_size(
        self,
        equity_usd: float,
        entry_price: float,
        token_profile: TokenRiskProfile,
        regime_config: RegimeConfig,
        min_trade_usd: float = 100.0  # Binance minimum
    ) -> Tuple[float, float, float]:
        """
        Compute position size, stop loss, and take profit

        Args:
            equity_usd: Current portfolio equity
            entry_price: Entry price for the trade
            token_profile: Risk profile for this token
            regime_config: Current market regime configuration
            min_trade_usd: Minimum trade size (Binance: $100)

        Returns:
            (position_size_usd, stop_loss_price, take_profit_price)
        """
        # 1. Calculate risk per trade
        base_risk_usd = equity_usd * regime_config.trade_risk_pct
        adjusted_risk_usd = base_risk_usd / token_profile.risk_score

        # 2. Calculate stop loss distance
        sl_distance = token_profile.sl_multiplier * token_profile.atr
        sl_distance *= regime_config.sl_tightness  # Adjust for regime

        if sl_distance <= 0:
            return 0, 0, 0

        # 3. Position size based on SL distance
        size_tokens = adjusted_risk_usd / sl_distance
        position_size_usd = size_tokens * entry_price

        # 4. Apply max position limit
        max_pos_usd = equity_usd * token_profile.max_position_pct
        if position_size_usd > max_pos_usd:
            position_size_usd = max_pos_usd
            size_tokens = position_size_usd / entry_price

        # 5. Enforce minimum trade size
        if position_size_usd < min_trade_usd:
            # Scale up to minimum, but warn about increased risk
            position_size_usd = min_trade_usd
            size_tokens = position_size_usd / entry_price
            logging.warning(
                f"Position size scaled to ${min_trade_usd:.2f} minimum. "
                f"Risk/reward may be suboptimal."
            )

        # 6. Calculate SL and TP prices
        stop_loss_price = entry_price - sl_distance
        # Target 2:1 or 3:1 risk/reward depending on regime
        rr_ratio = 2.5 if regime_config.name != "crisis" else 2.0
        take_profit_price = entry_price + (sl_distance * rr_ratio)

        return position_size_usd, stop_loss_price, take_profit_price

# ===========================
# MARKET REGIME DETECTOR
# ===========================

class MarketRegimeDetector:
    """Detects current market regime for adaptive risk"""

    def detect_regime(
        self,
        ohlcv_data: pd.DataFrame,
        portfolio_data: Optional[pd.DataFrame] = None
    ) -> Tuple[MarketRegime, RegimeConfig]:
        """
        Detect current market regime

        Args:
            ohlcv_data: OHLCV data for primary market (BTC usually)
            portfolio_data: Optional portfolio PnL history

        Returns:
            (MarketRegime, RegimeConfig)
        """
        close = ohlcv_data['close'].values
        high = ohlcv_data['high'].values
        low = ohlcv_data['low'].values

        # 1. TREND STRENGTH (ADX)
        adx = talib.ADX(high, low, close, timeperiod=14)[-1]
        plus_di = talib.PLUS_DI(high, low, close, timeperiod=14)[-1]
        minus_di = talib.MINUS_DI(high, low, close, timeperiod=14)[-1]

        # 2. VOLATILITY (ATR vs historical)
        atr = talib.ATR(high, low, close, timeperiod=14)
        atr_current = atr[-1]
        atr_avg = np.mean(atr[-50:])
        vol_ratio = atr_current / atr_avg

        # 3. PRICE vs MOVING AVERAGES
        sma_50 = talib.SMA(close, timeperiod=50)[-1]
        sma_200 = talib.SMA(close, timeperiod=200)[-1]
        price_current = close[-1]

        # REGIME DETECTION LOGIC

        # CRISIS: Volatility spike (ATR > 2x average)
        if vol_ratio > 2.0:
            return MarketRegime.CRISIS, RegimeConfig(
                name="crisis",
                trade_risk_pct=0.0025,  # 0.25% risk per trade (very low)
                max_daily_loss_pct=1.5,  # 1.5% max daily loss
                max_exposure_pct=0.30,   # Max 30% exposed
                sl_tightness=0.8,         # Tighter stops
                confidence_threshold=90   # High confidence required
            )

        # TRENDING UP: Strong uptrend
        if adx > 25 and plus_di > minus_di and price_current > sma_50 > sma_200:
            return MarketRegime.TRENDING_UP, RegimeConfig(
                name="trending_up",
                trade_risk_pct=0.0075,  # 0.75% risk per trade
                max_daily_loss_pct=4.0,  # 4% max daily loss
                max_exposure_pct=0.60,   # Can be more exposed
                sl_tightness=1.0,         # Normal stops
                confidence_threshold=70   # Lower confidence OK
            )

        # TRENDING DOWN: Strong downtrend
        if adx > 25 and minus_di > plus_di and price_current < sma_50 < sma_200:
            return MarketRegime.TRENDING_DOWN, RegimeConfig(
                name="trending_down",
                trade_risk_pct=0.005,   # 0.5% risk (medium caution)
                max_daily_loss_pct=3.0,  # 3% max daily loss
                max_exposure_pct=0.40,   # Less exposure
                sl_tightness=0.9,         # Slightly tighter stops
                confidence_threshold=75   # Medium confidence
            )

        # CHOPPY: Weak trend, high volatility
        if adx < 20 and vol_ratio > 1.2:
            return MarketRegime.CHOPPY, RegimeConfig(
                name="choppy",
                trade_risk_pct=0.0035,  # 0.35% risk (low)
                max_daily_loss_pct=2.5,  # 2.5% max daily loss
                max_exposure_pct=0.35,   # Low exposure
                sl_tightness=0.85,        # Tighter stops
                confidence_threshold=80   # Higher confidence needed
            )

        # FLAT: Weak trend, low volatility
        return MarketRegime.FLAT, RegimeConfig(
            name="flat",
            trade_risk_pct=0.005,   # 0.5% risk (normal)
            max_daily_loss_pct=3.0,  # 3% max daily loss
            max_exposure_pct=0.50,   # Medium exposure
            sl_tightness=1.0,         # Normal stops
            confidence_threshold=75   # Medium confidence
        )

# ===========================
# DYNAMIC LIMITS CALCULATOR
# ===========================

class DynamicLimitsCalculator:
    """Calculates adaptive portfolio-level limits"""

    def compute_limits(
        self,
        equity_usd: float,
        pnl_history: pd.DataFrame,
        regime_config: RegimeConfig,
        min_balance_usd: float = 100.0
    ) -> DynamicLimits:
        """
        Compute dynamic portfolio limits

        Args:
            equity_usd: Current portfolio equity
            pnl_history: DataFrame with timestamp and pnl_usd columns
            regime_config: Current market regime configuration
            min_balance_usd: Minimum balance threshold

        Returns:
            DynamicLimits object
        """
        # 1. Calculate recent PnL volatility (30-day standard deviation)
        if len(pnl_history) > 1:
            daily_pnl = pnl_history['pnl_usd'].diff().dropna()
            pnl_vol = daily_pnl.std() if len(daily_pnl) > 0 else 0
        else:
            # No history: use conservative estimate
            pnl_vol = equity_usd * 0.02  # Assume 2% daily vol

        # 2. Daily loss limit (based on PnL vol and regime)
        var_based_limit = 2.0 * pnl_vol  # 2x daily volatility
        regime_based_limit = equity_usd * regime_config.max_daily_loss_pct / 100

        # Take the more conservative of the two
        max_daily_loss_usd = min(var_based_limit, regime_based_limit)

        # Clamp between 1% and 5% of equity
        floor = equity_usd * 0.01
        cap = equity_usd * 0.05
        max_daily_loss_usd = min(max(max_daily_loss_usd, floor), cap)

        # 3. Session loss limit (12-hour window - 60% of daily)
        max_loss_usd = max_daily_loss_usd * 0.6

        # 4. Gain limit (2x loss limit for profit taking)
        max_gain_usd = max_loss_usd * 2.0

        # 5. Position size limit (from regime)
        max_position_pct = regime_config.max_exposure_pct / 3.0  # Individual position

        # 6. Total exposure limit
        max_total_exposure_pct = regime_config.max_exposure_pct

        return DynamicLimits(
            max_loss_usd=max_loss_usd,
            max_gain_usd=max_gain_usd,
            max_daily_loss_usd=max_daily_loss_usd,
            max_position_pct=max_position_pct,
            max_total_exposure_pct=max_total_exposure_pct,
            min_balance_usd=min_balance_usd,
            based_on_equity=equity_usd,
            based_on_pnl_vol=pnl_vol,
            current_regime=regime_config.name
        )

# ===========================
# MAIN RISK ENGINE
# ===========================

class DynamicRiskEngine:
    """
    Main risk management engine that coordinates all components
    """

    def __init__(self):
        self.token_scorer = TokenRiskScorer()
        self.position_sizer = VolatilityPositionSizer()
        self.regime_detector = MarketRegimeDetector()
        self.limits_calculator = DynamicLimitsCalculator()

        # Cache
        self.token_profiles: Dict[str, TokenRiskProfile] = {}
        self.current_regime: Optional[MarketRegime] = None
        self.current_regime_config: Optional[RegimeConfig] = None
        self.current_limits: Optional[DynamicLimits] = None

        logging.info("🌙 Dynamic Risk Engine initialized")

    def update_regime(self, market_data: pd.DataFrame):
        """Update market regime detection"""
        self.current_regime, self.current_regime_config = \
            self.regime_detector.detect_regime(market_data)
        logging.info(f"📊 Market Regime: {self.current_regime.value}")

    def update_token_profile(
        self,
        symbol: str,
        ohlcv_data: pd.DataFrame,
        volume_24h_usd: float,
        market_cap_usd: float,
        avg_spread_bps: float
    ):
        """Update risk profile for a token"""
        profile = self.token_scorer.compute_risk_score(
            symbol, ohlcv_data, volume_24h_usd, market_cap_usd, avg_spread_bps
        )
        self.token_profiles[symbol] = profile
        logging.info(
            f"🎯 {symbol} Risk Score: {profile.risk_score:.2f} "
            f"(Max Position: {profile.max_position_pct*100:.1f}%)"
        )

    def update_limits(
        self,
        equity_usd: float,
        pnl_history: pd.DataFrame,
        min_balance_usd: float = 100.0
    ):
        """Update dynamic portfolio limits"""
        if self.current_regime_config is None:
            raise ValueError("Must call update_regime() first")

        self.current_limits = self.limits_calculator.compute_limits(
            equity_usd, pnl_history, self.current_regime_config, min_balance_usd
        )
        logging.info(
            f"💰 Dynamic Limits Updated: "
            f"Max Loss: ${self.current_limits.max_loss_usd:.2f}, "
            f"Max Gain: ${self.current_limits.max_gain_usd:.2f}"
        )

    def get_position_sizing(
        self,
        symbol: str,
        equity_usd: float,
        entry_price: float,
        min_trade_usd: float = 100.0
    ) -> Tuple[float, float, float]:
        """
        Get position size, SL, and TP for a trade

        Returns:
            (position_size_usd, stop_loss_price, take_profit_price)
        """
        if symbol not in self.token_profiles:
            raise ValueError(f"No risk profile for {symbol}. Call update_token_profile() first.")

        if self.current_regime_config is None:
            raise ValueError("Must call update_regime() first")

        return self.position_sizer.compute_position_size(
            equity_usd,
            entry_price,
            self.token_profiles[symbol],
            self.current_regime_config,
            min_trade_usd
        )

    def check_trade_allowed(
        self,
        symbol: str,
        position_size_usd: float,
        current_exposure_usd: float,
        signal_confidence: float
    ) -> Tuple[bool, str]:
        """
        Check if a trade is allowed given current risk limits

        Returns:
            (allowed: bool, reason: str)
        """
        if self.current_limits is None or self.current_regime_config is None:
            return False, "Risk engine not initialized"

        # 1. Check confidence threshold
        if signal_confidence < self.current_regime_config.confidence_threshold:
            return False, f"Confidence {signal_confidence}% < {self.current_regime_config.confidence_threshold}% required"

        # 2. Check position size limit
        if symbol in self.token_profiles:
            max_pos_pct = self.token_profiles[symbol].max_position_pct
            if position_size_usd / self.current_limits.based_on_equity > max_pos_pct:
                return False, f"Position {position_size_usd:.2f} exceeds {max_pos_pct*100:.1f}% limit"

        # 3. Check total exposure limit
        new_exposure = current_exposure_usd + position_size_usd
        max_exposure = self.current_limits.based_on_equity * self.current_limits.max_total_exposure_pct
        if new_exposure > max_exposure:
            return False, f"Total exposure would exceed {self.current_limits.max_total_exposure_pct*100:.1f}%"

        return True, "Trade allowed"

    def get_risk_summary(self) -> Dict:
        """Get current risk status summary"""
        return {
            'regime': self.current_regime.value if self.current_regime else None,
            'regime_config': {
                'trade_risk_pct': self.current_regime_config.trade_risk_pct * 100,
                'max_daily_loss_pct': self.current_regime_config.max_daily_loss_pct,
                'confidence_threshold': self.current_regime_config.confidence_threshold
            } if self.current_regime_config else None,
            'limits': {
                'max_loss_usd': self.current_limits.max_loss_usd,
                'max_gain_usd': self.current_limits.max_gain_usd,
                'max_daily_loss_usd': self.current_limits.max_daily_loss_usd,
                'max_position_pct': self.current_limits.max_position_pct * 100,
                'max_exposure_pct': self.current_limits.max_total_exposure_pct * 100
            } if self.current_limits else None,
            'token_profiles': {
                symbol: {
                    'risk_score': profile.risk_score,
                    'max_position_pct': profile.max_position_pct * 100,
                    'trade_risk_pct': profile.trade_risk_pct * 100
                }
                for symbol, profile in self.token_profiles.items()
            }
        }

if __name__ == "__main__":
    # Set UTF-8 encoding for Windows terminal (fixes emoji display issues)
    import sys
    import io
    if os.name == 'nt':  # Windows
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # Example usage
    logging.basicConfig(level=logging.INFO)

    print("🌙 Moon Dev's Dynamic Risk Engine - Example Usage\n")

    # This would be integrated with your trading system
    # See integration examples in the README
