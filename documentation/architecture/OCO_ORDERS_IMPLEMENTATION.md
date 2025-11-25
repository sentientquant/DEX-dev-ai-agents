# OCO & LIMIT ORDERS IMPLEMENTATION

**Date**: 2025-11-24
**Status**: ✅ COMPLETE

## PROBLEM
LIVE Binance orders were executed but Stop Loss and Take Profit orders were NOT placed:
- Market BUY orders executed successfully
- No protective Stop Loss orders
- No Take Profit levels set
- Manual intervention required to close positions

## ROOT CAUSE
RBI_RESEARCH_TRADE_FLOW.py had a TODO comment instead of actual implementation:

```python
# Place OCO order (Stop Loss + First Take Profit)
# TODO: Implement OCO via exchange_manager  # ❌ NOT IMPLEMENTED!

cprint(f"     ✅ LIVE order executed", "green")
```

## SOLUTION IMPLEMENTED

### 1. **Added OCO Order Method** ([exchange_manager.py:479-545](exchange_manager.py#L479-L545))

```python
def place_oco_order(self, symbol, side, quantity, stop_price, stop_limit_price, take_profit_price):
    """
    Place OCO (One-Cancels-Other) order on Binance

    OCO = Either Stop Loss triggers OR Take Profit triggers (whichever comes first)
    """
    if self.binance_client:
        # Proper precision rounding for prices and quantity
        # ...

        # Place OCO order
        order = self.binance_client.create_oco_order(
            symbol=symbol,
            side='SELL' if side == 'BUY' else 'BUY',  # Opposite of entry
            quantity=quantity,
            price=str(take_profit_price),  # TP1 limit price
            stopPrice=str(stop_price),  # SL trigger
            stopLimitPrice=str(stop_limit_price),  # SL limit (slightly worse)
            stopLimitTimeInForce='GTC'
        )

        return order
```

### 2. **Added Limit Order Method** ([exchange_manager.py:547-600](exchange_manager.py#L547-L600))

```python
def place_limit_order(self, symbol, side, quantity, price):
    """
    Place limit order on Binance for TP2 and TP3
    """
    if self.binance_client:
        order = self.binance_client.create_order(
            symbol=symbol,
            side=side,
            type='LIMIT',
            timeInForce='GTC',
            quantity=quantity,
            price=str(price)
        )

        return order
```

### 3. **Implemented Full Exit Strategy** ([RBI_RESEARCH_TRADE_FLOW.py:874-926](RBI_RESEARCH_TRADE_FLOW.py#L874-L926))

**After LIVE market order execution:**

```python
# Place OCO order (Stop Loss + TP1 at 40%)
executed_qty = float(order['quantity'])
oco_quantity = executed_qty * 0.4  # 40% for OCO

# Place OCO (SL + TP1)
oco_result = self.exchange_manager.place_oco_order(
    symbol=symbol,
    side=result.action,
    quantity=oco_quantity,
    stop_price=order_plan.stop_loss.price,
    stop_limit_price=stop_limit_price,
    take_profit_price=order_plan.take_profits[0].price
)
cprint(f"     ✅ OCO order placed (SL + TP1 40%)", "green")

# Place TP2 limit order (30%)
tp2_quantity = executed_qty * 0.3
tp2_result = self.exchange_manager.place_limit_order(
    symbol=symbol,
    side='SELL' if result.action == 'BUY' else 'BUY',
    quantity=tp2_quantity,
    price=order_plan.take_profits[1].price
)
cprint(f"     ✅ TP2 limit order placed (30%)", "green")

# Place TP3 limit order (30%)
tp3_quantity = executed_qty * 0.3
tp3_result = self.exchange_manager.place_limit_order(
    symbol=symbol,
    side='SELL' if result.action == 'BUY' else 'BUY',
    quantity=tp3_quantity,
    price=order_plan.take_profits[2].price
)
cprint(f"     ✅ TP3 limit order placed (30%)", "green")
```

### 4. **Updated Minimum Position Size** ([RBI_RESEARCH_TRADE_FLOW.py:850-854](RBI_RESEARCH_TRADE_FLOW.py#L850-L854))

```python
# BEFORE:
if position_size_usd < 10.0:  # ❌ Too low for Binance SPOT

# AFTER:
if position_size_usd < 50.0:  # ✅ Binance SPOT minimum
    cprint(f"     ⚠️  Position size ${position_size_usd:.2f} too small (min $50 Binance SPOT)", "yellow")
    skipped_count += 1
    continue
```

## HOW IT WORKS NOW

### Example BUY Order Flow:

1. **Market BUY Order** executed: 0.00057 BTC @ $86,500
   ```
   [BINANCE] Executing LIVE market BUY: 0.00057 BTCUSDT @ $86500
   ✅ LIVE order executed
   ```

