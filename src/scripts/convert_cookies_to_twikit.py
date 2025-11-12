"""
🌙 Moon Dev's Cookie Converter for Twikit

This script converts manually exported browser cookies to twikit format.

USAGE:
1. Export your Twitter cookies manually (see MANUAL_COOKIE_EXPORT_GUIDE.md)
2. Save them as twitter_cookies_raw.json
3. Run this script: python src/scripts/convert_cookies_to_twikit.py
4. It will create cookies.json in the correct format for twikit
"""

import json
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint


def convert_cookies():
    """Convert manually exported cookies to twikit format"""

    cprint("🌙 Moon Dev's Cookie Converter", "cyan")
    cprint("=" * 50, "cyan")

    input_file = "twitter_cookies_raw.json"
    output_file = "cookies.json"

    # Check if input file exists
    if not Path(input_file).exists():
        cprint(f"❌ Error: {input_file} not found", "red")
        cprint("\n📖 Please follow these steps:", "yellow")
        cprint("1. Open Opera and go to https://x.com (logged in)", "yellow")
        cprint("2. Press F12 to open Developer Tools", "yellow")
        cprint("3. Go to Application > Cookies > https://x.com", "yellow")
        cprint("4. Copy the cookies manually or use an extension", "yellow")
        cprint("5. Save them to twitter_cookies_raw.json", "yellow")
        cprint("\n📄 See MANUAL_COOKIE_EXPORT_GUIDE.md for detailed instructions", "cyan")
        return False

    try:
        # Load the raw cookies
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_cookies = json.load(f)

        cprint(f"✅ Loaded {input_file}", "green")

        # Convert to twikit format (simple dict of name: value)
        twikit_cookies = {}

        # Handle different export formats
        if isinstance(raw_cookies, list):
            # Format from most cookie extensions: [{name, value, ...}, ...]
            for cookie in raw_cookies:
                if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                    twikit_cookies[cookie['name']] = cookie['value']
        elif isinstance(raw_cookies, dict):
            # Already in dict format or nested dict
            for key, value in raw_cookies.items():
                if isinstance(value, dict) and 'value' in value:
                    # Format: {name: {value: x, ...}}
                    twikit_cookies[key] = value['value']
                else:
                    # Format: {name: value}
                    twikit_cookies[key] = str(value)

        if not twikit_cookies:
            cprint("❌ No valid cookies found in the file", "red")
            cprint("💡 Check the format of your exported cookies", "yellow")
            return False

        cprint(f"✅ Converted {len(twikit_cookies)} cookies", "green")

        # Check for essential cookies
        essential_cookies = ['auth_token', 'ct0']
        found_essential = [c for c in essential_cookies if c in twikit_cookies]
        missing_essential = [c for c in essential_cookies if c not in twikit_cookies]

        if found_essential:
            cprint(f"✅ Found essential cookies: {', '.join(found_essential)}", "green")

        if missing_essential:
            cprint(f"⚠️ Missing essential cookies: {', '.join(missing_essential)}", "yellow")
            cprint("💡 The login might not work without these cookies", "yellow")

        # Save in twikit format
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(twikit_cookies, f, indent=2)

        cprint(f"✅ Saved to {output_file}", "green")
        cprint("=" * 50, "cyan")
        cprint("🚀 You can now run: python src/scripts/twitter_login.py", "green")

        # Show cookie summary
        cprint(f"\n📋 Cookies saved: {', '.join(sorted(twikit_cookies.keys()))}", "cyan")

        return True

    except json.JSONDecodeError as e:
        cprint(f"❌ Invalid JSON format: {str(e)}", "red")
        cprint("💡 Make sure the file contains valid JSON", "yellow")
        return False
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        import traceback
        cprint(f"🔍 Debug info:\n{traceback.format_exc()}", "yellow")
        return False


if __name__ == "__main__":
    success = convert_cookies()
    sys.exit(0 if success else 1)
