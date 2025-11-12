"""
🌙 Test Twitter Cookies

Simple script to test if extracted Twitter cookies are valid.
Tests by making a direct API request to Twitter with the cookies.
"""

import json
import sys
import httpx

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint


def test_cookies():
    """Test if cookies are valid by making a simple Twitter API request"""

    cprint("🌙 Testing Twitter Cookies", "cyan")
    cprint("=" * 50, "cyan")

    # Load cookies
    try:
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        cprint(f"✅ Loaded {len(cookies)} cookies from cookies.json", "green")
    except FileNotFoundError:
        cprint("❌ cookies.json not found", "red")
        cprint("💡 Run extract_opera_cookies_direct.py first", "yellow")
        return False
    except json.JSONDecodeError:
        cprint("❌ Invalid JSON in cookies.json", "red")
        return False

    # Check for essential cookies
    if 'auth_token' not in cookies:
        cprint("❌ Missing auth_token cookie", "red")
        cprint("💡 You need to be logged into Twitter", "yellow")
        return False

    if 'ct0' not in cookies:
        cprint("⚠️ Missing ct0 cookie (CSRF token)", "yellow")

    cprint("✅ Found essential cookies", "green")

    # Test with a simple API request
    cprint("\n🔍 Testing cookies with Twitter API...", "cyan")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'x-csrf-token': cookies.get('ct0', ''),
    }

    cookie_string = '; '.join([f'{k}={v}' for k, v in cookies.items()])
    headers['Cookie'] = cookie_string

    try:
        # Test with a simple settings endpoint
        response = httpx.get(
            'https://api.x.com/1.1/account/settings.json',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            screen_name = data.get('screen_name', 'Unknown')
            cprint(f"\n✅ SUCCESS! Cookies are valid!", "green")
            cprint(f"🎉 Logged in as: @{screen_name}", "green")
            cprint("=" * 50, "cyan")
            cprint("🚀 Your Twitter session is working!", "green")
            return True
        elif response.status_code == 403:
            cprint("\n❌ Cookies rejected (403 Forbidden)", "red")
            cprint("💡 Cookies might be expired or invalid", "yellow")
            cprint("💡 Try extracting cookies again after logging into Twitter", "yellow")
            return False
        elif response.status_code == 401:
            cprint("\n❌ Unauthorized (401)", "red")
            cprint("💡 auth_token is invalid or expired", "yellow")
            cprint("💡 Log into Twitter on Opera and extract cookies again", "yellow")
            return False
        else:
            cprint(f"\n⚠️ Unexpected response: {response.status_code}", "yellow")
            cprint(f"Response: {response.text[:200]}", "yellow")
            return False

    except httpx.RequestError as e:
        cprint(f"\n❌ Network error: {str(e)}", "red")
        return False
    except Exception as e:
        cprint(f"\n❌ Error: {str(e)}", "red")
        import traceback
        cprint(f"🔍 Debug:\n{traceback.format_exc()}", "yellow")
        return False


if __name__ == "__main__":
    success = test_cookies()
    sys.exit(0 if success else 1)
