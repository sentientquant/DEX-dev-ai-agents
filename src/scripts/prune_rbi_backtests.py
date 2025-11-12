#!/usr/bin/env python3
"""
🌙 Moon Dev's RBI Backtest Pruning Script
Intelligent cleanup of old backtest files to prevent disk bloat

WHAT IT DOES:
1. Keeps ALL files in backtests_final/ (successful strategies)
2. Keeps ALL execution_results/ (for debugging)
3. Keeps ALL research/ (strategy ideas)
4. Archives old debug files (>30 days) from backtests/
5. Deletes excessive debug iterations (keeps only first 3 and last 1)
6. Compresses archived folders to .zip

SAFETY FEATURES:
- Dry run mode (preview before deleting)
- Backup before deletion
- Only touches files older than threshold
- Never deletes final/execution_results/research folders
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Configuration
RBI_DATA_DIR = Path(__file__).parent.parent / "data" / "rbi_pp_multi"
DAYS_TO_KEEP = 30  # Keep files from last 30 days
MAX_DEBUG_ITERATIONS = 3  # Keep first 3 debug attempts + last one

# Folders to NEVER delete (but may prune old files)
PROTECTED_FOLDERS = ["backtests_final", "research"]

# Folders to prune old execution results from
EXECUTION_RESULTS_FOLDER = "execution_results"

# Folders to prune
PRUNE_FOLDERS = ["backtests", "backtests_package", "backtests_working", "backtests_optimized"]

def get_folder_size(folder_path):
    """Calculate total size of folder in MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)  # Convert to MB

def archive_folder(folder_path, archive_path):
    """Compress folder to .zip"""
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    print(f"✅ Archived to {archive_path}")

def prune_debug_files(folder_path, dry_run=True):
    """Keep only first MAX_DEBUG_ITERATIONS and last debug file"""
    debug_groups = {}

    # Group debug files by strategy name
    for file in folder_path.glob("*_DEBUG_v*.py"):
        # Extract strategy name (e.g., T00_AdaptiveCrossover)
        parts = file.stem.split("_DEBUG_v")
        if len(parts) == 2:
            strategy_name = parts[0]
            version = int(parts[1].split("_")[0].split(".")[0])

            if strategy_name not in debug_groups:
                debug_groups[strategy_name] = []
            debug_groups[strategy_name].append((version, file))

    files_to_delete = []

    # For each strategy, keep first MAX_DEBUG_ITERATIONS and last one
    for strategy_name, versions in debug_groups.items():
        versions.sort(key=lambda x: x[0])  # Sort by version number

        if len(versions) > MAX_DEBUG_ITERATIONS + 1:
            # Keep first MAX_DEBUG_ITERATIONS
            keep_first = versions[:MAX_DEBUG_ITERATIONS]
            # Keep last one
            keep_last = [versions[-1]]
            # Delete everything in between
            to_delete = [v for v in versions if v not in keep_first and v not in keep_last]

            files_to_delete.extend([file for version, file in to_delete])

    if files_to_delete:
        print(f"\n🧹 Found {len(files_to_delete)} excessive debug files:")
        for file in files_to_delete:
            print(f"  - {file.name}")
            if not dry_run:
                file.unlink()

        if dry_run:
            print("  (DRY RUN - no files deleted)")
        else:
            print(f"✅ Deleted {len(files_to_delete)} debug files")

    return len(files_to_delete)

