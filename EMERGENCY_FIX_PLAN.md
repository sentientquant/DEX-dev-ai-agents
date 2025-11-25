# EMERGENCY FIX PLAN 🚨

**Status:** READY TO IMPLEMENT
**Priority:** CRITICAL
**ETA:** 30 minutes

---

## FIXES TO IMPLEMENT

### Fix 1: Quantity Formatting for Binance API ✅ READY

**Problem:** Scientific notation `4.65e-05` rejected by Binance

**File:** `trading_modes/RBI_RESEARCH_TRADE_FLOW.py` Line 1250-1256

**Current Code:**
```python
remaining_qty = float(balance['free'])
cprint(f"     🔥 Market selling remaining balance: {remaining_qty} {token_asset}", "red")

# Execute market sell
close_order = self.exchange_manager.binance_client.order_market_sell(
    symbol=binance_symbol,
    quantity=remaining_qty  # ❌ Float with scientific notation
)
```

**Fixed Code:**
```python
remaining_qty = float(balance['free'])

# Format quantity for Binance (no scientific notation, proper precision)
quantity_str = f"{remaining_qty:.8f}".rstrip('0').rstrip('.')

cprint(f"     🔥 Market selling remaining balance: {quantity_str} {token_asset}", "red")

# Execute market sell with formatted quantity
close_order = self.exchange_manager.binance_client.order_market_sell(
    symbol=binance_symbol,
    quantity=quantity_str  # ✅ String with decimal format
)
```

---

### Fix 2: LOT_SIZE Compliance ✅ READY

**Problem:** Quantity `0.549084` doesn't meet Binance LOT_SIZE step_size

**File:** `src/exchange_manager.py` (Create new helper functions)

**Add Helper Function:**
```python
def get_symbol_filters(self, symbol: str) -> dict:
    """
    Get all filters for a symbol from Binance exchange info

    Returns dict with: LOT_SIZE, MIN_NOTIONAL, PRICE_FILTER, etc.
    """
    try:
        info = self.binance_client.get_symbol_info(symbol)
        filters = {}

        for f in info['filters']:
            filter_type = f['filterType']
            filters[filter_type] = f

        return filters
    except Exception as e:
        cprint(f"   ⚠️  Failed to get filters for {symbol}: {e}", "yellow")
        return {}

def round_quantity_to_lot_size(self, quantity: float, symbol: str) -> float:
    """
    Round quantity to Binance LOT_SIZE requirement

    Args:
        quantity: Raw quantity (e.g., 0.549084)
        symbol: Trading pair (e.g., 'SOLUSDT')

    Returns:
        Rounded quantity that meets LOT_SIZE filter (e.g., 0.54)
    """
    import math

    filters = self.get_symbol_filters(symbol)

    if 'LOT_SIZE' not in filters:
        cprint(f"   ⚠️  No LOT_SIZE filter for {symbol}, using raw quantity", "yellow")
        return quantity

    lot_filter = filters['LOT_SIZE']
    step_size = float(lot_filter['stepSize'])
    min_qty = float(lot_filter['minQty'])
    max_qty = float(lot_filter['maxQty'])

    # Round down to nearest step_size
    rounded = math.floor(quantity / step_size) * step_size

    # Ensure within min/max bounds
    if rounded < min_qty:
        cprint(f"   ⚠️  Quantity {rounded} below min {min_qty} for {symbol}", "yellow")
        return 0.0  # Signal that quantity is too small

    if rounded > max_qty:
        cprint(f"   ⚠️  Quantity {rounded} above max {max_qty} for {symbol}", "yellow")
        rounded = max_qty

    return rounded

def format_quantity_for_binance(self, quantity: float, symbol: str) -> str:
    """
    Format quantity for Binance API:
    1. Round to LOT_SIZE
    2. Format as decimal string (no scientific notation)
    3. Remove trailing zeros

    Args:
        quantity: Raw quantity
        symbol: Trading pair

    Returns:
        Formatted string ready for Binance API
    """
    # Step 1: Round to LOT_SIZE
    rounded = self.round_quantity_to_lot_size(quantity, symbol)

    if rounded == 0.0:
        return "0"

    # Step 2: Format to string with 8 decimals
    formatted = f"{rounded:.8f}"

    # Step 3: Remove trailing zeros and decimal point if needed
    formatted = formatted.rstrip('0').rstrip('.')

    return formatted
```

