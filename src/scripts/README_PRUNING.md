# 🌙 Moon Dev's RBI Backtest Pruning Guide

## Why Prune?

The RBI agent generates **thousands of backtest files** during parallel processing:
- 9 threads running simultaneously
- Each thread generates 10-50+ debug iterations
- Execution results can be 60MB+ each
- Over 1,327 files in a single day!

**Without pruning**, your disk will fill up fast.

## What Gets Pruned?

### ✅ KEPT (Never Deleted)
- `backtests_final/` - Successful strategies that hit target
- `research/` - Strategy ideas and research notes
- `execution_results/*.json` - Successful execution logs (success: true)

### 🗑️ DELETED (After 30 days)
- Excessive debug files (keeps first 3 + last 1)
- Failed backtest scripts
- Failed execution results (success: false)
- Old backtests_package/ files
- Old backtests_working/ files
- Old backtests_optimized/ files

### 📦 ARCHIVED (Optional)
- Entire date folders compressed to .zip in `archives/`

## Usage

### 1. Dry Run (Preview Only)
```bash
python src/scripts/prune_rbi_backtests.py
```

Shows what WOULD be deleted without actually deleting anything.

### 2. Execute Pruning
```bash
python src/scripts/prune_rbi_backtests.py --execute
```

Actually deletes old files and frees disk space.

### 3. Custom Days Threshold
```bash
python src/scripts/prune_rbi_backtests.py --execute --days 60
```

Keep files from last 60 days instead of 30.

### 4. Skip Archiving
```bash
python src/scripts/prune_rbi_backtests.py --execute --no-archive
```

Delete without creating .zip archives.

## Recommended Schedule

### Monthly Pruning (Automated)
Add to crontab or Windows Task Scheduler:

**Linux/Mac:**
```bash
# Run on 1st of every month at 3am
0 3 1 * * cd /path/to/DEX-dev-ai-agents && python src/scripts/prune_rbi_backtests.py --execute
```

**Windows Task Scheduler:**
- Program: `python.exe`
- Arguments: `src/scripts/prune_rbi_backtests.py --execute`
- Start in: `C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents`
- Trigger: Monthly, 1st day, 3:00 AM

### Manual Pruning
Before disk space becomes critical:
```bash
# Check disk usage
du -sh src/data/rbi_pp_multi/

# Dry run to preview
python src/scripts/prune_rbi_backtests.py

# Execute if satisfied
python src/scripts/prune_rbi_backtests.py --execute
```

## What You'll See

### Dry Run Output:
```
🌙 Moon Dev's RBI Backtest Pruner

📊 Found 5 date folders
✅ Keeping recent folder: 11_11_2025
✅ Keeping recent folder: 11_10_2025

🗓️ Processing old folder: 10_11_2025 (31 days old)
  🔒 backtests_final/: 3 files (PROTECTED)
  🔒 research/: 12 files (PROTECTED)

📂 Processing backtests/
🧹 Found 234 excessive debug files:
  - T00_AdaptiveCrossover_DEBUG_v4.py
  - T00_AdaptiveCrossover_DEBUG_v5.py
  ...
  (DRY RUN - no files deleted)

📂 Processing execution_results/
  🗑️ Deleting failed execution: T00_AdaptiveCrossover_130646.json (62.45 MB)
  (DRY RUN - would delete 156 failed execution results)

====================================================
📊 PRUNING SUMMARY
====================================================
Folders processed: 3
Files deleted: 390
Space freed: 2,145.67 MB
Folders archived: 0

⚠️ DRY RUN - No changes made
Run with --execute to actually delete files
```

### Execute Output:
```
✅ Deleted 234 debug files
✅ Deleted 156 failed execution results, freed 2145.67 MB
📦 Archiving 10_11_2025...
✅ Archived to archives/10_11_2025_archive.zip
✅ Pruning complete!
```

## Folder Structure After Pruning

```
rbi_pp_multi/
├── archives/
│   ├── 10_11_2025_archive.zip  # Old data archived
│   └── 09_11_2025_archive.zip
├── 11_11_2025/                 # Recent data kept
│   ├── backtests_final/        # ✅ All kept
│   ├── research/               # ✅ All kept
│   ├── execution_results/      # ✅ Successful kept, failed deleted
│   ├── backtests/              # 🗑️ Pruned (first 3 + last debug kept)
│   ├── backtests_package/      # 🗑️ Pruned
│   ├── backtests_working/      # 🗑️ Pruned
│   └── backtests_optimized/    # 🗑️ Pruned
└── 11_10_2025/                 # Recent data kept (all files)
```

## Safety Features

1. **Dry Run Default**: Never deletes without `--execute` flag
2. **Protected Folders**: `backtests_final/` and `research/` never touched
3. **Age Threshold**: Only touches folders older than `DAYS_TO_KEEP`
4. **Smart Debug Pruning**: Keeps first 3 attempts + last one (shows learning progression)
5. **Successful Results Kept**: Only deletes failed execution results
6. **Archive Option**: Creates .zip backups before deletion

## Troubleshooting

### "No date folders found"
- Check that RBI agent has run and created folders in `src/data/rbi_pp_multi/`

### "Permission denied"
- Run with admin/sudo privileges
- Close any programs accessing the files

### "Not enough space freed"
- Lower `--days` threshold (e.g., `--days 14`)
- Manually delete old archives after backing up

## Advanced Configuration

Edit `src/scripts/prune_rbi_backtests.py`:

```python
# Keep files from last N days
DAYS_TO_KEEP = 30

# Keep first N debug iterations + last one
MAX_DEBUG_ITERATIONS = 3

# Folders to prune
PRUNE_FOLDERS = ["backtests", "backtests_package", "backtests_working", "backtests_optimized"]
```

## Cost Analysis

**Before Pruning:**
- 1,327 files per day
- ~3-5 GB per day
- ~150 GB per month

**After Pruning:**
- ~50-100 files retained per day
- ~200-500 MB per day
- ~15 GB per month

**Savings: ~90% disk space reduction**
