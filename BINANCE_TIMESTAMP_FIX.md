# BINANCE TIMESTAMP & RECV_WINDOW FIX

**Date:** 2025-11-25
**Status:** FIXED ✅
**Error:** `Session.request() got an unexpected keyword argument 'recv_window'`

---

## PROBLEM

The Binance Python client was incorrectly configured, causing two critical errors:

1. **recv_window Parameter Error**: `Session.request() got an unexpected keyword argument 'recv_window'`
2. **Timestamp Sync Error**: `APIError(code=-1021): Timestamp for this request was 1000ms ahead of the server's time`

### Root Cause

The code was passing `recv_window` in the constructor's `requests_params` dictionary:

```python
# WRONG - This causes the error!
self.binance_client = BinanceClient(
    api_key,
    api_secret,
    {'timeout': 20, 'recv_window': 5000}  # ❌ recv_window doesn't belong here!
)
```

The `requests_params` dictionary is passed directly to Python's `requests.Session().request()` method, which doesn't understand Binance-specific parameters like `recv_window`.

---

## SOLUTION

### Understanding recvWindow

- **What it is**: Time window (in milliseconds) during which a request is valid after being sent
- **Default**: 5000ms (5 seconds)
- **Maximum**: 60000ms (60 seconds)
- **Purpose**: Prevents replay attacks and handles network delays

### Correct Implementation

`recv_window` must be passed as a parameter to **individual API calls**, not the constructor:

```python
# CORRECT - Initialize without recv_window
self.binance_client = BinanceClient(
    api_key,
    api_secret,
    {'timeout': 30}  # Only timeout here
)

# Pass recvWindow to individual API calls
account = self.binance_client.get_account(recvWindow=60000)
order = self.binance_client.create_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    quantity=0.001,
    price=88000,
    recvWindow=60000  # Pass here!
)
```

---

## FILES FIXED

### 1. src/exchange_manager.py

**Lines 86-157: Binance Initialization**
```python
# Before: Passing recv_window in constructor (WRONG)
# After: Pass recvWindow to API calls (CORRECT)

# Initialize without recv_window
self.binance_client = BinanceClient(
    binance_api_key,
    binance_secret_key,
    {'timeout': 30}  # NO recv_window here!
)

# Test with recvWindow as API parameter
account_info = self.binance_client.get_account(recvWindow=60000)
```

**Line 531: Get Account Balance**
```python
# Added recvWindow parameter
recv_window = getattr(self, 'recv_window', 60000)
account = self.binance_client.get_account(recvWindow=recv_window)
```

**Line 673: Create Order**
```python
# Added recvWindow parameter
recv_window = getattr(self, 'recv_window', 60000)
order = self.binance_client.create_order(
    symbol=symbol,
    side=side,
    type='LIMIT',
    timeInForce='GTC',
    quantity=quantity,
    price=str(price),
    recvWindow=recv_window  # Added this
)
```

### 2. trading_modes/RBI_RESEARCH_TRADE_FLOW.py

**Lines 1810 & 1850: Fixed OHLCV Data Fetching**
```python
# Before: Using invalid 'limit' parameter
fresh_ohlcv = BinanceTruthAPI.get_ohlcv_data(binance_symbol, '1h', limit=100)

# After: Using correct 'days_back' parameter
fresh_ohlcv = BinanceTruthAPI.get_ohlcv_data(binance_symbol, '1h', days_back=3)
```

---

## ADDITIONAL FEATURES

### 1. Automatic Retry Logic
The system now retries with increasing recvWindow values:
- Attempt 1: 10,000ms (10 seconds)
- Attempt 2: 20,000ms (20 seconds)
- Attempt 3: 30,000ms (30 seconds)
- Final fallback: 60,000ms (60 seconds)

### 2. Windows Time Sync
On the second failed attempt, the system tries to sync Windows time:
```python
if attempt == 1 and os.name == 'nt':
    subprocess.run(['w32tm', '/resync'], capture_output=True)
```

### 3. CCXT Configuration
CCXT is configured with proper timestamp handling:
```python
self.ccxt_binance = ccxt.binance({
    'options': {
        'recvWindow': 60000,  # CCXT handles this correctly
        'adjustForTimeDifference': True,  # Auto-adjust timestamps
    }
})
```

---

## TESTING

After restart, you should see:

### Successful Connection:
```
🕐 Time sync: Local=1764027933416, Server=1764027932183, Offset=-1233ms
✅ Binance connection successful (recvWindow=10000ms)
   Account Type: SPOT
```

### If Time Sync Fails:
```
⚠️  Attempt 1 failed: Timestamp issue, retrying with larger recvWindow...
   🔧 Attempted Windows time sync
⚠️  Attempt 2 failed: Timestamp issue, retrying with larger recvWindow...
✅ Binance connection successful (recvWindow=30000ms)
```

---

## PREVENTION

To prevent timestamp issues in the future:

1. **Keep System Time Synced**:
   - Windows: Settings → Time & Language → "Sync now"
   - Or run: `w32tm /resync` as Administrator

2. **Use NTP Server**:
   - Configure Windows to use `time.nist.gov` or `pool.ntp.org`

3. **Monitor Time Offset**:
   - If offset > 1000ms, sync your system time
   - The system shows offset in every connection attempt

---

## KEY LEARNINGS

1. **`recv_window` is NOT a constructor parameter** - it goes in API calls
2. **`recvWindow` (camelCase) for API calls**, not `recv_window` (snake_case)
3. **System time must be within 1 second** of Binance server time
4. **Always use maximum recvWindow (60000ms)** for slow/unstable connections
5. **CCXT handles timestamp sync better** than python-binance

---

## STATUS

✅ **FIXED** - System now properly handles:
- Correct recvWindow parameter placement
- Automatic retry with increasing tolerance
- Windows time synchronization attempts
- Fallback to maximum recvWindow
- Proper error messages and diagnostics

The trading system can now connect to Binance reliably even with minor time synchronization issues.