**Update Emergency Fallback in RBI_RESEARCH_TRADE_FLOW.py:**
```python
if balance and float(balance['free']) > 0:
    remaining_qty = float(balance['free'])

    # Format quantity properly for Binance
    quantity_formatted = self.exchange_manager.format_quantity_for_binance(
        remaining_qty,
        binance_symbol
    )

    # Check if quantity is too small after rounding
    if quantity_formatted == "0":
        cprint(f"     ℹ️  Balance too small to sell ({remaining_qty} {token_asset})", "cyan")
        cprint(f"     🔧 Closing position in database (dust remaining)", "cyan")

        # Close in database
        self.db.close_trade(
            trade_id=position['id'],
            exit_price=current_price,
            exit_reason='dust_remaining_below_min_notional'
        )
        continue

    cprint(f"     🔥 Market selling remaining balance: {quantity_formatted} {token_asset}", "red")

    # Execute market sell with formatted quantity
    close_order = self.exchange_manager.binance_client.order_market_sell(
        symbol=binance_symbol,
        quantity=quantity_formatted
    )
    cprint(f"     ✅ Remaining position closed at market", "green")
```

---

### Fix 3: Position Reconciliation (Ghost Position Cleanup) ✅ READY

**Problem:** Database shows positions that were already closed by Binance

**File:** `trading_modes/RBI_RESEARCH_TRADE_FLOW.py` (Add new function)

**Add Function:**
```python
def reconcile_positions_with_exchange(self):
    """
    Sync database positions with actual exchange balances
    Closes ghost positions that exist in database but not on exchange

    This fixes the issue where OCO orders execute but database isn't updated
    """
    cprint("\n  🔍 Reconciling positions with exchange...", "cyan")

    # Get open positions from database
    db_positions = self.db.get_open_trades()

    if not db_positions:
        cprint("     ✅ No positions to reconcile", "green")
        return

    # Get actual account balances from Binance
    try:
        account = self.exchange_manager.binance_client.get_account()
        exchange_balances = {b['asset']: float(b['free']) for b in account['balances']}
    except Exception as e:
        cprint(f"     ⚠️  Failed to get exchange balances: {e}", "yellow")
        return

    ghost_positions_found = 0

    for position in db_positions:
        symbol = position.get('symbol', '')
        trade_id = position.get('id', 0)
        entry_price = position.get('entry_price', 0)
        position_size_usd = position.get('position_size_usd', 0)

        # Extract base asset (e.g., 'ETH' from 'ETHUSDT')
        base_asset = symbol.replace('USDT', '').replace('-', '')

        # Calculate expected balance
        expected_balance = position_size_usd / entry_price if entry_price > 0 else 0

        # Get actual balance from exchange
        actual_balance = exchange_balances.get(base_asset, 0.0)

        # Check if position is a "ghost" (balance is dust or zero)
        # Consider it ghost if actual < 1% of expected
        is_ghost = actual_balance < (expected_balance * 0.01)

        if is_ghost:
            ghost_positions_found += 1
            cprint(f"     🚨 GHOST POSITION DETECTED: {symbol}", "yellow")
            cprint(f"        Database shows: {expected_balance:.8f} {base_asset}", "yellow")
            cprint(f"        Exchange shows: {actual_balance:.8f} {base_asset}", "yellow")
            cprint(f"        🔧 Closing ghost position in database...", "cyan")

            # Close position in database
            try:
                # Use last known price or entry price
                current_price = self.exchange_manager.binance_client.get_symbol_ticker(
                    symbol=symbol.replace('-', '')
                )
                exit_price = float(current_price['price'])
            except:
                exit_price = entry_price  # Fallback to entry price

            self.db.close_trade(
                trade_id=trade_id,
                exit_price=exit_price,
                exit_reason='ghost_position_cleanup_oco_filled'
            )
            cprint(f"        ✅ Ghost position closed in database", "green")

    if ghost_positions_found > 0:
        cprint(f"     🔧 Reconciliation complete: {ghost_positions_found} ghost position(s) cleaned up", "cyan")
    else:
        cprint(f"     ✅ All positions in sync with exchange", "green")
```

**Call at Start of Monitoring:**
```python
def monitor_positions(self):
    """Monitor open positions with real-time PnL tracking"""
    cprint("\n[5/5] Monitoring Open Positions with Real-time PnL & OCO Protection...", "cyan", attrs=['bold'])

    # FIRST: Reconcile positions with exchange
    self.reconcile_positions_with_exchange()

    # THEN: Get remaining positions (after cleanup)
    positions = self.db.get_open_trades()

    if not positions:
        cprint("  ✅ No open positions to monitor", "green")
        return

    cprint(f"  Monitoring {len(positions)} position(s)", "cyan")

    # ... rest of monitoring code ...
```

---

## IMPLEMENTATION ORDER

### Step 1: Add Helper Functions to ExchangeManager
1. Open `src/exchange_manager.py`
2. Add `get_symbol_filters()`
3. Add `round_quantity_to_lot_size()`
4. Add `format_quantity_for_binance()`
5. Test with: `python test_quantity_formatting.py`

