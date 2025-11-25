#!/usr/bin/env python3
"""
🌙 Example: Paper Trading with Backtested Strategy

Shows how to integrate the paper trading system with
converted backtested strategies from yesterday.

FLOW:
1. Initialize paper trading system (low balance support)
2. Load backtested strategy
3. Get strategy signal
4. Execute trade if signal is BUY
5. Monitor positions with real Binance prices
"""

import sys
import os
import io
if os.name == 'nt' and hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from risk_management.integrated_paper_trading import IntegratedPaperTradingSystem
import time

# ===========================
# MOCK STRATEGY (replace with real converted strategy)
# ===========================

class BreakoutStrategy:
    """
    Example strategy - replace with your converted backtest
    from yesterday's work
    """

    def generate_signal(self, symbol: str) -> dict:
        """
        Generate trading signal

        Returns:
            {
                'action': 'BUY' | 'SELL' | 'NOTHING',
                'confidence': 0-100,
                'reasoning': str
            }
        """
        # In real implementation, this would:
        # 1. Fetch market data
        # 2. Calculate indicators
        # 3. Apply strategy logic
        # 4. Return signal

        # For demo purposes:
        return {
            'action': 'BUY',
            'confidence': 85,
            'reasoning': 'Breakout above resistance with high volume'
        }


# ===========================
# MAIN TRADING LOOP
# ===========================

def main():
    print("=" * 60)
    print("PAPER TRADING WITH STRATEGY EXAMPLE")
    print("=" * 60)
    print()

    # Initialize paper trading system
    # (Low balance: $500, max 3 positions)
    system = IntegratedPaperTradingSystem(
        balance_usd=500,
        max_positions=3
    )

    # Initialize strategy
    # TODO: Replace with your converted backtest strategy
    strategy = BreakoutStrategy()

    print("\n" + "=" * 60)
    print("CHECKING STRATEGY SIGNAL")
    print("=" * 60)

    # Get signal from strategy
    signal = strategy.generate_signal('BTC')

    print(f"\nStrategy: {strategy.__class__.__name__}")
    print(f"Symbol: BTC")
    print(f"Signal: {signal['action']}")
    print(f"Confidence: {signal['confidence']}%")
    print(f"Reasoning: {signal['reasoning']}")

    # Execute trade if signal is BUY and confidence > 70%
    if signal['action'] == 'BUY' and signal['confidence'] > 70:
        print("\n✅ Signal meets criteria - executing trade...")

        success, msg = system.execute_trade('BTC', 'BUY')

        if success:
            print("\n✅ Trade executed successfully!")
        else:
            print(f"\n❌ Trade failed: {msg}")

    elif signal['action'] == 'SELL':
        print("\n⚠️  SELL signal - would close positions (not implemented in example)")

    else:
        print("\n⏸️  No action - signal does not meet criteria")

    # Monitor positions
    print("\n" + "=" * 60)
    print("MONITORING POSITIONS")
    print("=" * 60)

    for i in range(3):  # Check 3 times
        print(f"\nCheck #{i+1}:")
        system.monitor_positions()

        status = system.get_status()
        print(f"Balance: ${status['balance']:.2f}")
        print(f"PnL: ${status['total_pnl']:+.2f}")
        print(f"Open positions: {status['open_positions']}")

        if i < 2:
            time.sleep(2)  # Wait 2 seconds between checks

    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)

    status = system.get_status()
    print(f"\nStarting balance: ${status['starting_balance']:,.2f}")
    print(f"Current balance: ${status['balance']:,.2f}")
    print(f"Total PnL: ${status['total_pnl']:+.2f}")
    print(f"Return: {status['return_pct']:+.2f}%")
    print(f"Fees paid: ${status['total_fees']:.2f}")
    print(f"Open positions: {status['open_positions']}")
    print(f"Total trades: {status['total_trades']}")

    print("\n✅ Example complete!")
    print("\n📝 Next steps:")
    print("   1. Replace BreakoutStrategy with your converted backtest")
    print("   2. Add multiple strategies")
    print("   3. Run in continuous loop")
    print("   4. Add position management (when to close)")


if __name__ == "__main__":
    main()