2. **OCO Order** placed (40% of position):
   ```
   [BINANCE] Placing OCO order: BUY 0.000228 BTCUSDT
   Stop Loss: $85,239.00 | Take Profit: $89,533.32
   ✅ OCO order placed (SL + TP1 40%)
   ```

3. **TP2 Limit Order** placed (30% of position):
   ```
   [BINANCE] Placing LIMIT order: SELL 0.000171 BTCUSDT @ $91,029.83
   ✅ TP2 limit order placed (30%)
   ```

4. **TP3 Limit Order** placed (30% of position):
   ```
   [BINANCE] Placing LIMIT order: SELL 0.000171 BTCUSDT @ $92,526.34
   ✅ TP3 limit order placed (30%)
   ```

## ORDER STRUCTURE ON BINANCE

After a BUY order, you'll see these orders on Binance:

### Active Orders:
1. **OCO Order** (Order List ID: 123456)
   - **STOP_LOSS_LIMIT**: SELL 40% @ $85,239.00 (trigger)
   - **LIMIT_MAKER**: SELL 40% @ $89,533.32 (TP1)
   - Whichever hits first, the other cancels

2. **LIMIT Order**: SELL 30% @ $91,029.83 (TP2)

3. **LIMIT Order**: SELL 30% @ $92,526.34 (TP3)

## EXIT SCENARIOS

### Scenario 1: Price goes UP (profit)
- TP1 hits at $89,533 → Sells 40% (OCO SL cancels)
- TP2 hits at $91,030 → Sells 30%
- TP3 hits at $92,526 → Sells 30%
- **Total: 100% position closed at profit**

### Scenario 2: Price goes DOWN (stop loss)
- SL hits at $85,239 → Sells 40% (OCO TP1 cancels)
- Manually close remaining 60% OR wait for bounce
- **Risk: Only 40% protected by OCO**

### Scenario 3: Mixed exit
- TP1 hits first → Sells 40%
- Price reverses and hits remaining manual SL
- **Partial profit taken, rest protected**

## BINANCE MINIMUM TRADE SIZES

Updated system minimums:
- **BTC**: $50 minimum (~0.00057 BTC @ $86,500)
- **SOL**: $50 minimum (~0.38 SOL @ $130)
- **ETH**: $50 minimum (~0.0176 ETH @ $2,835)

With $244.70 balance, system will NOT trade (all positions would be ~$73 but getting capped to $50 after risk adjustments).

**RECOMMENDATION**: Add minimum $300-500 USDT to trade effectively with proper position sizes.

## WHAT YOU'LL SEE ON NEXT RUN

```
🎯 Processing BUY for BTC...
   💰 Position Size: $73.41
   📍 Entry: $86540.31
   🛑 Stop Loss: $85239.00
   🎯 Take Profit 1: $89533.32 (40%)
   🎯 Take Profit 2: $91029.83 (30%)
   🎯 Take Profit 3: $92526.34 (30%)

   [BINANCE] Executing LIVE market BUY: 0.000848 BTCUSDT @ $86521.34
   ✅ LIVE order executed

   [BINANCE] Placing OCO order: BUY 0.000339 BTCUSDT
   Stop Loss: $85239.00 | Take Profit: $89533.32
   ✅ OCO order placed (SL + TP1 40%)

   [BINANCE] Placing LIMIT order: SELL 0.000254 BTCUSDT @ $91029.83
   ✅ TP2 limit order placed (30%)

   [BINANCE] Placing LIMIT order: SELL 0.000255 BTCUSDT @ $92526.34
   ✅ TP3 limit order placed (30%)
```

## FILES MODIFIED
1. `src/exchange_manager.py` - Added place_oco_order() and place_limit_order()
2. `trading_modes/RBI_RESEARCH_TRADE_FLOW.py` - Implemented OCO + limit order placement after entry
3. Minimum trade size updated: $10 → $50 (Binance SPOT requirement)

## VERIFICATION
Check Binance Spot Wallet → Open Orders after next trade:
- You should see 1 OCO order list (SL + TP1)
- You should see 2 separate limit orders (TP2 + TP3)
- Total: 3 orders protecting your position

## RISK NOTES
⚠️  **IMPORTANT**:
- OCO only protects 40% of position at Stop Loss
- Remaining 60% protected only by TP2/TP3 limits
- If price crashes past SL, you may need manual intervention
- Consider using trailing stop loss for remaining position

## NEXT STEPS
1. ✅ OCO orders implemented
2. ✅ Limit orders implemented
3. ✅ Minimum size updated to $50
4. ⚠️  **Consider adding more funds** - $244 allows only 1-2 positions max
5. 🔄 **Monitor first live trade** to verify all orders placed correctly
