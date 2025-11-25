#!/usr/bin/env python3
"""
🌙 Moon Dev's INTEGRATED Paper Trading System
Combines: Simple Allocation Calculator + Binance-Truth Paper Trading

COMPLETE FLOW:
1. Get market data (real OHLCV from Binance)
2. Calculate smart allocation (5 factors, low-balance aware)
3. Determine stop loss and TPs dynamically
4. Execute paper trade with REAL Binance data
5. Track position with real price updates

LOW BALANCE SUPPORT:
- Min $100 balance
- Max 3 concurrent positions
- Smart allocation based on balance available
"""

import sys
import os
import io

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Import our modules
from order_management.simple_allocation_calculator import (
    SimpleAllocationCalculator,
    LowBalancePositionSizer,
    calculate_smart_allocation
)
from risk_management.binance_truth_paper_trading import (
    BinanceTruthAPI,
    BinanceTruthPaperTrader,
    PaperPosition
)
from risk_management.sharp_fibonacci_atr import (
    ATRFibonacciCalculator,
    SharpFibonacciLevels,
    SharpSwingDetector
)
from risk_management.trading_database import get_trading_db

# ===========================
# MARKET DATA FETCHER
# ===========================

class BinanceMarketData:
    """Fetch REAL market data from Binance"""

    @staticmethod
    def get_ohlcv(symbol: str, interval: str = '1h', limit: int = 200) -> pd.DataFrame:
        """
        Get REAL OHLCV data from Binance

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles (max 1000)
        """
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"

        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"❌ Failed to fetch OHLCV: {response.status_code}")
                return None

            data = response.json()

            # Parse into DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert to proper types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            print(f"❌ Error fetching OHLCV: {e}")
            return None

# ===========================
# USING: Sharp Fibonacci + ATR Calculator
# Evidence-based professional methodology
# - Williams Fractal swing detection
# - ZigZag filter (minimum 2% swing)
# - ATR-adjusted stops (2.0-3.0x multiplier)
# - Volume confirmation
# (NO STATIC RANGES!)
# ===========================

# ===========================
# INTEGRATED SYSTEM
# ===========================

