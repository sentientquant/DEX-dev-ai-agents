#!/usr/bin/env python3
"""
🌙 Moon Dev's Real-Time Risk Monitoring Dashboard
Terminal-based dashboard for monitoring risk metrics across all trading modes

PHILOSOPHY:
"You can't manage what you don't measure."
Real-time visibility prevents blow-ups and builds confidence.

FEATURES:
- Live risk metrics (regime, limits, exposure)
- Per-token risk scores
- Session PnL tracking
- Circuit breaker status
- Portfolio allocation breakdown
- Performance statistics
- Alert system for risk violations

DISPLAY LAYOUT:
┌─────────────────────────────────────────────────────────────┐
│ 🌙 MOON DEV'S RISK DASHBOARD                               │
│ Market Regime: TRENDING_UP | Session: 2.5h / 12h           │
├─────────────────────────────────────────────────────────────┤
│ PORTFOLIO STATUS                                            │
│ Equity: $10,245.50 | Exposure: $3,150.00 (30.7%)          │
│ Session PnL: +$245.50 (+2.45%)                             │
│ Max Loss Limit: -$420.00 | Max Gain: $840.00              │
├─────────────────────────────────────────────────────────────┤
│ TOKEN RISK SCORES                                           │
│ BTC: 0.85 (Low) | ETH: 0.95 (Low) | SOL: 1.25 (Med)      │
├─────────────────────────────────────────────────────────────┤
│ ACTIVE POSITIONS                                            │
│ BTC $1,500 +2.5% | ETH $1,200 +1.8% | SOL $450 -0.5%     │
├─────────────────────────────────────────────────────────────┤
│ CIRCUIT BREAKERS                                            │
│ ✅ Session Loss OK | ✅ Exposure OK | ✅ Balance OK        │
└─────────────────────────────────────────────────────────────┘

DESIGNED BY: Moon Dev
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from termcolor import colored

from risk_management.trading_mode_integration import RiskIntegrationLayer
from src.nice_funcs import get_portfolio_value, get_positions

# ===========================
# DASHBOARD RENDERER
# ===========================

class RiskDashboard:
    """
    Real-time terminal dashboard for risk monitoring
    """

    def __init__(self, risk_layer: RiskIntegrationLayer, refresh_seconds: int = 5):
        """
        Initialize risk dashboard

        Args:
            risk_layer: Risk integration layer instance
            refresh_seconds: Dashboard refresh interval
        """
        self.risk_layer = risk_layer
        self.refresh_seconds = refresh_seconds
        self.running = False

        # Dashboard history
        self.alert_history: List[Dict] = []
        self.max_alerts_shown = 5

    def start(self):
        """Start the dashboard (blocking)"""
        self.running = True
        print("🌙 Starting Risk Dashboard...")
        print("Press Ctrl+C to stop\n")

        try:
            while self.running:
                self._render()
                time.sleep(self.refresh_seconds)
        except KeyboardInterrupt:
            print("\n\n🌙 Dashboard stopped")
            self.running = False

    def stop(self):
        """Stop the dashboard"""
        self.running = False

    def _render(self):
        """Render the dashboard"""
        # Clear screen (cross-platform)
        os.system('cls' if os.name == 'nt' else 'clear')

        # Get risk status
        status = self.risk_layer.get_risk_status()

        # Render sections
        self._render_header(status)
        self._render_portfolio_status(status)
        self._render_token_risk_scores(status)
        self._render_active_positions()
        self._render_circuit_breakers(status)
        self._render_performance_stats(status)
        self._render_alerts()

        # Footer
        print("\n" + "─" * 70)
        print(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Refresh: {self.refresh_seconds}s")
        print("Press Ctrl+C to stop")

    def _render_header(self, status: Dict):
        """Render dashboard header"""
        print("┌" + "─" * 68 + "┐")
        print("│" + colored(" 🌙 MOON DEV'S RISK DASHBOARD", 'cyan', attrs=['bold']).ljust(78) + "│")

        # Regime and session info
        regime = status.get('regime', 'UNKNOWN').upper()
        regime_color = self._get_regime_color(regime)

        elapsed_hours = status.get('session_duration_hours', 0)
        session_info = f"Session: {elapsed_hours:.1f}h / 12h"

        line = f"│ Market Regime: {colored(regime, regime_color, attrs=['bold'])} | {session_info}"
        padding = 70 - len(f"Market Regime: {regime} | {session_info}")
        print(line + " " * padding + "│")

        print("├" + "─" * 68 + "┤")

    def _render_portfolio_status(self, status: Dict):
        """Render portfolio status section"""
        print("│ " + colored("PORTFOLIO STATUS", 'yellow', attrs=['bold']).ljust(76) + "│")

        equity = status.get('equity_usd', 0)
        exposure = status.get('exposure_usd', 0)
        exposure_pct = (exposure / equity * 100) if equity > 0 else 0

        # Equity and exposure
        equity_str = f"${equity:,.2f}"
        exposure_str = f"${exposure:,.2f} ({exposure_pct:.1f}%)"

        # Color code exposure based on limits
        limits = status.get('limits', {})
        max_exposure_pct = limits.get('max_exposure_pct', 60)
        exposure_color = 'green' if exposure_pct < max_exposure_pct * 0.7 else 'yellow' if exposure_pct < max_exposure_pct else 'red'

        print(f"│ Equity: {colored(equity_str, 'white', attrs=['bold'])} | Exposure: {colored(exposure_str, exposure_color)}")

        # Session PnL
        session_pnl = status.get('session_pnl_usd', 0)
        pnl_pct = (session_pnl / equity * 100) if equity > 0 else 0
        pnl_color = 'green' if session_pnl >= 0 else 'red'
        pnl_sign = '+' if session_pnl >= 0 else ''

        pnl_str = f"{pnl_sign}${session_pnl:,.2f} ({pnl_sign}{pnl_pct:.2f}%)"
        print(f"│ Session PnL: {colored(pnl_str, pnl_color, attrs=['bold'])}")

        # Limits
        if limits:
            max_loss = limits.get('max_loss_usd', 0)
            max_gain = limits.get('max_gain_usd', 0)
            print(f"│ Max Loss Limit: {colored(f'-${max_loss:,.2f}', 'red')} | Max Gain: {colored(f'${max_gain:,.2f}', 'green')}")

        print("├" + "─" * 68 + "┤")

    def _render_token_risk_scores(self, status: Dict):
        """Render token risk scores section"""
        print("│ " + colored("TOKEN RISK SCORES", 'yellow', attrs=['bold']).ljust(76) + "│")

        token_profiles = status.get('token_profiles', {})

        if not token_profiles:
            print("│ No tokens analyzed yet")
        else:
            # Show up to 5 tokens per line
            tokens = list(token_profiles.items())[:5]
            token_strs = []

            for symbol, profile in tokens:
                risk_score = profile.get('risk_score', 1.0)
                risk_level = self._get_risk_level_label(risk_score)
                risk_color = self._get_risk_score_color(risk_score)

                token_str = f"{symbol}: {colored(f'{risk_score:.2f}', risk_color)} ({risk_level})"
                token_strs.append(token_str)

            print("│ " + " | ".join(token_strs))

        print("├" + "─" * 68 + "┤")

    def _render_active_positions(self):
        """Render active positions section"""
        print("│ " + colored("ACTIVE POSITIONS", 'yellow', attrs=['bold']).ljust(76) + "│")

        try:
            # Get positions (would come from exchange in production)
            # For now, show placeholder
            print("│ No open positions (placeholder - integrate with exchange API)")
        except Exception as e:
            print(f"│ Error loading positions: {str(e)[:50]}")

        print("├" + "─" * 68 + "┤")

    def _render_circuit_breakers(self, status: Dict):
        """Render circuit breaker status"""
        print("│ " + colored("CIRCUIT BREAKERS", 'yellow', attrs=['bold']).ljust(76) + "│")

        limits = status.get('limits', {})
        session_pnl = status.get('session_pnl_usd', 0)
        equity = status.get('equity_usd', 0)
        exposure = status.get('exposure_usd', 0)

        breakers = []

        # Session loss check
        max_loss = limits.get('max_loss_usd', 0)
        if session_pnl <= -max_loss:
            breakers.append(colored("❌ SESSION LOSS LIMIT HIT", 'red', attrs=['bold', 'blink']))
        else:
            pct_used = abs(session_pnl / max_loss * 100) if max_loss > 0 else 0
            if pct_used > 80:
                breakers.append(colored(f"⚠️ Session Loss: {pct_used:.0f}% used", 'yellow'))
            else:
                breakers.append(colored("✅ Session Loss OK", 'green'))

        # Exposure check
        max_exposure_pct = limits.get('max_exposure_pct', 60)
        exposure_pct = (exposure / equity * 100) if equity > 0 else 0
        if exposure_pct > max_exposure_pct:
            breakers.append(colored("❌ EXPOSURE LIMIT EXCEEDED", 'red', attrs=['bold', 'blink']))
        elif exposure_pct > max_exposure_pct * 0.8:
            breakers.append(colored(f"⚠️ Exposure: {exposure_pct:.0f}%", 'yellow'))
        else:
            breakers.append(colored("✅ Exposure OK", 'green'))

        # Balance check
        min_balance = limits.get('min_balance_usd', 100)
        if equity < min_balance:
            breakers.append(colored("❌ MINIMUM BALANCE BREACHED", 'red', attrs=['bold', 'blink']))
        else:
            breakers.append(colored("✅ Balance OK", 'green'))

        print("│ " + " | ".join(breakers))

        print("├" + "─" * 68 + "┤")

    def _render_performance_stats(self, status: Dict):
        """Render performance statistics"""
        print("│ " + colored("PERFORMANCE STATS", 'yellow', attrs=['bold']).ljust(76) + "│")

        regime_config = status.get('regime_config', {})

        if regime_config:
            trade_risk = regime_config.get('trade_risk_pct', 0)
            max_daily_loss = regime_config.get('max_daily_loss_pct', 0)
            confidence_req = regime_config.get('confidence_threshold', 0)

            print(f"│ Trade Risk: {trade_risk:.2f}% | Max Daily Loss: {max_daily_loss:.1f}% | Min Confidence: {confidence_req:.0f}%")
        else:
            print("│ No regime configuration available")

        print("├" + "─" * 68 + "┤")

    def _render_alerts(self):
        """Render recent alerts"""
        print("│ " + colored("RECENT ALERTS", 'yellow', attrs=['bold']).ljust(76) + "│")

        if not self.alert_history:
            print("│ No alerts")
        else:
            for alert in self.alert_history[-self.max_alerts_shown:]:
                timestamp = alert['timestamp'].strftime('%H:%M:%S')
                severity = alert['severity']
                message = alert['message'][:50]  # Truncate long messages

                severity_color = {
                    'INFO': 'white',
                    'WARNING': 'yellow',
                    'ERROR': 'red'
                }.get(severity, 'white')

                print(f"│ [{timestamp}] {colored(severity, severity_color)}: {message}")

        print("└" + "─" * 68 + "┘")

    def add_alert(self, severity: str, message: str):
        """Add alert to history"""
        self.alert_history.append({
            'timestamp': datetime.now(),
            'severity': severity,
            'message': message
        })

        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

    # ===========================
    # HELPER METHODS
    # ===========================

    def _get_regime_color(self, regime: str) -> str:
        """Get color for market regime"""
        regime_colors = {
            'TRENDING_UP': 'green',
            'TRENDING_DOWN': 'red',
            'CHOPPY': 'yellow',
            'FLAT': 'white',
            'CRISIS': 'red',
            'UNKNOWN': 'white'
        }
        return regime_colors.get(regime, 'white')

    def _get_risk_score_color(self, score: float) -> str:
        """Get color for risk score"""
        if score < 0.7:
            return 'green'
        elif score < 1.2:
            return 'yellow'
        else:
            return 'red'

    def _get_risk_level_label(self, score: float) -> str:
        """Get risk level label"""
        if score < 0.7:
            return 'Low'
        elif score < 1.2:
            return 'Med'
        else:
            return 'High'


# ===========================
# STANDALONE DASHBOARD
# ===========================

def run_standalone_dashboard(
    starting_equity_usd: float = 10000.0,
    refresh_seconds: int = 5
):
    """
    Run standalone risk dashboard for testing

    Args:
        starting_equity_usd: Starting portfolio equity
        refresh_seconds: Dashboard refresh interval
    """
    logging.basicConfig(level=logging.WARNING)  # Suppress info logs for clean display

    # Initialize risk layer
    risk_layer = RiskIntegrationLayer(enable_risk_checks=True)

    # Update market conditions
    risk_layer.update_market_conditions(reference_symbol='BTC')

    # Update portfolio state
    risk_layer.update_portfolio_state(
        equity_usd=starting_equity_usd,
        exposure_usd=0.0
    )

    # Update token risks
    for symbol in ['BTC', 'ETH', 'SOL']:
        risk_layer.update_token_risk(symbol, timeframe='1H', days_back=7)

    # Create and start dashboard
    dashboard = RiskDashboard(risk_layer, refresh_seconds=refresh_seconds)

    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\n🌙 Dashboard stopped by user")


# ===========================
# SUMMARY REPORT GENERATOR
# ===========================

class RiskSummaryReport:
    """
    Generate text-based risk summary reports
    """

    @staticmethod
    def generate_report(risk_layer: RiskIntegrationLayer) -> str:
        """
        Generate comprehensive risk report

        Args:
            risk_layer: Risk integration layer

        Returns:
            Formatted text report
        """
        status = risk_layer.get_risk_status()

        report = []
        report.append("=" * 70)
        report.append("🌙 MOON DEV'S RISK MANAGEMENT REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Market Regime
        regime = status.get('regime', 'UNKNOWN')
        regime_config = status.get('regime_config', {})
        report.append(f"Market Regime: {regime.upper()}")
        if regime_config:
            report.append(f"  - Trade Risk: {regime_config.get('trade_risk_pct', 0):.2f}%")
            report.append(f"  - Max Daily Loss: {regime_config.get('max_daily_loss_pct', 0):.1f}%")
            report.append(f"  - Min Confidence: {regime_config.get('confidence_threshold', 0):.0f}%")

        # Portfolio Status
        report.append(f"\nPortfolio Status:")
        report.append(f"  - Equity: ${status.get('equity_usd', 0):,.2f}")
        report.append(f"  - Exposure: ${status.get('exposure_usd', 0):,.2f}")
        report.append(f"  - Session PnL: ${status.get('session_pnl_usd', 0):,.2f}")

        # Limits
        limits = status.get('limits', {})
        if limits:
            report.append(f"\nRisk Limits:")
            report.append(f"  - Max Loss (12h): ${limits.get('max_loss_usd', 0):,.2f}")
            report.append(f"  - Max Gain (12h): ${limits.get('max_gain_usd', 0):,.2f}")
            report.append(f"  - Max Position: {limits.get('max_position_pct', 0):.1f}%")
            report.append(f"  - Max Exposure: {limits.get('max_exposure_pct', 0):.1f}%")

        # Token Risk Scores
        token_profiles = status.get('token_profiles', {})
        if token_profiles:
            report.append(f"\nToken Risk Scores:")
            for symbol, profile in token_profiles.items():
                risk_score = profile.get('risk_score', 1.0)
                max_pos = profile.get('max_position_pct', 0)
                report.append(f"  - {symbol}: {risk_score:.2f} (Max Position: {max_pos:.1f}%)")

        report.append("\n" + "=" * 70)

        return "\n".join(report)


if __name__ == "__main__":
    print("🌙 Moon Dev's Risk Dashboard\n")
    print("Choose mode:")
    print("1. Run live dashboard (refreshes every 5 seconds)")
    print("2. Generate one-time report")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        run_standalone_dashboard(starting_equity_usd=10000.0, refresh_seconds=5)
    elif choice == "2":
        # Initialize and generate report
        logging.basicConfig(level=logging.WARNING)
        risk_layer = RiskIntegrationLayer(enable_risk_checks=True)
        risk_layer.update_market_conditions(reference_symbol='BTC')
        risk_layer.update_portfolio_state(equity_usd=10000.0, exposure_usd=0.0)

        report = RiskSummaryReport.generate_report(risk_layer)
        print("\n" + report)
    else:
        print("Invalid choice")
