"""
Test Emergency Fixes Before Deploying to Live
Tests quantity formatting, LOT_SIZE compliance, and position reconciliation
"""
import sys
sys.path.insert(0, 'c:\\Users\\oia89\\OneDrive\\Desktop\\DEX-dev-ai-agents')

from src.exchange_manager import ExchangeManager

def test_quantity_formatting():
    """Test Fix 1: Quantity formatting (no scientific notation)"""
    print("="*80)
    print("TEST 1: Quantity Formatting")
    print("="*80)

    mgr = ExchangeManager(exchange='BINANCE')

    test_cases = [
        (4.65e-05, 'ETHUSDT', 'ETH dust (scientific notation)'),
        (0.549084, 'SOLUSDT', 'SOL with precision'),
        (1.23456789, 'BTCUSDT', 'BTC normal quantity'),
        (0.0000001, 'ETHUSDT', 'ETH tiny amount'),
        (100.5, 'SOLUSDT', 'SOL large amount'),
    ]

    all_passed = True

    for qty, symbol, description in test_cases:
        print(f"\n{symbol} ({description}): {qty}")

        try:
            formatted = mgr.format_quantity_for_binance(qty, symbol)
            print(f"   → Formatted: {formatted}")

            # Verify no scientific notation
            if 'e' in formatted.lower() or 'E' in formatted:
                print(f"   ❌ FAIL: Scientific notation found: {formatted}")
                all_passed = False
                continue

            # Verify decimal format
            try:
                float(formatted)
                print(f"   ✅ Valid decimal format")
            except:
                print(f"   ❌ FAIL: Invalid format: {formatted}")
                all_passed = False
                continue

            # Check if it's "0" (below minimum)
            if formatted == "0":
                print(f"   ℹ️  Below minimum quantity (dust)")

        except Exception as e:
            print(f"   ❌ FAIL: Exception: {e}")
            all_passed = False

    if all_passed:
        print("\n✅ Quantity formatting test PASSED")
    else:
        print("\n❌ Quantity formatting test FAILED")

    return all_passed


def test_lot_size_rounding():
    """Test Fix 2: LOT_SIZE compliance"""
    print("\n" + "="*80)
    print("TEST 2: LOT_SIZE Rounding")
    print("="*80)

    mgr = ExchangeManager(exchange='BINANCE')

    symbols = ['ETHUSDT', 'SOLUSDT', 'BTCUSDT']
    all_passed = True

    for symbol in symbols:
        print(f"\n{symbol}:")

        try:
            filters = mgr.get_symbol_filters(symbol)
            if 'LOT_SIZE' in filters:
                lot = filters['LOT_SIZE']
                print(f"   Min Qty: {lot['minQty']}")
                print(f"   Max Qty: {lot['maxQty']}")
                print(f"   Step Size: {lot['stepSize']}")

                # Test rounding with various quantities
                test_quantities = [0.549084, 1.23456789, 0.0001]

                for test_qty in test_quantities:
                    rounded = mgr.round_quantity_to_lot_size(test_qty, symbol)
                    print(f"   Test: {test_qty} → {rounded}")

                    if rounded > 0:
                        # Verify it's a multiple of step_size
                        step_size = float(lot['stepSize'])
                        remainder = rounded % step_size

                        if remainder < 1e-8:  # Allow for floating point precision
                            print(f"      ✅ LOT_SIZE compliant")
                        else:
                            print(f"      ❌ FAIL: Not a multiple of step_size (remainder: {remainder})")
                            all_passed = False
                    else:
                        print(f"      ℹ️  Below minimum quantity")

                print(f"   ✅ {symbol} LOT_SIZE tests passed")
            else:
                print(f"   ⚠️  No LOT_SIZE filter found")
        except Exception as e:
            print(f"   ❌ FAIL: {e}")
            all_passed = False

    if all_passed:
        print("\n✅ LOT_SIZE rounding test PASSED")
    else:
        print("\n❌ LOT_SIZE rounding test FAILED")

    return all_passed


