# Manual Twitter Cookie Export Guide

Since automatic extraction isn't finding Opera's cookies, here's how to manually export your Twitter cookies.

## Method 1: Using EditThisCookie Extension (Recommended)

### Step 1: Install Extension
1. Open Opera browser
2. Go to: https://addons.opera.com/en/extensions/details/editthiscookie/
3. Click "Add to Opera"

### Step 2: Export Cookies
1. Go to https://x.com (make sure you're logged in)
2. Click the EditThisCookie extension icon in your toolbar
3. Click the "Export" button (looks like a folder with arrow)
4. This copies cookies to your clipboard in JSON format

### Step 3: Save Cookies
1. Create a file named `twitter_cookies_raw.json` in this folder
2. Paste the copied content into the file
3. Run: `python src/scripts/convert_cookies_to_twikit.py`

## Method 2: Using Browser Developer Tools

### Step 1: Open Developer Tools
1. Open Opera browser
2. Go to https://x.com (make sure you're logged in)
3. Press `F12` or `Ctrl+Shift+I` to open Developer Tools
4. Go to the "Application" tab (or "Storage" tab)

### Step 2: Export Cookies
1. In the left sidebar, expand "Cookies"
2. Click on "https://x.com"
3. You'll see all cookies for Twitter/X

### Step 3: Key Cookies to Copy
Look for these essential cookies and copy their values:
- `auth_token` - Most important
- `ct0` - CSRF token
- `twid` - Twitter ID

### Step 4: Manual JSON Creation
Create a file `cookies.json` with this format:
```json
{
  "auth_token": "paste_value_here",
  "ct0": "paste_value_here",
  "twid": "paste_value_here"
}
```

## Method 3: Using Cookie-Editor Extension

### Step 1: Install Extension
1. Open Opera
2. Go to Chrome Web Store (Opera supports Chrome extensions)
3. Search for "Cookie-Editor" by cgagnier
4. Install the extension

### Step 2: Export Cookies
1. Go to https://x.com (logged in)
2. Click Cookie-Editor extension icon
3. Click "Export" button
4. Choose "JSON" format
5. Copy the exported cookies

### Step 3: Save and Convert
1. Save to `twitter_cookies_raw.json`
2. Run the conversion script (see below)

## After Exporting Cookies

Once you have the cookies in `cookies.json` format, run:
```bash
python src/scripts/twitter_login.py
```

The script will automatically detect and validate your session!

## Troubleshooting

**Q: I can't find the cookies**
- Make sure you're logged into Twitter/X in Opera
- Cookies are domain-specific, make sure you're on x.com

**Q: The session doesn't work**
- Cookies might have expired
- Try logging out and back in on Opera, then export again
- Make sure you got the `auth_token` cookie

**Q: Which cookies are essential?**
Minimum required:
- `auth_token` - Authentication token
- `ct0` - CSRF token

Nice to have:
- `twid` - Twitter user ID
- `guest_id` - Guest identifier
- `personalization_id` - Personalization identifier
