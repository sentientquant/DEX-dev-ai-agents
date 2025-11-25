#!/usr/bin/env python3
"""
Test Hybrid Trailing Stop Loss in PAPER Mode
Creates a simulated BUY position and monitors trailing behavior
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from risk_management.trading_database import TradingDatabase
from risk_management.binance_truth_paper_trading import BinanceTruthAPI
from termcolor import cprint

def create_test_position():
    """Create a test PAPER position for BTC"""
    db = TradingDatabase()

    # Get current BTC price
    current_price = BinanceTruthAPI.get_live_price('BTCUSDT')
    cprint(f"\n📊 Current BTC Price: ${current_price:,.2f}", "cyan", attrs=['bold'])

    # Simulate a BUY entry at slightly lower price (so we start with profit)
    entry_price = current_price * 0.97  # Enter 3% below current (instant 3% profit)
    position_size_usd = 500.0

    # Calculate SL and TPs
    stop_loss = entry_price * 0.98  # -2% SL
    tp1_price = entry_price * 1.025  # +2.5% TP1
    tp2_price = entry_price * 1.05   # +5% TP2
    tp3_price = entry_price * 1.08   # +8% TP3

    # Create metadata with tracking fields
    metadata = {
        'highest_since_entry': current_price,  # Already higher than entry
        'trailing_activated': False,  # Will activate when we detect 3% profit
        'test_position': True,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    trade_id = f"TEST_BTC_{int(time.time())}"

    cprint(f"\n🎯 Creating Test Position:", "yellow", attrs=['bold'])
    cprint(f"   Trade ID: {trade_id}", "white")
    cprint(f"   Symbol: BTCUSDT", "white")
    cprint(f"   Entry Price: ${entry_price:,.2f} (3% below current)", "white")
    cprint(f"   Current Price: ${current_price:,.2f}", "white")
    cprint(f"   Instant Profit: {((current_price - entry_price) / entry_price * 100):.2f}%", "green")
    cprint(f"   Position Size: ${position_size_usd}", "white")
    cprint(f"   Stop Loss: ${stop_loss:,.2f} (-2%)", "red")
    cprint(f"   TP1: ${tp1_price:,.2f} (+2.5%)", "green")
    cprint(f"   TP2: ${tp2_price:,.2f} (+5%)", "green")
    cprint(f"   TP3: ${tp3_price:,.2f} (+8%)", "green")

    # Insert trade
    db.insert_trade(
        trade_id=trade_id,
        symbol='BTCUSDT',
        side='BUY',
        entry_price=entry_price,
        position_size_usd=position_size_usd,
        stop_loss=stop_loss,
        tp1_price=tp1_price,
        tp2_price=tp2_price,
        tp3_price=tp3_price,
        mode='PAPER',
        tp1_pct=40.0,
        tp2_pct=30.0,
        tp3_pct=30.0,
        strategy_name='TEST_VolatilityBracket',
        confidence='HIGH',
        metadata=metadata,
        oco_order_list_id=None  # PAPER mode
    )

    cprint(f"\n✅ Test position created successfully!", "green", attrs=['bold'])
    cprint(f"\n📋 Next Steps:", "cyan", attrs=['bold'])
    cprint(f"   1. Monitor the RBI_RESEARCH_TRADE_FLOW.py output", "white")
    cprint(f"   2. Watch for 'TRAILING ACTIVATED' message (at 3% profit)", "white")
    cprint(f"   3. Observe continuous trailing with ATR calculations", "white")
    cprint(f"   4. Check regime-adaptive multipliers (TRENDING_UP=1.3x, etc.)", "white")

    return trade_id

def monitor_position(trade_id, cycles=10):
    """Monitor the test position for trailing behavior"""
    db = TradingDatabase()

    cprint(f"\n🔍 Monitoring Position: {trade_id}", "cyan", attrs=['bold'])
    cprint(f"   Will check {cycles} times (every 5 seconds)\n", "white")

    for i in range(cycles):
        # Fetch trade
        trade = db.cursor.execute("""
            SELECT trade_id, symbol, side, entry_price, position_size_usd, stop_loss,
                   tp1_price, tp2_price, tp3_price, status, metadata
            FROM trades
            WHERE trade_id = ?
        """, (trade_id,)).fetchone()

        if not trade:
            cprint(f"❌ Trade not found!", "red")
            break

        if trade[9] != 'OPEN':  # status
            cprint(f"🛑 Position closed with status: {trade[9]}", "yellow")
            break

        # Get current price
        current_price = BinanceTruthAPI.get_live_price('BTCUSDT')
        entry_price = trade[3]
        stop_loss = trade[5]

        # Parse metadata
        metadata = json.loads(trade[10]) if trade[10] else {}
        highest_since_entry = metadata.get('highest_since_entry', current_price)
        trailing_activated = metadata.get('trailing_activated', False)

        # Calculate profit
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        unrealized_pnl = trade[4] * (profit_pct / 100)

        # Display status
        cprint(f"\n[Cycle {i+1}/{cycles}] {datetime.now().strftime('%H:%M:%S')}", "cyan", attrs=['bold'])
        cprint(f"   Current Price: ${current_price:,.2f}", "white")
        cprint(f"   Entry Price: ${entry_price:,.2f}", "white")
        cprint(f"   Profit: {profit_pct:+.2f}% (${unrealized_pnl:+.2f})", "green" if profit_pct > 0 else "red")
        cprint(f"   Stop Loss: ${stop_loss:,.2f}", "red")
        cprint(f"   Highest Since Entry: ${highest_since_entry:,.2f}", "yellow")
        cprint(f"   Trailing Activated: {'✅ YES' if trailing_activated else '❌ NO (waiting for 3% profit)'}",
               "green" if trailing_activated else "yellow")

        if trailing_activated:
            # Calculate what the trailing SL should be (3.0x ATR example)
            # This is just for display - actual calculation happens in RBI_RESEARCH_TRADE_FLOW.py
            atr_estimate = current_price * 0.03  # Rough 3% ATR estimate
            regime_mult = 1.3  # Assume TRENDING_UP for display
            sl_distance = 3.0 * atr_estimate * regime_mult
            expected_sl = highest_since_entry - sl_distance

            cprint(f"   Expected Trailing SL: ${expected_sl:,.2f} (from highest ${highest_since_entry:,.2f})", "cyan")

        time.sleep(5)  # Wait 5 seconds between checks

    cprint(f"\n✅ Monitoring complete!", "green", attrs=['bold'])

if __name__ == "__main__":
    cprint("\n" + "="*80, "cyan")
    cprint("HYBRID TRAILING STOP LOSS - TEST SUITE", "cyan", attrs=['bold'])
    cprint("="*80 + "\n", "cyan")

    # Create test position
    trade_id = create_test_position()

    # Wait a moment for user to see the creation
    time.sleep(3)

    # Monitor position
    monitor_position(trade_id, cycles=10)

    cprint(f"\n📝 Note: The actual trailing logic runs in RBI_RESEARCH_TRADE_FLOW.py", "yellow")
    cprint(f"   This script only created the test position and monitors it.", "white")
    cprint(f"   Check the RBI_RESEARCH_TRADE_FLOW.py output for trailing updates!\n", "white")
