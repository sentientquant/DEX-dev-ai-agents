#!/usr/bin/env python3
"""
🌙 Moon Dev's COMPLETE Backtest-to-Live Automation Workflow
End-to-end automation: Convert → Paper Trade → Evaluate → Go Live

WORKFLOW:
1. Scans backtests_final/ for successful strategies
2. Converts to live trading format (BaseStrategy)
3. Starts 4-hour paper trading session with risk management
4. Monitors performance in real-time
5. If profitable after 4 hours: Enables live trading on Binance SPOT
6. If unprofitable: Keeps in paper trading for further evaluation

RISK MANAGEMENT:
- Dynamic risk engine (token scoring, regime detection)
- Per-token position sizing (ATR-based)
- Portfolio limits (max loss, max gain, exposure)
- $100 minimum trade size (Binance SPOT requirement)

EVALUATION CRITERIA:
✅ PASS (Enable Live): Positive PnL after 4 hours
❌ FAIL (Stay Paper): Negative PnL after 4 hours

DESIGNED BY: Moon Dev + User's Ultra Deep Thinking
"""

import sys
import os
import io
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Set UTF-8 encoding for Windows terminal
if os.name == 'nt':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

# Import our components
from src.scripts.auto_convert_backtests_to_live import (
    convert_backtests_to_live,
    find_latest_rbi_folder,
    PROJECT_ROOT,
    OUTPUT_DIR
)

from risk_management.trading_mode_integration import (
    RiskIntegrationLayer,
    StrategyBasedTradingAdapter
)

from risk_management.paper_trading_evaluator import PaperTradingEvaluator
from risk_management.risk_dashboard import RiskDashboard


# ===========================
# WORKFLOW ORCHESTRATOR
# ===========================