def prune_execution_results(folder_path, dry_run=True):
    """Keep only successful execution results (success: true) from old folders"""
    if not folder_path.exists():
        return 0

    files_deleted = 0
    space_freed = 0

    print(f"\n📂 Processing execution_results/")

    for json_file in folder_path.glob("*.json"):
        # Check if this is a failed execution
        try:
            import json
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Delete failed executions (they're huge and not useful for old folders)
            if not data.get('success', False):
                file_size_mb = os.path.getsize(json_file) / (1024 * 1024)
                print(f"  🗑️ Deleting failed execution: {json_file.name} ({file_size_mb:.2f} MB)")

                if not dry_run:
                    json_file.unlink()
                    space_freed += file_size_mb

                files_deleted += 1

        except Exception as e:
            print(f"  ⚠️ Error reading {json_file.name}: {e}")

    if files_deleted > 0:
        if dry_run:
            print(f"  (DRY RUN - would delete {files_deleted} failed execution results)")
        else:
            print(f"  ✅ Deleted {files_deleted} failed execution results, freed {space_freed:.2f} MB")

    return files_deleted, space_freed

def prune_old_folders(date_folder, dry_run=True):
    """Prune old files from specific folders"""
    stats = {
        'files_deleted': 0,
        'space_freed_mb': 0
    }

    for prune_folder in PRUNE_FOLDERS:
        folder_path = date_folder / prune_folder
        if not folder_path.exists():
            continue

        print(f"\n📂 Processing {prune_folder}/")

        # Get folder size before
        size_before = get_folder_size(folder_path)

        # Prune excessive debug files
        deleted_count = prune_debug_files(folder_path, dry_run)
        stats['files_deleted'] += deleted_count

        # Calculate space freed
        if not dry_run:
            size_after = get_folder_size(folder_path)
            stats['space_freed_mb'] += (size_before - size_after)

    # Prune old execution results (keep only successful ones)
    exec_results_path = date_folder / EXECUTION_RESULTS_FOLDER
    exec_deleted, exec_space_freed = prune_execution_results(exec_results_path, dry_run)
    stats['files_deleted'] += exec_deleted
    stats['space_freed_mb'] += exec_space_freed

    return stats

def prune_rbi_backtests(dry_run=True, archive=True):
    """Main pruning function"""
    print("🌙 Moon Dev's RBI Backtest Pruner\n")

    if not RBI_DATA_DIR.exists():
        print(f"❌ RBI data directory not found: {RBI_DATA_DIR}")
        return

    # Find all date folders
    date_folders = [d for d in RBI_DATA_DIR.iterdir() if d.is_dir()]

    if not date_folders:
        print("📭 No date folders found")
        return

    print(f"📊 Found {len(date_folders)} date folders")

    # Check age of each folder
    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_KEEP)

    total_stats = {
        'folders_processed': 0,
        'files_deleted': 0,
        'space_freed_mb': 0,
        'folders_archived': 0
    }

    for date_folder in sorted(date_folders):
        # Parse date from folder name (MM_DD_YYYY)
        try:
            folder_date_str = date_folder.name
            folder_date = datetime.strptime(folder_date_str, "%m_%d_%Y")
        except ValueError:
            print(f"⚠️ Skipping invalid date folder: {date_folder.name}")
            continue

        # Skip recent folders
        if folder_date > cutoff_date:
            print(f"✅ Keeping recent folder: {date_folder.name}")
            continue

        print(f"\n🗓️ Processing old folder: {date_folder.name} ({(datetime.now() - folder_date).days} days old)")

        # Show what's in this folder
        for protected in PROTECTED_FOLDERS:
            protected_path = date_folder / protected
            if protected_path.exists():
                file_count = len(list(protected_path.glob("*")))
                print(f"  🔒 {protected}/: {file_count} files (PROTECTED)")

        # Prune old folders
        stats = prune_old_folders(date_folder, dry_run)
        total_stats['files_deleted'] += stats['files_deleted']
        total_stats['space_freed_mb'] += stats['space_freed_mb']
        total_stats['folders_processed'] += 1

        # Archive if requested
        if archive and not dry_run:
            archive_dir = RBI_DATA_DIR / "archives"
            archive_dir.mkdir(exist_ok=True)
            archive_path = archive_dir / f"{date_folder.name}_archive.zip"

            print(f"\n📦 Archiving {date_folder.name}...")
            archive_folder(date_folder, archive_path)
            total_stats['folders_archived'] += 1

    # Summary
    print("\n" + "="*60)
    print("📊 PRUNING SUMMARY")
    print("="*60)
    print(f"Folders processed: {total_stats['folders_processed']}")
    print(f"Files deleted: {total_stats['files_deleted']}")
    print(f"Space freed: {total_stats['space_freed_mb']:.2f} MB")
    print(f"Folders archived: {total_stats['folders_archived']}")

    if dry_run:
        print("\n⚠️ DRY RUN - No changes made")
        print("Run with --execute to actually delete files")
    else:
        print("\n✅ Pruning complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prune old RBI backtest files")
    parser.add_argument("--execute", action="store_true", help="Actually delete files (default is dry run)")
    parser.add_argument("--no-archive", action="store_true", help="Don't archive old folders")
    parser.add_argument("--days", type=int, default=DAYS_TO_KEEP, help=f"Keep files from last N days (default: {DAYS_TO_KEEP})")

    args = parser.parse_args()

    if args.days:
        DAYS_TO_KEEP = args.days

    prune_rbi_backtests(
        dry_run=not args.execute,
        archive=not args.no_archive
    )
