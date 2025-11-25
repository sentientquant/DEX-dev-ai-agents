"""
Simple SELL Signal Test - No Signal Bus
Direct arbitration test
"""
from datetime import datetime, timezone
from trading_modes.core.arbiter import DeterministicArbiter
from trading_modes.core.signal_bus import Signal
from risk_management.trading_database_typed import TradingDatabase

# Suppress emoji printing
import sys
import io
class SuppressEmoji:
    def write(self, s):
        try:
            sys.__stdout__.write(s)
        except UnicodeEncodeError:
            sys.__stdout__.write(s.encode('ascii', 'ignore').decode())
    def flush(self):
        sys.__stdout__.flush()

sys.stdout = SuppressEmoji()

print("\n" + "="*80)
print("TEST: STRATEGY-BASED SELL SIGNAL")
print("="*80)

# Check ETH position
print("\n[1] Checking ETH position...")
db = TradingDatabase()
trades = db.get_open_trades()
eth_trade = next((t for t in trades if 'ETH' in (t.symbol if hasattr(t, 'symbol') else t.get('symbol', ''))), None)

if not eth_trade:
    print("No ETH position - SELL would be ignored")
    sys.exit(0)

trade_id = eth_trade.trade_id if hasattr(eth_trade, 'trade_id') else eth_trade.get('id')
side = eth_trade.side.value if hasattr(eth_trade, 'side') else eth_trade.get('side')
entry_price = eth_trade.entry_price if hasattr(eth_trade, 'entry_price') else eth_trade.get('entry_price')
position_size = eth_trade.position_size_usd if hasattr(eth_trade, 'position_size_usd') else eth_trade.get('position_size_usd')

print(f"Found: {side} position ${entry_price:.2f} (${position_size:.2f})")

# Create SELL signal manually
print("\n[2] Creating SELL signal...")
sell_signal = Signal(
    source="RBI_STRATEGY",
    symbol="ETHUSDT",
    timeframe="1h",
    action="SELL",
    confidence=75.0,
    ttl_sec=1800,
    timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    metadata={'strategy_name': 'TEST_MANUAL', 'reasoning': 'Manual test signal'}
)
print(f"SELL @ 75% confidence")

# Test arbitration
print("\n[3] Testing arbitration...")
arbiter = DeterministicArbiter()

# Manually add signal to arbiter's bus
arbiter.bus.publish(sell_signal)

# Get arbitration result (use same symbol format as signal)
result = arbiter.arbitrate('ETHUSDT', '1h')

print(f"\n[4] ARBITRATION RESULT:")
print(f"   Action: {result.action}")
print(f"   Confidence: {result.confidence:.1f}%")
print(f"   Reasoning: {result.reasoning}")

# Check if approved
if result.action == 'SELL':
    print(f"\nSELL APPROVED (>= 50% threshold)")
    print(f"\nWHAT WOULD HAPPEN IN LIVE MODE:")
    print(f"1. Detect opposite signal: BUY position + SELL signal")
    print(f"2. Cancel OCO orders")
    print(f"3. Market SELL: {position_size / entry_price:.6f} ETH")
    print(f"4. Close trade (exit_reason: 'opposite_signal')")
    print(f"5. Calculate PnL")
    print(f"\nNOT EXECUTING - This is a test only")
elif result.action == 'WAIT':
    print(f"\nSELL REJECTED: {result.reasoning}")
else:
    print(f"\nUNEXPECTED: {result.action}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
