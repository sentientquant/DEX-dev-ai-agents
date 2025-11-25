#!/usr/bin/env python3
"""
Fix confidence field in database - convert string 'HIGH' to numeric values
"""

import sqlite3
from pathlib import Path
from termcolor import cprint

def fix_confidence_values():
    """Fix confidence values in trades table"""
    db_path = Path(__file__).parent / "trading_system.db"

    cprint("\n" + "="*80, "cyan")
    cprint("FIXING CONFIDENCE VALUES IN DATABASE", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current problematic trades
    cursor.execute("""
        SELECT trade_id, symbol, confidence, status
        FROM trades
        WHERE typeof(confidence) = 'text' OR confidence LIKE '%HIGH%' OR confidence LIKE '%MEDIUM%' OR confidence LIKE '%LOW%'
    """)

    problematic = cursor.fetchall()

    if problematic:
        cprint(f"Found {len(problematic)} trades with string confidence values:", "yellow")
        for trade in problematic:
            cprint(f"   {trade[0]}: {trade[1]} - confidence='{trade[2]}' (status: {trade[3]})", "white")

        # Fix them
        cprint("\nFixing confidence values...", "cyan")

        # Map string to numeric
        confidence_map = {
            'HIGH': 75,
            'MEDIUM': 60,
            'LOW': 45
        }

        for trade in problematic:
            trade_id = trade[0]
            old_conf = trade[2]

            # Try to extract numeric value if it's like "56.0" or just use mapping
            try:
                new_conf = float(old_conf)
                if new_conf > 100:
                    new_conf = 75  # Default to HIGH
            except (ValueError, TypeError):
                # String value like 'HIGH', 'MEDIUM', 'LOW'
                new_conf = confidence_map.get(old_conf, 60)  # Default to MEDIUM

            cursor.execute("UPDATE trades SET confidence = ? WHERE trade_id = ?", (new_conf, trade_id))
            cprint(f"   Updated {trade_id}: '{old_conf}' -> {new_conf}", "green")

        conn.commit()
        cprint(f"\n✅ Fixed {len(problematic)} trades", "green", attrs=['bold'])
    else:
        cprint("✅ No problematic confidence values found", "green", attrs=['bold'])

    # Verify all open trades
    cursor.execute("SELECT trade_id, symbol, confidence, status FROM trades WHERE status = 'OPEN'")
    open_trades = cursor.fetchall()

    if open_trades:
        cprint(f"\n📌 Open Trades ({len(open_trades)}):", "cyan", attrs=['bold'])
        for trade in open_trades:
            cprint(f"   {trade[0]}: {trade[1]} - confidence={trade[2]} (status: {trade[3]})", "white")
    else:
        cprint("\n📌 No open trades", "cyan", attrs=['bold'])

    conn.close()

    cprint("\n" + "="*80, "cyan")
    cprint("DATABASE FIX COMPLETE", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

if __name__ == "__main__":
    fix_confidence_values()
