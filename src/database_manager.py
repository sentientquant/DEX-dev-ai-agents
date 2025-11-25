"""
🌙 Moon Dev's Unified Database Manager
Built with love by Moon Dev 🚀

PERMANENT SOLUTION to database fragmentation.
Single connection pool, transaction management, unified interface.

This consolidates:
- risk_management/trading_database.py (TradingDatabase)
- trading_modes/core/altcoin_database.py (AltcoinPairsDB)
- Various ad-hoc sqlite3.connect() calls scattered across codebase
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from pathlib import Path
# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text


class DatabaseManager:
    """
    Singleton database manager for entire trading system.

    Features:
    - Single connection pool (prevents "database is locked" errors)
    - Thread-safe access
    - Transaction management
    - Automatic schema initialization
    - Connection reuse
    - Proper cleanup

    Usage:
        from src.database_manager import get_db_manager

        db = get_db_manager()

        # Context manager for transactions
        with db.transaction() as conn:
            conn.execute("INSERT INTO trades (...) VALUES (...)")

        # Or use helper methods
        db.record_trade(symbol="BTCUSDT", ...)
    """

    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()

    def __new__(cls, database_path: str = "trading_system_unified.db"):
        """Singleton pattern - only one instance exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, database_path: str = "trading_system_unified.db"):
        """Initialize database manager (only runs once due to singleton)"""
        if self._initialized:
            return

        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        self._local = threading.local()  # Thread-local storage for connections
        self._initialized = True

        # Initialize schemas
        self._initialize_schemas()

        cprint(f"[DATABASE] Initialized at {self.database_path}", "green")

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create thread-local database connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.database_path),
                check_same_thread=False,
                timeout=30.0  # 30 second timeout to prevent locks
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
        return self._local.connection

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            with db.transaction() as conn:
                conn.execute("INSERT ...")
                conn.execute("UPDATE ...")
            # Auto-commit on success, auto-rollback on error
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            cprint(f"[DATABASE ERROR] Transaction rolled back: {e}", "red")
            raise

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute SELECT query and return results

        Args:
            query: SQL query string
            params: Query parameters (tuple)

        Returns:
            List of sqlite3.Row objects (dict-like)
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            cprint(f"[DATABASE ERROR] Query failed: {e}", "red")
            cprint(f"  Query: {query}", "yellow")
            raise

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute INSERT/UPDATE/DELETE query

        Args:
            query: SQL query string
            params: Query parameters (tuple)

        Returns:
            Number of rows affected
        """
        with self.transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount

    def _initialize_schemas(self):
        """Initialize all database schemas"""
        with self.transaction() as conn:
            # =========================================================
            # TRADING TABLES (from trading_database.py)
            # =========================================================

            # Trades table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    position_size REAL NOT NULL,
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP,
                    pnl_usd REAL,
                    pnl_pct REAL,
                    exit_reason TEXT,
                    status TEXT DEFAULT 'OPEN',
                    metadata TEXT
                )
            """)

            # Strategies table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    strategy_code TEXT NOT NULL,
                    backtest_metrics TEXT,
                    live_metrics TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Risk events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS risk_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # System events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    component TEXT,
                    message TEXT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =========================================================
            # SCANNER TABLES (from altcoin_database.py)
            # =========================================================

            # Altcoin pairs cache
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scanner_pairs (
                    symbol TEXT PRIMARY KEY,
                    market_cap REAL,
                    volume_24h REAL,
                    price_change_pct REAL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Active pairs being monitored
            conn.execute("""
                CREATE TABLE IF NOT EXISTS active_pairs (
                    symbol TEXT PRIMARY KEY,
                    score REAL,
                    signal TEXT,
                    timeframe TEXT,
                    entry_price REAL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Scanner results cache
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scanner_cache (
                    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    method TEXT NOT NULL,
                    results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_mode ON trades(mode)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scanner_pairs_symbol ON scanner_pairs(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_active_pairs_symbol ON active_pairs(symbol)")

    # =========================================================
    # HIGH-LEVEL TRADING METHODS
    # =========================================================

    def record_trade(
        self,
        trade_id: str,
        symbol: str,
        mode: str,
        direction: str,
        entry_price: float,
        position_size: float,
        metadata: Optional[str] = None
    ) -> None:
        """Record a new trade"""
        query = """
            INSERT INTO trades (trade_id, symbol, mode, direction, entry_price, position_size, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_update(query, (trade_id, symbol, mode, direction, entry_price, position_size, metadata))
        cprint(f"[DATABASE] Recorded trade: {symbol} {direction} @ ${entry_price:.4f}", "green")

    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        pnl_usd: float,
        pnl_pct: float,
        exit_reason: str
    ) -> None:
        """Close an existing trade"""
        query = """
            UPDATE trades
            SET exit_price = ?, exit_time = CURRENT_TIMESTAMP, pnl_usd = ?, pnl_pct = ?,
                exit_reason = ?, status = 'CLOSED'
            WHERE trade_id = ?
        """
        self.execute_update(query, (exit_price, pnl_usd, pnl_pct, exit_reason, trade_id))
        pnl_color = "green" if pnl_usd > 0 else "red"
        cprint(f"[DATABASE] Closed trade: {trade_id} | PnL: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)", pnl_color)

    def get_open_trades(self, mode: Optional[str] = None) -> List[Dict]:
        """Get all open trades, optionally filtered by mode"""
        if mode:
            query = "SELECT * FROM trades WHERE status = 'OPEN' AND mode = ? ORDER BY entry_time DESC"
            rows = self.execute_query(query, (mode,))
        else:
            query = "SELECT * FROM trades WHERE status = 'OPEN' ORDER BY entry_time DESC"
            rows = self.execute_query(query)
        return [dict(row) for row in rows]

    def get_all_trades(self, mode: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get all trades, optionally filtered by mode"""
        if mode:
            query = "SELECT * FROM trades WHERE mode = ? ORDER BY entry_time DESC LIMIT ?"
            rows = self.execute_query(query, (mode, limit))
        else:
            query = "SELECT * FROM trades ORDER BY entry_time DESC LIMIT ?"
            rows = self.execute_query(query, (limit,))
        return [dict(row) for row in rows]

    def get_total_pnl(self, mode: Optional[str] = None) -> float:
        """Calculate total PnL from closed trades"""
        if mode:
            query = "SELECT SUM(pnl_usd) as total FROM trades WHERE status = 'CLOSED' AND mode = ?"
            rows = self.execute_query(query, (mode,))
        else:
            query = "SELECT SUM(pnl_usd) as total FROM trades WHERE status = 'CLOSED'"
            rows = self.execute_query(query)

        return float(rows[0]['total']) if rows and rows[0]['total'] else 0.0

    # =========================================================
    # SCANNER METHODS
    # =========================================================

    def cache_scanner_pairs(self, pairs: List[Dict[str, Any]]) -> None:
        """Cache scanner pairs for reuse"""
        with self.transaction() as conn:
            for pair in pairs:
                conn.execute("""
                    INSERT OR REPLACE INTO scanner_pairs
                    (symbol, market_cap, volume_24h, price_change_pct, last_updated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    pair.get('symbol'),
                    pair.get('market_cap'),
                    pair.get('volume_24h'),
                    pair.get('price_change_pct')
                ))

    def get_cached_pairs(self, max_age_hours: int = 4) -> List[Dict]:
        """Get cached scanner pairs (if not stale)"""
        query = """
            SELECT * FROM scanner_pairs
            WHERE last_updated >= datetime('now', '-' || ? || ' hours')
            ORDER BY market_cap DESC
        """
        rows = self.execute_query(query, (max_age_hours,))
        return [dict(row) for row in rows]

    def add_active_pair(self, symbol: str, score: float, signal: str, timeframe: str, entry_price: float) -> None:
        """Add pair to active monitoring"""
        query = """
            INSERT OR REPLACE INTO active_pairs (symbol, score, signal, timeframe, entry_price, added_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        self.execute_update(query, (symbol, score, signal, timeframe, entry_price))

    def get_active_pairs(self) -> List[Dict]:
        """Get all actively monitored pairs"""
        rows = self.execute_query("SELECT * FROM active_pairs ORDER BY added_at DESC")
        return [dict(row) for row in rows]

    def remove_active_pair(self, symbol: str) -> None:
        """Remove pair from active monitoring"""
        self.execute_update("DELETE FROM active_pairs WHERE symbol = ?", (symbol,))

    def cleanup(self):
        """Clean up database connections"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
        cprint("[DATABASE] Connections closed", "yellow")


# =================================================================
# SINGLETON INSTANCE
# =================================================================

_db_manager: Optional[DatabaseManager] = None

def get_db_manager(database_path: str = "trading_system_unified.db") -> DatabaseManager:
    """
    Get singleton database manager instance.

    Usage:
        from src.database_manager import get_db_manager

        db = get_db_manager()

        # Record trade
        db.record_trade(
            trade_id="trade_123",
            symbol="BTCUSDT",
            mode="PAPER",
            direction="BUY",
            entry_price=98000.0,
            position_size=0.01
        )

        # Get open trades
        open_trades = db.get_open_trades(mode="PAPER")

        # Close trade
        db.close_trade(
            trade_id="trade_123",
            exit_price=99000.0,
            pnl_usd=10.0,
            pnl_pct=1.02,
            exit_reason="TAKE_PROFIT"
        )
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_path)
    return _db_manager
