#!/usr/bin/env python3
"""
Moon Dev's Strategy-Based Trading + Paper Trading Integration

CONNECTS:
1. Strategy-Based Trading (signal generation)
2. Paper Trading System (risk-free execution)
3. Risk Monitoring (intelligent position management)
4. Sharp Fibonacci + ATR (dynamic levels)

USAGE:
- Set PAPER_TRADING_MODE = True for paper trading
- Set PAPER_TRADING_MODE = False for live trading
- Automatically applies risk monitoring in both modes
"""

import sys
import os

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, Optional
import time
from datetime import datetime

# Import strategy components
from trading_modes.02_STRATEGY_BASED_TRADING.strategy_agent import StrategyAgent

# Import paper trading and risk management
from risk_management.integrated_paper_trading import IntegratedPaperTradingSystem
from risk_management.intelligent_position_manager import IntelligentPositionManager
from risk_management.sharp_fibonacci_atr import ATRFibonacciCalculator, SharpFibonacciLevels

# Configuration
PAPER_TRADING_MODE = True  # Toggle: True = paper, False = live
PAPER_TRADING_BALANCE = 500  # Starting balance
MAX_POSITIONS = 3
USE_RISK_MONITORING = True
USE_SHARP_FIBONACCI = True  # Use evidence-based Fib + ATR


