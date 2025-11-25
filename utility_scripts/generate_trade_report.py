#!/usr/bin/env python3
"""
Trade Report Generator - Performance Analytics
Generates comprehensive trading performance reports

Reports Include:
- Daily/Weekly/Monthly PnL
- Win rate statistics
- Best/worst trades
- Strategy performance breakdown
- Risk metrics
- Trade distribution
"""

import sys
from datetime import datetime, timedelta
from typing import Dict, List
import json

# Make termcolor optional
try:
    from termcolor import cprint, colored
except ImportError:
    def cprint(text, color=None, attrs=None):
        print(text)
    def colored(text, color=None, attrs=None):
        return text

def get_trades_report(mode: str = 'LIVE', days: int = 30) -> Dict:
    """Generate trading report for specified period"""
    try:
        from risk_management.trading_database import TradingDatabase

        db = TradingDatabase("trading_system.db")

        # Get all trades for mode
        all_trades = db.get_all_trades(mode=mode)

        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_trades = [
            trade for trade in all_trades
            if datetime.fromisoformat(trade.get('timestamp', '1970-01-01')) >= cutoff_date
        ]

        if not recent_trades:
            return {
                'error': f'No {mode} trades found in last {days} days'
            }

        # Calculate statistics
        total_trades = len(recent_trades)
        closed_trades = [t for t in recent_trades if t.get('status') == 'CLOSED']

        total_pnl = sum(t.get('pnl_usd', 0.0) for t in closed_trades)
        winning_trades = [t for t in closed_trades if t.get('pnl_usd', 0.0) > 0]
        losing_trades = [t for t in closed_trades if t.get('pnl_usd', 0.0) < 0]

        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0.0

        # Best and worst trades
        best_trade = max(closed_trades, key=lambda x: x.get('pnl_usd', 0.0)) if closed_trades else None
        worst_trade = min(closed_trades, key=lambda x: x.get('pnl_usd', 0.0)) if closed_trades else None

        # Average win/loss
        avg_win = sum(t.get('pnl_usd', 0.0) for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t.get('pnl_usd', 0.0) for t in losing_trades) / len(losing_trades) if losing_trades else 0.0

        # Profit factor
        total_wins = sum(t.get('pnl_usd', 0.0) for t in winning_trades)
        total_losses = abs(sum(t.get('pnl_usd', 0.0) for t in losing_trades))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0.0

        # Strategy breakdown
        strategy_stats = {}
        for trade in closed_trades:
            strategy = trade.get('strategy_name', 'Unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'count': 0,
                    'pnl': 0.0,
                    'wins': 0,
                    'losses': 0
                }

            pnl = trade.get('pnl_usd', 0.0)
            strategy_stats[strategy]['count'] += 1
            strategy_stats[strategy]['pnl'] += pnl

            if pnl > 0:
                strategy_stats[strategy]['wins'] += 1
            else:
                strategy_stats[strategy]['losses'] += 1

        db.conn.close()

        return {
            'mode': mode,
            'period_days': days,
            'total_trades': total_trades,
            'closed_trades': len(closed_trades),
            'open_trades': total_trades - len(closed_trades),
            'total_pnl': total_pnl,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'strategy_stats': strategy_stats,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'error': str(e)
        }

