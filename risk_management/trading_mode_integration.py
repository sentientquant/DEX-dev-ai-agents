#!/usr/bin/env python3
"""
🌙 Moon Dev's Trading Mode Integration Layer
Connects Dynamic Risk Engine to all 4 trading modes with unified interface

PHILOSOPHY:
One risk engine, four trading modes, zero risk duplication.
Each mode gets risk-adjusted position sizes, SL/TP, and trade approvals.

TRADING MODES:
1. AI Swarm Trading - Multi-agent consensus
2. Strategy-Based Trading - Backtested strategies
3. CopyBot Trading - Following top traders
4. RBI Research Trading - AI-generated strategies

INTEGRATION POINTS:
- Pre-trade validation (confidence, exposure, limits)
- Position sizing (equity, ATR, token risk, regime)
- Stop loss / Take profit calculation
- Portfolio limit checks (max loss, max gain, exposure)
- Real-time regime adaptation

DESIGNED BY: Moon Dev
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from datetime import datetime
import logging

from risk_management.dynamic_risk_engine import (
    DynamicRiskEngine,
    TokenRiskProfile,
    MarketRegime,
    DynamicLimits
)

# Import trading utilities
from src.nice_funcs import get_ohlcv_data, token_price, get_portfolio_value

class RiskIntegrationLayer:
    """
    Unified risk integration for all trading modes
    """

    def __init__(self, enable_risk_checks: bool = True):
        """
        Initialize risk integration layer

        Args:
            enable_risk_checks: If False, acts as passthrough (for testing)
        """
        self.risk_engine = DynamicRiskEngine()
        self.enable_risk_checks = enable_risk_checks

        # Track current portfolio state
        self.current_equity_usd: float = 0.0
        self.current_exposure_usd: float = 0.0
        self.session_pnl_usd: float = 0.0
        self.session_start_time: datetime = datetime.now()

        # PnL history for dynamic limits
        self.pnl_history: List[Dict] = []

        logging.info(f"🌙 Risk Integration Layer initialized (checks: {'ON' if enable_risk_checks else 'OFF'})")

    def update_market_conditions(self, reference_symbol: str = 'BTC'):
        """
        Update market regime using reference asset (usually BTC)

        Args:
            reference_symbol: Symbol to use for regime detection (default: BTC)
        """
        try:
            # Get OHLCV data for reference asset
            ohlcv = get_ohlcv_data(reference_symbol, timeframe='1H', days_back=10)

            if ohlcv is None or len(ohlcv) < 200:
                logging.warning(f"⚠️ Insufficient data for regime detection ({reference_symbol})")
                return False

            # Update regime
            self.risk_engine.update_regime(ohlcv)

            return True

        except Exception as e:
            logging.error(f"❌ Error updating market conditions: {e}")
            return False

    def update_token_risk(
        self,
        symbol: str,
        timeframe: str = '15m',
        days_back: int = 7
    ) -> bool:
        """
        Update risk profile for a token

        Args:
            symbol: Token symbol
            timeframe: OHLCV timeframe
            days_back: Days of historical data

        Returns:
            True if successful
        """
        try:
            # Get OHLCV data
            ohlcv = get_ohlcv_data(symbol, timeframe=timeframe, days_back=days_back)

            if ohlcv is None or len(ohlcv) < 50:
                logging.warning(f"⚠️ Insufficient data for {symbol}")
                return False

            # Get market data (would come from API in production)
            # For now, use estimates based on symbol
            volume_24h_usd = self._estimate_volume(symbol, ohlcv)
            market_cap_usd = self._estimate_market_cap(symbol)
            avg_spread_bps = self._estimate_spread(symbol)

            # Update token profile
            self.risk_engine.update_token_profile(
                symbol=symbol,
                ohlcv_data=ohlcv,
                volume_24h_usd=volume_24h_usd,
                market_cap_usd=market_cap_usd,
                avg_spread_bps=avg_spread_bps
            )

            return True

        except Exception as e:
            logging.error(f"❌ Error updating token risk for {symbol}: {e}")
            return False

    def update_portfolio_state(self, equity_usd: float, exposure_usd: float):
        """
        Update current portfolio state

        Args:
            equity_usd: Total portfolio equity
            exposure_usd: Total position exposure (sum of all open positions)
        """
        self.current_equity_usd = equity_usd
        self.current_exposure_usd = exposure_usd

        # Calculate session PnL
        if len(self.pnl_history) > 0:
            session_start_equity = self.pnl_history[0]['equity_usd']
            self.session_pnl_usd = equity_usd - session_start_equity

        # Store PnL history
        self.pnl_history.append({
            'timestamp': datetime.now(),
            'equity_usd': equity_usd,
            'pnl_usd': self.session_pnl_usd
        })

        # Update dynamic limits
        pnl_df = pd.DataFrame(self.pnl_history)
        self.risk_engine.update_limits(
            equity_usd=equity_usd,
            pnl_history=pnl_df,
            min_balance_usd=100.0  # Binance minimum
        )

    def validate_trade(
        self,
        symbol: str,
        signal_confidence: float,
        trade_direction: str,
        strategy_name: str = "Unknown"
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate if trade should be taken

        Args:
            symbol: Token symbol
            signal_confidence: Strategy confidence (0-100)
            trade_direction: 'BUY' or 'SELL'
            strategy_name: Name of strategy/agent generating signal

        Returns:
            (allowed: bool, reason: str, trade_params: Dict or None)

        trade_params contains:
            - position_size_usd: Dollar amount to trade
            - stop_loss_price: SL price
            - take_profit_price: TP price
            - risk_score: Token risk score
            - regime: Current market regime
        """
        # If risk checks disabled, allow all trades
        if not self.enable_risk_checks:
            return True, "Risk checks disabled", {
                'position_size_usd': 100.0,  # Binance minimum
                'stop_loss_price': None,
                'take_profit_price': None,
                'risk_score': 1.0,
                'regime': 'unknown'
            }

        try:
            # 1. Check if token profile exists
            if symbol not in self.risk_engine.token_profiles:
                # Try to create it
                if not self.update_token_risk(symbol):
                    return False, f"Could not create risk profile for {symbol}", None

            # 2. Get current price
            entry_price = token_price(symbol)
            if entry_price is None or entry_price <= 0:
                return False, f"Invalid price for {symbol}", None

            # 3. Calculate position sizing
            position_size_usd, sl_price, tp_price = self.risk_engine.get_position_sizing(
                symbol=symbol,
                equity_usd=self.current_equity_usd,
                entry_price=entry_price,
                min_trade_usd=100.0  # Binance minimum
            )

            if position_size_usd < 100.0:
                return False, f"Position size ${position_size_usd:.2f} < $100 Binance minimum", None

            # 4. Check trade allowed
            allowed, reason = self.risk_engine.check_trade_allowed(
                symbol=symbol,
                position_size_usd=position_size_usd,
                current_exposure_usd=self.current_exposure_usd,
                signal_confidence=signal_confidence
            )

            if not allowed:
                return False, reason, None

            # 5. Check session limits
            if self.risk_engine.current_limits:
                # Check max loss limit
                if self.session_pnl_usd <= -self.risk_engine.current_limits.max_loss_usd:
                    return False, f"Session loss limit hit: ${-self.session_pnl_usd:.2f}", None

                # Check max gain limit (profit taking)
                if self.session_pnl_usd >= self.risk_engine.current_limits.max_gain_usd:
                    return False, f"Session gain limit hit: ${self.session_pnl_usd:.2f} (profit taking)", None

            # 6. Build trade parameters
            trade_params = {
                'position_size_usd': position_size_usd,
                'stop_loss_price': sl_price,
                'take_profit_price': tp_price,
                'risk_score': self.risk_engine.token_profiles[symbol].risk_score,
                'regime': self.risk_engine.current_regime.value if self.risk_engine.current_regime else 'unknown',
                'entry_price': entry_price,
                'confidence': signal_confidence,
                'strategy': strategy_name,
                'timestamp': datetime.now()
            }

            logging.info(
                f"✅ Trade APPROVED: {symbol} {trade_direction} "
                f"${position_size_usd:.2f} @ ${entry_price:.6f} "
                f"(Risk: {trade_params['risk_score']:.2f}, "
                f"Regime: {trade_params['regime']})"
            )

            return True, "Trade approved", trade_params

        except Exception as e:
            logging.error(f"❌ Error validating trade: {e}")
            return False, f"Validation error: {str(e)}", None

    def get_risk_status(self) -> Dict:
        """
        Get current risk status for monitoring

        Returns:
            Dict with risk metrics
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'equity_usd': self.current_equity_usd,
            'exposure_usd': self.current_exposure_usd,
            'session_pnl_usd': self.session_pnl_usd,
            'session_duration_hours': (datetime.now() - self.session_start_time).seconds / 3600,
        }

        # Add risk engine summary
        risk_summary = self.risk_engine.get_risk_summary()
        status.update(risk_summary)

        return status

    def reset_session(self):
        """Reset session tracking (call at start of new trading session)"""
        self.session_pnl_usd = 0.0
        self.session_start_time = datetime.now()
        self.pnl_history = []
        logging.info("🔄 Risk session reset")

    # ===========================
    # HELPER METHODS (estimates)
    # ===========================

    def _estimate_volume(self, symbol: str, ohlcv: pd.DataFrame) -> float:
        """Estimate 24h volume from OHLCV data"""
        if 'volume' in ohlcv.columns:
            # Last 24 hours of data
            recent_vol = ohlcv['volume'].tail(96).sum()  # 96 x 15m bars = 24h
            avg_price = ohlcv['close'].tail(96).mean()
            return recent_vol * avg_price
        return 5_000_000  # Default estimate

    def _estimate_market_cap(self, symbol: str) -> float:
        """Estimate market cap based on symbol"""
        # Major coins
        if symbol in ['BTC', 'BTCUSDT', 'BITCOIN']:
            return 1_000_000_000_000  # $1T
        elif symbol in ['ETH', 'ETHUSDT', 'ETHEREUM']:
            return 300_000_000_000  # $300B
        elif symbol in ['SOL', 'SOLUSDT', 'SOLANA']:
            return 50_000_000_000  # $50B
        elif symbol in ['BNB', 'BNBUSDT']:
            return 60_000_000_000  # $60B
        else:
            # Default to small cap
            return 100_000_000  # $100M

    def _estimate_spread(self, symbol: str) -> float:
        """Estimate spread in basis points"""
        # Major pairs have tight spreads
        if symbol in ['BTC', 'BTCUSDT', 'ETH', 'ETHUSDT']:
            return 2  # 2 bps
        elif symbol in ['SOL', 'SOLUSDT', 'BNB', 'BNBUSDT']:
            return 5  # 5 bps
        else:
            return 20  # 20 bps for smaller tokens


# ===========================
# TRADING MODE ADAPTERS
# ===========================

class StrategyBasedTradingAdapter:
    """
    Adapter for Strategy-Based Trading Mode
    Wraps BaseStrategy signals with risk management
    """

    def __init__(self, risk_layer: RiskIntegrationLayer):
        self.risk_layer = risk_layer

    def process_strategy_signal(
        self,
        symbol: str,
        signal: Dict,
        strategy_name: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process strategy signal through risk layer

        Args:
            symbol: Token symbol
            signal: Dict with 'action', 'confidence', 'reasoning'
            strategy_name: Strategy name

        Returns:
            (execute: bool, reason: str, trade_params: Dict or None)
        """
        if signal['action'] not in ['BUY', 'SELL']:
            return False, f"Action {signal['action']} not tradeable", None

        return self.risk_layer.validate_trade(
            symbol=symbol,
            signal_confidence=signal.get('confidence', 50),
            trade_direction=signal['action'],
            strategy_name=strategy_name
        )


