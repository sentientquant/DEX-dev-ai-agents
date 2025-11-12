"""
🌙 Moon Dev's Direct Opera Cookie Extractor

This script directly extracts Twitter cookies from Opera's cookie database.
Works with Opera Air Stable browser.
"""

import json
import sys
import os
import sqlite3
import shutil
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
except ImportError:
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome.Protocol.KDF import PBKDF2
    except ImportError:
        cprint("❌ Error: pycryptodome not installed", "red")
        cprint("📦 Install it with: pip install pycryptodome", "yellow")
        sys.exit(1)


def extract_cookies_direct():
    """Extract cookies directly from Opera's database"""

    cprint("🌙 Moon Dev's Direct Opera Cookie Extractor", "cyan")
    cprint("=" * 50, "cyan")

    # Opera cookie database path
    opera_cookie_path = Path(os.path.expandvars(
        r"%APPDATA%\Opera Software\Opera Air Stable\Default\Network\Cookies"
    ))

    if not opera_cookie_path.exists():
        cprint(f"❌ Opera cookie database not found at:", "red")
        cprint(f"   {opera_cookie_path}", "yellow")
        cprint("\n💡 Make sure Opera Air Stable is installed", "yellow")
        return False

    cprint(f"✅ Found Opera cookie database", "green")

    # Create temporary copy (database might be locked)
    temp_cookie_path = Path("temp_opera_cookies.db")
    try:
        shutil.copy2(opera_cookie_path, temp_cookie_path)
        cprint("✅ Created temporary cookie database copy", "green")
    except Exception as e:
        cprint(f"❌ Failed to copy cookie database: {str(e)}", "red")
        cprint("💡 Make sure Opera is completely closed", "yellow")
        return False

    try:
        # Connect to the cookie database
        conn = sqlite3.connect(str(temp_cookie_path))
        cursor = conn.cursor()

        # Query Twitter/X cookies
        cursor.execute("""
            SELECT name, value, host_key
            FROM cookies
            WHERE host_key LIKE '%twitter.com%' OR host_key LIKE '%x.com%'
        """)

        cookies = cursor.fetchall()
        conn.close()

        if not cookies:
            cprint("❌ No Twitter cookies found in Opera", "red")
            cprint("💡 Make sure you're logged into Twitter/X on Opera", "yellow")
            return False

        cprint(f"✅ Found {len(cookies)} Twitter cookies", "green")

        # Convert to twikit format
        twikit_cookies = {}
        for name, value, host in cookies:
            # Note: Chromium-based browsers encrypt cookie values
            # The 'value' might be encrypted, but for session cookies it's often plain
            twikit_cookies[name] = value

        # Check for essential cookies
        essential_cookies = ['auth_token', 'ct0']
        found_essential = [c for c in essential_cookies if c in twikit_cookies]
        missing_essential = [c for c in essential_cookies if c not in twikit_cookies]

        if found_essential:
            cprint(f"✅ Found essential cookies: {', '.join(found_essential)}", "green")

        if missing_essential:
            cprint(f"⚠️ Missing essential cookies: {', '.join(missing_essential)}", "yellow")

        # Save cookies
        cookies_file = "cookies.json"
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(twikit_cookies, f, indent=2)

        cprint(f"✅ Cookies saved to {cookies_file}", "green")
        cprint("=" * 50, "cyan")
        cprint("🚀 You can now run: python src/scripts/twitter_login.py", "green")

        # Show cookie summary
        cprint(f"\n📋 Cookies extracted: {', '.join(sorted(twikit_cookies.keys()))}", "cyan")

        return True

    except Exception as e:
        cprint(f"❌ Error extracting cookies: {str(e)}", "red")
        import traceback
        cprint(f"🔍 Debug info:\n{traceback.format_exc()}", "yellow")
        return False

    finally:
        # Clean up temporary database
        if temp_cookie_path.exists():
            try:
                temp_cookie_path.unlink()
                cprint("✅ Cleaned up temporary files", "green")
            except:
                pass


if __name__ == "__main__":
    success = extract_cookies_direct()
    sys.exit(0 if success else 1)
