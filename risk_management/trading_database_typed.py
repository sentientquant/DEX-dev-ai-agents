"""
Trading Database - Type-Safe Wrapper

PERMANENT FIX:
Wraps TradingDatabase to return typed Trade objects instead of untyped dicts.
Eliminates all field name confusion (direction/side) at the database boundary.

Before:
    trades = db.get_open_trades(mode='PAPER')  # Returns List[Dict]
    for trade in trades:
        side = trade.get('side') or trade.get('direction', 'BUY')  # Fallback chain!

After:
    result = db.get_open_trades(mode=TradingMode.PAPER)  # Returns Result[List[Trade]]
    if result.is_success():
        for trade in result.value:
            side = trade.side.value  # Type-safe, always exists!
"""

from typing import List, Optional, Any, cast
from risk_management.trading_database import TradingDatabase

# Type-safe models
from trading_modes.models.domain import Trade, TradingMode
from trading_modes.models.result import Result, success, failure


class TradingDatabaseTyped:
    """
    Type-safe wrapper around TradingDatabase

    Returns Result[List[Trade]] instead of List[Dict]
    Single conversion point from database → domain models
    """

    def __init__(self, db_path: str = "trading_system.db"):
        """Initialize with underlying database"""
        self.db = TradingDatabase(db_path)

    def insert_trade(self, trade: Trade) -> Result[int]:
        """
        Insert trade using typed Trade object

        Args:
            trade: Type-safe Trade object

        Returns:
            Success[int] - Database row ID
            Failure - Error details
        """
        try:
            # Convert Trade to dict for database
            trade_dict = trade.to_dict()

            row_id = self.db.insert_trade(
                trade_id=trade_dict['trade_id'],
                symbol=trade_dict['symbol'],
                side=trade_dict['side'],
                entry_price=trade_dict['entry_price'],
                position_size_usd=trade_dict['position_size_usd'],
                stop_loss=trade_dict['stop_loss'],
                tp1_price=trade_dict['tp1_price'],
                tp2_price=trade_dict['tp2_price'],
                tp3_price=trade_dict['tp3_price'],
                mode=trade_dict['mode'],
                tp1_pct=cast(Any, trade_dict.get('tp1_pct')),
                tp2_pct=cast(Any, trade_dict.get('tp2_pct')),
                tp3_pct=cast(Any, trade_dict.get('tp3_pct')),
                strategy_name=cast(Any, trade_dict.get('strategy_name')),
                swing_bars_ago=cast(Any, trade_dict.get('swing_bars_ago')),
                swing_strength=cast(Any, trade_dict.get('swing_strength')),
                atr_pct=cast(Any, trade_dict.get('atr_pct')),
                atr_multiplier=cast(Any, trade_dict.get('atr_multiplier')),
                confidence=cast(Any, str(trade_dict.get('confidence')) if trade_dict.get('confidence') else None),
                metadata=cast(Any, trade_dict.get('metadata'))
            )

            if row_id == -1:
                return failure(
                    error=f"Trade {trade.trade_id} already exists",
                    error_type="DuplicateTradeError"
                )

            return success(row_id)

        except Exception as e:
            return failure(
                error=f"Failed to insert trade: {e}",
                error_type=type(e).__name__
            )

    def get_open_trades(self, mode: Optional[TradingMode] = None) -> Result[List[Trade]]:
        """
        Get all open trades as typed Trade objects

        Args:
            mode: Optional trading mode filter

        Returns:
            Success[List[Trade]] - List of typed Trade objects
            Failure - Error details

        Example:
            result = db.get_open_trades(mode=TradingMode.PAPER)
            if result.is_success():
                for trade in result.value:
                    print(f"{trade.symbol}: {trade.side.value}")  # Type-safe!
        """
        try:
            # Get dicts from underlying database
            mode_str = mode.value if mode else None
            trade_dicts = self.db.get_open_trades(mode=cast(Any, mode_str))

            # Convert to typed Trade objects at boundary
            trades = [Trade.from_db_row(row) for row in trade_dicts]

            return success(trades)

        except Exception as e:
            return failure(
                error=f"Failed to get open trades: {e}",
                error_type=type(e).__name__,
                mode=mode.value if mode else None
            )

    def get_all_trades(
        self,
        mode: Optional[TradingMode] = None,
        limit: Optional[int] = None
    ) -> Result[List[Trade]]:
        """
        Get all trades (OPEN and CLOSED) as typed Trade objects

        Args:
            mode: Optional trading mode filter
            limit: Optional limit on number of results

        Returns:
            Success[List[Trade]] - List of typed Trade objects
            Failure - Error details
        """
        try:
            mode_str = mode.value if mode else None
            trade_dicts = self.db.get_all_trades(mode=cast(Any, mode_str), limit=cast(Any, limit))

            trades = [Trade.from_db_row(row) for row in trade_dicts]

            return success(trades)

        except Exception as e:
            return failure(
                error=f"Failed to get all trades: {e}",
                error_type=type(e).__name__,
                mode=mode.value if mode else None,
                limit=limit
            )

    def get_trade_by_id(self, trade_id: str) -> Result[Optional[Trade]]:
        """
        Get specific trade by ID

        Args:
            trade_id: Trade identifier

        Returns:
            Success[Trade] - Trade object if found
            Success[None] - If trade not found
            Failure - Error details
        """
        try:
            trade_dict = self.db.get_trade_by_id(trade_id)

            if trade_dict is None:
                return success(None)

            trade = Trade.from_db_row(trade_dict)
            return success(trade)

        except Exception as e:
            return failure(
                error=f"Failed to get trade {trade_id}: {e}",
                error_type=type(e).__name__,
                trade_id=trade_id
            )

    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        pnl_usd: float,
        pnl_pct: float,
        exit_reason: str
    ) -> Result[bool]:
        """
        Close existing trade

        Args:
            trade_id: Trade to close
            exit_price: Exit price
            pnl_usd: Profit/loss in USD
            pnl_pct: Profit/loss percentage
            exit_reason: Reason for exit

        Returns:
            Success[bool] - True if trade was closed
            Failure - Error details
        """
        try:
            success_flag = self.db.close_trade(
                trade_id=trade_id,
                exit_price=exit_price,
                pnl_usd=pnl_usd,
                pnl_pct=pnl_pct,
                exit_reason=exit_reason
            )

            return success(success_flag)

        except Exception as e:
            return failure(
                error=f"Failed to close trade {trade_id}: {e}",
                error_type=type(e).__name__,
                trade_id=trade_id
            )


# Backward compatibility: expose typed version as default
# Future code should use TradingDatabaseTyped directly
def get_typed_database(db_path: str = "trading_system.db") -> TradingDatabaseTyped:
    """Factory function to get typed database instance"""
    return TradingDatabaseTyped(db_path)
