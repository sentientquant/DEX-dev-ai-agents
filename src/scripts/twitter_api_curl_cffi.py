"""
🌙 Moon Dev's Twitter API with curl_cffi (Cloudflare Bypass)

curl_cffi uses real Chrome's TLS fingerprint to bypass Cloudflare protection.
Works where httpx and requests fail.

REQUIREMENTS:
pip install curl-cffi

USAGE:
python src/scripts/twitter_api_curl_cffi.py
"""

import json
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint

try:
    from curl_cffi import requests
except ImportError:
    cprint("❌ Error: curl-cffi not installed", "red")
    cprint("📦 Install with: pip install curl-cffi", "yellow")
    sys.exit(1)


def test_twitter_with_curl_cffi():
    """Test Twitter API access using curl_cffi to bypass Cloudflare"""

    cprint("🌙 Testing Twitter API with curl_cffi", "cyan")
    cprint("=" * 50, "cyan")

    # Load cookies
    try:
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        cprint(f"✅ Loaded {len(cookies)} cookies", "green")
    except FileNotFoundError:
        cprint("❌ cookies.json not found", "red")
        return False

    # Prepare headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'x-csrf-token': cookies.get('ct0', ''),
        'x-twitter-active-user': 'yes',
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-client-language': 'en',
        'Referer': 'https://x.com/home',
        'Origin': 'https://x.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    cprint("🔍 Testing API access with curl_cffi (Chrome impersonation)...", "cyan")

    try:
        # Test multiple endpoints to find which one works
        endpoints = [
            ('https://api.x.com/1.1/account/verify_credentials.json', 'REST API'),
            ('https://x.com/i/api/1.1/account/verify_credentials.json', 'Internal API'),
            ('https://twitter.com/i/api/1.1/account/verify_credentials.json', 'Twitter Domain'),
        ]

        for url, name in endpoints:
            cprint(f"🔍 Trying {name}...", "cyan")

            response = requests.get(
                url,
                headers=headers,
                cookies=cookies,
                impersonate='chrome120',  # Impersonate Chrome 120
                timeout=15
            )

            cprint(f"📊 {name} Response: {response.status_code}", "cyan")

            if response.status_code == 200:
                data = response.json()
                screen_name = data.get('screen_name', 'Unknown')
                cprint(f"\n✅ SUCCESS! Bypassed Cloudflare with {name}!", "green")
                cprint(f"🎉 Logged in as: @{screen_name}", "green")
                cprint(f"📝 Name: {data.get('name', 'N/A')}", "green")
                cprint(f"👥 Followers: {data.get('followers_count', 0):,}", "green")
                cprint(f"💬 Tweets: {data.get('statuses_count', 0):,}", "green")
                cprint("=" * 50, "cyan")
                cprint("🚀 curl_cffi successfully bypassed Cloudflare!", "green")
                return True

            elif response.status_code != 404:
                # If not 404, show response for debugging
                cprint(f"⚠️ Response preview: {response.text[:100]}", "yellow")

        # If we get here, all endpoints failed
        cprint("\n⚠️ All endpoints returned non-200 status", "yellow")
        return False

    except Exception as e:
        cprint(f"\n❌ Error: {str(e)}", "red")
        import traceback
        cprint(f"🔍 Debug:\n{traceback.format_exc()}", "yellow")
        return False


if __name__ == "__main__":
    success = test_twitter_with_curl_cffi()
    sys.exit(0 if success else 1)
