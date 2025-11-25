"""
Clean up invalid $0 position trades from database
These can block future trades on the same symbol
"""
from risk_management.trading_database import get_trading_db

db = get_trading_db()

# Get all open trades
open_trades = db.get_open_trades()
print(f"Found {len(open_trades)} open trades (all modes)")

# Find invalid trades (position size <= 0)
invalid_trades = [t for t in open_trades if t['position_size_usd'] <= 0]
print(f"\nInvalid trades to clean up: {len(invalid_trades)}")

for trade in invalid_trades:
    print(f"  - {trade['trade_id']}: {trade['symbol']} ${trade['position_size_usd']:.2f} ({trade['mode']})")
    db.close_trade(
        trade_id=trade['trade_id'],
        exit_price=trade['entry_price'],
        pnl_usd=0.0,
        exit_reason="Invalid $0 position - cleanup"
    )
    print(f"    ✅ Closed")

print(f"\n✅ Cleanup complete! Closed {len(invalid_trades)} invalid trades")
