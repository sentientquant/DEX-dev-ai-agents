"""
Convert both BTC strategies using the proper logic extraction converter
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import converter (it handles encoding internally)
from risk_management.backtest_to_live_converter import BacktestToLiveConverter

def main():
    print("="*80)
    print("CONVERTING BOTH BTC STRATEGIES WITH PROPER LOGIC EXTRACTION")
    print("="*80)

    # Initialize converter
    converter = BacktestToLiveConverter()

    # Strategy 1: BTC 5m VolatilityOutlier
    print("\n" + "="*80)
    print("STRATEGY 1: BTC 5m VolatilityOutlier")
    print("="*80)

    backtest_file_1 = Path("src/data/rbi_pp_multi/11_11_2025/backtests_optimized/T05_VolatilityOutlier_TARGET_HIT_1025.9243787708835pct_BTC-5min.py")
    output_file_1 = Path("trading_modes/02_STRATEGY_BASED_TRADING/strategies/custom/BTC_5m_VolatilityOutlier_1025pct.py")

    if backtest_file_1.exists():
        converted_code_1 = converter.convert_backtest_to_live(
            backtest_file=backtest_file_1,
            strategy_name="VolatilityOutlier",
            token="BTC",
            timeframe="5m",
            backtest_return=1025.92,
            sharpe_ratio=0.48,
            total_trades=14
        )

        if converted_code_1:
            converter.save_converted_strategy(converted_code_1, output_file_1)
            print(f"\n✅ SUCCESS: Saved to {output_file_1}")
        else:
            print(f"\n❌ FAILED: Could not convert strategy")
    else:
        print(f"\n❌ ERROR: Backtest file not found: {backtest_file_1}")

    # Strategy 2: BTC 4h VerticalBullish
    print("\n" + "="*80)
    print("STRATEGY 2: BTC 4h VerticalBullish")
    print("="*80)

    backtest_file_2 = Path("src/data/rbi_pp_multi/11_11_2025/backtests_optimized/T06_VerticalBullish_TARGET_HIT_977.7579966000036pct_BTC-4hour.py")
    output_file_2 = Path("trading_modes/02_STRATEGY_BASED_TRADING/strategies/custom/BTC_4h_VerticalBullish_977pct.py")

    if backtest_file_2.exists():
        converted_code_2 = converter.convert_backtest_to_live(
            backtest_file=backtest_file_2,
            strategy_name="VerticalBullish",
            token="BTC",
            timeframe="4h",
            backtest_return=977.76,
            sharpe_ratio=0.80,
            total_trades=111
        )

        if converted_code_2:
            converter.save_converted_strategy(converted_code_2, output_file_2)
            print(f"\n✅ SUCCESS: Saved to {output_file_2}")
        else:
            print(f"\n❌ FAILED: Could not convert strategy")
    else:
        print(f"\n❌ ERROR: Backtest file not found: {backtest_file_2}")

    print("\n" + "="*80)
    print("CONVERSION COMPLETE!")
    print("="*80)
    print("\nBoth strategies have been converted with PROPER logic extraction.")
    print("Next steps:")
    print("  1. Validate converted strategies")
    print("  2. Deploy if validation passes")
    print("  3. Run paper trading")

if __name__ == "__main__":
    main()
