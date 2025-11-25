#!/usr/bin/env python3
"""
EMERGENCY: Add ETH protection using exchange_manager method
"""

from termcolor import cprint
from risk_management.trading_database import TradingDatabase
from trading_modes.models.domain import Trade
from src.exchange_manager import ExchangeManager
from risk_management.binance_truth_paper_trading import BinanceTruthAPI
import json

def fix_eth_now():
    cprint("\n" + "="*80, "red")
    cprint("EMERGENCY: ADDING ETH PROTECTION NOW", "red", attrs=['bold'])
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
    cprint(f"  TP2: ${trade.tp2_price:.2f}", "white")
    cprint(f"  TP3: ${trade.tp3_price:.2f}", "white")

    # 2. Get balance
    em = ExchangeManager(exchange='BINANCE')
    eth_balance = em.binance_client.get_asset_balance(asset='ETH')
    eth_qty = float(eth_balance['free'])

    cprint(f"\nETH Balance: {eth_qty:.6f} ETH", "white")

    current_price = BinanceTruthAPI.get_live_price('ETHUSDT')
    cprint(f"Current Price: ${current_price:.2f}\n", "white")

    # 3. Calculate quantities
    position_qty = eth_qty
    tp1_qty = position_qty * 0.40  # 40% for TP1
    sl_qty = position_qty  # 100% for SL protection

    tp2_qty = position_qty * 0.30  # 30% for TP2
    tp3_qty = position_qty * 0.30  # 30% for TP3

    # 4. Use exchange_manager to place OCO
    cprint("="*80, "cyan")
    cprint("PLACING OCO ORDER (TP1 + SL)...", "cyan", attrs=['bold'])

    # Calculate stop limit price (slightly below stop for buffer)
    stop_limit_price = trade.stop_loss * 0.995

    try:
        result = em.place_oco_order(
            symbol='ETHUSDT',
            side='BUY',  # Entry side was BUY, function will determine OCO as SELL
            tp1_quantity=tp1_qty,
            sl_quantity=sl_qty,
            stop_price=trade.stop_loss,
            stop_limit_price=stop_limit_price,
            take_profit_price=trade.tp1_price
        )

        if result['success']:
            oco_order_list_id = result['orderListId']
            cprint(f"\n✅ OCO ORDER PLACED!", "green", attrs=['bold'])
            cprint(f"   Order List ID: {oco_order_list_id}", "green")
            cprint(f"   TP1 ({tp1_qty:.6f} ETH @ ${trade.tp1_price:.2f})", "green")
            cprint(f"   SL ({sl_qty:.6f} ETH @ ${trade.stop_loss:.2f})", "green")

            # Update metadata
            metadata = trade.metadata if isinstance(trade.metadata, dict) else {}
            metadata['oco_order_list_id'] = oco_order_list_id
            metadata['emergency_protection_added'] = True
            db.update_trade_metadata(trade.trade_id, json.dumps(metadata))
        else:
            cprint(f"\n❌ OCO FAILED: {result.get('error')}", "red", attrs=['bold'])
            return

    except Exception as e:
        cprint(f"\n❌ OCO ERROR: {e}", "red", attrs=['bold'])
        return

    # 5. Place TP2
    cprint(f"\n{'='*80}", "cyan")
    cprint("PLACING TP2 LIMIT ORDER...", "cyan", attrs=['bold'])

    try:
        tp2_result = em.place_limit_order(
            symbol='ETHUSDT',
            side='SELL',
            quantity=tp2_qty,
            price=trade.tp2_price
        )

        if tp2_result['success']:
            cprint(f"✅ TP2 PLACED ({tp2_qty:.6f} ETH @ ${trade.tp2_price:.2f})", "green", attrs=['bold'])
        else:
            cprint(f"⚠️  TP2 FAILED: {tp2_result.get('error')}", "yellow")

    except Exception as e:
        cprint(f"⚠️  TP2 ERROR: {e}", "yellow")

    # 6. Place TP3
    cprint(f"\n{'='*80}", "cyan")
    cprint("PLACING TP3 LIMIT ORDER...", "cyan", attrs=['bold'])

    try:
        tp3_result = em.place_limit_order(
            symbol='ETHUSDT',
            side='SELL',
            quantity=tp3_qty,
            price=trade.tp3_price
        )

        if tp3_result['success']:
            cprint(f"✅ TP3 PLACED ({tp3_qty:.6f} ETH @ ${trade.tp3_price:.2f})", "green", attrs=['bold'])
        else:
            cprint(f"⚠️  TP3 FAILED: {tp3_result.get('error')}", "yellow")

    except Exception as e:
        cprint(f"⚠️  TP3 ERROR: {e}", "yellow")

    # 7. Verify
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
    cprint("="*80 + "\n", "green")

if __name__ == "__main__":
    fix_eth_now()