class IntegratedPaperTradingSystem:
    """
    Complete paper trading system:
    1. Fetch real market data
    2. Calculate smart allocation
    3. Calculate dynamic levels
    4. Execute paper trade
    5. Monitor with real prices
    """

    def __init__(
        self,
        balance_usd: float = 500.0,
        max_positions: int = 3
    ):
        self.paper_trader = BinanceTruthPaperTrader(balance_usd, max_positions)
        self.allocation_calc = SimpleAllocationCalculator()
        # Use Sharp Fibonacci + ATR calculator (EVIDENCE-BASED!)
        self.level_calc = ATRFibonacciCalculator()
        # Connect to database
        self.db = get_trading_db()

        print(f"🌙 Integrated Paper Trading System")
        print(f"   Starting balance: ${balance_usd:,.2f}")
        print(f"   Max positions: {max_positions}")
        print(f"   Level calculator: SHARP FIBONACCI + ATR (evidence-based)")
        print(f"   - Williams Fractal swing detection")
        print(f"   - ZigZag filter (2% minimum)")
        print(f"   - ATR multiplier (2.0-3.0x)")
        print(f"   Database: CONNECTED")
        print(f"   Status: READY\n")

    def execute_trade(
        self,
        symbol: str,
        side: str = 'BUY',
        position_size_usd: Optional[float] = None,
        strategy_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Execute complete trade flow

        Args:
            symbol: Token symbol (e.g., 'BTC')
            side: 'BUY' or 'SELL'
            position_size_usd: Override position size (None = auto-calculate)
            strategy_name: Name of strategy generating this trade

        Returns:
            (success, message)
        """
        print(f"\n{'='*60}")
        print(f"EXECUTING TRADE: {side} {symbol}")
        print(f"{'='*60}\n")

        # Step 1: Fetch real market data
        print("📊 Step 1: Fetching real market data from Binance...")
        ohlcv = BinanceMarketData.get_ohlcv(symbol, interval='1h', limit=200)

        if ohlcv is None:
            return False, "Failed to fetch market data"

        print(f"   ✅ Fetched {len(ohlcv)} candles")
        print(f"   Current price: ${ohlcv['close'].iloc[-1]:.2f}")

        # Step 2: Calculate smart allocation
        print("\n💡 Step 2: Calculating smart allocation...")

        num_open = len([p for p in self.paper_trader.positions if p.remaining_pct > 0])

        result = calculate_smart_allocation(
            ohlcv,
            self.paper_trader.balance,
            num_open
        )

        if not result['can_trade']:
            return False, f"Cannot trade: {result['reasoning']}"

        if position_size_usd is None:
            position_size_usd = result['position_size_usd']

        print(f"   ✅ Position size: ${position_size_usd:.2f}")
        print(f"   ✅ Allocation: TP1={result['tp1_pct']:.0f}% | TP2={result['tp2_pct']:.0f}% | TP3={result['tp3_pct']:.0f}%")
        print(f"   ✅ Reasoning: {result['reasoning']}")

        # Step 3: Calculate SHARP Fibonacci + ATR levels (EVIDENCE-BASED!)
        print("\n🎯 Step 3: Calculating SHARP Fibonacci + ATR levels (evidence-based)...")

        entry_price = BinanceTruthAPI.get_live_price(symbol)
        if entry_price is None:
            return False, "Could not fetch current price"

        levels_obj = self.level_calc.calculate_sharp_fibonacci_atr(ohlcv, entry_price, side)
        levels = levels_obj.to_dict()  # Convert dataclass to dict

        print(f"   ✅ Stop Loss: ${levels['stop_loss']:.2f} ({levels['sl_pct']:.2f}%)")
        print(f"   ✅ TP1: ${levels['tp1']:.2f} (+{levels['tp1_pct']:.2f}%, Fib {levels['tp1_fib_level']:.3f})")
        print(f"   ✅ TP2: ${levels['tp2']:.2f} (+{levels['tp2_pct']:.2f}%, Fib {levels['tp2_fib_level']:.3f})")
        print(f"   ✅ TP3: ${levels['tp3']:.2f} (+{levels['tp3_pct']:.2f}%, Fib {levels['tp3_fib_level']:.3f})")
        print(f"   ✅ Logic:")
        print(f"      {levels['logic']}")
        print(f"   ✅ ATR: {levels['atr_pct']:.2f}%, Multiplier: {levels['atr_multiplier']:.1f}x")
        print(f"   ✅ Swing: {levels['swing_bars_ago']} bars ago (confidence: {levels['confidence']})")
        print(f"   ✅ Swing strength: {levels['swing_strength']:.0f}/100")

        # Step 4: Execute paper trade
        print("\n💰 Step 4: Executing paper trade with REAL Binance data...")

        success, msg = self.paper_trader.open_position(
            symbol=symbol,
            side=side,
            size_usd=position_size_usd,
            stop_loss=levels['stop_loss'],
            tp1_price=levels['tp1'], tp1_pct=result['tp1_pct'],
            tp2_price=levels['tp2'], tp2_pct=result['tp2_pct'],
            tp3_price=levels['tp3'], tp3_pct=result['tp3_pct'],
            strategy_name=strategy_name
        )

        if not success:
            return False, msg

        # Step 5: Log to database
        print("\n💾 Step 5: Logging trade to database...")
        trade_id = f"{symbol}_{side}_{int(datetime.now().timestamp())}"

        self.db.insert_trade(
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            position_size_usd=position_size_usd,
            stop_loss=levels['stop_loss'],
            tp1_price=levels['tp1'],
            tp2_price=levels['tp2'],
            tp3_price=levels['tp3'],
            tp1_pct=result['tp1_pct'],
            tp2_pct=result['tp2_pct'],
            tp3_pct=result['tp3_pct'],
            mode="PAPER",
            swing_bars_ago=levels['swing_bars_ago'],
            swing_strength=levels['swing_strength'],
            atr_pct=levels['atr_pct'],
            atr_multiplier=levels['atr_multiplier'],
            confidence=levels['confidence'],
            metadata={
                'allocation_reasoning': result['reasoning'],
                'fib_logic': levels['logic']
            }
        )

        # Cache Fibonacci levels
        self.db.cache_fibonacci_levels(symbol, entry_price, levels)

        print(f"   ✅ Trade logged to database: {trade_id}")

        print(f"\n✅ TRADE EXECUTED SUCCESSFULLY")
        return True, "Trade executed"

    def monitor_positions(self):
        """Check all positions with REAL Binance prices"""
        self.paper_trader.check_all_positions()

    def get_status(self) -> Dict:
        """Get current system status"""
        return self.paper_trader.get_status()


# ===========================
# TEST / DEMO
# ===========================

if __name__ == "__main__":
    # Fix encoding for Windows
    if os.name == 'nt' and hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Moon Dev's Integrated Paper Trading System - TEST\n")

    # Initialize with low balance
    system = IntegratedPaperTradingSystem(balance_usd=500, max_positions=3)

    # Execute BTC trade
    success, msg = system.execute_trade('BTC', 'BUY', position_size_usd=150)

    if success:
        print("\n" + "="*60)
        print("MONITORING POSITIONS")
        print("="*60)
        system.monitor_positions()

        print("\n" + "="*60)
        print("SYSTEM STATUS")
        print("="*60)
        status = system.get_status()
        for key, value in status.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")

    else:
        print(f"\n❌ Trade failed: {msg}")

    print("\n✅ System uses REAL Binance data at every step!")
    print("✅ Dynamic allocation based on balance and market conditions")
    print("✅ SHARP Fibonacci + ATR levels (evidence-based)")
    print("   - Williams Fractal swing detection")
    print("   - ZigZag filter removes noise")
    print("   - ATR multiplier 2.0-3.0x (97% confidence)")
    print("   - Volume confirmation")
    print("✅ No static ranges - all levels based on recent market structure")
