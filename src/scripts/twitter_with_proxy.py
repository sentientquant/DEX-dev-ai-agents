"""
🌙 Moon Dev's Twitter Login with Proxy Support

Use residential proxies or rotating proxies to bypass IP-based blocks.
Supports SOCKS5 and HTTP proxies.

REQUIREMENTS:
pip install twikit

PROXY SERVICES (recommended):
- Bright Data (brightdata.com) - Residential proxies
- Smartproxy (smartproxy.com) - Rotating proxies
- Oxylabs (oxylabs.io) - Premium proxies

FREE PROXIES (less reliable):
- Free-Proxy-List.net
- ProxyScrape.com

USAGE:
1. Add to .env:
   PROXY_URL=socks5://username:password@proxy-server:port
   OR
   PROXY_URL=http://proxy-server:port

2. Run: python src/scripts/twitter_with_proxy.py
"""

import json
import sys
import os
import asyncio

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint
from dotenv import load_dotenv

try:
    from twikit import Client
    from twikit.errors import TwitterException
except ImportError:
    cprint("❌ Error: twikit not installed", "red")
    cprint("📦 Install with: pip install twikit", "yellow")
    sys.exit(1)

load_dotenv()


async def login_with_proxy():
    """Login to Twitter using a proxy to bypass IP blocks"""

    cprint("🌙 Moon Dev's Twitter Login with Proxy", "cyan")
    cprint("=" * 50, "cyan")

    username = os.getenv('TWITTER_USERNAME')
    password = os.getenv('TWITTER_PASSWORD')
    email = os.getenv('TWITTER_EMAIL')
    proxy_url = os.getenv('PROXY_URL')

    if not username or not password:
        cprint("❌ Missing TWITTER_USERNAME or TWITTER_PASSWORD in .env", "red")
        return False

    if not proxy_url:
        cprint("⚠️ No PROXY_URL in .env", "yellow")
        cprint("💡 Add: PROXY_URL=socks5://user:pass@server:port", "yellow")
        cprint("💡 Or use free proxies (less reliable)", "yellow")

        # Option to use free proxy
        use_free = input("\nTry with a free proxy? (y/n): ").lower()
        if use_free == 'y':
            proxy_url = await get_free_proxy()
            if not proxy_url:
                cprint("❌ Could not get free proxy", "red")
                return False
        else:
            return False

    cprint(f"✅ Using proxy: {proxy_url.split('@')[1] if '@' in proxy_url else proxy_url.split('//')[1]}", "green")

    try:
        # Initialize client with proxy
        cprint("🔌 Connecting through proxy...", "cyan")

        client = Client('en-US', proxy=proxy_url)

        cprint("✅ Proxy connected", "green")

        # Try to load existing cookies first
        if os.path.exists('cookies.json'):
            cprint("📂 Loading existing cookies...", "cyan")
            try:
                client.load_cookies('cookies.json')
                cprint("✅ Cookies loaded", "green")

                # Validate session
                user = await client.user()
                cprint(f"✅ Session valid! Logged in as: @{user.screen_name}", "green")
                cprint("=" * 50, "cyan")
                cprint("🚀 Proxy bypass successful!", "green")
                return True

            except Exception as e:
                cprint(f"⚠️ Cookies invalid: {str(e)[:50]}", "yellow")
                cprint("🔄 Attempting fresh login...", "cyan")

        # Fresh login with proxy
        cprint("🔑 Logging in with credentials...", "cyan")

        login_params = {
            'auth_info_1': username,
            'password': password
        }

        if email:
            login_params['auth_info_2'] = email

        await client.login(**login_params)

        cprint("✅ Login successful through proxy!", "green")

        # Save cookies
        client.save_cookies('cookies.json')
        cprint("✅ Cookies saved", "green")

        # Validate
        user = await client.user()
        cprint(f"🎉 Logged in as: @{user.screen_name}", "green")
        cprint("=" * 50, "cyan")
        cprint("🚀 Proxy bypass successful!", "green")

        return True

    except TwitterException as e:
        cprint(f"\n❌ Twitter error: {str(e)}", "red")

        if '403' in str(e):
            cprint("💡 Proxy might be blocked by Twitter", "yellow")
            cprint("💡 Try a different proxy or residential proxy service", "yellow")
        elif '401' in str(e):
            cprint("💡 Authentication failed - check credentials", "yellow")

        return False

    except Exception as e:
        cprint(f"\n❌ Error: {str(e)}", "red")
        import traceback
        cprint(f"🔍 Debug:\n{traceback.format_exc()}", "yellow")
        return False


async def get_free_proxy():
    """Get a free SOCKS5 proxy (unreliable, for testing only)"""

    cprint("\n🔍 Fetching free proxy list...", "cyan")

    try:
        import httpx

        # Fetch from free proxy list
        response = httpx.get('https://api.proxyscrape.com/v2/?request=get&protocol=socks5&timeout=10000&country=all')

        if response.status_code == 200:
            proxies = response.text.strip().split('\n')
            if proxies:
                proxy = proxies[0].strip()
                proxy_url = f'socks5://{proxy}'
                cprint(f"✅ Got free proxy: {proxy}", "green")
                return proxy_url

        cprint("❌ Could not fetch free proxy", "red")
        return None

    except Exception as e:
        cprint(f"❌ Error getting proxy: {str(e)}", "red")
        return None


if __name__ == "__main__":
    success = asyncio.run(login_with_proxy())
    sys.exit(0 if success else 1)