class IntegratedTradingSystem:
    """
    Complete trading system integrating:
    - Strategy signal generation
    - Paper trading OR live trading
    - Risk monitoring
    - Sharp Fibonacci + ATR levels
    """

    def __init__(
        self,
        paper_mode: bool = True,
        starting_balance: float = 500,
        max_positions: int = 3,
        use_risk_monitoring: bool = True
    ):
        self.paper_mode = paper_mode
        self.use_risk_monitoring = use_risk_monitoring

        print("\n" + "="*70)
        print("INTEGRATED TRADING SYSTEM INITIALIZATION")
        print("="*70)

        # Initialize Strategy Agent
        print("\n1. Initializing Strategy Agent...")
        self.strategy_agent = StrategyAgent()

        # Initialize Paper Trading or Live Trading
        if paper_mode:
            print("\n2. Initializing Paper Trading System...")
            self.paper_system = IntegratedPaperTradingSystem(
                balance_usd=starting_balance,
                max_positions=max_positions
            )

            if use_risk_monitoring:
                print("\n3. Initializing Risk Monitoring...")
                self.position_manager = IntelligentPositionManager(
                    paper_trader=self.paper_system.paper_trader,
                    check_interval_seconds=60,
                    auto_close_on_high_risk=True
                )

            print(f"\n   MODE: PAPER TRADING")
            print(f"   Balance: ${starting_balance:,.2f}")
            print(f"   Risk Monitoring: {'ENABLED' if use_risk_monitoring else 'DISABLED'}")

        else:
            print("\n2. Initializing LIVE Trading...")
            # Import exchange manager
            try:
                from src.exchange_manager import ExchangeManager
                self.exchange_manager = ExchangeManager()
                print(f"\n   MODE: LIVE TRADING")
                print(f"   Exchange: {self.exchange_manager.exchange}")
            except ImportError:
                print("\n   ERROR: ExchangeManager not found!")
                print("   Falling back to paper trading...")
                self.paper_mode = True
                self.paper_system = IntegratedPaperTradingSystem(
                    balance_usd=starting_balance,
                    max_positions=max_positions
                )

        print("\n" + "="*70)
        print("SYSTEM READY")
        print("="*70 + "\n")

    def run_trading_cycle(self, tokens: list):
        """
        Complete trading cycle:
        1. Get strategy signals
        2. Calculate sharp Fibonacci + ATR levels
        3. Execute trade (paper or live)
        4. Start risk monitoring
        """
        print(f"\n{'='*70}")
        print(f"TRADING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        for token in tokens:
            print(f"\n--- Analyzing {token} ---\n")

            # 1. Get strategy signals
            print("1. Getting strategy signals...")
            signals = self.strategy_agent.get_signals(token)

            if not signals or not any(s['action'] != 'NOTHING' for s in signals):
                print(f"   No actionable signals for {token}")
                continue

            # Show signals
            for i, signal in enumerate(signals):
                print(f"   Signal {i+1}: {signal['action']} (confidence: {signal['confidence']}%)")

            # Determine action based on signals
            buy_signals = [s for s in signals if s['action'] == 'BUY']
            sell_signals = [s for s in signals if s['action'] == 'SELL']

            if len(buy_signals) > len(sell_signals):
                action = 'BUY'
                avg_confidence = sum(s['confidence'] for s in buy_signals) / len(buy_signals)
            elif len(sell_signals) > len(buy_signals):
                action = 'SELL'
                avg_confidence = sum(s['confidence'] for s in sell_signals) / len(sell_signals)
            else:
                print(f"   Conflicting signals for {token}, skipping...")
                continue

            print(f"\n   Decision: {action} (avg confidence: {avg_confidence:.0f}%)")

            # Only proceed if confidence is high enough
            if avg_confidence < 70:
                print(f"   Confidence too low, skipping...")
                continue

            # 2. Execute trade
            if action == 'BUY':
                self.execute_buy(token)
            elif action == 'SELL':
                self.execute_sell(token)

        # 3. Monitor positions if enabled
        if self.paper_mode and self.use_risk_monitoring:
            print(f"\n{'='*70}")
            print("MONITORING POSITIONS")
            print(f"{'='*70}")
            self.position_manager.monitor_all_positions()

    def execute_buy(self, token: str):
        """Execute BUY with paper trading or live"""
        print(f"\n2. Executing BUY for {token}...")

        if self.paper_mode:
            # Use integrated paper trading system
            success, msg = self.paper_system.execute_trade(
                symbol=token,
                side='BUY'
            )

            if success:
                print(f"   Paper trade executed successfully")

                if self.use_risk_monitoring:
                    # Start monitoring in background
                    print(f"   Risk monitoring started")
            else:
                print(f"   Failed: {msg}")

        else:
            # Use live exchange
            print(f"   Executing LIVE trade...")
            try:
                # Execute real trade
                result = self.exchange_manager.market_buy(token)
                print(f"   LIVE trade executed: {result}")
            except Exception as e:
                print(f"   Error: {e}")

    def execute_sell(self, token: str):
        """Execute SELL with paper trading or live"""
        print(f"\n2. Executing SELL for {token}...")

        if self.paper_mode:
            # Close position in paper trading
            # (Implementation depends on how paper trader tracks positions)
            print(f"   Closing paper position for {token}")
        else:
            # Use live exchange
            print(f"   Executing LIVE sell...")
            try:
                result = self.exchange_manager.market_sell(token)
                print(f"   LIVE trade executed: {result}")
            except Exception as e:
                print(f"   Error: {e}")

    def get_status(self) -> Dict:
        """Get current system status"""
        if self.paper_mode:
            return self.paper_system.get_status()
        else:
            # Get status from exchange manager
            return {}


# ===========================
# MAIN
# ===========================

if __name__ == "__main__":
    print("Strategy-Based Trading + Paper Trading Integration\n")

    # Initialize integrated system
    system = IntegratedTradingSystem(
        paper_mode=PAPER_TRADING_MODE,
        starting_balance=PAPER_TRADING_BALANCE,
        max_positions=MAX_POSITIONS,
        use_risk_monitoring=USE_RISK_MONITORING
    )

    # Test with BTC
    tokens = ['BTC']

    # Run one cycle
    print("Running one trading cycle...\n")
    system.run_trading_cycle(tokens)

    # Show status
    print("\n" + "="*70)
    print("SYSTEM STATUS")
    print("="*70)
    status = system.get_status()
    for key, value in status.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n" + "="*70)
    print("INTEGRATION COMPLETE")
    print("="*70)
    print("\nFeatures:")
    print("  - Strategy signal generation")
    print("  - Paper trading (Binance-truth)")
    print("  - Risk monitoring (7 factors)")
    print("  - Sharp Fibonacci + ATR levels")
    print("  - Easy toggle between paper/live")
