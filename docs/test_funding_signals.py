"""Quick test of funding agent signal export"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.funding_agent import FundingAgent

print("\n[TEST] Testing Funding Agent Signal Export\n")
print("=" * 60)

# Create agent
agent = FundingAgent()

# Run one cycle (fetches data and exports signals)
print("\n[TEST] Running monitoring cycle...")
agent.run_monitoring_cycle()

# Check if signals were exported
signals_file = Path("src/data/signals/funding_signals.json")
if signals_file.exists():
    print(f"\n[OK] Signals exported to: {signals_file}")

    # Read and display signals
    import json
    with open(signals_file, 'r') as f:
        signals = json.load(f)

    print(f"\n[RESULTS] Exported {len(signals)} funding signals:")
    print("=" * 60)

    for symbol, data in signals.items():
        print(f"\n{symbol}:")
        print(f"  Action: {data['action']}")
        print(f"  Confidence: {data['confidence']}%")
        print(f"  Reasoning: {data['reasoning']}")
        print(f"  Positioning: {data['data']['positioning']}")
        print(f"  Annual Rate: {data['data']['annual_rate']}%")
        print(f"  Squeeze Risk: {data['data']['squeeze_risk']}")
else:
    print(f"\n[ERROR] Signals file not found at: {signals_file}")

print("\n" + "=" * 60)
print("[TEST] Complete!")
