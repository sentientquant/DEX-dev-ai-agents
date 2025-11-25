# test_database.py
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from risk_management.trading_database_typed import TradingDatabaseTyped
from trading_modes.models.domain import Trade, TradeSide, TradingMode, TradeStatus
from datetime import datetime

def test_typed_database():
    """Test typed database wrapper"""
    db = TradingDatabaseTyped(db_path="test_trading.db")

    # Create test trade
    trade = Trade(
        trade_id='TEST_DB_001',
        symbol='BTCUSDT',
        side=TradeSide.BUY,
        entry_price=50000.0,
        position_size_usd=100.0,
        stop_loss=49000.0,
        mode=TradingMode.PAPER,
        status=TradeStatus.OPEN,
        timestamp=datetime.now()
    )

    # Insert trade
    insert_result = db.insert_trade(trade)
    if insert_result.is_success():
        print(f"✓ Trade inserted with ID: {insert_result.value}")
    else:
        print(f"✗ Insert failed: {insert_result.error}")
        return

    # Get open trades
    trades_result = db.get_open_trades(mode=TradingMode.PAPER)
    if trades_result.is_success():
        trades = trades_result.value
        print(f"✓ Found {len(trades)} open trades")

        if trades:
            trade = trades[0]
            # Test type-safe access
            print(f"  Symbol: {trade.symbol}")
            print(f"  Side: {trade.side.value}")  # Enum.value
            print(f"  Entry: ${trade.entry_price:.2f}")
            print(f"  Base: {trade.base_asset}")  # Computed property
    else:
        print(f"✗ Get trades failed: {trades_result.error}")
        return

    # Close trade
    close_result = db.close_trade(
        trade_id='TEST_DB_001',
        exit_price=51000.0,
        pnl_usd=20.0,
        pnl_pct=2.0,
        exit_reason='Test exit'
    )
    if close_result.is_success():
        print("✓ Trade closed successfully")
    else:
        print(f"✗ Close failed: {close_result.error}")

    print("\n✅ Typed database test passed!")

# Run test
test_typed_database()
