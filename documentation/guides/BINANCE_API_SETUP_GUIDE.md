# BINANCE API SETUP & TROUBLESHOOTING GUIDE

## Current Error: 401 - Invalid API-key, IP, or permissions

**Error Message**:
```
{"code":-2015,"msg":"Invalid API-key, IP, or permissions for action."}
```

This means one of three things is wrong:
1. ❌ API Key is incorrect
2. ❌ API Secret is incorrect
3. ❌ IP restrictions are blocking the request
4. ❌ API permissions are not enabled

---

## STEP-BY-STEP FIX

### Step 1: Verify API Keys in .env

**Check your `.env` file**:
```env
BINANCE_API_KEY=your_key_here_without_quotes
BINANCE_API_SECRET=your_secret_here_without_quotes
```

**Common Mistakes**:
- ❌ Extra spaces: `BINANCE_API_KEY= your_key` (space before key)
- ❌ Quotes: `BINANCE_API_KEY="your_key"` (remove quotes)
- ❌ Wrong key: Using API key instead of secret or vice versa
- ❌ Newlines: Key split across multiple lines

**Correct Format**:
```env
BINANCE_API_KEY=AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
BINANCE_API_SECRET=aBcDeFgHiJkLmNoPqRsTuVwXyZ0987654321
```

### Step 2: Verify API Key on Binance

1. **Log into Binance.com**
2. **Go to**: Account → API Management
3. **Check**:
   - API key is ACTIVE (not disabled)
   - API key is NOT expired
   - API key matches what's in `.env`

### Step 3: Check IP Restrictions

**Option A: Unrestricted Access (Easier, Less Secure)**:
1. Go to Binance → API Management → Your API Key
2. Under "API restrictions"
3. Select: **"Unrestricted (Not recommended)"**
4. Save changes
5. Wait 2-3 minutes for changes to propagate

**Option B: IP Whitelist (Recommended for Production)**:
1. Find your current IP address:
   ```bash
   curl ifconfig.me
   ```
2. Add your IP to whitelist on Binance API Management page
3. Format: `123.45.67.89` (your actual IP)
4. Wait 2-3 minutes for changes to propagate

### Step 4: Enable Required Permissions

**On Binance API Management page**:

Enable these permissions:
- ✅ **Enable Reading** (REQUIRED for balance checks)
- ❌ **Enable Spot & Margin Trading** (Only if you want LIVE trading)
- ❌ **Enable Withdrawals** (NEVER enable unless absolutely necessary)

**Minimum Required**:
- For BALANCE CHECK ONLY: Enable Reading
- For LIVE TRADING: Enable Reading + Enable Spot & Margin Trading

### Step 5: Create NEW API Key (If Above Fails)

If API key/secret is lost or corrupted, create a new one:

1. **Delete old API key** on Binance
2. **Create new API key**:
   - Go to API Management
   - Click "Create API"
   - Choose "System generated"
   - Enable 2FA verification
   - Save BOTH key AND secret immediately
3. **Update `.env`** with new credentials
4. **Configure permissions** (see Step 4)
5. **Configure IP restrictions** (see Step 3)

---

## TESTING & VERIFICATION

