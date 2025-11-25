"""
Quick test of signal fusion layer
Tests the fusion algorithm with volume agent signals
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.signal_fusion import SignalFusion
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

def main():
    cprint("\n" + "="*80, "cyan")
    cprint("🧪 SIGNAL FUSION LAYER TEST", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

    # Initialize fusion
    fusion = SignalFusion()

    # Test symbols
    symbols = ['BTC', 'ETH', 'SOL']

    cprint("[1/4] Collecting signals from all agents...", "yellow")
    print(f"       Looking for signals in: {fusion.collect_signals.__module__}\n")

    # Generate fused signals
    fused_results = fusion.fuse_all_symbols(symbols)

    cprint("[2/4] Calculating fusion scores...", "yellow")
    for symbol, result in fused_results.items():
        print(f"       {symbol}: Score={result['fusion_score']:+.1f}, "
              f"Action={result['action']}, "
              f"Confidence={result['confidence']:.1f}%")
    print()

    cprint("[3/4] Saving fused signals...", "yellow")
    fusion.save_fused_signals(fused_results)
    signals_file = PROJECT_ROOT / "src" / "data" / "signals" / "fused_signals.json"
    cprint(f"       Saved to: {signals_file}", "green")
    print()

    cprint("[4/4] Displaying fused intelligence...", "yellow")
    fusion.display_fused_signals(fused_results)

    cprint("\n✅ Test complete!\n", "green", attrs=['bold'])

    # Show signal breakdown
    cprint("📊 Signal Source Summary:", "cyan")
    for symbol, result in fused_results.items():
        print(f"\n{symbol}:")
        signals = result.get('signals', {})
        for agent, signal in signals.items():
            status = "✅" if not signal.get('missing') else "⚠️ "
            print(f"  {status} {agent:12} {signal.get('action', 'N/A'):8} "
                  f"Conf: {signal.get('confidence', 0):5.1f}% "
                  f"Age: {signal.get('age_minutes', 0):4.0f}min")

    print()

if __name__ == "__main__":
    main()
