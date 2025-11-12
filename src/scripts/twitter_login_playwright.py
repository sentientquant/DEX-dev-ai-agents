"""
🌙 Moon Dev's Twitter Login with Playwright (Stealth Mode)

Playwright is better than Selenium at bypassing Cloudflare and bot detection.
Uses undetected browser fingerprints and realistic user behavior.

REQUIREMENTS:
pip install playwright playwright-stealth
playwright install chromium

USAGE:
python src/scripts/twitter_login_playwright.py
"""

import json
import sys
import os
import time
import asyncio
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint
from dotenv import load_dotenv

try:
    from playwright.async_api import async_playwright
except ImportError:
    cprint("❌ Error: playwright not installed", "red")
    cprint("📦 Install with:", "yellow")
    cprint("  pip install playwright", "yellow")
    cprint("  playwright install chromium", "yellow")
    sys.exit(1)

load_dotenv()


async def twitter_login_stealth():
    """Login to Twitter using Playwright with stealth mode"""

    cprint("🌙 Moon Dev's Stealth Twitter Login (Playwright)", "cyan")
    cprint("=" * 50, "cyan")

    username = os.getenv('TWITTER_USERNAME')
    password = os.getenv('TWITTER_PASSWORD')
    email = os.getenv('TWITTER_EMAIL')

    if not username or not password:
        cprint("❌ Missing TWITTER_USERNAME or TWITTER_PASSWORD in .env", "red")
        return False

    cprint("✅ Loaded credentials", "green")

    async with async_playwright() as p:
        # Launch browser with stealth settings
        cprint("🌐 Launching stealth browser...", "cyan")

        browser = await p.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--flag-switches-begin --disable-site-isolation-trials --flag-switches-end'
            ]
        )

        # Create context with realistic fingerprint
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'longitude': -74.0060, 'latitude': 40.7128},  # NYC
            color_scheme='dark',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        )

        # Add JavaScript to hide webdriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.navigator.chrome = {
                runtime: {}
            };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        page = await context.new_page()
        cprint("✅ Stealth browser launched", "green")

        try:
            # Navigate to Twitter with human-like delays
            cprint("🔗 Navigating to Twitter...", "cyan")
            await page.goto('https://x.com/i/flow/login', wait_until='domcontentloaded')

            # Random delay to simulate human behavior
            await asyncio.sleep(2 + (hash(username) % 3))

            cprint("✅ Page loaded", "green")

            # Enter username with human-like typing
            cprint("⌨️ Entering username...", "cyan")
            username_field = await page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            await username_field.click()
            await asyncio.sleep(0.5)

            # Type with realistic delays between keystrokes
            for char in username:
                await username_field.type(char, delay=50 + (hash(char) % 100))

            await asyncio.sleep(1)

            # Look for "Next" button and click it
            try:
                # Try different selectors for the Next button
                next_button_selectors = [
                    'button[role="button"]:has-text("Next")',
                    'div[role="button"]:has-text("Next")',
                    '[data-testid="LoginForm_Login_Button"]'
                ]

                next_clicked = False
                for selector in next_button_selectors:
                    try:
                        next_button = await page.wait_for_selector(selector, timeout=2000)
                        await next_button.click()
                        cprint("✅ Clicked Next button", "green")
                        next_clicked = True
                        break
                    except:
                        continue

                if not next_clicked:
                    # Fallback to pressing Enter
                    await page.keyboard.press('Enter')
                    cprint("✅ Pressed Enter (no Next button found)", "green")

            except Exception as e:
                cprint(f"⚠️ Button click error: {str(e)[:50]}", "yellow")
                await page.keyboard.press('Enter')

            await asyncio.sleep(4)  # Increased wait time for page transition
            cprint("✅ Username submitted", "green")

            # Take a screenshot to see what page we're on
            await page.screenshot(path='after_username.png')
            cprint("📸 Screenshot saved (after username): after_username.png", "cyan")
            cprint(f"📍 Current URL: {page.url}", "cyan")

            # Wait for page to load new content
            await asyncio.sleep(2)

            # Check for email verification
            try:
                cprint("🔍 Checking for email verification...", "cyan")
                email_field = await page.wait_for_selector('input[data-testid="ocfEnterTextTextInput"]', timeout=5000)

                if email:
                    cprint("⌨️ Entering email...", "cyan")
                    await email_field.click()
                    await asyncio.sleep(0.3)
                    for char in email:
                        await email_field.type(char, delay=50 + (hash(char) % 100))
                    await asyncio.sleep(0.5)
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(2)
                    cprint("✅ Email entered", "green")
                else:
                    cprint("⚠️ Email verification needed but TWITTER_EMAIL not in .env", "yellow")
                    cprint("💡 Waiting 30 seconds for manual entry...", "yellow")
                    await asyncio.sleep(30)
            except:
                cprint("✓ No email verification needed", "cyan")

            # Enter password with human-like typing
            cprint("⌨️ Entering password...", "cyan")

            # Try multiple selectors for password field
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[autocomplete="current-password"]'
            ]

            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await page.wait_for_selector(selector, timeout=5000)
                    cprint(f"✅ Found password field with selector: {selector}", "green")
                    break
                except:
                    continue

            if not password_field:
                cprint("❌ Could not find password field", "red")
                cprint("💡 The page might not have advanced. Taking screenshot...", "yellow")
                await page.screenshot(path='login_error.png')
                cprint("📸 Screenshot saved to login_error.png", "cyan")
                raise Exception("Password field not found")

            await password_field.click()
            await asyncio.sleep(0.4)

            for char in password:
                await password_field.type(char, delay=50 + (hash(char) % 100))

            await asyncio.sleep(0.5)

            # Try to find and click login button
            try:
                login_button_selectors = [
                    'button[data-testid="LoginForm_Login_Button"]',
                    'div[role="button"]:has-text("Log in")',
                    'button:has-text("Log in")'
                ]

                login_clicked = False
                for selector in login_button_selectors:
                    try:
                        login_button = await page.wait_for_selector(selector, timeout=2000)
                        await login_button.click()
                        cprint("✅ Clicked Log in button", "green")
                        login_clicked = True
                        break
                    except:
                        continue

                if not login_clicked:
                    await page.keyboard.press('Enter')
                    cprint("✅ Pressed Enter", "green")

            except:
                await page.keyboard.press('Enter')

            cprint("✅ Password submitted", "green")

            # Wait for login to complete
            cprint("⏳ Waiting for login...", "cyan")
            try:
                await page.wait_for_url('**/home', timeout=15000)
                cprint("✅ Login successful!", "green")
            except:
                cprint("⚠️ Checking if logged in...", "yellow")
                await asyncio.sleep(5)

            # Extract cookies
            cprint("\n🍪 Extracting cookies...", "cyan")
            cookies = await context.cookies()

            # Convert to twikit format
            twikit_cookies = {cookie['name']: cookie['value'] for cookie in cookies}

            cprint(f"✅ Extracted {len(twikit_cookies)} cookies", "green")

            # Check for essential cookies
            if 'auth_token' in twikit_cookies and 'ct0' in twikit_cookies:
                cprint("✅ Found auth_token and ct0", "green")
            else:
                cprint("⚠️ Missing essential cookies", "yellow")

            # Save cookies
            with open('cookies.json', 'w', encoding='utf-8') as f:
                json.dump(twikit_cookies, f, indent=2)

            cprint(f"✅ Cookies saved to cookies.json", "green")
            cprint("=" * 50, "cyan")
            cprint("🚀 Login complete!", "green")

            # Keep browser open briefly
            await asyncio.sleep(3)

            return True

        except Exception as e:
            cprint(f"\n❌ Error: {str(e)}", "red")
            import traceback
            cprint(f"🔍 Debug:\n{traceback.format_exc()}", "yellow")

            cprint("\n💡 Keeping browser open for inspection...", "yellow")
            await asyncio.sleep(30)

            return False

        finally:
            await browser.close()


if __name__ == "__main__":
    success = asyncio.run(twitter_login_stealth())
    sys.exit(0 if success else 1)
