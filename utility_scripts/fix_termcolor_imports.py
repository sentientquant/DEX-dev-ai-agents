#!/usr/bin/env python3
"""
Fix termcolor imports in all files - make them optional with fallback
"""

import os
import re

FILES_TO_FIX = [
    "trading_modes/RBI_RESEARCH_TRADE_FLOW.py",
    "trading_modes/core/signal_verification_agent.py",
    "trading_modes/SCANNER_SWARM_TRADE_FLOW.py",
    "trading_modes/binance_altcoin_scanner.py",
    "trading_modes/core/strategy_verification_agent.py",
    "trading_modes/core/strategy_verification_agent_legacy.py",
    "trading_modes/core/signal_verification_agent_old.py",
    "trading_modes/core/signal_verification_agent_legacy.py",
    "trading_modes/AI_SWARM_TRADE_FLOW.py",
    "trading_modes/core/market_analysis_agent.py",
    "trading_modes/live_chart_viewer.py"
]

TERMCOLOR_PATTERN = r'^from termcolor import (.+)$'
REPLACEMENT = '''# Make termcolor optional
try:
    from termcolor import \\1
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text'''

def fix_file(filepath):
    """Fix termcolor import in a single file"""
    if not os.path.exists(filepath):
        print(f"[SKIP] File not found: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already fixed
    if 'try:\n    from termcolor import' in content:
        print(f"[OK] Already fixed: {filepath}")
        return True

    # Replace the import
    new_content = re.sub(
        TERMCOLOR_PATTERN,
        REPLACEMENT,
        content,
        count=1,
        flags=re.MULTILINE
    )

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[FIXED] {filepath}")
        return True
    else:
        print(f"[SKIP] No termcolor import found: {filepath}")
        return False

if __name__ == "__main__":
    print("="*80)
    print(" FIXING TERMCOLOR IMPORTS")
    print("="*80)

    fixed_count = 0
    for filepath in FILES_TO_FIX:
        if fix_file(filepath):
            fixed_count += 1

    print("\n" + "="*80)
    print(f" COMPLETE: Fixed {fixed_count}/{len(FILES_TO_FIX)} files")
    print("="*80)
