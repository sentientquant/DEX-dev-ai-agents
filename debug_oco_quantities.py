#!/usr/bin/env python3
"""
Debug OCO quantity precision issue
"""

from termcolor import cprint
from src.exchange_manager import ExchangeManager

em = ExchangeManager(exchange='BINANCE')

# Get ETH balance
eth_balance = em.binance_client.get_asset_balance(asset='ETH')
eth_qty = float(eth_balance['free'])

cprint(f"\n ETH Balance: {eth_qty:.8f} ETH", "cyan")

# Calculate quantities
tp1_qty = eth_qty * 0.40
sl_qty = eth_qty

cprint(f"\nBefore Rounding:", "white")
cprint(f"  TP1 (40%): {tp1_qty:.8f} ETH", "white")
cprint(f"  SL (100%): {sl_qty:.8f} ETH", "white")

# Get symbol info for precision
symbol_info = em.binance_client.get_symbol_info('ETHUSDT')
price_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')
lot_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')

cprint(f"\nBinance Filters:", "cyan")
cprint(f"  Price tick size: {price_filter['tickSize']}", "white")
cprint(f"  Lot step size: {lot_filter['stepSize']}", "white")

# Calculate precision (exchange_manager method)
price_precision = price_filter['tickSize'].find('1') - 1
qty_precision = lot_filter['stepSize'].find('1') - 1

cprint(f"\nCalculated Precision:", "cyan")
cprint(f"  Price precision: {price_precision} decimals", "white")
cprint(f"  Quantity precision: {qty_precision} decimals", "white")

# Round quantities
tp1_rounded = round(tp1_qty, qty_precision)
sl_rounded = round(sl_qty, qty_precision)

cprint(f"\nAfter Rounding:", "white")
cprint(f"  TP1: {tp1_rounded:.8f} ETH", "white")
cprint(f"  SL: {sl_rounded:.8f} ETH", "white")

cprint(f"\nAs Strings (for Binance):", "white")
cprint(f"  TP1: '{str(tp1_rounded)}'", "white")
cprint(f"  SL: '{str(sl_rounded)}'", "white")

# Check if they're valid
cprint(f"\nValidation:", "cyan")
if tp1_rounded > 0 and sl_rounded > 0:
    cprint(f"  ✅ Both quantities > 0", "green")
else:
    cprint(f"  ❌ One or both quantities = 0!", "red")

if len(str(tp1_rounded)) > 0 and len(str(sl_rounded)) > 0:
    cprint(f"  ✅ Both strings non-empty", "green")
else:
    cprint(f"  ❌ One or both strings empty!", "red")

cprint("")
