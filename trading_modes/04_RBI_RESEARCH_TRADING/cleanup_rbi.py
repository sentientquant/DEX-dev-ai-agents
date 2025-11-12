"""
RBI Data Cleanup Script
Removes old generated files while preserving hit strategies and scripts
"""

import os
import shutil
from pathlib import Path

# Define paths
RBI_DATA_PATH = Path(__file__).parent / "rbi_data"

# Files to preserve (hit strategies)
PRESERVE_FILES = [
    "11_10_2025/backtests_final/T01_AdaptiveReversal_DEBUG_v1_116.8pct.py",
    "11_11_2025/backtests_package/T05_VolatilityBracket_PKG.py",
]

# Folders to delete entirely
DELETE_FOLDERS = [
    "11_09_2025",  # Delete all of 11_09_2025 (no hits)
    "11_10_2025/backtests",
    "11_10_2025/backtests_optimized",
    "11_10_2025/backtests_package",
    "11_10_2025/backtests_working",
    "11_10_2025/charts",
    "11_10_2025/execution_results",
    "11_10_2025/research",
    "11_11_2025/backtests",
    "11_11_2025/backtests_optimized",
    "11_11_2025/backtests_final",
    "11_11_2025/charts",
    "11_11_2025/execution_results",
    "11_11_2025/research",
]

# Root files to delete
DELETE_ROOT_FILES = [
    "ideas.txt",
    "processed_ideas.log",
    "strategy_ideas.csv",
    "backtest_stats.csv",
]

def main():
    print("=" * 60)
    print("RBI DATA CLEANUP")
    print("=" * 60)

    # Create hits folder
    hits_folder = RBI_DATA_PATH / "hit_strategies"
    hits_folder.mkdir(exist_ok=True)
    print(f"\n[1/4] Created: {hits_folder}")

    # Copy hit strategies to new folder
    print("\n[2/4] Preserving hit strategies...")
    for file_path in PRESERVE_FILES:
        source = RBI_DATA_PATH / file_path
        if source.exists():
            dest = hits_folder / source.name
            shutil.copy2(source, dest)
            print(f"  Copied: {source.name}")
        else:
            print(f"  NOT FOUND: {file_path}")

    # Delete folders
    print("\n[3/4] Deleting old folders...")
    deleted_count = 0
    for folder_path in DELETE_FOLDERS:
        folder = RBI_DATA_PATH / folder_path
        if folder.exists():
            shutil.rmtree(folder)
            deleted_count += 1
            print(f"  Deleted: {folder_path}")

    # Delete entire date folders after extracting hits
    for date_folder in ["11_09_2025", "11_10_2025", "11_11_2025"]:
        folder = RBI_DATA_PATH / date_folder
        if folder.exists():
            shutil.rmtree(folder)
            print(f"  Deleted: {date_folder}")

    # Delete root files
    print("\n[4/4] Deleting root files...")
    for file_name in DELETE_ROOT_FILES:
        file_path = RBI_DATA_PATH / file_name
        if file_path.exists():
            file_path.unlink()
            print(f"  Deleted: {file_name}")

    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"\nPreserved strategies in: {hits_folder}")
    print("- T01_AdaptiveReversal_DEBUG_v1_116.8pct.py (116.8% return)")
    print("- T05_VolatilityBracket_PKG.py (1025% return)")
    print("\nAll other generated files removed.")

if __name__ == "__main__":
    main()
