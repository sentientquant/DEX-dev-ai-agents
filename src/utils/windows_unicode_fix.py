"""
🌙 Moon Dev's Windows Unicode Fix Utility
Fixes UnicodeEncodeError on Windows by setting UTF-8 encoding for console output

PROBLEM: Windows console uses cp1252 encoding by default, which can't handle emojis and Unicode characters
SOLUTION: Force UTF-8 encoding for all print statements

Usage: Import at the top of any agent file
    from src.utils.windows_unicode_fix import fix_windows_unicode
    fix_windows_unicode()
"""

import sys
import codecs


def fix_windows_unicode():
    """
    Fix Windows console encoding to support UTF-8 (emojis, Unicode characters)

    This prevents UnicodeEncodeError when printing emojis or special characters
    on Windows systems that use cp1252 encoding by default.

    Call this at the start of any agent that uses emojis or Unicode.
    """
    if sys.platform == 'win32':
        # Fix stdout
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, codecs.StreamWriter):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

        # Fix stderr
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, codecs.StreamWriter):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')


# Auto-fix on import (optional - agents can call fix_windows_unicode() explicitly)
fix_windows_unicode()