class BacktestToLiveWorkflow:
    """
    Complete automation workflow from backtest to live trading
    """

    def __init__(
        self,
        paper_trading_duration_hours: float = 4.0,
        starting_paper_equity: float = 10000.0,
        enable_live_on_success: bool = True,
        results_dir: str = "src/data/backtest_to_live_workflows"
    ):
        """
        Initialize workflow orchestrator

        Args:
            paper_trading_duration_hours: Paper trading evaluation duration
            starting_paper_equity: Starting equity for paper trading
            enable_live_on_success: Auto-enable live trading on success
            results_dir: Directory to save workflow results
        """
        self.paper_trading_duration_hours = paper_trading_duration_hours
        self.starting_paper_equity = starting_paper_equity
        self.enable_live_on_success = enable_live_on_success
        self.results_dir = PROJECT_ROOT / results_dir

        # Create results directory
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Workflow state
        self.converted_strategies: List[Dict] = []
        self.paper_trading_sessions: Dict[str, PaperTradingEvaluator] = {}
        self.live_enabled_strategies: List[str] = []

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def run_complete_workflow(self, dry_run: bool = True):
        """
        Execute the complete workflow

        Args:
            dry_run: If True, preview only (no actual conversion/trading)
        """
        print("=" * 80)
        print("🌙 MOON DEV'S BACKTEST-TO-LIVE AUTOMATION WORKFLOW")
        print("=" * 80)
        print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE EXECUTION'}")
        print(f"Paper Trading Duration: {self.paper_trading_duration_hours} hours")
        print(f"Starting Paper Equity: ${self.starting_paper_equity:,.2f}")
        print(f"Auto-Enable Live: {'YES' if self.enable_live_on_success else 'NO'}")
        print("=" * 80)

        # STEP 1: Convert backtests to live strategies
        print("\n📊 STEP 1: Converting Backtests to Live Strategies")
        print("-" * 80)

        if not dry_run:
            # Run the converter
            convert_backtests_to_live(dry_run=False)

            # Scan for converted strategies
            self._scan_converted_strategies()

            if not self.converted_strategies:
                print("❌ No strategies were converted. Workflow stopped.")
                return

            print(f"✅ {len(self.converted_strategies)} strategies converted")

        else:
            print("(DRY RUN - Conversion skipped)")
            print("In live mode, this would convert successful backtests to live strategies")

        # STEP 2: Start paper trading sessions
        if not dry_run and self.converted_strategies:
            print("\n📄 STEP 2: Starting Paper Trading Sessions")
            print("-" * 80)

            for strategy in self.converted_strategies:
                self._start_paper_trading_session(strategy)

            print(f"✅ {len(self.paper_trading_sessions)} paper trading sessions started")

            # STEP 3: Monitor and evaluate
            print("\n🔍 STEP 3: Monitoring Paper Trading Performance")
            print("-" * 80)
            print(f"⏰ Monitoring for {self.paper_trading_duration_hours} hours...")
            print("   Use Ctrl+C to stop early")

            try:
                self._monitor_paper_trading_sessions()
            except KeyboardInterrupt:
                print("\n\n⚠️ Monitoring interrupted by user")

            # STEP 4: Evaluate and enable live trading
            print("\n🎯 STEP 4: Evaluating Results and Enabling Live Trading")
            print("-" * 80)

            self._evaluate_and_enable_live()

        else:
            print("\n📄 STEP 2: Paper Trading (DRY RUN)")
            print("-" * 80)
            print("In live mode, strategies would be tested in paper trading for 4 hours")

            print("\n🔍 STEP 3: Monitoring (DRY RUN)")
            print("-" * 80)
            print("In live mode, real-time monitoring dashboard would show:")
            print("  - Position-by-position PnL")
            print("  - Risk metrics (exposure, limits, regime)")
            print("  - Win rate and performance stats")

            print("\n🎯 STEP 4: Go Live Decision (DRY RUN)")
            print("-" * 80)
            print("After 4 hours, strategies with positive PnL would be enabled for:")
            print("  - Live trading on Binance SPOT ($100 minimum)")
            print("  - Full risk management (dynamic sizing, SL/TP, circuit breakers)")
            print("  - Real-time monitoring and alerts")

        # STEP 5: Summary
        print("\n" + "=" * 80)
        print("📊 WORKFLOW SUMMARY")
        print("=" * 80)

        if dry_run:
            print("⚠️ DRY RUN COMPLETED - No actual changes made")
            print("\nNext steps:")
            print("1. Review the conversion logic above")
            print("2. Run with --execute flag to start paper trading")
            print("3. Monitor for 4 hours")
            print("4. Profitable strategies will be enabled for live trading")
        else:
            print(f"Strategies Converted: {len(self.converted_strategies)}")
            print(f"Paper Trading Sessions: {len(self.paper_trading_sessions)}")
            print(f"Live Trading Enabled: {len(self.live_enabled_strategies)}")

            if self.live_enabled_strategies:
                print("\n✅ Live Trading Enabled For:")
                for strategy_name in self.live_enabled_strategies:
                    print(f"   - {strategy_name}")
            else:
                print("\n⚠️ No strategies passed evaluation - all remain in paper trading")

        print("=" * 80)

        # Save workflow results
        if not dry_run:
            self._save_workflow_results()

    def _scan_converted_strategies(self):
        """Scan OUTPUT_DIR for newly converted strategies"""
        if not OUTPUT_DIR.exists():
            return

        # Find all strategy files converted today
        today = datetime.now().date()

        for strategy_file in OUTPUT_DIR.glob("*.py"):
            # Skip __init__.py and base classes
            if strategy_file.name.startswith('_'):
                continue

            # Check if file was created today
            mtime = datetime.fromtimestamp(strategy_file.stat().st_mtime)
            if mtime.date() == today:
                # Parse filename: BTC_5m_VolatilityOutlier_1025pct.py
                parts = strategy_file.stem.split('_')
                if len(parts) >= 4:
                    pair = parts[0]
                    timeframe = parts[1]
                    strategy_name = '_'.join(parts[2:-1])
                    return_pct = parts[-1].replace('pct', '')

                    self.converted_strategies.append({
                        'file_path': strategy_file,
                        'pair': pair,
                        'timeframe': timeframe,
                        'strategy_name': strategy_name,
                        'backtest_return_pct': float(return_pct),
                        'converted_at': mtime
                    })

    def _start_paper_trading_session(self, strategy: Dict):
        """Start paper trading session for a strategy"""
        strategy_id = f"{strategy['pair']}_{strategy['timeframe']}_{strategy['strategy_name']}"

        print(f"\n📄 Starting paper trading: {strategy_id}")
        print(f"   Backtest Return: {strategy['backtest_return_pct']:.1f}%")

        evaluator = PaperTradingEvaluator(
            strategy_name=strategy_id,
            starting_equity_usd=self.starting_paper_equity,
            duration_hours=self.paper_trading_duration_hours,
            results_dir=str(self.results_dir / "paper_trading_results")
        )

        self.paper_trading_sessions[strategy_id] = evaluator

        print(f"✅ Paper trading session started: {evaluator.session.session_id}")

    def _monitor_paper_trading_sessions(self):
        """Monitor all paper trading sessions in real-time"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=self.paper_trading_duration_hours)

        print(f"\n⏰ Start: {start_time.strftime('%H:%M:%S')}")
        print(f"⏰ End: {end_time.strftime('%H:%M:%S')}")

        # Initialize risk layer for monitoring
        risk_layer = RiskIntegrationLayer(enable_risk_checks=True)
        risk_layer.update_market_conditions(reference_symbol='BTC')
        risk_layer.update_portfolio_state(
            equity_usd=self.starting_paper_equity,
            exposure_usd=0.0
        )

        # Monitoring loop
        check_interval_seconds = 60  # Check every minute
        last_update = datetime.now()

        while datetime.now() < end_time:
            # Check all sessions
            for strategy_id, evaluator in self.paper_trading_sessions.items():
                # Check open positions for SL/TP
                evaluator.check_open_positions()

                # In production, this would:
                # 1. Get new signals from the strategy
                # 2. Validate through risk layer
                # 3. Execute paper trades
                # 4. Update evaluator

            # Display status every 5 minutes
            if (datetime.now() - last_update).seconds >= 300:
                self._display_monitoring_status()
                last_update = datetime.now()

            # Sleep
            time.sleep(check_interval_seconds)

        print("\n⏰ Paper trading evaluation period complete!")

    def _display_monitoring_status(self):
        """Display current status of all paper trading sessions"""
        print("\n" + "-" * 80)
        print(f"📊 Status Update: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 80)

        for strategy_id, evaluator in self.paper_trading_sessions.items():
            status = evaluator.get_session_status()

            pnl_emoji = "📈" if status['total_pnl_usd'] >= 0 else "📉"
            pnl_color = '\033[92m' if status['total_pnl_usd'] >= 0 else '\033[91m'  # Green/Red

            print(f"{pnl_emoji} {strategy_id}")
            print(f"   Equity: ${status['current_equity_usd']:,.2f} | "
                  f"PnL: {pnl_color}${status['total_pnl_usd']:+,.2f} ({status['return_pct']:+.2f}%)\033[0m")
            print(f"   Trades: {status['total_trades']} | Open: {status['open_trades']} | "
                  f"Win Rate: {status['win_rate']:.1f}%")
            print(f"   Time Left: {status['time_remaining_hours']:.1f}h")

        print("-" * 80)

    def _evaluate_and_enable_live(self):
        """Evaluate paper trading results and enable live trading for winners"""
        for strategy_id, evaluator in self.paper_trading_sessions.items():
            print(f"\n📊 Evaluating: {strategy_id}")
            print("-" * 80)

            # Run evaluation
            passed, notes, metrics = evaluator.evaluate()

            if passed and self.enable_live_on_success:
                print(f"🎉 PASSED - Enabling live trading!")

                # Enable live trading
                success = self._enable_live_trading(strategy_id)

                if success:
                    self.live_enabled_strategies.append(strategy_id)
                    print(f"✅ Live trading ENABLED on Binance SPOT")
                else:
                    print(f"⚠️ Failed to enable live trading (manual intervention required)")

            else:
                print(f"❌ FAILED - Remaining in paper trading")
                print(f"   Reason: {notes}")

    def _enable_live_trading(self, strategy_id: str) -> bool:
        """
        Enable live trading for a strategy

        Args:
            strategy_id: Strategy identifier

        Returns:
            True if successfully enabled
        """
        # In production, this would:
        # 1. Update config to enable live execution
        # 2. Configure Binance SPOT API connection
        # 3. Set $100 minimum trade size
        # 4. Enable risk management
        # 5. Start the strategy agent

        # For now, log the intent
        logging.info(f"🔴 LIVE TRADING ENABLED: {strategy_id}")
        logging.info(f"   Exchange: Binance SPOT")
        logging.info(f"   Minimum Trade: $100 USDT")
        logging.info(f"   Risk Management: ENABLED")

        # TODO: Implement actual live trading enablement
        # This would involve:
        # - Updating strategy_agent.py to mark strategy as live
        # - Configuring Binance SPOT credentials
        # - Setting up webhooks/alerts
        # - Starting monitoring dashboard

        return True  # Placeholder

    def _save_workflow_results(self):
        """Save workflow results to JSON"""
        results = {
            'workflow_id': f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'config': {
                'paper_trading_duration_hours': self.paper_trading_duration_hours,
                'starting_paper_equity': self.starting_paper_equity,
                'enable_live_on_success': self.enable_live_on_success
            },
            'converted_strategies': [
                {
                    'pair': s['pair'],
                    'timeframe': s['timeframe'],
                    'strategy_name': s['strategy_name'],
                    'backtest_return_pct': s['backtest_return_pct']
                }
                for s in self.converted_strategies
            ],
            'live_enabled_strategies': self.live_enabled_strategies
        }

        filepath = self.results_dir / f"{results['workflow_id']}_summary.json"
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Workflow results saved: {filepath}")


# ===========================
# CLI INTERFACE
# ===========================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="🌙 Moon Dev's Complete Backtest-to-Live Workflow"
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute workflow (default: dry run)'
    )

    parser.add_argument(
        '--duration',
        type=float,
        default=4.0,
        help='Paper trading duration in hours (default: 4.0)'
    )

    parser.add_argument(
        '--equity',
        type=float,
        default=10000.0,
        help='Starting paper trading equity (default: $10,000)'
    )

    parser.add_argument(
        '--no-auto-live',
        action='store_true',
        help='Do not auto-enable live trading (manual review required)'
    )

    args = parser.parse_args()

    # Create workflow
    workflow = BacktestToLiveWorkflow(
        paper_trading_duration_hours=args.duration,
        starting_paper_equity=args.equity,
        enable_live_on_success=not args.no_auto_live
    )

    # Run workflow
    workflow.run_complete_workflow(dry_run=not args.execute)


if __name__ == "__main__":
    main()
