#!/usr/bin/env python3
"""
Trading Database System - SQLite
Tracks all trades, strategies, and system events
Ensures complete traceability and connectivity
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd

class TradingDatabase:
    """
    Complete trading database for tracking:
    - Paper and live trades
    - Strategy performance
    - Converted strategies from RBI Agent
    - Risk events
    - System health
    """

    def __init__(self, db_path: str = "trading_system.db"):
        """Initialize database connection"""
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Create all necessary tables"""

        # Trades table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                position_size_usd REAL NOT NULL,
                stop_loss REAL NOT NULL,
                tp1_price REAL,
                tp2_price REAL,
                tp3_price REAL,
                tp1_pct REAL,
                tp2_pct REAL,
                tp3_pct REAL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                exit_price REAL,
                exit_timestamp DATETIME,
                pnl_usd REAL,
                pnl_pct REAL,
                exit_reason TEXT,
                strategy_name TEXT,
                swing_bars_ago INTEGER,
                swing_strength REAL,
                atr_pct REAL,
                atr_multiplier REAL,
                confidence TEXT,
                metadata TEXT
            )
        """)

        # Strategies table (RBI converted strategies)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT UNIQUE NOT NULL,
                created_timestamp DATETIME NOT NULL,
                source_type TEXT NOT NULL,
                source_url TEXT,
                backtest_return REAL,
                backtest_sharpe REAL,
                backtest_max_drawdown REAL,
                backtest_win_rate REAL,
                backtest_trades INTEGER,
                converted_timestamp DATETIME,
                validation_timestamp DATETIME,
                validation_return REAL,
                validation_passed INTEGER,
                validation_reason TEXT,
                deployed INTEGER DEFAULT 0,
                deployed_timestamp DATETIME,
                code_path TEXT,
                metadata TEXT
            )
        """)

        # Strategy performance tracking
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                trades_count INTEGER,
                win_rate REAL,
                avg_pnl_pct REAL,
                total_pnl_usd REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                status TEXT,
                FOREIGN KEY (strategy_name) REFERENCES strategies(strategy_name)
            )
        """)

        # Risk events table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                trade_id TEXT,
                event_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                risk_score REAL,
                action_taken TEXT,
                reasoning TEXT,
                metadata TEXT,
                FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
            )
        """)

        # System events table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                event_type TEXT NOT NULL,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                metadata TEXT
            )
        """)

        # Strategy token assignments table
        # Evidence: Codd (1970) - First Normal Form (atomic values, not JSON)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                token TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                data_file TEXT NOT NULL,
                backtest_return REAL,
                backtest_sharpe REAL,
                backtest_trades INTEGER,
                validation_return REAL,
                validation_passed INTEGER DEFAULT 0,
                is_primary INTEGER DEFAULT 0,
                created_timestamp DATETIME NOT NULL,
                FOREIGN KEY (strategy_name) REFERENCES strategies(strategy_name),
                UNIQUE(strategy_name, token, timeframe)
            )
        """)

        # Fibonacci levels cache
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fibonacci_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                entry_price REAL NOT NULL,
                swing_high REAL,
                swing_low REAL,
                swing_bars_ago INTEGER,
                swing_strength REAL,
                atr REAL,
                atr_pct REAL,
                atr_multiplier REAL,
                stop_loss REAL,
                tp1 REAL,
                tp2 REAL,
                tp3 REAL,
                confidence TEXT,
                metadata TEXT
            )
        """)

        self.conn.commit()

    # ==========================================
    # TRADE OPERATIONS
    # ==========================================

    def insert_trade(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        position_size_usd: float,
        stop_loss: float,
        tp1_price: float,
        tp2_price: float,
        tp3_price: float,
        mode: str,
        tp1_pct: float = None,
        tp2_pct: float = None,
        tp3_pct: float = None,
        strategy_name: str = None,
        swing_bars_ago: int = None,
        swing_strength: float = None,
        atr_pct: float = None,
        atr_multiplier: float = None,
        confidence: str = None,
        metadata: dict = None
    ) -> int:
        """Insert new trade"""
        try:
            self.cursor.execute("""
                INSERT INTO trades (
                    trade_id, timestamp, symbol, side, entry_price,
                    position_size_usd, stop_loss, tp1_price, tp2_price, tp3_price,
                    tp1_pct, tp2_pct, tp3_pct, mode, status, strategy_name,
                    swing_bars_ago, swing_strength, atr_pct, atr_multiplier,
                    confidence, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_id, datetime.now(), symbol, side, entry_price,
                position_size_usd, stop_loss, tp1_price, tp2_price, tp3_price,
                tp1_pct, tp2_pct, tp3_pct, mode, 'OPEN', strategy_name,
                swing_bars_ago, swing_strength, atr_pct, atr_multiplier,
                confidence, json.dumps(metadata) if metadata else None
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Trade {trade_id} already exists!")
            return -1

    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        pnl_usd: float,
        pnl_pct: float,
        exit_reason: str
    ) -> bool:
        """Close existing trade"""
        self.cursor.execute("""
            UPDATE trades
            SET status = 'CLOSED',
                exit_price = ?,
                exit_timestamp = ?,
                pnl_usd = ?,
                pnl_pct = ?,
                exit_reason = ?
            WHERE trade_id = ?
        """, (exit_price, datetime.now(), pnl_usd, pnl_pct, exit_reason, trade_id))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_open_trades(self, mode: str = None) -> List[Dict]:
        """Get all open trades"""
        if mode:
            self.cursor.execute("""
                SELECT * FROM trades WHERE status = 'OPEN' AND UPPER(mode) = UPPER(?)
                ORDER BY timestamp DESC
            """, (mode,))
        else:
            self.cursor.execute("""
                SELECT * FROM trades WHERE status = 'OPEN'
                ORDER BY timestamp DESC
            """)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_trade_by_id(self, trade_id: str) -> Optional[Dict]:
        """Get specific trade"""
        self.cursor.execute("SELECT * FROM trades WHERE trade_id = ?", (trade_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_trades_by_strategy(self, strategy_name: str, limit: int = 100) -> List[Dict]:
        """Get trades for specific strategy"""
        self.cursor.execute("""
            SELECT * FROM trades
            WHERE strategy_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (strategy_name, limit))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_trade_stats(self, mode: str = None, days: int = 30) -> Dict:
        """Get trading statistics"""
        query = """
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl_usd <= 0 THEN 1 ELSE 0 END) as losses,
                AVG(pnl_pct) as avg_pnl_pct,
                SUM(pnl_usd) as total_pnl_usd,
                MAX(pnl_pct) as max_win_pct,
                MIN(pnl_pct) as max_loss_pct
            FROM trades
            WHERE status = 'CLOSED'
            AND timestamp >= datetime('now', '-{} days')
        """.format(days)

        if mode:
            query += " AND UPPER(mode) = UPPER(?)"
            self.cursor.execute(query, (mode,))
        else:
            self.cursor.execute(query)

        row = self.cursor.fetchone()
        if not row:
            return {}

        stats = dict(row)
        if stats['total_trades'] > 0:
            stats['win_rate'] = (stats['wins'] / stats['total_trades']) * 100
        else:
            stats['win_rate'] = 0

        return stats

    # ==========================================
    # STRATEGY OPERATIONS
    # ==========================================

    def insert_strategy(
        self,
        strategy_name: str,
        source_type: str,
        backtest_return: float,
        backtest_sharpe: float,
        backtest_max_drawdown: float,
        backtest_win_rate: float,
        backtest_trades: int,
        source_url: str = None,
        code_path: str = None,
        metadata: dict = None
    ) -> int:
        """Insert new strategy from RBI Agent"""
        try:
            self.cursor.execute("""
                INSERT INTO strategies (
                    strategy_name, created_timestamp, source_type, source_url,
                    backtest_return, backtest_sharpe, backtest_max_drawdown,
                    backtest_win_rate, backtest_trades, code_path, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                strategy_name, datetime.now(), source_type, source_url,
                backtest_return, backtest_sharpe, backtest_max_drawdown,
                backtest_win_rate, backtest_trades, code_path,
                json.dumps(metadata) if metadata else None
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Strategy {strategy_name} already exists!")
            return -1

    def update_strategy_validation(
        self,
        strategy_name: str,
        validation_return: float,
        validation_passed: bool,
        validation_reason: str
    ) -> bool:
        """Update strategy validation results"""
        self.cursor.execute("""
            UPDATE strategies
            SET validation_timestamp = ?,
                validation_return = ?,
                validation_passed = ?,
                validation_reason = ?
            WHERE strategy_name = ?
        """, (
            datetime.now(),
            validation_return,
            1 if validation_passed else 0,
            validation_reason,
            strategy_name
        ))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def deploy_strategy(self, strategy_name: str) -> bool:
        """Mark strategy as deployed"""
        self.cursor.execute("""
            UPDATE strategies
            SET deployed = 1,
                deployed_timestamp = ?
            WHERE strategy_name = ?
        """, (datetime.now(), strategy_name))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_strategy(self, strategy_name: str) -> Optional[Dict]:
        """Get strategy details"""
        self.cursor.execute("SELECT * FROM strategies WHERE strategy_name = ?", (strategy_name,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_deployed_strategies(self) -> List[Dict]:
        """Get all deployed strategies"""
        self.cursor.execute("""
            SELECT * FROM strategies
            WHERE deployed = 1
            ORDER BY deployed_timestamp DESC
        """)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_strategies_pending_validation(self) -> List[Dict]:
        """Get strategies awaiting validation"""
        self.cursor.execute("""
            SELECT * FROM strategies
            WHERE validation_timestamp IS NULL
            ORDER BY created_timestamp DESC
        """)
        return [dict(row) for row in self.cursor.fetchall()]

    # ==========================================
    # RISK EVENT OPERATIONS
    # ==========================================

    def insert_risk_event(
        self,
        event_type: str,
        risk_level: str,
        risk_score: float,
        action_taken: str,
        reasoning: str,
        trade_id: str = None,
        metadata: dict = None
    ) -> int:
        """Log risk event"""
        self.cursor.execute("""
            INSERT INTO risk_events (
                timestamp, trade_id, event_type, risk_level,
                risk_score, action_taken, reasoning, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(), trade_id, event_type, risk_level,
            risk_score, action_taken, reasoning,
            json.dumps(metadata) if metadata else None
        ))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_recent_risk_events(self, hours: int = 24) -> List[Dict]:
        """Get recent risk events"""
        self.cursor.execute("""
            SELECT * FROM risk_events
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        """.format(hours))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_high_risk_trades(self) -> List[Dict]:
        """Get trades with HIGH risk events"""
        self.cursor.execute("""
            SELECT DISTINCT t.*, r.risk_score, r.reasoning
            FROM trades t
            JOIN risk_events r ON t.trade_id = r.trade_id
            WHERE r.risk_level = 'HIGH'
            AND t.status = 'OPEN'
            ORDER BY r.timestamp DESC
        """)
        return [dict(row) for row in self.cursor.fetchall()]

    # ==========================================
    # SYSTEM EVENT OPERATIONS
    # ==========================================

    def log_system_event(
        self,
        event_type: str,
        component: str,
        status: str,
        message: str,
        metadata: dict = None
    ) -> int:
        """Log system event"""
        self.cursor.execute("""
            INSERT INTO system_events (
                timestamp, event_type, component, status, message, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(), event_type, component, status, message,
            json.dumps(metadata) if metadata else None
        ))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_system_health(self) -> Dict:
        """Get system health status"""
        # Check recent errors
        self.cursor.execute("""
            SELECT COUNT(*) as error_count
            FROM system_events
            WHERE status = 'ERROR'
            AND timestamp >= datetime('now', '-1 hour')
        """)
        recent_errors = self.cursor.fetchone()['error_count']

        # Check open trades
        open_trades = len(self.get_open_trades())

        # Check high risk events
        self.cursor.execute("""
            SELECT COUNT(*) as high_risk_count
            FROM risk_events
            WHERE risk_level = 'HIGH'
            AND timestamp >= datetime('now', '-1 hour')
        """)
        recent_high_risk = self.cursor.fetchone()['high_risk_count']

        # Determine health
        if recent_errors > 10 or recent_high_risk > 5:
            health = "CRITICAL"
        elif recent_errors > 5 or recent_high_risk > 2:
            health = "WARNING"
        else:
            health = "HEALTHY"

        return {
            'health': health,
            'recent_errors': recent_errors,
            'open_trades': open_trades,
            'recent_high_risk': recent_high_risk,
            'timestamp': datetime.now().isoformat()
        }

    # ==========================================
    # FIBONACCI LEVELS CACHE
    # ==========================================

    def cache_fibonacci_levels(
        self,
        symbol: str,
        entry_price: float,
        levels: Dict
    ) -> int:
        """Cache calculated Fibonacci levels"""
        self.cursor.execute("""
            INSERT INTO fibonacci_levels (
                symbol, timestamp, entry_price, swing_high, swing_low,
                swing_bars_ago, swing_strength, atr, atr_pct,
                atr_multiplier, stop_loss, tp1, tp2, tp3, confidence, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol, datetime.now(), entry_price,
            levels.get('swing_high'), levels.get('swing_low'),
            levels.get('swing_bars_ago'), levels.get('swing_strength'),
            levels.get('atr'), levels.get('atr_pct'), levels.get('atr_multiplier'),
            levels.get('stop_loss'), levels.get('tp1'), levels.get('tp2'),
            levels.get('tp3'), levels.get('confidence'),
            json.dumps(levels.get('raw_swing_data')) if levels.get('raw_swing_data') else None
        ))
        self.conn.commit()
        return self.cursor.lastrowid

    # ==========================================
    # REPORTING
    # ==========================================

    def get_daily_report(self) -> pd.DataFrame:
        """Get daily trading report"""
        query = """
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as trades,
                SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
                SUM(pnl_usd) as total_pnl,
                AVG(pnl_pct) as avg_pnl_pct,
                MAX(pnl_pct) as best_trade,
                MIN(pnl_pct) as worst_trade
            FROM trades
            WHERE status = 'CLOSED'
            AND timestamp >= datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """
        return pd.read_sql_query(query, self.conn)

    def get_strategy_comparison(self) -> pd.DataFrame:
        """Compare all deployed strategies"""
        query = """
            SELECT
                s.strategy_name,
                s.backtest_return,
                s.validation_return,
                COUNT(t.id) as live_trades,
                AVG(t.pnl_pct) as avg_live_pnl,
                SUM(CASE WHEN t.pnl_usd > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(t.id) as win_rate
            FROM strategies s
            LEFT JOIN trades t ON s.strategy_name = t.strategy_name AND t.status = 'CLOSED'
            WHERE s.deployed = 1
            GROUP BY s.strategy_name
            ORDER BY avg_live_pnl DESC
        """
        return pd.read_sql_query(query, self.conn)

    # ==========================================
    # STRATEGY TOKEN OPERATIONS
    # ==========================================

    def add_strategy_token(
        self,
        strategy_name: str,
        token: str,
        timeframe: str,
        data_file: str,
        backtest_return: float,
        backtest_sharpe: float = None,
        backtest_trades: int = None,
        is_primary: bool = False
    ) -> int:
        """
        Add token/timeframe assignment for strategy

        Evidence: Codd (1970) - Atomic values in normalized tables
        Each strategy can work on multiple tokens/timeframes
        """
        try:
            self.cursor.execute("""
                INSERT INTO strategy_tokens (
                    strategy_name, token, timeframe, data_file,
                    backtest_return, backtest_sharpe, backtest_trades,
                    is_primary, created_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                strategy_name, token, timeframe, data_file,
                backtest_return, backtest_sharpe, backtest_trades,
                1 if is_primary else 0, datetime.now()
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Token assignment {strategy_name}+{token}+{timeframe} already exists!")
            return -1

    def update_strategy_token_validation(
        self,
        strategy_name: str,
        token: str,
        timeframe: str,
        validation_return: float,
        validation_passed: bool
    ):
        """Update validation results for specific token/timeframe"""
        self.cursor.execute("""
            UPDATE strategy_tokens
            SET validation_return = ?, validation_passed = ?
            WHERE strategy_name = ? AND token = ? AND timeframe = ?
        """, (validation_return, 1 if validation_passed else 0, strategy_name, token, timeframe))
        self.conn.commit()

    def get_strategies_for_token(self, token: str, deployed_only: bool = True) -> List[Dict]:
        """
        Get all deployed strategies that work for this token

        Returns: List of {strategy_name, timeframe, data_file, backtest_return, validation_passed}

        Evidence: Query optimization (Chen et al., 1976)
        """
        query = """
            SELECT
                st.strategy_name,
                st.token,
                st.timeframe,
                st.data_file,
                st.backtest_return,
                st.backtest_sharpe,
                st.validation_return,
                st.validation_passed,
                st.is_primary,
                s.code_path,
                s.deployed_timestamp
            FROM strategy_tokens st
            JOIN strategies s ON st.strategy_name = s.strategy_name
            WHERE st.token = ?
            AND st.validation_passed = 1
        """

        if deployed_only:
            query += " AND s.deployed = 1"

        query += " ORDER BY st.backtest_return DESC"

        self.cursor.execute(query, (token,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_best_token_for_strategy(self, strategy_name: str) -> Dict:
        """Get the best performing token/timeframe for a strategy"""
        self.cursor.execute("""
            SELECT *
            FROM strategy_tokens
            WHERE strategy_name = ?
            ORDER BY backtest_return DESC
            LIMIT 1
        """, (strategy_name,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_strategy_tokens(self, strategy_name: str) -> List[Dict]:
        """Get all token/timeframe combinations for a strategy"""
        self.cursor.execute("""
            SELECT *
            FROM strategy_tokens
            WHERE strategy_name = ?
            ORDER BY backtest_return DESC
        """, (strategy_name,))
        return [dict(row) for row in self.cursor.fetchall()]

    def close(self):
        """Close database connection"""
        self.conn.close()

    def __del__(self):
        """Ensure connection is closed"""
        try:
            self.conn.close()
        except:
            pass


# ==========================================
# SINGLETON INSTANCE
# ==========================================

_db_instance = None

def get_trading_db() -> TradingDatabase:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        db_path = Path(__file__).parent.parent / "trading_system.db"
        _db_instance = TradingDatabase(str(db_path))
    return _db_instance


# ==========================================
# TESTING
# ==========================================

if __name__ == "__main__":
    import sys
    import io
    # Fix encoding for Windows
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Testing Trading Database System...\n")

    # Initialize database
    db = TradingDatabase("test_trading.db")

    # Test: Insert trade
    print("1. Inserting test trade...")
    trade_id = f"TEST_{datetime.now().timestamp()}"
    db.insert_trade(
        trade_id=trade_id,
        symbol="BTC",
        side="BUY",
        entry_price=105000.0,
        position_size_usd=500.0,
        stop_loss=103948.24,
        tp1_price=109159.20,
        tp2_price=111269.80,
        tp3_price=117369.80,
        mode="PAPER",
        strategy_name="TestStrategy",
        swing_bars_ago=7,
        swing_strength=78.0,
        atr_pct=0.53,
        atr_multiplier=2.0,
        confidence="HIGH"
    )
    print(f"   ✅ Trade inserted: {trade_id}")

    # Test: Get open trades
    print("\n2. Getting open trades...")
    open_trades = db.get_open_trades(mode="PAPER")
    print(f"   ✅ Found {len(open_trades)} open trades")

    # Test: Insert strategy
    print("\n3. Inserting test strategy...")
    db.insert_strategy(
        strategy_name="TestStrategy",
        source_type="RBI_VIDEO",
        backtest_return=150.5,
        backtest_sharpe=2.3,
        backtest_max_drawdown=-15.2,
        backtest_win_rate=65.5,
        backtest_trades=100,
        source_url="https://youtube.com/example"
    )
    print("   ✅ Strategy inserted")

    # Test: Update validation
    print("\n4. Updating strategy validation...")
    db.update_strategy_validation(
        strategy_name="TestStrategy",
        validation_return=148.2,
        validation_passed=True,
        validation_reason="Within 20% of backtest"
    )
    print("   ✅ Validation updated")

    # Test: Deploy strategy
    print("\n5. Deploying strategy...")
    db.deploy_strategy("TestStrategy")
    print("   ✅ Strategy deployed")

    # Test: Insert risk event
    print("\n6. Inserting risk event...")
    db.insert_risk_event(
        event_type="HIGH_RISK_DETECTED",
        risk_level="HIGH",
        risk_score=75.5,
        action_taken="POSITION_CLOSED",
        reasoning="Price broke support + high volume",
        trade_id=trade_id
    )
    print("   ✅ Risk event logged")

    # Test: Close trade
    print("\n7. Closing trade...")
    db.close_trade(
        trade_id=trade_id,
        exit_price=109200.0,
        pnl_usd=20.0,
        pnl_pct=4.0,
        exit_reason="TP1_HIT"
    )
    print("   ✅ Trade closed")

    # Test: Get stats
    print("\n8. Getting trade statistics...")
    stats = db.get_trade_stats(mode="PAPER")
    print(f"   ✅ Stats: {stats}")

    # Test: System health
    print("\n9. Checking system health...")
    health = db.get_system_health()
    print(f"   ✅ Health: {health['health']}")

    print("\n✅ All database tests passed!")
    print(f"\nDatabase created at: test_trading.db")

    db.close()
