# 🌙 Simple Twitter Cookie Export (5 Minutes)

## Easiest Method: Using Browser Developer Tools

### Step 1: Open Twitter in Opera
1. Open Opera browser
2. Go to https://x.com
3. Make sure you're logged in

### Step 2: Open Developer Tools
1. Press `F12` on your keyboard
2. OR right-click anywhere and select "Inspect"

### Step 3: Go to Application Tab
1. Click the "Application" tab at the top of Developer Tools
2. In the left sidebar, expand "Storage" → "Cookies"
3. Click on "https://x.com"

### Step 4: Copy the Important Cookies
You'll see a list of cookies. Find and copy these TWO cookies:

**1. auth_token**
   - Click on the row that says `auth_token`
   - Double-click the "Value" column
   - Copy the value (it's a long string)
   - Save it somewhere

**2. ct0**
   - Click on the row that says `ct0`
   - Double-click the "Value" column
   - Copy the value
   - Save it somewhere

### Step 5: Create cookies.json File
1. Open Notepad or any text editor
2. Paste this template:
```json
{
  "auth_token": "PASTE_AUTH_TOKEN_VALUE_HERE",
  "ct0": "PASTE_CT0_VALUE_HERE"
}
```

3. Replace `PASTE_AUTH_TOKEN_VALUE_HERE` with the auth_token value you copied
4. Replace `PASTE_CT0_VALUE_HERE` with the ct0 value you copied
5. Save the file as `cookies.json` in: `C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\`

### Step 6: Test the Cookies
Run this command:
```bash
python src/scripts/test_twitter_cookies.py
```

If it works, you'll see:
```
✅ SUCCESS! Cookies are valid!
🎉 Logged in as: @your_username
```

---

## Alternative: Quick Copy All Cookies

If you want all cookies at once:

1. Open Developer Tools (F12)
2. Go to Console tab
3. Paste this JavaScript code and press Enter:
```javascript
copy(JSON.stringify(Object.fromEntries(document.cookie.split('; ').map(c => c.split('=')))))
```

4. This copies all cookies to your clipboard
5. Paste into a new file called `cookies.json`
6. Format it properly (add quotes around names and values)

---

## Troubleshooting

**Q: I can't find the Application tab**
- Try the "Storage" tab instead (same thing, different name)

**Q: The cookies.json file won't work**
- Make sure there are NO spaces before or after the values
- Make sure you have quotes around both the names and values
- Make sure the JSON format is correct (use a JSON validator online)

**Q: Where exactly do I save cookies.json?**
- Save it in: `C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\cookies.json`
- Same folder as the src/ folder

---

Once your cookies.json is working, you can use it with the twitter_login.py script!
