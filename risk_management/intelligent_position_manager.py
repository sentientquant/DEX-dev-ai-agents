#!/usr/bin/env python3
"""
🌙 Moon Dev's Intelligent Position Manager

COMPLETE REAL-TIME POSITION MANAGEMENT SYSTEM

Combines:
1. Real-time risk monitoring (LOW/MODERATE/HIGH)
2. Dynamic level adjustment (cancel and update SL/TP)
3. Automatic position closing on HIGH risk
4. Profit maximization through trailing stops
5. Continuous monitoring loop

FEATURES:
- Monitors position every 30-60 seconds
- Reassesses risk based on 7 factors
- Automatically closes on HIGH risk (before hitting SL)
- Adjusts levels dynamically to maximize profits
- Trails stop loss when in profit
- Cancels and replaces orders as needed
- Logs all actions and decisions

RISK-BASED ACTIONS:
- LOW RISK: Hold, trail stop if in profit
- MODERATE RISK: Tighten stop loss, monitor closely
- HIGH RISK: Close immediately at market price
"""

import sys
import os
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pandas as pd
from datetime import datetime
from typing import Dict, Optional

from risk_management.realtime_risk_monitor import (
    RealTimeRiskMonitor,
    RiskLevel,
    RiskAssessment
)
from risk_management.binance_truth_paper_trading import (
    BinanceTruthAPI,
    BinanceTruthPaperTrader,
    PaperPosition
)