### Test 1: Verify .env is Loaded
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('BINANCE_API_KEY')[:10] + '...' if os.getenv('BINANCE_API_KEY') else 'MISSING'); print('API Secret:', os.getenv('BINANCE_API_SECRET')[:10] + '...' if os.getenv('BINANCE_API_SECRET') else 'MISSING')"
```

**Expected Output**:
```
API Key: AbCdEfGhIj...
API Secret: aBcDeFgHiJ...
```

### Test 2: Test Server Time (No Auth Required)
```bash
python -c "import requests; r = requests.get('https://api.binance.com/api/v3/time'); print(f'Server Time: {r.json()}')"
```

**Expected Output**:
```
Server Time: {'serverTime': 1731936000000}
```

### Test 3: Test Balance Fetch (Requires Auth)
```bash
python -c "from risk_management.binance_truth_paper_trading import BinanceTruthAPI; balance = BinanceTruthAPI.get_usdt_balance(); print(f'Balance: ${balance:.2f}' if balance else 'ERROR: Check API keys/permissions')"
```

**Expected Output**:
```
Balance: $1234.56
```

**If This Fails**: Check API permissions and IP restrictions

### Test 4: Test Public Market Data (No Auth)
```bash
python -c "from risk_management.binance_truth_paper_trading import BinanceTruthAPI; ticker = BinanceTruthAPI.token_overview('BTCUSDT'); print(f'BTC Price: ${ticker.get(\"last_price\", \"ERROR\")}')"
```

**Expected Output**:
```
BTC Price: $98123.45
```

---

## COMMON ERRORS & SOLUTIONS

### Error: -2015 "Invalid API-key, IP, or permissions"

**Causes**:
- Wrong API key or secret in `.env`
- IP not whitelisted
- API permissions not enabled

**Solution**:
1. Double-check `.env` file (no extra spaces, no quotes)
2. Enable "Unrestricted" access OR add your IP to whitelist
3. Enable "Reading" permission minimum
4. Wait 2-3 minutes after changes

### Error: -1021 "Timestamp ahead of server time"

**Cause**: System clock not synchronized

**Solution**: ✅ ALREADY FIXED
- We now fetch Binance server time
- No manual clock sync needed

### Error: -1022 "Signature for this request is not valid"

**Causes**:
- API secret is wrong
- API secret has extra spaces or newlines
- Encoding issue

**Solution**:
1. Copy API secret directly from Binance (no manual typing)
2. Paste into `.env` without quotes
3. No spaces before or after
4. Single line only

### Error: 401 Unauthorized

**Causes**:
- API key disabled or deleted on Binance
- API key expired
- Wrong API endpoint (using testnet key on mainnet)

**Solution**:
1. Verify API key is active on Binance.com
2. Create new API key if needed
3. Make sure using mainnet API (not testnet)

---

## SECURITY BEST PRACTICES

### ✅ DO:
- Enable IP whitelist in production
- Enable "Reading" permission only for balance checks
- Store API secret securely (password manager)
- Use different API keys for different purposes
- Regenerate API keys periodically
- Never commit `.env` to git

### ❌ DON'T:
- Enable withdrawals unless absolutely necessary
- Share API secret with anyone
- Store API secret in plaintext files online
- Use same API key across multiple servers
- Leave "Unrestricted" access in production

---

## ALTERNATIVE: PAPER TRADING (No API Secret Needed)

If you're having trouble with Binance API or don't want to enable it:

**PAPER mode works perfectly without BINANCE_API_SECRET**:
```bash
python trading_modes/SCANNER_SWARM_TRADE_FLOW.py --mode PAPER
```

**Benefits**:
- ✅ No API keys required
- ✅ Test strategies risk-free
- ✅ Track PnL in database
- ✅ All features except real balance fetching

**Only Difference from LIVE**:
- Balance tracked from starting amount + PnL (instead of real Binance balance)
- No real money at risk

---

## FINAL CHECKLIST

Before LIVE trading, verify:

1. ✅ API key is correct in `.env`
2. ✅ API secret is correct in `.env`
3. ✅ API key is ACTIVE on Binance
4. ✅ "Enable Reading" permission is ON
5. ✅ IP restrictions are configured (Unrestricted OR your IP whitelisted)
6. ✅ Waited 2-3 minutes after any changes
7. ✅ Balance test returns actual balance (not error)
8. ✅ NO "Enable Withdrawals" permission (security risk)

---

## CONTACT BINANCE SUPPORT

If none of the above works:

**Binance Support**:
- Live Chat: Binance.com → Support → Chat
- Ticket: https://www.binance.com/en/support

**Common Support Issues**:
- API key not working after following all steps
- IP restrictions not applying correctly
- API permissions showing but not working

---

## CURRENT STATUS

**API Keys**: ✅ Configured in `.env`
**Server Time Sync**: ✅ Fixed (using Binance server time)
**Current Error**: ❌ 401 - Invalid API-key, IP, or permissions

**Next Steps**:
1. Verify API key/secret in `.env` (no spaces, no quotes)
2. Check Binance API Management → Enable "Reading" permission
3. Check IP restrictions → Use "Unrestricted" for testing
4. Wait 2-3 minutes
5. Test again

**OR**: Use PAPER mode (no API setup needed)

---

**Guide Created**: 2025-11-18
**Issue**: API authentication failing
**Solution**: Follow steps above to fix API key/permissions
