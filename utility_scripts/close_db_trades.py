#!/usr/bin/env python3
"""Close open trades in database"""
import sys
sys.path.insert(0, 'c:/Users/oia89/OneDrive/Desktop/DEX-dev-ai-agents')

from risk_management.trading_database import TradingDatabase

db = TradingDatabase()
open_trades = db.get_open_trades()

print(f'Open trades in DB: {len(open_trades)}')
for t in open_trades:
    print(f"  ID={t['id']}, Symbol={t['symbol']}, Entry=${t['entry_price']}")
    # Close the trade
    db.close_trade(t['id'], 86696.82, 'manual_close', 0.0, 'manual')
    print(f"  [OK] Closed trade {t['id']}")

print('\nAll trades closed')
