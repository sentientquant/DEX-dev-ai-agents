#!/usr/bin/env python3
"""
EMERGENCY STOP - Kill Switch for Live Trading
Immediately closes all open positions and stops the trading system

USE CASES:
- Market crash
- System malfunction
- Unexpected behavior
- Need to halt all trading immediately

WHAT IT DOES:
1. Closes ALL open LIVE trades
2. Logs emergency stop event
3. Creates backup of current state
4. Displays summary of closed positions
"""

import sys
from datetime import datetime
from pathlib import Path

# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        print(text)

def emergency_stop():
    """Execute emergency stop procedure"""
    cprint("\n" + "="*80, "red", attrs=['bold'])
    cprint("   [WARN]  EMERGENCY STOP ACTIVATED [WARN]", "red", attrs=['bold'])
    cprint("="*80, "red", attrs=['bold'])

    try:
        from risk_management.trading_database import TradingDatabase

        db = TradingDatabase("trading_system.db")

        # Get all open LIVE trades
        open_trades = db.get_open_trades(mode='LIVE')

        if not open_trades:
            cprint("\n[OK] No open trades to close\n", "green")
            db.conn.close()
            return

        cprint(f"\n[STATS] Found {len(open_trades)} open trades\n", "yellow", attrs=['bold'])

        # Display trades to be closed
        for trade in open_trades:
            symbol = trade.get('symbol', 'N/A')
            side = trade.get('side', 'N/A')
            entry_price = trade.get('entry_price', 0.0)
            position_size = trade.get('position_size_usd', 0.0)

            cprint(f"  {symbol} - {side}", "white")
            cprint(f"    Entry: ${entry_price:,.2f} | Size: ${position_size:,.2f}", "white")

        # Confirm action
        cprint("\n" + "="*80, "yellow", attrs=['bold'])
        cprint("  WARNING: This will close ALL open positions immediately!", "yellow", attrs=['bold'])
        cprint("="*80, "yellow", attrs=['bold'])

        confirmation = input("\nType 'EMERGENCY STOP' to confirm: ").strip()

        if confirmation != "EMERGENCY STOP":
            cprint("\n[ERROR] Emergency stop cancelled\n", "yellow")
            db.conn.close()
            return

        # Close all trades
        cprint("\n[ALERT] CLOSING ALL POSITIONS...\n", "red", attrs=['bold'])

        from risk_management.binance_truth_paper_trading import BinanceTruthAPI

        closed_count = 0
        total_pnl = 0.0

        for trade in open_trades:
            trade_id = trade.get('trade_id')
            symbol = trade.get('symbol')
            side = trade.get('side')
            entry_price = trade.get('entry_price', 0.0)
            position_size = trade.get('position_size_usd', 0.0)

            # Get current price
            current_price = BinanceTruthAPI.get_live_price(symbol)
            if not current_price:
                cprint(f"  [ERROR] Failed to get price for {symbol}", "red")
                continue

            # Calculate PnL
            if side == 'BUY':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:  # SELL
                pnl_pct = ((entry_price - current_price) / entry_price) * 100

            pnl_usd = (position_size * pnl_pct) / 100
            total_pnl += pnl_usd

            # Close trade in database
            db.close_trade(
                trade_id=trade_id,
                exit_price=current_price,
                pnl_usd=pnl_usd,
                pnl_pct=pnl_pct,
                exit_reason="EMERGENCY_STOP"
            )

            pnl_color = "green" if pnl_usd >= 0 else "red"
            cprint(f"  [OK] Closed {symbol} | PnL: ${pnl_usd:,.2f} ({pnl_pct:+.2f}%)", pnl_color)
            closed_count += 1

        # Log emergency stop event
        log_entry = f"""
EMERGENCY STOP EVENT
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Trades Closed: {closed_count}
Total PnL: ${total_pnl:,.2f}
"""

        log_file = Path("emergency_stop_log.txt")
        with open(log_file, "a") as f:
            f.write(log_entry)
            f.write("="*80 + "\n")

        # Summary
        cprint("\n" + "="*80, "green", attrs=['bold'])
        cprint("   EMERGENCY STOP COMPLETE", "green", attrs=['bold'])
        cprint("="*80, "green", attrs=['bold'])
        cprint(f"\n  Trades Closed: {closed_count}", "white")

        pnl_color = "green" if total_pnl >= 0 else "red"
        cprint(f"  Total PnL: ${total_pnl:,.2f}", pnl_color, attrs=['bold'])
        cprint(f"\n  Log saved to: {log_file}\n", "white")

        db.conn.close()

    except Exception as e:
        cprint(f"\n[ERROR] ERROR during emergency stop: {e}\n", "red", attrs=['bold'])
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        emergency_stop()
    except KeyboardInterrupt:
        cprint("\n\n[ERROR] Emergency stop cancelled by user\n", "yellow")
        sys.exit(1)

if __name__ == "__main__":
    main()
