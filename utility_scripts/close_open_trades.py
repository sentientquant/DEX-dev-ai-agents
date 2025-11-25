#!/usr/bin/env python3
"""
Close All Open Trades in Database
Closes all trades with status='OPEN' across PAPER and LIVE modes
"""

import sys
from pathlib import Path
# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from risk_management.trading_database import TradingDatabase
from risk_management.binance_truth_paper_trading import BinanceTruthAPI

def close_all_open_trades():
    """Close all open trades in database"""
    db = TradingDatabase()

    cprint("\n" + "="*80, "yellow", attrs=['bold'])
    cprint("CLOSING ALL OPEN TRADES", "yellow", attrs=['bold'])
    cprint("="*80 + "\n", "yellow")

    # Get open trades
    open_trades = db.get_open_trades()

    if not open_trades:
        cprint("[INFO] No open trades to close", "green")
        return

    cprint(f"[FOUND] {len(open_trades)} open trades:\n", "cyan")

    closed_count = 0
    error_count = 0

    for trade in open_trades:
        symbol = trade.get('symbol', 'UNKNOWN')
        entry_price = trade.get('entry_price', 0)
        position_size = trade.get('position_size', 0)
        mode = trade.get('mode', 'UNKNOWN')
        trade_id = trade.get('trade_id')

        try:
            # Get current price
            ticker = BinanceTruthAPI.token_overview(symbol)
            current_price = ticker.get('last_price', entry_price)

            # Calculate PnL
            pnl_usd = (current_price - entry_price) * position_size
            pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0

            # Close trade in database
            db.close_trade(
                trade_id=trade_id,
                exit_price=current_price,
                pnl_usd=pnl_usd,
                pnl_pct=pnl_pct,
                exit_reason='MANUAL_CLOSE_ALL'
            )

            closed_count += 1

            pnl_color = "green" if pnl_usd > 0 else "red" if pnl_usd < 0 else "yellow"
            cprint(f"  ✅ {symbol:12s} | Mode: {mode:5s} | Entry: ${entry_price:>8.4f} | Exit: ${current_price:>8.4f} | "
                   f"PnL: ${pnl_usd:>+8.2f} ({pnl_pct:>+6.2f}%)", pnl_color)

        except Exception as e:
            error_count += 1
            cprint(f"  ❌ {symbol:12s} | Mode: {mode:5s} | Error: {str(e)[:50]}", "red")

    # Summary
    cprint("\n" + "="*80, "cyan")
    cprint(f"✅ Closed: {closed_count} trades", "green")
    if error_count > 0:
        cprint(f"❌ Errors: {error_count} trades", "red")
    cprint("="*80 + "\n", "cyan")

    # Show updated stats
    open_remaining = db.get_open_trades()
    all_trades = db.get_all_trades()
    closed_total = len(all_trades) - len(open_remaining)

    cprint(f"[FINAL] Total trades: {len(all_trades)} | Open: {len(open_remaining)} | Closed: {closed_total}", "white")

if __name__ == "__main__":
    close_all_open_trades()
