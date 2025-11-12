"""
🌙 Moon Dev's Twitter Cookie Extractor for Opera Browser

This script extracts Twitter cookies from your Opera browser and saves them
in a format that twikit can use. This allows you to skip the login process
and use your existing authenticated session.

REQUIREMENTS:
1. Must be logged into Twitter/X on Opera browser
2. Opera browser must be CLOSED when running this script
3. Install required package: pip install browser-cookie3

USAGE:
1. Log into Twitter on Opera browser
2. Close Opera browser completely
3. Run this script: python src/scripts/extract_twitter_cookies_opera.py
4. The script will create cookies.json that twitter_login.py can use
"""

import json
import sys
import os
from pathlib import Path

# Fix Windows encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint

try:
    import browser_cookie3
except ImportError:
    cprint("❌ Error: browser-cookie3 not installed", "red")
    cprint("📦 Install it with: pip install browser-cookie3", "yellow")
    sys.exit(1)


def extract_opera_cookies():
    """Extract Twitter cookies from Opera browser"""

    cprint("🌙 Moon Dev's Twitter Cookie Extractor", "cyan")
    cprint("=" * 50, "cyan")

    try:
        cprint("🔍 Searching for Opera browser cookies...", "cyan")

        # Try different methods to get cookies
        twitter_cookies = []
        methods_tried = []

        # Method 1: Try Opera directly
        try:
            cprint("  → Trying Opera browser...", "cyan")
            cookies = browser_cookie3.opera(domain_name='x.com')
            twitter_cookies = list(cookies)
            methods_tried.append("Opera")
        except Exception as e1:
            cprint(f"  ✗ Opera method failed: {str(e1)[:50]}...", "yellow")

            # Method 2: Try Chromium (Opera is Chromium-based)
            try:
                cprint("  → Trying Chromium method (Opera is Chromium-based)...", "cyan")
                cookies = browser_cookie3.chromium(domain_name='x.com')
                twitter_cookies = list(cookies)
                methods_tried.append("Chromium")
            except Exception as e2:
                cprint(f"  ✗ Chromium method failed: {str(e2)[:50]}...", "yellow")

                # Method 3: Try Chrome (similar to Opera)
                try:
                    cprint("  → Trying Chrome method...", "cyan")
                    cookies = browser_cookie3.chrome(domain_name='x.com')
                    twitter_cookies = list(cookies)
                    methods_tried.append("Chrome")
                except Exception as e3:
                    cprint(f"  ✗ Chrome method failed: {str(e3)[:50]}...", "yellow")
                    twitter_cookies = []

        if not twitter_cookies:
            cprint("❌ No Twitter cookies found", "red")
            cprint(f"   Methods tried: {', '.join(methods_tried) if methods_tried else 'None'}", "yellow")
            cprint("\n💡 Troubleshooting:", "yellow")
            cprint("  1. Make sure you're logged into Twitter/X on Opera", "yellow")
            cprint("  2. Close Opera browser completely before running this script", "yellow")
            cprint("  3. Try running as administrator", "yellow")
            return False

        method_used = methods_tried[-1] if methods_tried else "Unknown"
        cprint(f"✅ Found {len(twitter_cookies)} Twitter cookies using {method_used} method", "green")

        # Convert to twikit format
        cookie_dict = {}
        for cookie in twitter_cookies:
            cookie_dict[cookie.name] = cookie.value

        # Check for essential cookies
        essential_cookies = ['auth_token', 'ct0']
        missing_cookies = [c for c in essential_cookies if c not in cookie_dict]

        if missing_cookies:
            cprint(f"⚠️ Warning: Missing essential cookies: {missing_cookies}", "yellow")
            cprint("💡 Make sure you're fully logged into Twitter on Opera", "yellow")

        # Save cookies to JSON file in twikit format
        cookies_file = "cookies.json"

        # Twikit expects a specific format
        twikit_cookies = {}
        for name, value in cookie_dict.items():
            twikit_cookies[name] = value

        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(twikit_cookies, f, indent=2)

        cprint(f"✅ Cookies saved to {cookies_file}", "green")
        cprint("=" * 50, "cyan")
        cprint("🚀 You can now run twitter_login.py to validate the session!", "green")

        # Display cookie names found
        cprint(f"\n📋 Cookies extracted: {', '.join(sorted(cookie_dict.keys()))}", "cyan")

        return True

    except Exception as e:
        cprint(f"❌ Error extracting cookies: {str(e)}", "red")
        cprint("\n💡 Troubleshooting tips:", "yellow")
        cprint("  1. Make sure Opera browser is completely closed", "yellow")
        cprint("  2. Ensure you're logged into Twitter/X on Opera", "yellow")
        cprint("  3. Try running this script as administrator", "yellow")
        cprint("  4. Check if Opera is using a custom profile location", "yellow")

        import traceback
        cprint(f"\n🔍 Debug info:\n{traceback.format_exc()}", "yellow")
        return False


if __name__ == "__main__":
    success = extract_opera_cookies()
    sys.exit(0 if success else 1)
