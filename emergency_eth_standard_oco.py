#!/usr/bin/env python3
"""
EMERGENCY: Add ETH protection using STANDARD OCO + additional SL
"""

from termcolor import cprint
from risk_management.trading_database import TradingDatabase
from trading_modes.models.domain import Trade
from src.exchange_manager import ExchangeManager
from risk_management.binance_truth_paper_trading import BinanceTruthAPI
import json

def fix_eth_standard_oco():
    cprint("\n" + "="*80, "red")
    cprint("EMERGENCY: ADDING ETH PROTECTION (STANDARD OCO APPROACH)", "red", attrs=['bold'])
    cprint("="*80 + "\n", "red")

    # 1. Get ETH trade
    db = TradingDatabase()
    rows = db.get_open_trades()
    trades = [Trade.from_db_row(row) for row in rows]
    eth_trades = [t for t in trades if 'ETH' in t.symbol]

    if not eth_trades:
        cprint("❌ No ETH trade found!", "red")
        return

    trade = eth_trades[0]
    cprint(f"ETH Trade: {trade.trade_id}", "cyan", attrs=['bold'])
    cprint(f"  Entry: ${trade.entry_price:.2f}", "white")
    cprint(f"  SL: ${trade.stop_loss:.2f}", "white")
    cprint(f"  TP1: ${trade.tp1_price:.2f}", "white")

    # 2. Get balance
    em = ExchangeManager(exchange='BINANCE')
    eth_balance = em.binance_client.get_asset_balance(asset='ETH')
    eth_qty = float(eth_balance['free'])

    current_price = BinanceTruthAPI.get_live_price('ETHUSDT')
    cprint(f"\nETH Balance: {eth_qty:.6f} ETH", "white")
    cprint(f"Current Price: ${current_price:.2f}\n", "white")

    # 3. Get precision
    symbol_info = em.binance_client.get_symbol_info('ETHUSDT')
    price_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')
    lot_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')

    tick_size = float(price_filter['tickSize'])
    step_size = float(lot_filter['stepSize'])

    price_precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0
    qty_precision = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0

    # Round prices and quantity
    tp1_price_rounded = round(trade.tp1_price, price_precision)
    sl_price_rounded = round(trade.stop_loss, price_precision)
    sl_limit_price = round(trade.stop_loss * 0.995, price_precision)
    eth_qty_rounded = round(eth_qty, qty_precision)

    cprint(f"Precision: {price_precision} decimals (price), {qty_precision} decimals (qty)", "white")
    cprint(f"Rounded Prices: TP1=${tp1_price_rounded:.{price_precision}f} | SL=${sl_price_rounded:.{price_precision}f}", "white")
    cprint(f"Rounded Quantity: {eth_qty_rounded:.{qty_precision}f} ETH\n", "white")

    # 4. Place STANDARD OCO (symmetric - full quantity for both SL and TP1)
    cprint("="*80, "cyan")
    cprint("PLACING STANDARD OCO (Full Protection)...", "cyan", attrs=['bold'])

    try:
        oco_result = em.binance_client.create_oco_order(
            symbol='ETHUSDT',
            side='SELL',
            quantity=str(eth_qty_rounded),

            # TP1 leg
            aboveType='LIMIT_MAKER',
            abovePrice=str(tp1_price_rounded),

            # SL leg
            belowType='STOP_LOSS_LIMIT',
            belowStopPrice=str(sl_price_rounded),
            belowPrice=str(sl_limit_price),
            belowTimeInForce='GTC'
        )

        oco_order_list_id = oco_result['orderListId']
        cprint(f"\n✅ STANDARD OCO PLACED!", "green", attrs=['bold'])
        cprint(f"   Order List ID: {oco_order_list_id}", "green")
        cprint(f"   Quantity: {eth_qty_rounded:.{qty_precision}f} ETH (100%)", "green")
        cprint(f"   TP1: ${trade.tp1_price:.2f}", "green")
        cprint(f"   SL: ${trade.stop_loss:.2f}", "green")

        # Update metadata
        metadata = trade.metadata if isinstance(trade.metadata, dict) else {}
        metadata['oco_order_list_id'] = oco_order_list_id
        metadata['emergency_protection_added'] = True
        metadata['oco_type'] = 'standard_symmetric'
        db.update_trade_metadata(trade.trade_id, json.dumps(metadata))

    except Exception as e:
        cprint(f"\n❌ OCO FAILED: {e}", "red", attrs=['bold'])
        return

    # 5. Verify
    cprint(f"\n{'='*80}", "cyan")
    cprint("VERIFICATION: Checking Binance Orders...", "cyan", attrs=['bold'])

    orders = em.binance_client.get_open_orders(symbol='ETHUSDT')
    cprint(f"\n✅ Total ETHUSDT Orders: {len(orders)}", "green", attrs=['bold'])

    for o in orders:
        cprint(f"\n  [{o['type']}] {o['side']}", "white")
        cprint(f"  Price: {o.get('price', o.get('stopPrice', 'MARKET'))}", "white")
        cprint(f"  Quantity: {o['origQty']} ETH", "white")

    cprint(f"\n{'='*80}", "green")
    cprint("✅ ETH POSITION NOW PROTECTED!", "green", attrs=['bold'])
    cprint("\nNOTE: Using standard OCO (TP1 + SL both @ 100%)", "yellow")
    cprint("When TP1 hits, manually place TP2/TP3 or system will handle it", "yellow")
    cprint("="*80 + "\n", "green")

if __name__ == "__main__":
    fix_eth_standard_oco()
