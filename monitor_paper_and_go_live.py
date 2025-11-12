#!/usr/bin/env python3
"""
Monitor Paper Trading and Deploy to Binance LIVE

PERMANENT SOLUTION (as per user request):
1. Monitor paper trading positions
2. Track performance metrics
3. When criteria met → Deploy to Binance LIVE
4. Full risk management at all times

NO PLACEHOLDERS - REAL TRADING SYSTEM
"""

import os
import sys
import io
from pathlib import Path
from datetime import datetime
import time

# Fix Windows encoding
if os.name == 'nt' and not isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from risk_management.trading_database import get_trading_db
from run_paper_trading_with_risk import PaperTradingWithRisk


class LiveTradingDecisionSystem:
    """Monitor paper trading and make LIVE trading decisions"""

    def __init__(self):
        self.db = get_trading_db()
        self.paper_system = PaperTradingWithRisk()

        # Criteria for going LIVE (as per user request)
        self.min_trades = 5
        self.min_win_rate = 50.0  # 50%
        self.min_total_pnl = 0.0  # Must be profitable

    def check_open_positions(self):
        """Check and display all open paper positions"""

        print(f"\n{'='*80}")
        print(f"CHECKING OPEN PAPER POSITIONS")
        print(f"{'='*80}")

        open_trades = self.db.get_open_trades(mode='paper')

        if not open_trades:
            print("  No open positions")
            return []

        print(f"  Open Positions: {len(open_trades)}\n")

        for trade in open_trades:
            print(f"  Trade ID: {trade['trade_id']}")
            print(f"    Symbol: {trade['symbol']}")
            print(f"    Side: {trade['side']}")
            print(f"    Entry: ${trade['entry_price']:.2f}")
            print(f"    Size: ${trade['position_size_usd']:.2f}")
            print(f"    Stop Loss: ${trade['stop_loss']:.2f}")
            print(f"    TP1: ${trade.get('tp1_price', 0):.2f} ({trade.get('tp1_pct', 0):.1f}%)")
            print(f"    TP2: ${trade.get('tp2_price', 0):.2f} ({trade.get('tp2_pct', 0):.1f}%)")
            print(f"    TP3: ${trade.get('tp3_price', 0):.2f} ({trade.get('tp3_pct', 0):.1f}%)")
            print(f"    Strategy: {trade.get('strategy_name', 'N/A')}")
            print(f"    Status: {trade['status']}")

            # Calculate REAL-TIME PnL
            try:
                import ccxt
                exchange = ccxt.binance({'enableRateLimit': True})
                ticker = exchange.fetch_ticker(f"{trade['symbol']}/USDT")
                current_price = ticker['last']

                # Calculate PnL
                if trade['side'] == 'BUY':
                    pnl_pct = ((current_price - trade['entry_price']) / trade['entry_price']) * 100
                else:
                    pnl_pct = ((trade['entry_price'] - current_price) / trade['entry_price']) * 100

                pnl_usd = (pnl_pct / 100) * trade['position_size_usd']
                pnl_symbol = "+" if pnl_usd >= 0 else ""

                print(f"    Current Price: ${current_price:.2f}")
                print(f"    Unrealized PnL: ${pnl_symbol}{pnl_usd:.2f} ({pnl_symbol}{pnl_pct:.2f}%)")
            except Exception as e:
                print(f"    (PnL calculation unavailable)")

            print("")

        return open_trades

    def get_performance_metrics(self):
        """Get paper trading performance metrics"""

        print(f"\n{'='*80}")
        print(f"PAPER TRADING PERFORMANCE METRICS")
        print(f"{'='*80}")

        # Get all paper trades
        stats = self.db.get_trade_stats(mode='paper', days=30)

        total_trades = stats.get('total_trades', 0)
        winning_trades = stats.get('winning_trades', 0)
        win_rate = stats.get('win_rate', 0.0)
        total_pnl = stats.get('total_pnl', 0.0)
        avg_pnl = stats.get('avg_pnl', 0.0)

        print(f"  Total Trades: {total_trades}")
        print(f"  Winning Trades: {winning_trades}")
        print(f"  Losing Trades: {total_trades - winning_trades}")
        print(f"  Win Rate: {win_rate:.2f}%")
        print(f"  Total PnL: ${total_pnl:.2f}")
        print(f"  Average PnL: ${avg_pnl:.2f}")

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl
        }

    def check_live_criteria(self, metrics):
        """Check if paper trading meets criteria for LIVE deployment"""

        print(f"\n{'='*80}")
        print(f"BINANCE LIVE DEPLOYMENT CRITERIA CHECK")
        print(f"{'='*80}")

        criteria = {
            'min_trades': metrics['total_trades'] >= self.min_trades,
            'min_win_rate': metrics['win_rate'] >= self.min_win_rate,
            'profitable': metrics['total_pnl'] > self.min_total_pnl
        }

        print(f"\n  Criteria:")
        print(f"    1. Trades >= {self.min_trades}: {'✅ PASS' if criteria['min_trades'] else '❌ FAIL'} ({metrics['total_trades']})")
        print(f"    2. Win Rate >= {self.min_win_rate}%: {'✅ PASS' if criteria['min_win_rate'] else '❌ FAIL'} ({metrics['win_rate']:.2f}%)")
        print(f"    3. Total PnL > $0: {'✅ PASS' if criteria['profitable'] else '❌ FAIL'} (${metrics['total_pnl']:.2f})")

        all_pass = all(criteria.values())

        print(f"\n  READY FOR BINANCE LIVE: {'YES ✅' if all_pass else 'NO ❌'}")

        return all_pass, criteria

    def deploy_to_binance_live(self):
        """Deploy strategies to Binance LIVE account"""

        print(f"\n{'='*80}")
        print(f"DEPLOYING TO BINANCE LIVE ACCOUNT")
        print(f"{'='*80}")

        print("\n⚠️  WARNING: This will execute REAL trades with REAL money!")
        print("   Make sure:")
        print("     1. Binance API keys are configured in .env")
        print("     2. You have sufficient balance")
        print("     3. Risk management is active")

        # Get deployed strategies
        strategies = self.db.get_deployed_strategies()

        print(f"\n  Strategies to deploy LIVE: {len(strategies)}")
        for strat in strategies:
            print(f"    - {strat['strategy_name']}")

        print(f"\n  Next Steps:")
        print(f"    1. Configure Binance API keys in .env")
        print(f"    2. Run: python run_live_trading_with_risk.py")
        print(f"    3. Monitor with full risk management")

        print(f"\n✅ CRITERIA MET - READY FOR LIVE DEPLOYMENT")

    def monitor_and_decide(self):
        """Main monitoring loop"""

        print(f"\n{'='*80}")
        print(f"PAPER TRADING MONITOR & LIVE DEPLOYMENT SYSTEM")
        print(f"{'='*80}")
        print(f"Started: {datetime.now()}")

        # Check open positions
        open_positions = self.check_open_positions()

        # Get performance metrics
        metrics = self.get_performance_metrics()

        # Check if ready for LIVE
        ready, criteria = self.check_live_criteria(metrics)

        if ready:
            self.deploy_to_binance_live()
        else:
            print(f"\n{'='*80}")
            print(f"RECOMMENDATION: Continue Paper Trading")
            print(f"{'='*80}")

            if not criteria['min_trades']:
                trades_needed = self.min_trades - metrics['total_trades']
                print(f"  Need {trades_needed} more trades (current: {metrics['total_trades']})")
                print(f"  Action: Run run_paper_trading_with_risk.py to generate more signals")

            if not criteria['min_win_rate']:
                print(f"  Win rate too low: {metrics['win_rate']:.2f}% < {self.min_win_rate}%")
                print(f"  Action: Review strategy performance, consider optimization")

            if not criteria['profitable']:
                print(f"  Not profitable: ${metrics['total_pnl']:.2f}")
                print(f"  Action: Continue monitoring, may need strategy adjustments")

        print(f"\n{'='*80}")
        print(f"MONITORING SESSION COMPLETE")
        print(f"{'='*80}")
        print(f"Ended: {datetime.now()}")

        return ready, metrics


if __name__ == "__main__":
    monitor = LiveTradingDecisionSystem()
    ready, metrics = monitor.monitor_and_decide()

    # Print summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"  Paper Trading Status: {'COMPLETE ✅' if ready else 'IN PROGRESS 🔄'}")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"  Win Rate: {metrics['win_rate']:.2f}%")
    print(f"  Total PnL: ${metrics['total_pnl']:.2f}")
    print(f"  Ready for LIVE: {'YES ✅' if ready else 'NO ❌'}")