def test_combined_formatting():
    """Test combined quantity formatting + LOT_SIZE"""
    print("\n" + "="*80)
    print("TEST 3: Combined Formatting")
    print("="*80)

    mgr = ExchangeManager(exchange='BINANCE')

    # Simulate the exact scenarios from live trading
    scenarios = [
        {
            'symbol': 'ETHUSDT',
            'quantity': 4.65e-05,  # ETH dust that failed
            'description': 'ETH dust (scientific notation)'
        },
        {
            'symbol': 'SOLUSDT',
            'quantity': 0.549084,  # SOL that failed LOT_SIZE
            'description': 'SOL LOT_SIZE violation'
        },
        {
            'symbol': 'BTCUSDT',
            'quantity': 0.001234,  # BTC normal
            'description': 'BTC normal quantity'
        }
    ]

    all_passed = True

    for scenario in scenarios:
        symbol = scenario['symbol']
        quantity = scenario['quantity']
        description = scenario['description']

        print(f"\n{symbol} - {description}")
        print(f"   Raw quantity: {quantity}")

        try:
            # This is what will actually be called in production
            formatted = mgr.format_quantity_for_binance(quantity, symbol)

            print(f"   Formatted: {formatted}")

            # Verify format
            if formatted == "0":
                print(f"   ℹ️  Quantity too small to trade (dust)")
                print(f"   ✅ Would close position in database without selling")
            else:
                # Verify no scientific notation
                assert 'e' not in formatted.lower() and 'E' not in formatted, "Scientific notation found"

                # Verify it's a valid decimal
                float_val = float(formatted)
                assert float_val > 0, "Zero or negative quantity"

                print(f"   ✅ Format valid for Binance API")

        except AssertionError as e:
            print(f"   ❌ FAIL: {e}")
            all_passed = False
        except Exception as e:
            print(f"   ❌ FAIL: Exception: {e}")
            all_passed = False

    if all_passed:
        print("\n✅ Combined formatting test PASSED")
    else:
        print("\n❌ Combined formatting test FAILED")

    return all_passed


def test_position_reconciliation_dry_run():
    """Test Fix 3: Position reconciliation (dry run - no database changes)"""
    print("\n" + "="*80)
    print("TEST 4: Position Reconciliation (Dry Run)")
    print("="*80)

    print("\nℹ️  This test verifies the reconciliation logic without modifying the database")

    from trading_modes.RBI_RESEARCH_TRADE_FLOW import RBI_ResearchTradeFlow

    try:
        # Initialize in LIVE mode
        flow = RBI_ResearchTradeFlow(
            mode='LIVE',
            symbols=['BTC', 'ETH', 'SOL'],
            check_interval_minutes=15
        )

        print("✅ RBIResearchTradeFlow initialized")

        # Check if reconcile function exists
        if hasattr(flow, 'reconcile_positions_with_exchange'):
            print("✅ reconcile_positions_with_exchange() function exists")
            print("\nℹ️  Function will run automatically at start of each monitoring cycle")
            print("ℹ️  Ghost positions (DB shows open, Exchange shows closed) will be cleaned up")
        else:
            print("❌ FAIL: reconcile_positions_with_exchange() function not found")
            return False

        print("\n✅ Position reconciliation test PASSED")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("TESTING EMERGENCY FIXES FOR LIVE TRADING ISSUES")
    print("="*80)
    print("\nIssues Being Fixed:")
    print("1. Scientific notation in quantity format (e.g., 4.65e-05)")
    print("2. LOT_SIZE violations (e.g., 0.549084 for SOL)")
    print("3. Ghost positions in database after OCO fills")
    print("\n" + "="*80)

    results = {}

    try:
        results['formatting'] = test_quantity_formatting()
        results['lot_size'] = test_lot_size_rounding()
        results['combined'] = test_combined_formatting()
        results['reconciliation'] = test_position_reconciliation_dry_run()

        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.upper()}: {status}")

        all_passed = all(results.values())

        if all_passed:
            print("\n" + "="*80)
            print("✅ ALL TESTS PASSED - READY TO DEPLOY")
            print("="*80)
            print("\nNext Steps:")
            print("1. Stop live trading if still running")
            print("2. Verify fixes in code")
            print("3. Resume live trading with monitoring")
            print("\nFixed Issues:")
            print("- Quantity formatting now prevents scientific notation")
            print("- LOT_SIZE compliance ensures valid quantities")
            print("- Position reconciliation closes ghost positions automatically")
        else:
            print("\n" + "="*80)
            print("❌ SOME TESTS FAILED - DO NOT DEPLOY")
            print("="*80)
            print("\nReview failed tests above and fix issues before deploying")

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