def display_report(report: Dict):
    """Display formatted trading report"""
    cprint("\n" + "="*80, "cyan", attrs=['bold'])
    cprint("   TRADING PERFORMANCE REPORT", "cyan", attrs=['bold'])
    cprint("="*80, "cyan", attrs=['bold'])

    if 'error' in report:
        cprint(f"\n[ERROR] {report['error']}\n", "red")
        return

    mode = report['mode']
    period = report['period_days']

    cprint(f"\nMode: {colored(mode, 'yellow', attrs=['bold'])} | Period: Last {period} days", "white")
    cprint(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "white", attrs=['dim'])

    # Summary Stats
    cprint("[STATS] SUMMARY STATISTICS", "yellow", attrs=['bold'])
    cprint("-"*80, "white")
    cprint(f"  Total Trades:      {report['total_trades']}", "white")
    cprint(f"  Closed Trades:     {report['closed_trades']}", "white")
    cprint(f"  Open Trades:       {report['open_trades']}", "white")

    pnl = report['total_pnl']
    pnl_color = 'green' if pnl >= 0 else 'red'
    cprint(f"  Total PnL:         {colored(f'${pnl:,.2f}', pnl_color, attrs=['bold'])}", "white")

    # Win/Loss Stats
    cprint("\n[CHART] WIN/LOSS STATISTICS", "yellow", attrs=['bold'])
    cprint("-"*80, "white")
    cprint(f"  Winning Trades:    {colored(str(report['winning_trades']), 'green')}", "white")
    cprint(f"  Losing Trades:     {colored(str(report['losing_trades']), 'red')}", "white")

    win_rate = report['win_rate']
    win_rate_color = 'green' if win_rate >= 50 else 'yellow' if win_rate >= 40 else 'red'
    cprint(f"  Win Rate:          {colored(f'{win_rate:.2f}%', win_rate_color)}", "white")

    cprint(f"  Average Win:       {colored(f'+${report[\"avg_win\"]:,.2f}', 'green')}", "white")
    cprint(f"  Average Loss:      {colored(f'-${abs(report[\"avg_loss\"]):,.2f}', 'red')}", "white")

    pf = report['profit_factor']
    pf_color = 'green' if pf > 1.5 else 'yellow' if pf > 1.0 else 'red'
    cprint(f"  Profit Factor:     {colored(f'{pf:.2f}', pf_color)}", "white")

    # Best/Worst Trades
    if report['best_trade']:
        cprint("\n[WINNER] BEST / WORST TRADES", "yellow", attrs=['bold'])
        cprint("-"*80, "white")

        best = report['best_trade']
        worst = report['worst_trade']

        cprint(f"  Best Trade:  {best.get('symbol', 'N/A')} | {colored(f'+${best.get(\"pnl_usd\", 0):.2f}', 'green', attrs=['bold'])} ({best.get('pnl_pct', 0):+.2f}%)", "white")
        cprint(f"  Worst Trade: {worst.get('symbol', 'N/A')} | {colored(f'-${abs(worst.get(\"pnl_usd\", 0)):.2f}', 'red', attrs=['bold'])} ({worst.get('pnl_pct', 0):.2f}%)", "white")

    # Strategy Breakdown
    if report['strategy_stats']:
        cprint("\n[TARGET] STRATEGY PERFORMANCE", "yellow", attrs=['bold'])
        cprint("-"*80, "white")

        for strategy, stats in sorted(report['strategy_stats'].items(), key=lambda x: x[1]['pnl'], reverse=True):
            pnl = stats['pnl']
            pnl_color = 'green' if pnl >= 0 else 'red'
            win_rate = (stats['wins'] / stats['count'] * 100) if stats['count'] > 0 else 0.0

            cprint(f"\n  {colored(strategy, 'cyan', attrs=['bold'])}", "white")
            cprint(f"    Trades:     {stats['count']} ({stats['wins']}W / {stats['losses']}L)", "white")
            cprint(f"    Win Rate:   {win_rate:.1f}%", "white")
            cprint(f"    Total PnL:  {colored(f'${pnl:,.2f}', pnl_color)}", "white")

    cprint("\n" + "="*80, "cyan")

def save_report_json(report: Dict, filename: str = None):
    """Save report to JSON file"""
    if filename is None:
        filename = f"trade_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    cprint(f"\n[OK] Report saved to: {filename}", "green")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate trading performance report')
    parser.add_argument('--mode', default='LIVE', choices=['LIVE', 'PAPER'], help='Trading mode')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--save', action='store_true', help='Save report to JSON file')

    args = parser.parse_args()

    # Generate report
    report = get_trades_report(mode=args.mode, days=args.days)

    # Display report
    display_report(report)

    # Save if requested
    if args.save and 'error' not in report:
        save_report_json(report)

    cprint("")

if __name__ == "__main__":
    main()
