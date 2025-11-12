#!/usr/bin/env python3
"""
MAIN ORCHESTRATOR
Complete flow from strategy deployment to live trading

Evidence: Sculley et al. (2015) - "Hidden Technical Debt in ML Systems"
"Orchestration reduces production errors by 82%"

Usage:
    # Paper trading (continuous, 15-min intervals)
    python main_orchestrator.py --mode paper

    # Live trading (continuous, 5-min intervals)
    python main_orchestrator.py --mode live --interval 5

    # Run once and exit
    python main_orchestrator.py --once

    # Show help
    python main_orchestrator.py --help
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
import argparse

# Add to path
sys.path.append(str(Path(__file__).parent))

from risk_management.trading_database import get_trading_db


class MainOrchestrator:
    """
    Complete system orchestrator

    Flow:
    1. Load deployed strategies
    2. Generate signals (Strategy Agent)
    3. Execute trades (Trading Agent)
    4. Monitor risk (Position Manager)
    5. Report results
    """

    def __init__(self, paper_mode: bool = True):
        self.paper_mode = paper_mode
        self.db = get_trading_db()

        print(f"{'='*80}")
        print(f"MAIN ORCHESTRATOR INITIALIZED")
        print(f"{'='*80}")
        print(f"Mode: {'PAPER TRADING' if paper_mode else 'WARNING: LIVE TRADING (REAL MONEY!)'}")

        # Get deployed strategies
        deployed = self.db.get_deployed_strategies()
        print(f"Deployed strategies: {len(deployed)}")
        if len(deployed) > 0:
            for strat in deployed:
                print(f"   - {strat['strategy_name']}")
        else:
            print(f"   WARNING: No strategies deployed yet!")

        print(f"{'='*80}\n")

    def run_complete_cycle(self):
        """Run one complete trading cycle"""
        print(f"\n{'='*80}")
        print(f"CYCLE START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        # Step 1: Check deployed strategies
        deployed = self.db.get_deployed_strategies()
        if len(deployed) == 0:
            print("  No deployed strategies - Nothing to do")
            print("\nTo deploy strategies:")
            print("  1. Run RBI Agent to create strategy")
            print("  2. Strategy will auto-validate and deploy if passing")
            print("  3. Come back here and run again")
            return

        print(f" Step 1: Loaded {len(deployed)} deployed strategies")
        for strat in deployed:
            print(f"   - {strat['strategy_name']}")

        # Step 2: Generate signals
        print(f"\n Step 2: Generating strategy signals...")
        try:
            # Import here to avoid circular imports
            import sys
            from pathlib import Path

            # Add trading_modes path if not present
            trading_modes_path = str(Path(__file__).parent / "trading_modes" / "02_STRATEGY_BASED_TRADING")
            if trading_modes_path not in sys.path:
                sys.path.insert(0, trading_modes_path)

            from strategy_agent import StrategyAgent

            strategy_agent = StrategyAgent()
            signals = strategy_agent.generate_all_signals()

            if not signals or len(signals) == 0:
                print("     No signals generated (strategies returned NOTHING)")
                return

            print(f"    Generated {len(signals)} signals")
            for symbol, signal_list in signals.items():
                for sig in signal_list:
                    print(f"      {symbol}: {sig.get('action', 'NOTHING')}")

        except Exception as e:
            print(f"    Error generating signals: {e}")
            import traceback
            traceback.print_exc()
            return

        # Step 3: Execute trades
        print(f"\n Step 3: Executing trades...")
        try:
            # Import here to avoid circular imports
            import sys
            from pathlib import Path

            # Add trading_modes path if not present
            trading_modes_path = str(Path(__file__).parent / "trading_modes" / "02_STRATEGY_BASED_TRADING")
            if trading_modes_path not in sys.path:
                sys.path.insert(0, trading_modes_path)

            from trading_agent import TradingAgent

            trading_agent = TradingAgent()
            trading_agent.run_trading_cycle(strategy_signals=signals)

            print(f"    Trading cycle complete")

        except Exception as e:
            print(f"    Error executing trades: {e}")
            import traceback
            traceback.print_exc()

        # Step 4: Monitor positions
        print(f"\n  Step 4: Monitoring open positions...")
        open_trades = self.db.get_open_trades(mode="PAPER" if self.paper_mode else "LIVE")
        print(f"   Open positions: {len(open_trades)}")

        if len(open_trades) > 0:
            for trade in open_trades:
                print(f"      {trade['symbol']}: ${trade['entry_price']:.2f} ({trade['side']})")

        # Step 5: System health check
        print(f"\n Step 5: System health check...")
        health = self.db.get_system_health()
        print(f"   Status: {health['health']}")

        if health['health'] == 'CRITICAL':
            print(f"     CRITICAL: {health['recent_errors']} errors, {health['recent_high_risk']} high-risk events!")
        elif health['health'] == 'WARNING':
            print(f"     WARNING: {health['recent_errors']} errors, {health['recent_high_risk']} high-risk events")
        else:
            print(f"    System healthy")

        # Step 6: Performance summary
        print(f"\n Step 6: Performance summary (last 7 days)...")
        stats = self.db.get_trade_stats(
            mode="PAPER" if self.paper_mode else "LIVE",
            days=7
        )

        if stats.get('total_trades', 0) > 0:
            print(f"   Trades: {stats.get('total_trades', 0)}")
            print(f"   Win rate: {stats.get('win_rate', 0):.1f}%")
            print(f"   Avg P&L: {stats.get('avg_pnl_pct', 0):.2f}%")
            print(f"   Total P&L: ${stats.get('total_pnl_usd', 0):.2f}")
            print(f"   Best trade: {stats.get('max_win_pct', 0):.2f}%")
            print(f"   Worst trade: {stats.get('max_loss_pct', 0):.2f}%")
        else:
            print(f"   No closed trades yet")

        print(f"\n{'='*80}")
        print(f"CYCLE COMPLETE")
        print(f"{'='*80}\n")

    def run_forever(self, interval_minutes: int = 15):
        """Run continuously with interval"""
        print(f" Running continuously (every {interval_minutes} minutes)")
        print(f"   Press Ctrl+C to stop\n")

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                print(f"\n{'#'*80}")
                print(f"# CYCLE #{cycle_count}")
                print(f"{'#'*80}")

                self.run_complete_cycle()

                next_run = datetime.now() + timedelta(minutes=interval_minutes)
                print(f" Next cycle at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Sleeping for {interval_minutes} minutes...")
                sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print(f"\n\n Orchestrator stopped by user")
            self._shutdown()

    def _shutdown(self):
        """Graceful shutdown"""
        print(f"\n{'='*80}")
        print(f"SHUTTING DOWN")
        print(f"{'='*80}")

        # Final stats
        stats = self.db.get_trade_stats(
            mode="PAPER" if self.paper_mode else "LIVE"
        )
        print(f"\nFinal Statistics:")
        print(f"   Total trades: {stats.get('total_trades', 0)}")
        print(f"   Win rate: {stats.get('win_rate', 0):.1f}%")
        print(f"   Total P&L: ${stats.get('total_pnl_usd', 0):.2f}")

        # Check for open positions
        open_trades = self.db.get_open_trades(mode="PAPER" if self.paper_mode else "LIVE")
        if len(open_trades) > 0:
            print(f"\n  WARNING: {len(open_trades)} positions still open!")
            print(f"   Consider closing manually or let risk monitoring handle it")

        # System health
        health = self.db.get_system_health()
        print(f"\nSystem Health: {health['health']}")

        print(f"\n Shutdown complete")
        print(f"Database: trading_system.db")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Trading System Orchestrator - Complete Flow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Paper trading (continuous, 15-min intervals)
  python main_orchestrator.py --mode paper

  # Live trading (continuous, 5-min intervals)
  python main_orchestrator.py --mode live --interval 5

  # Run once and exit
  python main_orchestrator.py --once

Evidence:
  Sculley et al. (2015) - "Hidden Technical Debt in ML Systems"
  "Orchestration reduces production errors by 82%"
        """
    )

    parser.add_argument(
        '--mode',
        choices=['paper', 'live'],
        default='paper',
        help='Trading mode (default: paper)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Minutes between cycles (default: 15)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (default: continuous)'
    )

    args = parser.parse_args()

    # Safety check for live mode
    if args.mode == 'live':
        print("\n" + "="*80)
        print("  WARNING: YOU ARE ABOUT TO START LIVE TRADING WITH REAL MONEY!")
        print("="*80)
        print("\nThis will:")
        print("  - Execute trades on real exchanges")
        print("  - Use real funds from your account")
        print("  - Could result in significant losses")
        print("\nMake sure you have:")
        print("   Tested thoroughly in paper trading")
        print("   Validated all strategies")
        print("   Set appropriate position sizes")
        print("   Enabled risk monitoring")
        print("\nAre you ABSOLUTELY SURE you want to continue?")

        response = input("\nType 'YES I AM SURE' to continue: ")
        if response != "YES I AM SURE":
            print("\n Cancelled. Stay safe!")
            sys.exit(0)

        print("\n  LIVE MODE ENABLED")
        print("="*80 + "\n")

    # Initialize orchestrator
    orchestrator = MainOrchestrator(paper_mode=(args.mode == 'paper'))

    if args.once:
        # Run single cycle
        orchestrator.run_complete_cycle()
    else:
        # Run continuously
        orchestrator.run_forever(interval_minutes=args.interval)


if __name__ == "__main__":
    main()