class AISwarmTradingAdapter:
    """
    Adapter for AI Swarm Trading Mode
    Validates consensus decisions with risk management
    """

    def __init__(self, risk_layer: RiskIntegrationLayer):
        self.risk_layer = risk_layer

    def process_swarm_consensus(
        self,
        symbol: str,
        consensus_action: str,
        consensus_confidence: float,
        participating_agents: List[str]
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process swarm consensus through risk layer

        Args:
            symbol: Token symbol
            consensus_action: 'BUY' or 'SELL'
            consensus_confidence: Weighted confidence (0-100)
            participating_agents: List of agent names in consensus

        Returns:
            (execute: bool, reason: str, trade_params: Dict or None)
        """
        strategy_name = f"Swarm ({len(participating_agents)} agents)"

        return self.risk_layer.validate_trade(
            symbol=symbol,
            signal_confidence=consensus_confidence,
            trade_direction=consensus_action,
            strategy_name=strategy_name
        )


class CopyBotTradingAdapter:
    """
    Adapter for CopyBot Trading Mode
    Validates copied trades with risk management
    """

    def __init__(self, risk_layer: RiskIntegrationLayer):
        self.risk_layer = risk_layer

    def process_copy_trade(
        self,
        symbol: str,
        action: str,
        source_trader: str,
        source_confidence: float = 75.0  # Default high confidence for copy trading
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process copied trade through risk layer

        Args:
            symbol: Token symbol
            action: 'BUY' or 'SELL'
            source_trader: Address/name of trader being copied
            source_confidence: Confidence in this trader (0-100)

        Returns:
            (execute: bool, reason: str, trade_params: Dict or None)
        """
        strategy_name = f"CopyBot ({source_trader[:8]}...)"

        return self.risk_layer.validate_trade(
            symbol=symbol,
            signal_confidence=source_confidence,
            trade_direction=action,
            strategy_name=strategy_name
        )


class RBIResearchTradingAdapter:
    """
    Adapter for RBI Research Trading Mode
    Validates AI-generated strategies with risk management
    """

    def __init__(self, risk_layer: RiskIntegrationLayer):
        self.risk_layer = risk_layer

    def process_rbi_signal(
        self,
        symbol: str,
        signal: Dict,
        backtest_return_pct: float,
        strategy_name: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process RBI strategy signal through risk layer

        Args:
            symbol: Token symbol
            signal: Dict with 'action', 'confidence', 'reasoning'
            backtest_return_pct: Historical backtest return (%)
            strategy_name: RBI strategy name

        Returns:
            (execute: bool, reason: str, trade_params: Dict or None)
        """
        # Adjust confidence based on backtest performance
        base_confidence = signal.get('confidence', 70)

        # Boost confidence for strong backtests
        if backtest_return_pct > 50:
            confidence_boost = min(backtest_return_pct / 10, 20)  # Cap at +20
            adjusted_confidence = min(base_confidence + confidence_boost, 100)
        else:
            adjusted_confidence = base_confidence

        strategy_label = f"RBI_{strategy_name} ({backtest_return_pct:.1f}%)"

        return self.risk_layer.validate_trade(
            symbol=symbol,
            signal_confidence=adjusted_confidence,
            trade_direction=signal['action'],
            strategy_name=strategy_label
        )


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    print("🌙 Moon Dev's Risk Integration Layer - Example Usage\n")

    # Initialize
    risk_layer = RiskIntegrationLayer(enable_risk_checks=True)

    # Update market conditions
    print("📊 Updating market regime...")
    risk_layer.update_market_conditions(reference_symbol='BTC')

    # Update portfolio state
    print("💰 Updating portfolio state...")
    risk_layer.update_portfolio_state(equity_usd=10000.0, exposure_usd=0.0)

    # Update token risk
    print("🎯 Analyzing token risk...")
    risk_layer.update_token_risk('BTC', timeframe='1H', days_back=7)

    # Validate trade
    print("\n✅ Validating sample trade...")
    allowed, reason, params = risk_layer.validate_trade(
        symbol='BTC',
        signal_confidence=85,
        trade_direction='BUY',
        strategy_name='Example Strategy'
    )

    print(f"Trade Allowed: {allowed}")
    print(f"Reason: {reason}")
    if params:
        print(f"Position Size: ${params['position_size_usd']:.2f}")
        print(f"Stop Loss: ${params['stop_loss_price']:.2f}")
        print(f"Take Profit: ${params['take_profit_price']:.2f}")

    # Get risk status
    print("\n📊 Current Risk Status:")
    status = risk_layer.get_risk_status()
    print(f"Regime: {status.get('regime', 'N/A')}")
    print(f"Equity: ${status.get('equity_usd', 0):.2f}")
    print(f"Session PnL: ${status.get('session_pnl_usd', 0):.2f}")
