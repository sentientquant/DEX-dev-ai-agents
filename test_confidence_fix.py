#!/usr/bin/env python3
"""Test that confidence fix works"""

from risk_management.trading_database_typed import TradingDatabaseTyped
from termcolor import cprint

db = TradingDatabaseTyped()
result = db.get_open_trades()

if result.is_success:
    cprint(f"[OK] Successfully loaded {len(result.value)} open trades", "green")
    for trade in result.value:
        cprint(f"  {trade.trade_id}: {trade.symbol} confidence={trade.confidence}", "white")
else:
    cprint(f"[ERROR] Failed to load trades: {result.error}", "red")
