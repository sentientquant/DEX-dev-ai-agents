#!/usr/bin/env python3
"""
Live Trading Monitor - Real-time Performance Dashboard
Monitors active trades, PnL, and system health during live trading

Features:
- Real-time balance tracking
- Active trades monitoring
- PnL calculations
- Win rate statistics
- Alert notifications
- Performance metrics
"""

import time
import os
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Make termcolor optional
try:
    from termcolor import cprint, colored
except ImportError:
    def cprint(text, color=None, attrs=None):
        print(text)
    def colored(text, color=None, attrs=None):
        return text

load_dotenv()

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_live_status() -> Dict:
    """Get current trading system status"""
    try:
        from risk_management.trading_database import TradingDatabase
        from risk_management.binance_truth_paper_trading import BinanceTruthAPI

        db = TradingDatabase("trading_system.db")

        # Get current balance
        current_balance = BinanceTruthAPI.get_usdt_balance()
        if current_balance is None:
            current_balance = 0.0

        # Get all LIVE trades
        all_trades = db.get_all_trades(mode='LIVE')
        open_trades = db.get_open_trades(mode='LIVE')

        # Calculate stats
        total_trades = len(all_trades)
        active_trades = len(open_trades)

        # Calculate PnL
        total_pnl = 0.0
        winning_trades = 0
        losing_trades = 0

        for trade in all_trades:
            if trade.get('status') == 'CLOSED':
                pnl = trade.get('pnl_usd', 0.0)
                if pnl:
                    total_pnl += pnl
                    if pnl > 0:
                        winning_trades += 1
                    else:
                        losing_trades += 1

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        db.conn.close()

        return {
            'current_balance': current_balance,
            'total_trades': total_trades,
            'active_trades': active_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'open_trades': open_trades,
            'timestamp': datetime.now()
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now()
        }

def display_dashboard(status: Dict):
    """Display trading dashboard"""
    clear_screen()

    timestamp = status['timestamp'].strftime("%Y-%m-%d %H:%M:%S")

    cprint("="*80, "cyan", attrs=['bold'])
    cprint(f"   MOON DEV LIVE TRADING MONITOR - {timestamp}", "cyan", attrs=['bold'])
    cprint("="*80, "cyan", attrs=['bold'])

    if 'error' in status:
        cprint(f"\n[ERROR] ERROR: {status['error']}\n", "red", attrs=['bold'])
        return

    # Balance
    balance = status['current_balance']
    pnl = status['total_pnl']
    pnl_pct = (pnl / balance * 100) if balance > 0 else 0.0

    cprint("\n[97] ACCOUNT BALANCE", "yellow", attrs=['bold'])
    cprint("-"*80, "white")
    cprint(f"  Current Balance:  ${balance:,.2f} USDT", "white")

    if pnl >= 0:
        cprint(f"  Total PnL:        {colored(f'+${pnl:,.2f}', 'green')} ({colored(f'+{pnl_pct:.2f}%', 'green')})", "white")
    else:
        cprint(f"  Total PnL:        {colored(f'-${abs(pnl):,.2f}', 'red')} ({colored(f'{pnl_pct:.2f}%', 'red')})", "white")

    # Trade Statistics
    cprint("\n[STATS] TRADE STATISTICS", "yellow", attrs=['bold'])
    cprint("-"*80, "white")
    cprint(f"  Total Trades:     {status['total_trades']}", "white")
    cprint(f"  Active Trades:    {colored(str(status['active_trades']), 'green' if status['active_trades'] > 0 else 'white')}", "white")
    cprint(f"  Winning Trades:   {colored(str(status['winning_trades']), 'green')}", "white")
    cprint(f"  Losing Trades:    {colored(str(status['losing_trades']), 'red')}", "white")

    win_rate = status['win_rate']
    win_rate_color = 'green' if win_rate >= 50 else 'yellow' if win_rate >= 40 else 'red'
    cprint(f"  Win Rate:         {colored(f'{win_rate:.1f}%', win_rate_color)}", "white")

    # Active Trades
    if status['active_trades'] > 0:
        cprint("\n[FIRE] ACTIVE TRADES", "yellow", attrs=['bold'])
        cprint("-"*80, "white")

        for trade in status['open_trades']:
            symbol = trade.get('symbol', 'N/A')
            side = trade.get('side', 'N/A')
            entry_price = trade.get('entry_price', 0.0)
            position_size = trade.get('position_size_usd', 0.0)
            stop_loss = trade.get('stop_loss', 0.0)

            side_color = 'green' if side == 'BUY' else 'red'
            cprint(f"\n  {colored(symbol, 'cyan', attrs=['bold'])} - {colored(side, side_color, attrs=['bold'])}", "white")
            cprint(f"    Entry Price:    ${entry_price:,.2f}", "white")
            cprint(f"    Position Size:  ${position_size:,.2f}", "white")
            cprint(f"    Stop Loss:      ${stop_loss:,.2f}", "white")

    cprint("\n" + "="*80, "cyan")
    cprint("  Press Ctrl+C to exit  |  Refreshing every 30 seconds...", "white", attrs=['dim'])
    cprint("="*80, "cyan")

def main():
    """Main monitoring loop"""
    try:
        while True:
            status = get_live_status()
            display_dashboard(status)
            time.sleep(30)  # Refresh every 30 seconds

    except KeyboardInterrupt:
        cprint("\n\n[OK] Monitor stopped by user\n", "yellow")
    except Exception as e:
        cprint(f"\n\n[ERROR] Monitor error: {e}\n", "red")

if __name__ == "__main__":
    main()
