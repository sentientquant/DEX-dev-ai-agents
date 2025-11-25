"""
Test Symbol Matching Fixes
Verify that strategies are properly matched to symbols
"""
import sys
sys.path.insert(0, r'c:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents')

from trading_modes.RBI_RESEARCH_TRADE_FLOW import RBI_ResearchTradeFlow

print("="*80)
print("TESTING SYMBOL MATCHING FIXES")
print("="*80)

# Initialize flow
print("\n[1] Initializing RBI_ResearchTradeFlow...")
flow = RBI_ResearchTradeFlow(config={
    'mode': 'LIVE',  # Use LIVE mode to load deployed strategies
    'exchange': 'BINANCE',
    'check_interval_minutes': 15
})

# Manually load strategies (normally done by run() or analyze_rbi())
print("\n[2] Loading strategies from database...")
flow.load_rbi_strategies()

print(f"\nLoaded {len(flow.rbi_strategies)} strategies")

# Test symbol extraction
print("\n[3] Testing get_symbols_from_strategies()...")
symbols = flow.get_symbols_from_strategies()

if not symbols:
    print("ERROR: No symbols extracted from strategies!")
    sys.exit(1)

print(f"\nExtracted symbols: {symbols}")

# Verify normalization
from trading_modes.utils.symbol_utils import normalize_symbol

print("\n[4] Testing symbol normalization...")
test_cases = [
    ('BTC', 'BTCUSDT'),
    ('ETH', 'ETHUSDT'),
    ('SOL', 'SOLUSDT'),
    ('BTCUSDT', 'BTCUSDT'),
    ('eth-usdt', 'ETHUSDT'),
]

for input_sym, expected in test_cases:
    result = normalize_symbol(input_sym, 'USDT')
    status = "PASS" if result == expected else "FAIL"
    print(f"   {input_sym:12} -> {result:10} (expected: {expected:10}) [{status}]")

print("\n[5] Testing strategy target_pair values...")
for strat_info in flow.rbi_strategies:
    strategy = strat_info['instance']
    if hasattr(strategy, 'target_pair'):
        print(f"   {strat_info['name']:40} -> target_pair = '{strategy.target_pair}'")
    else:
        print(f"   {strat_info['name']:40} -> NO target_pair attribute!")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\nNow restart your live trading system and check for:")
print("1. '📊 Strategy targets: XXXUSDT' messages during startup")
print("2. '🔍 {name} analyzing {symbol}...' messages during signal generation")
print("3. NO 'No strategies matched' warnings")
