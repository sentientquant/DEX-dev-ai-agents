#!/usr/bin/env python3
"""
EMERGENCY: Check ETH position status
"""

from termcolor import cprint
from risk_management.trading_database import TradingDatabase
from trading_modes.models.domain import Trade
from src.exchange_manager import ExchangeManager
from risk_management.binance_truth_paper_trading import BinanceTruthAPI

def check_eth_emergency():
    cprint("\n" + "="*80, "red")
    cprint("EMERGENCY ETH POSITION CHECK", "red", attrs=['bold'])
    cprint("="*80 + "\n", "red")

    # 1. Check database
    db = TradingDatabase()
    rows = db.get_open_trades()
    trades = [Trade.from_db_row(row) for row in rows]

    eth_trades = [t for t in trades if 'ETH' in t.symbol]

    cprint(f"DATABASE ETH POSITIONS: {len(eth_trades)}", "cyan", attrs=['bold'])
    for t in eth_trades:
        cprint(f"\n  Symbol: {t.symbol}", "white")
        cprint(f"  Trade ID: {t.trade_id}", "white")
        cprint(f"  Entry: ${t.entry_price:.2f}", "white")
        cprint(f"  SL: ${t.stop_loss:.2f}", "white")
        cprint(f"  TP1: ${t.tp1_price:.2f}", "white")
        cprint(f"  Status: {t.status.value}", "white")
        cprint(f"  Size USD: ${t.position_size_usd:.2f}", "white")

    # 2. Check Binance balance
    cprint(f"\n{'='*80}", "cyan")
    cprint("BINANCE ETH BALANCE", "cyan", attrs=['bold'])

    em = ExchangeManager(exchange='BINANCE')
    try:
        eth_balance = em.binance_client.get_asset_balance(asset='ETH')
        cprint(f"\n  ETH Free: {eth_balance['free']}", "white")
        cprint(f"  ETH Locked: {eth_balance['locked']}", "white")

        eth_free = float(eth_balance['free'])
        eth_locked = float(eth_balance['locked'])

        if eth_free > 0.01:
            cprint(f"\n  ⚠️  UNPROTECTED ETH POSITION: {eth_free:.6f} ETH", "red", attrs=['bold'])

            # Get current price
            current_price = BinanceTruthAPI.get_live_price('ETHUSDT')
            if current_price:
                usd_value = eth_free * current_price
                cprint(f"  USD Value: ${usd_value:,.2f}", "yellow", attrs=['bold'])
    except Exception as e:
        cprint(f"  ❌ Error getting balance: {e}", "red")

    # 3. Check Binance orders
    cprint(f"\n{'='*80}", "cyan")
    cprint("BINANCE ETHUSDT ORDERS", "cyan", attrs=['bold'])

    try:
        orders = em.binance_client.get_open_orders(symbol='ETHUSDT')
        cprint(f"\n  Total Orders: {len(orders)}", "white")

        if len(orders) == 0:
            cprint(f"\n  ❌ NO PROTECTION ORDERS FOUND!", "red", attrs=['bold'])
        else:
            for o in orders:
                cprint(f"\n  Order ID: {o['orderId']}", "white")
                cprint(f"  Type: {o['type']}", "white")
                cprint(f"  Side: {o['side']}", "white")
                cprint(f"  Price: {o.get('price', 'MARKET')}", "white")
                cprint(f"  Quantity: {o['origQty']}", "white")
    except Exception as e:
        cprint(f"  ❌ Error getting orders: {e}", "red")

    cprint(f"\n{'='*80}\n", "red")

if __name__ == "__main__":
    check_eth_emergency()