class IntelligentPositionManager:
    """
    Manages open positions intelligently with real-time risk monitoring

    Continuously:
    1. Fetches latest market data
    2. Assesses risk (LOW/MODERATE/HIGH)
    3. Takes action based on risk level
    4. Adjusts levels dynamically
    5. Closes position if risk is HIGH
    """

    def __init__(
        self,
        paper_trader: BinanceTruthPaperTrader,
        check_interval_seconds: int = 60,
        auto_close_on_high_risk: bool = True
    ):
        """
        Args:
            paper_trader: Paper trading engine
            check_interval_seconds: How often to check (30-60 seconds)
            auto_close_on_high_risk: Auto-close if risk becomes HIGH
        """
        self.paper_trader = paper_trader
        self.check_interval = check_interval_seconds
        self.auto_close_on_high_risk = auto_close_on_high_risk

        # Track monitors for each position
        self.position_monitors: Dict[str, RealTimeRiskMonitor] = {}

        print("\nIntelligent Position Manager initialized")
        print(f"   Check interval: {check_interval_seconds}s")
        print(f"   Auto-close on HIGH risk: {auto_close_on_high_risk}")

    def start_monitoring(self, position: PaperPosition):
        """
        Start monitoring a position

        Creates risk monitor and begins continuous assessment
        """
        print(f"\nStarting monitoring for {position.symbol}...")

        # Create risk monitor for this position
        monitor = RealTimeRiskMonitor(
            symbol=position.symbol,
            entry_price=position.entry_price,
            entry_time=position.entry_time,
            position_size=position.size_usd,
            side=position.side,
            initial_sl=position.stop_loss,
            initial_tp1=position.tp1_price,
            initial_tp2=position.tp2_price,
            initial_tp3=position.tp3_price,
            auto_close_on_high_risk=self.auto_close_on_high_risk
        )

        self.position_monitors[position.symbol] = monitor

    def monitor_all_positions(self):
        """
        Check all open positions and take appropriate actions

        This should be called continuously in a loop
        """
        # Get open positions
        open_positions = [p for p in self.paper_trader.positions if p.remaining_pct > 0]

        if not open_positions:
            return

        print(f"\n{'='*60}")
        print(f"MONITORING {len(open_positions)} POSITION(S) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        for position in open_positions:
            # Start monitoring if not already
            if position.symbol not in self.position_monitors:
                self.start_monitoring(position)

            # Fetch latest market data
            ohlcv = self._fetch_latest_data(position.symbol)
            if ohlcv is None:
                print(f"⚠️ Could not fetch data for {position.symbol}, skipping...")
                continue

            current_price = BinanceTruthAPI.get_live_price(position.symbol)
            if current_price is None:
                print(f"⚠️ Could not fetch current price for {position.symbol}, skipping...")
                continue

            # Get monitor
            monitor = self.position_monitors[position.symbol]

            # Assess risk
            assessment = monitor.assess_risk(ohlcv, current_price)

            # Print assessment
            monitor.print_assessment(assessment, current_price)

            # Take action based on risk level
            self._take_action(position, assessment, current_price)

    def _take_action(
        self,
        position: PaperPosition,
        assessment: RiskAssessment,
        current_price: float
    ):
        """
        Take appropriate action based on risk assessment

        Actions:
        - HIGH RISK: Close position immediately at market
        - MODERATE RISK: Tighten stop loss, or close if unprofitable
        - LOW RISK: Trail stop if in profit
        """

        # Calculate current PnL
        if position.side == 'BUY':
            pnl_pct = (current_price - position.entry_price) / position.entry_price * 100
        else:
            pnl_pct = (position.entry_price - current_price) / position.entry_price * 100

        # ========================================
        # HIGH RISK: CLOSE NOW!
        # ========================================
        if assessment.risk_level == RiskLevel.HIGH:
            print(f"\n🚨 HIGH RISK DETECTED! Closing {position.symbol} immediately...")
            print(f"   Current PnL: {pnl_pct:+.2f}%")
            print(f"   Reason: {assessment.reasoning}")

            # Close position at market
            self._close_position_at_market(position, current_price, assessment.reasoning)

            # Remove monitor
            del self.position_monitors[position.symbol]

            return

        # ========================================
        # MODERATE RISK: ADJUST OR CLOSE
        # ========================================
        elif assessment.risk_level == RiskLevel.MODERATE:
            print(f"\n⚠️ MODERATE RISK for {position.symbol}")

            # If unprofitable and moderate risk, consider closing
            if pnl_pct < 0 and assessment.risk_score > 50:
                print(f"   Unprofitable position with high moderate risk")
                print(f"   Closing to prevent further loss...")
                self._close_position_at_market(position, current_price, "Moderate risk + unprofitable")
                del self.position_monitors[position.symbol]
                return

            # If profitable, tighten stop loss
            if assessment.suggested_sl:
                print(f"   Adjusting stop loss...")
                print(f"   Old SL: ${position.stop_loss:,.2f}")
                print(f"   New SL: ${assessment.suggested_sl:,.2f}")

                # Update stop loss
                position.stop_loss = assessment.suggested_sl
                self.position_monitors[position.symbol].current_sl = assessment.suggested_sl

        # ========================================
        # LOW RISK: OPTIMIZE FOR PROFIT
        # ========================================
        elif assessment.risk_level == RiskLevel.LOW:
            # Trail stop loss if in decent profit
            if pnl_pct > 3:
                self._trail_stop_loss(position, current_price, pnl_pct)

            # Consider widening TPs if strong trend
            if pnl_pct > 5 and assessment.regime_change_risk < 20:
                print(f"\n✅ Strong trend + good profit for {position.symbol}")
                print(f"   Consider letting position run longer")
                # Could recalculate TPs here with new historical data

    def _close_position_at_market(
        self,
        position: PaperPosition,
        current_price: float,
        reason: str
    ):
        """
        Close position immediately at market price

        Simulates market order execution
        """
        # Calculate PnL
        if position.side == 'BUY':
            pnl = (current_price - position.entry_price) / position.entry_price * position.size_usd
            pnl_pct = (current_price - position.entry_price) / position.entry_price * 100
        else:
            pnl = (position.entry_price - current_price) / position.entry_price * position.size_usd
            pnl_pct = (position.entry_price - current_price) / position.entry_price * 100

        # Apply fees
        exit_fee = position.size_usd * (position.remaining_pct / 100) * 0.001  # 0.1% exit fee
        pnl -= exit_fee

        # Update position
        position.realized_pnl += pnl
        position.fees_paid += exit_fee
        position.remaining_pct = 0

        # Update trader balance
        self.paper_trader.balance += position.size_usd + pnl

        print(f"\n   ✅ Position closed at market")
        print(f"   Price: ${current_price:,.2f}")
        print(f"   PnL: ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
        print(f"   Fee: ${exit_fee:.2f}")
        print(f"   Reason: {reason}")
        print(f"   New balance: ${self.paper_trader.balance:,.2f}")

    def _trail_stop_loss(self, position: PaperPosition, current_price: float, pnl_pct: float):
        """
        Trail stop loss to protect profits

        Trails based on profit level:
        - +3-5%: Trail to breakeven
        - +5-10%: Trail to +2%
        - +10%+: Trail to +5%
        """
        if position.side == 'BUY':
            current_sl = position.stop_loss

            # Determine trail level
            if pnl_pct > 10:
                target_sl = position.entry_price * 1.05  # Lock in +5%
            elif pnl_pct > 5:
                target_sl = position.entry_price * 1.02  # Lock in +2%
            else:
                target_sl = position.entry_price * 1.001  # Breakeven

            # Only update if new SL is higher
            if target_sl > current_sl:
                print(f"\n   📈 Trailing stop loss for {position.symbol}")
                print(f"   Profit: +{pnl_pct:.2f}%")
                print(f"   Old SL: ${current_sl:,.2f}")
                print(f"   New SL: ${target_sl:,.2f} (locking in gains)")

                position.stop_loss = target_sl
                self.position_monitors[position.symbol].current_sl = target_sl

        else:
            # Trail for shorts (inverse logic)
            current_sl = position.stop_loss

            if pnl_pct > 10:
                target_sl = position.entry_price * 0.95
            elif pnl_pct > 5:
                target_sl = position.entry_price * 0.98
            else:
                target_sl = position.entry_price * 0.999

            # Only update if new SL is lower
            if target_sl < current_sl:
                print(f"\n   📈 Trailing stop loss for {position.symbol}")
                print(f"   Profit: +{pnl_pct:.2f}%")
                print(f"   Old SL: ${current_sl:,.2f}")
                print(f"   New SL: ${target_sl:,.2f} (locking in gains)")

                position.stop_loss = target_sl
                self.position_monitors[position.symbol].current_sl = target_sl

    def _fetch_latest_data(self, symbol: str, interval: str = '1h', limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch latest OHLCV data from Binance"""
        import requests

        try:
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"

            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()

            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        except Exception:
            return None

    def run_monitoring_loop(self, duration_minutes: Optional[int] = None):
        """
        Run continuous monitoring loop

        Args:
            duration_minutes: How long to run (None = forever)
        """
        print(f"\n{'='*60}")
        print("STARTING CONTINUOUS MONITORING LOOP")
        print(f"{'='*60}")
        print(f"Check interval: {self.check_interval}s")
        if duration_minutes:
            print(f"Duration: {duration_minutes} minutes")
        else:
            print("Duration: Until manually stopped (Ctrl+C)")

        start_time = datetime.now()
        check_count = 0

        try:
            while True:
                check_count += 1

                # Check all positions
                self.monitor_all_positions()

                # Check if duration reached
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        print(f"\n✅ Monitoring duration reached ({duration_minutes} min)")
                        break

                # Wait before next check
                print(f"\n⏰ Waiting {self.check_interval}s before next check...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print(f"\n\n⛔ Monitoring stopped by user")

        print(f"\nMonitoring summary:")
        print(f"   Total checks: {check_count}")
        print(f"   Duration: {(datetime.now() - start_time).total_seconds() / 60:.1f} minutes")


# ===========================
# TEST / DEMO
# ===========================

if __name__ == "__main__":
    # Fix encoding for Windows
    if os.name == 'nt' and hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Moon Dev's Intelligent Position Manager - TEST\n")

    # Initialize paper trader
    paper_trader = BinanceTruthPaperTrader(
        starting_balance_usd=500,
        max_positions=3
    )

    # Open a test position
    print("\nOpening test BTC position...")
    success, msg = paper_trader.open_position(
        symbol='BTC',
        side='BUY',
        size_usd=150,
        stop_loss=103000,
        tp1_price=109000, tp1_pct=25,
        tp2_price=111000, tp2_pct=30,
        tp3_price=117000, tp3_pct=45
    )

    if success:
        print(f"✅ Position opened")

        # Initialize intelligent manager
        manager = IntelligentPositionManager(
            paper_trader=paper_trader,
            check_interval_seconds=30,  # Check every 30 seconds
            auto_close_on_high_risk=True
        )

        # Run monitoring for 2 minutes (4 checks)
        print("\nRunning monitoring loop for 2 minutes...")
        manager.run_monitoring_loop(duration_minutes=2)

        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        print("\nIn production:")
        print("- This runs continuously while positions are open")
        print("- Checks every 30-60 seconds")
        print("- Automatically closes on HIGH risk")
        print("- Trails stops to protect profits")
        print("- Adjusts levels dynamically")

    else:
        print(f"❌ Failed to open position: {msg}")
