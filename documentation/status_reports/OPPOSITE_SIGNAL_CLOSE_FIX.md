# OPPOSITE SIGNAL AUTO-CLOSE IMPLEMENTATION

**Date**: 2025-11-24
**Status**: ✅ IMPLEMENTED

## USER REQUIREMENT

User requested two behaviors for open positions:

1. **SAME DIRECTION SIGNAL**: Skip if already holding same direction
   - Example: BUY signal when holding BUY → SKIP

2. **OPPOSITE DIRECTION SIGNAL**: Close position immediately at market price
   - Example: SELL signal when holding BUY → CLOSE BUY at market, then open SELL

## PREVIOUS BEHAVIOR

**Before Fix:**
```python
if symbol in open_symbols:
    cprint(f"SKIPPED - {symbol} already has an OPEN trade")
    continue  # ALWAYS skipped, regardless of direction
```

**Problem:**
- System would skip ALL new signals if position already open
- Could NOT exit losing positions when market reverses
- Missed opportunity to flip positions on strong opposite signals

## NEW BEHAVIOR

**After Fix** ([RBI_RESEARCH_TRADE_FLOW.py:760-873](trading_modes/RBI_RESEARCH_TRADE_FLOW.py#L760-L873))

### Logic Flow:

```python
if symbol in open_symbols:
    existing_trade = get existing trade from database
    existing_side = existing_trade['side']  # 'BUY' or 'SELL'

    # Check if opposite signal
    if (existing_side == 'BUY' and new_signal == 'SELL') or \
       (existing_side == 'SELL' and new_signal == 'BUY'):

        # OPPOSITE SIGNAL: Close at market
        1. Cancel all open orders (SL/TP)
        2. Execute market close order
        3. Update database with PnL
        4. Remove from open_symbols
        5. Continue to process new signal

    else:
        # SAME DIRECTION: Skip
        cprint("SKIPPED - already has open {existing_side} trade")
        continue
```

## IMPLEMENTATION DETAILS

### Step 1: Detect Opposite Signal

```python
existing_side = existing_trade.get('side', 'UNKNOWN')

is_opposite_signal = (existing_side == 'BUY' and result.action == 'SELL') or \
                     (existing_side == 'SELL' and result.action == 'BUY')
```

### Step 2: Cancel Open Orders (LIVE mode)

```python
# Cancel all SL/TP orders for this symbol
open_orders = binance_client.get_open_orders(symbol=f"{symbol}USDT")
for order in open_orders:
    binance_client.cancel_order(symbol=f"{symbol}USDT", orderId=order['orderId'])
```

**This cancels:**
- OCO order (Stop Loss + TP1)
- TP2 limit order
- TP3 limit order

### Step 3: Close Position at Market

```python
# Get actual balance from Binance
account = binance_client.get_account()
balance = next((b for b in account['balances'] if b['asset'] == symbol), None)
close_qty = float(balance['free'])

# Execute market close
if existing_side == 'BUY':
    # Close BUY by selling at market
    binance_client.order_market_sell(symbol=f"{symbol}USDT", quantity=close_qty)
else:
    # Close SELL by buying at market
    binance_client.order_market_buy(symbol=f"{symbol}USDT", quantity=close_qty)
```

### Step 4: Calculate PnL and Update Database

```python
entry_price = existing_trade.get('entry_price', current_price)

if existing_side == 'BUY':
    pnl_usd = (current_price - entry_price) * close_qty
else:
    pnl_usd = (entry_price - current_price) * close_qty

pnl_pct = (pnl_usd / (entry_price * close_qty)) * 100

db.close_trade(
    trade_id=existing_trade['id'],
    exit_price=current_price,
    exit_reason='opposite_signal',
    pnl_usd=pnl_usd,
    pnl_pct=pnl_pct
)
```

### Step 5: Continue to New Trade

```python
# Remove from open_symbols so new trade can proceed
open_symbols.discard(symbol)

# Code continues to process the new SELL signal...
```

## EXAMPLE SCENARIOS

### Scenario 1: BUY → SELL Signal (Opposite)

**Setup:**
- Open: BUY 0.001 BTC @ $86,000
- Current Price: $84,000
- Signal: SELL @ 56% confidence

**Actions:**
1. Detect opposite signal (BUY → SELL)
2. Cancel OCO + TP2 + TP3 orders
3. Market SELL 0.001 BTC @ $84,000
4. Calculate PnL: ($84,000 - $86,000) × 0.001 = **-$2.00 loss**
5. Close in database with exit_reason='opposite_signal'
6. **Proceed to open new SELL position**

**Output:**
```
🔄 OPPOSITE SIGNAL DETECTED
📍 Existing: BUY | New Signal: SELL
🚨 Closing BUY position at MARKET PRICE
⚠️  Cancelling all open orders for BTC...
✅ Cancelled 4 orders
[BINANCE] Market SELL: 0.001 BTC @ $84000
✅ Position closed at market
💰 PnL: $-2.00 (-2.33%)
✅ Trade closed in database
```

### Scenario 2: BUY → BUY Signal (Same Direction)

**Setup:**
- Open: BUY 0.916 SOL @ $131
- Signal: BUY @ 58% confidence

**Actions:**
1. Detect same direction signal
2. **SKIP** - don't add to existing position

**Output:**
```
⚠️  SKIPPED - SOL already has an OPEN BUY trade
💡 Waiting for existing position to close before opening new trade
```

### Scenario 3: No Open Position

**Setup:**
- No open trades for ETH
- Signal: BUY @ 56% confidence

**Actions:**
1. No open position detected
2. **Proceed normally** to open new BUY position

**Output:**
```
🎯 Processing BUY for ETH...
📊 Market Regime: trending_up
💰 Position Size: $119.99
[BINANCE] Executing LIVE market BUY: 0.0424 ETHUSDT @ $2828.46
✅ LIVE order executed
✅ OCO order placed (SL + TP1 40%)
✅ TP2 limit order placed (30%)
✅ TP3 limit order placed (30%)
```

## PAPER MODE BEHAVIOR

In PAPER mode, the system:
1. Does NOT cancel actual orders (no Binance interaction)
2. Does NOT execute market close (simulated)
3. DOES update database with simulated PnL
4. DOES proceed to open new position

## RISK MANAGEMENT

### Benefits:
✅ **Quick exits** on strong reversal signals
✅ **Prevents being trapped** in losing positions
✅ **Allows position flipping** in trending markets
✅ **Preserves capital** during market reversals

### Risks:
⚠️ **Slippage** on market orders (may exit worse than expected)
⚠️ **False reversals** (may exit early on temporary pullbacks)
⚠️ **Increased trading fees** (more round trips)
⚠️ **Whipsaws** (rapid BUY/SELL/BUY could lose on fees)

### Mitigation:
- Only triggers on **opposite signals above confidence threshold**
- Requires **strong signal** (BUY: 55%+, SELL: 50%+)
- Uses **market orders** for immediate execution
- **Calculates and logs PnL** for performance tracking

## FILES MODIFIED

1. **[trading_modes/RBI_RESEARCH_TRADE_FLOW.py:760-873](trading_modes/RBI_RESEARCH_TRADE_FLOW.py#L760-L873)**
   - Added opposite signal detection logic
   - Implemented automatic market close
   - Added order cancellation
   - Added PnL calculation and database update

## TESTING CHECKLIST

When next opposite signal occurs:

- [ ] System detects opposite signal (logs "OPPOSITE SIGNAL DETECTED")
- [ ] All open orders cancelled (logs "Cancelled X orders")
- [ ] Market close order executed (logs "Market SELL/BUY: X tokens")
- [ ] Position closed on Binance (verify in Binance UI)
- [ ] Database updated with PnL (verify with trading_system.db query)
- [ ] New position opened in opposite direction
- [ ] New OCO + TP2 + TP3 orders placed for new position

## EXPECTED BEHAVIOR SUMMARY

| Current Position | New Signal | Action |
|-----------------|------------|---------|
| None | BUY | Open BUY |
| None | SELL | Open SELL |
| BUY | BUY | SKIP |
| BUY | SELL | **Close BUY → Open SELL** |
| SELL | SELL | SKIP |
| SELL | BUY | **Close SELL → Open BUY** |

---

**System now supports intelligent position management with automatic reversal on opposite signals.**