### Step 2: Fix Emergency Fallback in RBI_RESEARCH_TRADE_FLOW
1. Open `trading_modes/RBI_RESEARCH_TRADE_FLOW.py`
2. Find line ~1250 (Market selling remaining balance)
3. Replace quantity handling with formatted version
4. Add dust check logic

### Step 3: Add Position Reconciliation
1. Still in `trading_modes/RBI_RESEARCH_TRADE_FLOW.py`
2. Add `reconcile_positions_with_exchange()` function
3. Call it at start of `monitor_positions()`

### Step 4: Test Before Live
1. Create test script
2. Test quantity formatting
3. Test LOT_SIZE rounding
4. Test position reconciliation
5. Run in PAPER mode first

---

## TEST SCRIPT

Create `test_emergency_fixes.py`:
```python
"""
Test emergency fixes before deploying to live
"""
from src.exchange_manager import ExchangeManager
from trading_modes.RBI_RESEARCH_TRADE_FLOW import RBIResearchTradeFlow

def test_quantity_formatting():
    """Test Fix 1: Quantity formatting"""
    print("="*80)
    print("TEST 1: Quantity Formatting")
    print("="*80)

    mgr = ExchangeManager(mode='PAPER')

    test_cases = [
        (4.65e-05, 'ETHUSDT'),    # Scientific notation
        (0.549084, 'SOLUSDT'),     # Needs LOT_SIZE rounding
        (1.23456789, 'BTCUSDT'),   # Normal quantity
    ]

    for qty, symbol in test_cases:
        formatted = mgr.format_quantity_for_binance(qty, symbol)
        print(f"\n{symbol}: {qty} → {formatted}")

        # Verify no scientific notation
        assert 'e' not in formatted.lower(), f"Scientific notation found: {formatted}"

        # Verify decimal format
        try:
            float(formatted)
            print(f"   ✅ Valid decimal format")
        except:
            print(f"   ❌ Invalid format: {formatted}")

    print("\n✅ Quantity formatting test PASSED")

def test_lot_size_rounding():
    """Test Fix 2: LOT_SIZE compliance"""
    print("\n" + "="*80)
    print("TEST 2: LOT_SIZE Rounding")
    print("="*80)

    mgr = ExchangeManager(mode='PAPER')

    symbols = ['ETHUSDT', 'SOLUSDT', 'BTCUSDT']

    for symbol in symbols:
        print(f"\n{symbol}:")

        filters = mgr.get_symbol_filters(symbol)
        if 'LOT_SIZE' in filters:
            lot = filters['LOT_SIZE']
            print(f"   Min Qty: {lot['minQty']}")
            print(f"   Max Qty: {lot['maxQty']}")
            print(f"   Step Size: {lot['stepSize']}")

            # Test rounding
            test_qty = 0.549084
            rounded = mgr.round_quantity_to_lot_size(test_qty, symbol)
            print(f"   Test: {test_qty} → {rounded}")

            # Verify it's a multiple of step_size
            step_size = float(lot['stepSize'])
            remainder = rounded % step_size
            assert remainder < 1e-8, f"Not a multiple of step_size: {remainder}"
            print(f"   ✅ LOT_SIZE compliant")
        else:
            print(f"   ⚠️  No LOT_SIZE filter found")

    print("\n✅ LOT_SIZE rounding test PASSED")

def test_position_reconciliation():
    """Test Fix 3: Ghost position cleanup"""
    print("\n" + "="*80)
    print("TEST 3: Position Reconciliation")
    print("="*80)

    flow = RBIResearchTradeFlow(
        mode='PAPER',
        symbols=['BTC', 'ETH', 'SOL'],
        check_interval_minutes=15
    )

    print("\nRunning reconciliation...")
    flow.reconcile_positions_with_exchange()

    positions = flow.db.get_open_trades()
    print(f"\n✅ Open positions after reconciliation: {len(positions)}")

if __name__ == '__main__':
    print("TESTING EMERGENCY FIXES")
    print("="*80)

    try:
        test_quantity_formatting()
        test_lot_size_rounding()
        test_position_reconciliation()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED - READY TO DEPLOY")
        print("="*80)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
```

---

## DEPLOYMENT CHECKLIST

- [ ] Stop live trading system
- [ ] Implement Fix 1 (Quantity formatting)
- [ ] Implement Fix 2 (LOT_SIZE compliance)
- [ ] Implement Fix 3 (Position reconciliation)
- [ ] Run test_emergency_fixes.py
- [ ] Verify all tests pass
- [ ] Test in PAPER mode for 1 hour
- [ ] Resume live trading with monitoring

---

**ETA:** 30 minutes to implement + 15 minutes to test = 45 minutes total
**Risk:** Low (fixes are defensive and handle edge cases better)
**Reward:** HIGH (prevents future position management failures)
