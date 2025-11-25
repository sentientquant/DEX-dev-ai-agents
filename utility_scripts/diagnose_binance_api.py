#!/usr/bin/env python3
"""
Binance API Diagnostic Tool
Identifies exact issue with Binance API authentication
"""

import sys
import os
from pathlib import Path
# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text
from dotenv import load_dotenv
import requests
import hmac
import hashlib
import time

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows Unicode encoding issues
from src.utils.windows_unicode_fix import fix_windows_unicode
fix_windows_unicode()

def test_env_loading():
    """Test 1: Verify .env file is loading"""
    cprint("\n" + "="*80, "cyan", attrs=['bold'])
    cprint("TEST 1: Environment Variable Loading", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")

    load_dotenv()

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    if api_key:
        cprint(f"  ✅ BINANCE_API_KEY: Found ({len(api_key)} chars)", "green")
        cprint(f"     Preview: {api_key[:10]}...{api_key[-10:]}", "white")

        # Check for common issues
        if ' ' in api_key:
            cprint("  ⚠️  WARNING: API key contains spaces!", "yellow")
        if '\n' in api_key:
            cprint("  ⚠️  WARNING: API key contains newlines!", "yellow")
        if api_key.startswith('"') or api_key.startswith("'"):
            cprint("  ⚠️  WARNING: API key starts with quotes!", "yellow")
    else:
        cprint("  ❌ BINANCE_API_KEY: NOT FOUND in .env", "red")
        return False

    if api_secret:
        cprint(f"  ✅ BINANCE_API_SECRET: Found ({len(api_secret)} chars)", "green")
        cprint(f"     Preview: {api_secret[:10]}...{api_secret[-10:]}", "white")

        # Check for common issues
        if ' ' in api_secret:
            cprint("  ⚠️  WARNING: API secret contains spaces!", "yellow")
        if '\n' in api_secret:
            cprint("  ⚠️  WARNING: API secret contains newlines!", "yellow")
        if api_secret.startswith('"') or api_secret.startswith("'"):
            cprint("  ⚠️  WARNING: API secret starts with quotes!", "yellow")
    else:
        cprint("  ❌ BINANCE_API_SECRET: NOT FOUND in .env", "red")
        return False

    return True

def test_server_connection():
    """Test 2: Test basic Binance server connection"""
    cprint("\n" + "="*80, "cyan", attrs=['bold'])
    cprint("TEST 2: Binance Server Connection (No Auth)", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")

    try:
        response = requests.get("https://api.binance.com/api/v3/time", timeout=10)

        if response.status_code == 200:
            server_time = response.json()['serverTime']
            cprint(f"  ✅ Binance server reachable", "green")
            cprint(f"     Server Time: {server_time}", "white")
            cprint(f"     Local Time: {int(time.time() * 1000)}", "white")

            time_diff = abs(int(time.time() * 1000) - server_time)
            if time_diff > 5000:
                cprint(f"  ⚠️  WARNING: Time difference is {time_diff}ms (should be <1000ms)", "yellow")
            else:
                cprint(f"  ✅ Time sync OK (difference: {time_diff}ms)", "green")

            return True
        else:
            cprint(f"  ❌ Server connection failed: {response.status_code}", "red")
            return False
    except Exception as e:
        cprint(f"  ❌ Server connection error: {e}", "red")
        return False

def test_public_api():
    """Test 3: Test public API endpoint"""
    cprint("\n" + "="*80, "cyan", attrs=['bold'])
    cprint("TEST 3: Public Market Data (No Auth)", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")

    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)

        if response.status_code == 200:
            data = response.json()
            price = float(data['price'])
            cprint(f"  ✅ Public API working", "green")
            cprint(f"     BTC Price: ${price:,.2f}", "white")
            return True
        else:
            cprint(f"  ❌ Public API failed: {response.status_code}", "red")
            cprint(f"     Response: {response.text[:100]}", "red")
            return False
    except Exception as e:
        cprint(f"  ❌ Public API error: {e}", "red")
        return False

def test_authenticated_api():
    """Test 4: Test authenticated API endpoint"""
    cprint("\n" + "="*80, "cyan", attrs=['bold'])
    cprint("TEST 4: Authenticated API - Account Balance", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")

    load_dotenv()

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    if not api_key or not api_secret:
        cprint("  ❌ API keys not configured", "red")
        return False

    try:
        # Get server time
        server_time_response = requests.get("https://api.binance.com/api/v3/time", timeout=5)
        if server_time_response.status_code == 200:
            timestamp = server_time_response.json()['serverTime']
        else:
            timestamp = int(time.time() * 1000)

        # Create signature
        query_string = f'timestamp={timestamp}'
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Make authenticated request
        headers = {'X-MBX-APIKEY': api_key}
        url = f"https://api.binance.com/api/v3/account?{query_string}&signature={signature}"

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            account_data = response.json()

            # Find USDT balance
            usdt_balance = 0.0
            for balance in account_data.get('balances', []):
                if balance['asset'] == 'USDT':
                    free = float(balance['free'])
                    locked = float(balance['locked'])
                    usdt_balance = free + locked
                    break

            cprint(f"  ✅ Authenticated API working!", "green")
            cprint(f"     USDT Balance: ${usdt_balance:,.2f}", "white")
            cprint(f"     Total Assets: {len(account_data.get('balances', []))}", "white")

            return True
        else:
            cprint(f"  ❌ Authentication failed: {response.status_code}", "red")
            cprint(f"     Response: {response.text[:200]}", "red")

            # Specific error messages
            try:
                error_data = response.json()
                error_code = error_data.get('code')
                error_msg = error_data.get('msg')

                cprint(f"\n  📋 Error Details:", "yellow")
                cprint(f"     Code: {error_code}", "white")
                cprint(f"     Message: {error_msg}", "white")

                if error_code == -2015:
                    cprint(f"\n  💡 SOLUTION:", "cyan", attrs=['bold'])
                    cprint(f"     1. Check API key/secret in .env (no spaces, no quotes)", "white")
                    cprint(f"     2. Go to Binance → API Management", "white")
                    cprint(f"     3. Enable 'Reading' permission", "white")
                    cprint(f"     4. Set IP restrictions to 'Unrestricted' (for testing)", "white")
                    cprint(f"     5. Wait 2-3 minutes for changes to apply", "white")
                elif error_code == -1021:
                    cprint(f"\n  💡 SOLUTION:", "cyan", attrs=['bold'])
                    cprint(f"     Timestamp sync issue - already handled in code", "white")
                elif error_code == -1022:
                    cprint(f"\n  💡 SOLUTION:", "cyan", attrs=['bold'])
                    cprint(f"     API secret is incorrect or has extra characters", "white")
                    cprint(f"     Copy secret directly from Binance (no manual typing)", "white")
            except:
                pass

            return False
    except Exception as e:
        cprint(f"  ❌ Authentication error: {e}", "red")
        import traceback
        cprint(f"     {traceback.format_exc()[:200]}", "red")
        return False

def main():
    """Run all diagnostic tests"""
    cprint("\n" + "="*80, "magenta", attrs=['bold'])
    cprint("🔧 BINANCE API DIAGNOSTIC TOOL", "magenta", attrs=['bold'])
    cprint("="*80 + "\n", "magenta")

    results = {
        'env_loading': False,
        'server_connection': False,
        'public_api': False,
        'authenticated_api': False
    }

    # Run tests
    results['env_loading'] = test_env_loading()

    if results['env_loading']:
        results['server_connection'] = test_server_connection()
        results['public_api'] = test_public_api()
        results['authenticated_api'] = test_authenticated_api()

    # Summary
    cprint("\n" + "="*80, "magenta", attrs=['bold'])
    cprint("📊 DIAGNOSTIC SUMMARY", "magenta", attrs=['bold'])
    cprint("="*80, "magenta")

    status_icon = lambda x: "✅" if x else "❌"
    status_color = lambda x: "green" if x else "red"

    cprint(f"  {status_icon(results['env_loading'])} Environment Loading", status_color(results['env_loading']))
    cprint(f"  {status_icon(results['server_connection'])} Server Connection", status_color(results['server_connection']))
    cprint(f"  {status_icon(results['public_api'])} Public API Access", status_color(results['public_api']))
    cprint(f"  {status_icon(results['authenticated_api'])} Authenticated API Access", status_color(results['authenticated_api']))

    # Overall status
    cprint("\n" + "="*80, "cyan")
    if all(results.values()):
        cprint("🎉 ALL TESTS PASSED - LIVE MODE READY!", "green", attrs=['bold'])
    elif results['env_loading'] and results['server_connection'] and results['public_api']:
        cprint("⚠️  API AUTHENTICATION FAILED - Check API permissions on Binance", "yellow", attrs=['bold'])
        cprint("\n  Next Steps:", "cyan")
        cprint("  1. Go to Binance.com → Account → API Management", "white")
        cprint("  2. Verify API key is ACTIVE", "white")
        cprint("  3. Enable 'Reading' permission", "white")
        cprint("  4. Set IP to 'Unrestricted' (for testing)", "white")
        cprint("  5. Wait 2-3 minutes", "white")
        cprint("  6. Run this script again", "white")
    else:
        cprint("❌ BASIC SETUP FAILED - Check .env file and internet connection", "red", attrs=['bold'])

    cprint("="*80 + "\n", "cyan")

    # Documentation reference
    cprint("📖 For detailed setup instructions, see:", "cyan")
    cprint("   BINANCE_API_SETUP_GUIDE.md\n", "white")

if __name__ == "__main__":
    main()
