#!/usr/bin/env python3
"""
Verify that database open trades match Binance actual open orders
"""

from termcolor import cprint
from risk_management.trading_database import TradingDatabase
from trading_modes.models.domain import Trade
from src.exchange_manager import ExchangeManager
import json

def verify_database_vs_binance():
    """Compare database open trades with Binance open orders"""

    cprint("\n" + "="*80, "cyan")
    cprint("VERIFYING DATABASE VS BINANCE ORDERS", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

    # 1. Load open trades from database
    db = TradingDatabase()
    rows = db.get_open_trades()

    if not rows:
        cprint("❌ No open trades in database", "red")
        return

    trades = [Trade.from_db_row(row) for row in rows]
    cprint(f"[OK] Loaded {len(trades)} open trades from DATABASE\n", "green", attrs=['bold'])

    for i, trade in enumerate(trades, 1):
        cprint(f"[{i}] {trade.symbol} ({trade.side.value})", "yellow", attrs=['bold'])
        cprint(f"    Trade ID: {trade.trade_id}", "white")
        cprint(f"    Entry: ${trade.entry_price:,.6f}", "white")
        cprint(f"    Stop Loss: ${trade.stop_loss:,.6f}", "white")
        cprint(f"    TP1: ${trade.tp1_price:,.6f}", "white")
        cprint(f"    Status: {trade.status.value}", "green" if trade.status.value == 'OPEN' else "red")

        # Check metadata
        if trade.metadata:
            meta = trade.metadata if isinstance(trade.metadata, dict) else json.loads(trade.metadata)
            if 'oco_order_list_id' in meta:
                cprint(f"    OCO Order ID: {meta['oco_order_list_id']}", "cyan")
        cprint("")

    # 2. Load open orders from Binance
    cprint("="*80, "cyan")
    cprint("BINANCE OPEN ORDERS", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

    exchange_manager = ExchangeManager(exchange='BINANCE')

    if not exchange_manager.binance_client:
        cprint("❌ Binance client not initialized", "red")
        return

    # Get open orders for each symbol
    all_binance_orders = {}

    for trade in trades:
        symbol = trade.symbol if trade.symbol.endswith('USDT') else f"{trade.symbol}USDT"

        try:
            orders = exchange_manager.binance_client.get_open_orders(symbol=symbol)
            all_binance_orders[symbol] = orders

            if orders:
                cprint(f"📋 {symbol}: {len(orders)} open orders", "cyan", attrs=['bold'])
                for order in orders:
                    cprint(f"   Order ID: {order['orderId']}", "white")
                    cprint(f"   Type: {order['type']}", "white")
                    cprint(f"   Side: {order['side']}", "white")
                    cprint(f"   Price: ${float(order['price']):,.6f}", "white")
                    cprint(f"   Qty: {float(order['origQty'])}", "white")
                    if 'orderListId' in order and order['orderListId'] != -1:
                        cprint(f"   OCO List ID: {order['orderListId']}", "cyan")
                    cprint("")
            else:
                cprint(f"⚠️  {symbol}: NO OPEN ORDERS", "yellow", attrs=['bold'])
                cprint("")
        except Exception as e:
            cprint(f"❌ Error fetching orders for {symbol}: {e}", "red")
            cprint("")

    # 3. Compare and report discrepancies
    cprint("="*80, "cyan")
    cprint("VERIFICATION RESULTS", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

    mismatches = []

    for trade in trades:
        symbol = trade.symbol if trade.symbol.endswith('USDT') else f"{trade.symbol}USDT"
        binance_orders = all_binance_orders.get(symbol, [])

        cprint(f"Checking {trade.symbol}:", "cyan", attrs=['bold'])
        cprint(f"  Database: OPEN {trade.side.value} @ ${trade.entry_price:,.6f}", "white")

        if binance_orders:
            # Check if OCO orders exist
            oco_orders = [o for o in binance_orders if o.get('type') in ['STOP_LOSS_LIMIT', 'LIMIT_MAKER']]

            if oco_orders:
                cprint(f"  Binance: {len(oco_orders)} OCO orders (SL/TP) ✅", "green")

                # Verify SL and TP1 prices match
                for order in oco_orders:
                    order_price = float(order['price'])
                    if order['type'] == 'STOP_LOSS_LIMIT':
                        if abs(order_price - trade.stop_loss) / trade.stop_loss < 0.01:
                            cprint(f"  Stop Loss: ${order_price:,.6f} ✅ MATCH", "green")
                        else:
                            cprint(f"  Stop Loss: ${order_price:,.6f} ❌ MISMATCH (DB: ${trade.stop_loss:,.6f})", "red")
                            mismatches.append(f"{symbol}: SL mismatch")
                    elif order['type'] == 'LIMIT_MAKER' and order['side'] == 'SELL':
                        if abs(order_price - trade.tp1_price) / trade.tp1_price < 0.01:
                            cprint(f"  TP1: ${order_price:,.6f} ✅ MATCH", "green")
                        else:
                            cprint(f"  TP1: ${order_price:,.6f} ❌ MISMATCH (DB: ${trade.tp1_price:,.6f})", "red")
                            mismatches.append(f"{symbol}: TP1 mismatch")
            else:
                cprint(f"  Binance: ❌ NO OCO ORDERS (likely triggered)", "red", attrs=['bold'])
                cprint(f"  Action: Position may have exited via SL or TP1", "yellow")
                mismatches.append(f"{symbol}: Missing OCO orders")
        else:
            cprint(f"  Binance: ❌ NO ORDERS AT ALL", "red", attrs=['bold'])
            cprint(f"  Action: Database should be updated to CLOSED", "yellow")
            mismatches.append(f"{symbol}: No Binance orders but DB shows OPEN")

        cprint("")

    # Final summary
    cprint("="*80, "cyan")
    if not mismatches:
        cprint("✅ ALL SYSTEMS IN SYNC", "green", attrs=['bold'])
        cprint("Database and Binance orders match perfectly!", "green")
    else:
        cprint(f"⚠️  FOUND {len(mismatches)} DISCREPANCIES", "yellow", attrs=['bold'])
        for mismatch in mismatches:
            cprint(f"   • {mismatch}", "yellow")
        cprint("\nRecommended Actions:", "cyan", attrs=['bold'])
        cprint("   1. Check if positions were closed via SL/TP", "white")
        cprint("   2. Update database to match Binance reality", "white")
        cprint("   3. Restart LIVE mode to sync state", "white")

    cprint("="*80 + "\n", "cyan")

if __name__ == "__main__":
    verify_database_vs_binance()
