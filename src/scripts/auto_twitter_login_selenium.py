"""
🌙 Moon Dev's Automated Twitter Login with Selenium

This script uses Selenium to automatically login to Twitter and extract cookies.
It will open a browser window, login, and save the authenticated cookies.

REQUIREMENTS:
1. pip install selenium
2. Chrome browser installed
3. Twitter credentials in .env file

USAGE:
python src/scripts/auto_twitter_login_selenium.py

The script will:
1. Open Chrome browser
2. Navigate to Twitter
3. Enter your credentials automatically
4. Save cookies to cookies.json
5. Close the browser
"""

import json
import sys
import os
import time
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint
from dotenv import load_dotenv

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    cprint("❌ Error: selenium not installed", "red")
    cprint("📦 Install it with: pip install selenium", "yellow")
    sys.exit(1)

# Load environment variables
load_dotenv()


def auto_login_twitter():
    """Automatically login to Twitter using Selenium and extract cookies"""

    cprint("🌙 Moon Dev's Automated Twitter Login", "cyan")
    cprint("=" * 50, "cyan")

    # Get credentials from .env
    username = os.getenv('TWITTER_USERNAME')
    password = os.getenv('TWITTER_PASSWORD')
    email = os.getenv('TWITTER_EMAIL')

    if not username or not password:
        cprint("❌ Missing TWITTER_USERNAME or TWITTER_PASSWORD in .env", "red")
        return False

    cprint("✅ Loaded credentials from .env", "green")
    cprint(f"   Username: {username}", "cyan")

    # Setup Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Uncomment to run without opening browser
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = None

    try:
        cprint("\n🌐 Opening Chrome browser...", "cyan")
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()

        cprint("✅ Browser opened", "green")

        # Navigate to Twitter login
        cprint("🔗 Navigating to Twitter login page...", "cyan")
        driver.get("https://x.com/i/flow/login")

        # Wait for page to load
        time.sleep(3)

        cprint("✅ Login page loaded", "green")

        # Enter username
        cprint("⌨️ Entering username...", "cyan")
        try:
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_input.clear()
            username_input.send_keys(username)
            username_input.send_keys(Keys.RETURN)
            time.sleep(2)
            cprint("✅ Username entered", "green")
        except TimeoutException:
            cprint("❌ Could not find username input field", "red")
            return False

        # Check if email verification is needed
        try:
            cprint("🔍 Checking for email verification...", "cyan")
            email_input = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]'))
            )
            if email:
                cprint("⌨️ Entering email for verification...", "cyan")
                email_input.clear()
                email_input.send_keys(email)
                email_input.send_keys(Keys.RETURN)
                time.sleep(2)
                cprint("✅ Email entered", "green")
            else:
                cprint("⚠️ Email verification required but TWITTER_EMAIL not set in .env", "yellow")
                cprint("💡 Please enter your email manually in the browser", "yellow")
                input("Press Enter after entering email...")
        except TimeoutException:
            cprint("✓ No email verification needed", "cyan")

        # Enter password - try multiple selectors
        cprint("⌨️ Entering password...", "cyan")
        password_entered = False

        # Try different selectors for password field
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[autocomplete="current-password"]'
        ]

        for selector in password_selectors:
            try:
                password_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                password_input.clear()
                time.sleep(0.5)
                password_input.send_keys(password)
                password_input.send_keys(Keys.RETURN)
                time.sleep(3)
                cprint(f"✅ Password entered using selector: {selector}", "green")
                password_entered = True
                break
            except TimeoutException:
                continue

        if not password_entered:
            cprint("⚠️ Could not find password input field automatically", "yellow")
            cprint("💡 Please enter password manually in the browser", "yellow")
            input("Press Enter after entering password and logging in...")

        # Wait for login to complete
        cprint("⏳ Waiting for login to complete...", "cyan")
        try:
            WebDriverWait(driver, 15).until(
                EC.url_contains("home")
            )
            cprint("✅ Login successful!", "green")
        except TimeoutException:
            cprint("⚠️ Login might have failed or needs manual action", "yellow")
            cprint("💡 Check the browser window", "yellow")
            input("Press Enter after you're logged in...")

        # Extract cookies
        cprint("\n🍪 Extracting cookies...", "cyan")
        time.sleep(2)

        # Get all cookies
        selenium_cookies = driver.get_cookies()

        # Convert to twikit format
        twikit_cookies = {}
        for cookie in selenium_cookies:
            twikit_cookies[cookie['name']] = cookie['value']

        cprint(f"✅ Extracted {len(twikit_cookies)} cookies", "green")

        # Check for essential cookies
        essential_cookies = ['auth_token', 'ct0']
        found_essential = [c for c in essential_cookies if c in twikit_cookies]
        missing_essential = [c for c in essential_cookies if c not in twikit_cookies]

        if found_essential:
            cprint(f"✅ Found essential cookies: {', '.join(found_essential)}", "green")

        if missing_essential:
            cprint(f"⚠️ Missing essential cookies: {', '.join(missing_essential)}", "yellow")
            cprint("💡 Login might not have completed successfully", "yellow")

        # Save cookies
        cookies_file = "cookies.json"
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(twikit_cookies, f, indent=2)

        cprint(f"✅ Cookies saved to {cookies_file}", "green")
        cprint("=" * 50, "cyan")
        cprint("🚀 You can now run: python src/scripts/twitter_login.py", "green")

        # Show cookie summary
        cprint(f"\n📋 Cookies extracted: {', '.join(sorted(twikit_cookies.keys()))}", "cyan")

        # Keep browser open for a moment
        cprint("\n⏳ Keeping browser open for 5 seconds...", "cyan")
        time.sleep(5)

        return True

    except Exception as e:
        cprint(f"\n❌ Error: {str(e)}", "red")
        import traceback
        cprint(f"🔍 Debug info:\n{traceback.format_exc()}", "yellow")

        if driver:
            cprint("\n💡 Browser will stay open for manual inspection", "yellow")
            input("Press Enter to close browser...")

        return False

    finally:
        if driver:
            cprint("\n🔒 Closing browser...", "cyan")
            driver.quit()
            cprint("✅ Browser closed", "green")


if __name__ == "__main__":
    success = auto_login_twitter()
    sys.exit(0 if success else 1)
