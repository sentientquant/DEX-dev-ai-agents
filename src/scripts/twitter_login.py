"""
🌙 Moon Dev's Twitter Login Script
Updated with latest twikit library (https://github.com/d60/twikit)

SETUP INSTRUCTIONS:
1. First, create a .env file in your project root with:
   TWITTER_USERNAME=your_username
   TWITTER_EMAIL=your_email
   TWITTER_PASSWORD=your_password
   TWITTER_TOTP_SECRET=your_totp_secret  # Optional, for 2FA

2. Install required packages:
   pip install twikit
   pip install python-dotenv
   pip install termcolor

3. Run this script once to generate cookies.json
4. After successful login, you can use the cookies.json for other scripts

NOTE: If you get login errors, try:
- Logging into Twitter manually first
- Waiting a few minutes between attempts
- Checking if your account needs verification
- If using 2FA, ensure TWITTER_TOTP_SECRET is set

USAGE:
- First run: Performs login and saves cookies.json
- Subsequent runs: Loads cookies.json to skip login
- Validates session is still active
"""

from datetime import datetime
import time
import os
import asyncio
from pathlib import Path
import sys

# Fix Windows encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from twikit import Client
from twikit.errors import (
    TooManyRequests,
    BadRequest,
    Unauthorized,
    TwitterException,
    AccountLocked,
    AccountSuspended
)
from termcolor import cprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
COOKIES_FILE = "cookies.json"
LANGUAGE = 'en-US'

async def login_with_credentials(client):
    """Perform fresh login with credentials from .env"""
    USERNAME = os.getenv('TWITTER_USERNAME')
    EMAIL = os.getenv('TWITTER_EMAIL')
    PASSWORD = os.getenv('TWITTER_PASSWORD')
    TOTP_SECRET = os.getenv('TWITTER_TOTP_SECRET')  # Optional 2FA

    if not all([USERNAME, PASSWORD]):
        cprint("❌ Error: Missing TWITTER_USERNAME and TWITTER_PASSWORD in .env file!", "red")
        cprint("🔍 Please check the setup instructions at the top of this file.", "yellow")
        exit(1)

    cprint("🔑 Attempting fresh login with credentials...", "cyan")

    # Login with optional 2FA support
    login_params = {
        'auth_info_1': USERNAME,
        'password': PASSWORD,
    }

    # Add email if provided
    if EMAIL:
        login_params['auth_info_2'] = EMAIL

    # Add TOTP secret if provided (for 2FA)
    if TOTP_SECRET:
        login_params['totp_secret'] = TOTP_SECRET
        cprint("🔐 2FA detected, using TOTP secret...", "yellow")

    await client.login(**login_params)

    # Save cookies for future use
    client.save_cookies(COOKIES_FILE)
    cprint(f"✅ Login successful! Cookies saved to {COOKIES_FILE}", "green")


async def validate_session(client):
    """Validate that the current session is still active"""
    try:
        # Try to get user info to validate session
        user = await client.user()
        cprint(f"✅ Session validated! Logged in as: @{user.screen_name}", "green")
        return True
    except (Unauthorized, TwitterException):
        cprint("⚠️ Session expired or invalid", "yellow")
        return False


async def main():
    cprint("🌙 Moon Dev's Twitter Login Script", "cyan")
    cprint("=" * 50, "cyan")

    try:
        # Initialize client with language preference
        client = Client(LANGUAGE)

        cookies_path = Path(COOKIES_FILE)

        # Check if cookies file exists
        if cookies_path.exists():
            cprint(f"📂 Found existing {COOKIES_FILE}, attempting to load...", "cyan")

            try:
                # Load existing cookies
                client.load_cookies(COOKIES_FILE)
                cprint("✅ Cookies loaded successfully", "green")

                # Validate the session is still active
                if await validate_session(client):
                    cprint("🚀 You're all set! Session is active.", "green")
                    return
                else:
                    cprint("🔄 Session invalid, performing fresh login...", "yellow")
                    await login_with_credentials(client)

            except Exception as e:
                cprint(f"⚠️ Failed to load cookies: {str(e)}", "yellow")
                cprint("🔄 Performing fresh login...", "yellow")
                await login_with_credentials(client)
        else:
            # No cookies file, perform fresh login
            cprint("📝 No cookies file found, performing fresh login...", "cyan")
            await login_with_credentials(client)

        # Final validation
        await validate_session(client)
        cprint("=" * 50, "cyan")
        cprint("🚀 You can now use other scripts that require Twitter login!", "green")

    except AccountLocked as e:
        cprint(f"🔒 Account is locked: {str(e)}", "red")
        cprint("💡 Please unlock your account on Twitter and try again", "yellow")

    except AccountSuspended as e:
        cprint(f"⛔ Account is suspended: {str(e)}", "red")
        cprint("💡 Please resolve the suspension on Twitter", "yellow")

    except BadRequest as e:
        cprint(f"❌ Login request failed: {str(e)}", "red")
        cprint("🔍 This might be due to Twitter's automation detection.", "yellow")
        cprint("💡 Try these solutions:", "yellow")
        cprint("  1. Wait a few minutes and try again", "yellow")
        cprint("  2. Try logging in manually on Twitter first", "yellow")
        cprint("  3. Check if your account needs verification", "yellow")
        cprint("  4. Ensure credentials in .env are correct", "yellow")

    except TooManyRequests as e:
        cprint(f"⏱️ Rate limited: {str(e)}", "red")
        cprint("💡 Please wait before trying again", "yellow")

    except Unauthorized as e:
        cprint(f"🚫 Unauthorized: {str(e)}", "red")
        cprint("💡 Check your credentials in .env file", "yellow")

    except TwitterException as e:
        cprint(f"❌ Twitter API error: {str(e)}", "red")

    except Exception as e:
        cprint(f"❌ Unexpected error: {str(e)}", "red")
        import traceback
        cprint(f"🔍 Debug info:\n{traceback.format_exc()}", "yellow")


if __name__ == "__main__":
    asyncio.run(main())