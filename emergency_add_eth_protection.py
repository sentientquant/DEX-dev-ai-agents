#!/usr/bin/env python3
"""
EMERGENCY: Add SL/TP protection to unprotected ETH position
"""

from termcolor import cprint
from risk_management.trading_database import TradingDatabase
from trading_modes.models.domain import Trade
from src.exchange_manager import ExchangeManager
from risk_management.binance_truth_paper_trading import BinanceTruthAPI
import json

def add_eth_protection():
    cprint("\n" + "="*80, "red")
    cprint("EMERGENCY: ADDING ETH PROTECTION", "red", attrs=['bold'])
    cprint("="*80 + "\n", "red")

    # 1. Get ETH trade from database
    db = TradingDatabase()
    rows = db.get_open_trades()
    trades = [Trade.from_db_row(row) for row in rows]
    eth_trades = [t for t in trades if 'ETH' in t.symbol]

    if not eth_trades:
        cprint("❌ No ETH trade found in database!", "red")
        return

    trade = eth_trades[0]
    cprint(f"Found ETH Trade:", "cyan", attrs=['bold'])
    cprint(f"  Trade ID: {trade.trade_id}", "white")
    cprint(f"  Entry: ${trade.entry_price:.2f}", "white")
    cprint(f"  SL: ${trade.stop_loss:.2f}", "white")
    cprint(f"  TP1: ${trade.tp1_price:.2f}", "white")
    cprint(f"  TP2: ${trade.tp2_price:.2f}", "white")
    cprint(f"  TP3: ${trade.tp3_price:.2f}", "white")
    cprint(f"  Size USD: ${trade.position_size_usd:.2f}", "white")

    # 2. Get current ETH balance
    em = ExchangeManager(exchange='BINANCE')
    eth_balance = em.binance_client.get_asset_balance(asset='ETH')
    eth_qty = float(eth_balance['free'])

    cprint(f"\nETH Balance: {eth_qty:.6f} ETH", "white")

    # 3. Calculate quantities for OCO and TPs
    current_price = BinanceTruthAPI.get_live_price('ETHUSDT')
    cprint(f"Current Price: ${current_price:.2f}", "white")

    # OCO: TP1 (40%) and SL (100%)
    tp1_qty = eth_qty * 0.40
    sl_qty = eth_qty  # Full protection

    # Standalone TPs: TP2 (30%) and TP3 (30%)
    tp2_qty = eth_qty * 0.30
    tp3_qty = eth_qty * 0.30

    cprint(f"\nOrder Quantities:", "cyan", attrs=['bold'])
    cprint(f"  TP1 (40%): {tp1_qty:.6f} ETH", "white")
    cprint(f"  SL (100%): {sl_qty:.6f} ETH", "white")
    cprint(f"  TP2 (30%): {tp2_qty:.6f} ETH", "white")
    cprint(f"  TP3 (30%): {tp3_qty:.6f} ETH", "white")

    # 4. Get Binance precision for ETHUSDT
    symbol_info = em.binance_client.get_symbol_info('ETHUSDT')
    price_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')
    lot_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')

    tick_size = float(price_filter['tickSize'])
    step_size = float(lot_filter['stepSize'])

    # Calculate precision
    price_precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0
    qty_precision = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0

    cprint(f"\nBinance Precision:", "cyan", attrs=['bold'])
    cprint(f"  Price precision: {price_precision} decimals", "white")
    cprint(f"  Quantity precision: {qty_precision} decimals", "white")

    # Round prices and quantities
    sl_price = round(trade.stop_loss, price_precision)
    tp1_price = round(trade.tp1_price, price_precision)
    tp2_price = round(trade.tp2_price, price_precision)
    tp3_price = round(trade.tp3_price, price_precision)

    tp1_qty_rounded = round(tp1_qty, qty_precision)
    sl_qty_rounded = round(sl_qty, qty_precision)
    tp2_qty_rounded = round(tp2_qty, qty_precision)
    tp3_qty_rounded = round(tp3_qty, qty_precision)

    cprint(f"\nRounded Order Prices:", "cyan", attrs=['bold'])
    cprint(f"  SL: ${sl_price:.2f}", "white")
    cprint(f"  TP1: ${tp1_price:.2f}", "white")
    cprint(f"  TP2: ${tp2_price:.2f}", "white")
    cprint(f"  TP3: ${tp3_price:.2f}", "white")

    # 5. Place OCO order (TP1 + SL)
    cprint(f"\n{'='*80}", "cyan")
    cprint("STEP 1: Placing OCO Order (TP1 + SL)...", "cyan", attrs=['bold'])

    try:
        # SL limit price (slightly below stop price for buffer)
        sl_limit_price = round(sl_price * 0.995, price_precision)

        cprint(f"\nOCO Parameters:", "white")
        cprint(f"  Symbol: ETHUSDT", "white")
        cprint(f"  Side: SELL", "white")
        cprint(f"  TP1 Price: ${tp1_price:.2f} ({tp1_qty_rounded:.6f} ETH)", "white")
        cprint(f"  SL Stop: ${sl_price:.2f}", "white")
        cprint(f"  SL Limit: ${sl_limit_price:.2f} ({sl_qty_rounded:.6f} ETH)", "white")

        oco_result = em.binance_client.create_oco_order(
            symbol='ETHUSDT',
            side='SELL',
            quantity=str(sl_qty_rounded),  # Full quantity for SL protection
            price=str(tp1_price),  # TP1 price
            stopPrice=str(sl_price),  # SL trigger
            stopLimitPrice=str(sl_limit_price),  # SL limit
            stopLimitTimeInForce='GTC',

            # ASYMMETRIC OCO - different quantities
            aboveType='LIMIT_MAKER',
            abovePrice=str(tp1_price),
            aboveQuantity=str(tp1_qty_rounded),  # 40% for TP1

            belowType='STOP_LOSS_LIMIT',
            belowStopPrice=str(sl_price),
            belowPrice=str(sl_limit_price),
            belowQuantity=str(sl_qty_rounded),  # 100% for SL
            belowTimeInForce='GTC'
        )

        oco_order_list_id = oco_result['orderListId']
        cprint(f"\n✅ OCO Order Created!", "green", attrs=['bold'])
        cprint(f"   Order List ID: {oco_order_list_id}", "green")

    except Exception as e:
        cprint(f"\n❌ OCO Order Failed: {e}", "red", attrs=['bold'])
        return

    # 6. Place standalone TP2 order
    cprint(f"\n{'='*80}", "cyan")
    cprint("STEP 2: Placing TP2 Limit Order...", "cyan", attrs=['bold'])

    try:
        tp2_result = em.binance_client.create_order(
            symbol='ETHUSDT',
            side='SELL',
            type='LIMIT',
            timeInForce='GTC',
            quantity=str(tp2_qty_rounded),
            price=str(tp2_price)
        )

        cprint(f"✅ TP2 Order Created!", "green", attrs=['bold'])
        cprint(f"   Order ID: {tp2_result['orderId']}", "green")
        cprint(f"   Price: ${tp2_price:.2f}", "green")
        cprint(f"   Quantity: {tp2_qty_rounded:.6f} ETH", "green")

    except Exception as e:
        cprint(f"❌ TP2 Order Failed: {e}", "red")

    # 7. Place standalone TP3 order
    cprint(f"\n{'='*80}", "cyan")
    cprint("STEP 3: Placing TP3 Limit Order...", "cyan", attrs=['bold'])

    try:
        tp3_result = em.binance_client.create_order(
            symbol='ETHUSDT',
            side='SELL',
            type='LIMIT',
            timeInForce='GTC',
            quantity=str(tp3_qty_rounded),
            price=str(tp3_price)
        )

        cprint(f"✅ TP3 Order Created!", "green", attrs=['bold'])
        cprint(f"   Order ID: {tp3_result['orderId']}", "green")
        cprint(f"   Price: ${tp3_price:.2f}", "green")
        cprint(f"   Quantity: {tp3_qty_rounded:.6f} ETH", "green")

    except Exception as e:
        cprint(f"❌ TP3 Order Failed: {e}", "red")

    # 8. Update metadata in database
    cprint(f"\n{'='*80}", "cyan")
    cprint("STEP 4: Updating Trade Metadata...", "cyan", attrs=['bold'])

    try:
        metadata = trade.metadata if isinstance(trade.metadata, dict) else {}
        metadata['oco_order_list_id'] = oco_order_list_id
        metadata['emergency_protection_added'] = True
        metadata['protection_timestamp'] = str(BinanceTruthAPI.get_current_timestamp())

        db.update_trade_metadata(trade.trade_id, json.dumps(metadata))

        cprint(f"✅ Metadata Updated!", "green", attrs=['bold'])

    except Exception as e:
        cprint(f"⚠️  Metadata update failed: {e}", "yellow")

    # 9. Verify orders on Binance
    cprint(f"\n{'='*80}", "cyan")
    cprint("VERIFICATION: Checking Binance Orders...", "cyan", attrs=['bold'])

    orders = em.binance_client.get_open_orders(symbol='ETHUSDT')
    cprint(f"\n✅ Total ETHUSDT Orders: {len(orders)}", "green", attrs=['bold'])

    for o in orders:
        cprint(f"\n  Order ID: {o['orderId']}", "white")
        cprint(f"  Type: {o['type']}", "white")
        cprint(f"  Side: {o['side']}", "white")
        cprint(f"  Price: {o.get('price', 'MARKET')}", "white")
        cprint(f"  Quantity: {o['origQty']}", "white")

    cprint(f"\n{'='*80}", "green")
    cprint("✅ ETH POSITION NOW PROTECTED!", "green", attrs=['bold'])
    cprint("="*80 + "\n", "green")

if __name__ == "__main__":
    add_eth_protection()
