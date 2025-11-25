"""
TEST PATHWAY 1: Strategy-Based SELL Signal
Force a SELL signal to test execution path
"""
import sys
from datetime import datetime, timezone
from trading_modes.core.signal_bus import SignalBus, Signal
from trading_modes.core.arbiter import DeterministicArbiter
from risk_management.trading_database_typed import TradingDatabase

def test_strategy_sell_signal():
    """
    Test SELL signal execution for ETH (currently holding BUY position)

    Expected Behavior:
    1. Force SELL signal into bus
    2. Arbiter should approve (confidence 75% > 50% threshold)
    3. System should close BUY position at market
    4. Exit reason: 'opposite_signal' or 'strategy_sell_signal'
    """

    print("\n" + "="*80)
    print("TEST: PATHWAY 1 - STRATEGY-BASED SELL SIGNAL")
    print("="*80)

    # Initialize components
    signal_bus = SignalBus()
    arbiter = DeterministicArbiter()
    db = TradingDatabase()

    # Check current ETH position
    print("\n[1/4] Checking current ETH position...")
    trades = db.get_open_trades()
    # Handle both dict and Trade object
    eth_trade = next((t for t in trades if 'ETH' in (t.symbol if hasattr(t, 'symbol') else t.get('symbol', ''))), None)

    if not eth_trade:
        print(" No open ETH position found - cannot test SELL execution")
        print("   (SELL signal would be ignored on SPOT with no position)")
        return

    # Extract values (handle both dict and object)
    trade_id = eth_trade.trade_id if hasattr(eth_trade, 'trade_id') else eth_trade.get('id')
    side = eth_trade.side.value if hasattr(eth_trade, 'side') else eth_trade.get('side')
    entry_price = eth_trade.entry_price if hasattr(eth_trade, 'entry_price') else eth_trade.get('entry_price')
    position_size = eth_trade.position_size_usd if hasattr(eth_trade, 'position_size_usd') else eth_trade.get('position_size_usd')

    print(f"Found open ETH position:")
    print(f"   Trade ID: {trade_id}")
    print(f"   Side: {side}")
    print(f"   Entry: ${entry_price:.2f}")
    print(f"   Size: ${position_size:.2f}")

    if side != 'BUY':
        print(f"Position is {side}, not BUY - unexpected for SPOT")
        return

    # Create SELL signal
    print("\n[2/4] Creating manual SELL signal...")
    sell_signal = Signal(
        source="RBI_STRATEGY",
        symbol="ETHUSDT",
        timeframe="1h",
        action="SELL",
        confidence=75.0,
        ttl_sec=1800,
        timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        metadata={
            'strategy_name': 'TEST_MANUAL_SELL',
            'reasoning': 'TEST: Manual SELL signal to verify execution path',
            'verified': True,
            'verification_agreement': 'test'
        }
    )

    print(f" Created SELL signal:")
    print(f"   Symbol: {sell_signal.symbol}")
    print(f"   Action: {sell_signal.action}")
    print(f"   Confidence: {sell_signal.confidence}%")
    print(f"   Source: {sell_signal.source}")

    # Publish to bus
    print("\n[3/4] Publishing signal to bus...")
    signal_bus.publish(sell_signal)
    print(" Signal published")

    # Get signals from bus
    signals = signal_bus.get_signals('ETH', '1h')
    print(f"   Signals in bus: {len(signals)}")

    # Run arbitration
    print("\n[4/4] Running arbitration...")
    result = arbiter.arbitrate('ETH', '1h')

    print(f"\n ARBITRATION RESULT:")
    print(f"   Action: {result.action}")
    print(f"   Confidence: {result.confidence:.1f}%")
    print(f"   Reasoning: {result.reasoning}")
    print(f"   Size Multiplier: {result.size_multiplier:.2f}")

    # Check if SELL approved
    if result.action == 'SELL':
        print(f"\n SELL SIGNAL APPROVED")
        print(f"   Confidence {result.confidence:.1f}% >= 50% threshold")
        print(f"\n  EXECUTION WOULD HAPPEN IN LIVE MODE:")
        print(f"   1. Detect opposite signal (BUY position + SELL signal)")
        print(f"   2. Cancel all OCO orders")
        print(f"   3. Market SELL {position_size / entry_price:.6f} ETH")
        print(f"   4. Close trade in database (exit_reason: 'opposite_signal')")
        print(f"   5. Calculate PnL")
        print(f"\n NOT EXECUTING IN TEST MODE - Would close your real position!")
    elif result.action == 'WAIT':
        print(f"\n SELL SIGNAL REJECTED")
        print(f"   Reason: {result.reasoning}")
    else:
        print(f"\n  UNEXPECTED ACTION: {result.action}")

    print("\n" + "="*80)
    print(" TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    test_strategy_sell_signal()
