"""
Check why SELL signals are not generating for ETH, SOL, BTC
"""
import pandas as pd
import talib
import numpy as np
from risk_management.binance_truth_paper_trading import BinanceTruthAPI

def check_strategy_conditions(symbol, timeframe='1h'):
    """Check if SELL conditions are close to being met"""

    # Get OHLCV data
    ohlcv = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe=timeframe, days_back=7)

    if ohlcv is None or len(ohlcv) < 100:
        print(f"❌ {symbol}: Insufficient data")
        return

    # Extract arrays
    high = ohlcv['high'].values
    low = ohlcv['low'].values
    close = ohlcv['close'].values

    # Strategy parameters (from VolatilityBracket)
    atr_period = 14
    multiplier = 1.5
    ma_period = 50
    rsi_period = 14

    # Calculate indicators
    atr = talib.ATR(high, low, close, timeperiod=atr_period)
    sma = talib.SMA(close, timeperiod=ma_period)
    rsi = talib.RSI(close, timeperiod=rsi_period)

    # Current values
    current_price = close[-1]
    atr_value = atr[-1]
    sma_value = sma[-1]
    rsi_value = rsi[-1]

    # Calculate brackets
    upper_bracket = sma_value + (multiplier * atr_value)
    lower_bracket = sma_value - (multiplier * atr_value)

    # Calculate SMA slope
    prev_sma_value = sma[-2]
    sma_slope_up = sma_value > prev_sma_value
    sma_slope_down = sma_value < prev_sma_value

    # RSI bias
    rsi_up_bias = rsi_value > 50
    rsi_down_bias = rsi_value < 50

    # Calculate distances
    distance_to_upper_pct = ((upper_bracket - current_price) / current_price) * 100
    distance_to_lower_pct = ((current_price - lower_bracket) / current_price) * 100

    print(f"\n{'='*80}")
    print(f"📊 {symbol} STRATEGY ANALYSIS")
    print(f"{'='*80}")
    print(f"Current Price: ${current_price:,.2f}")
    print(f"SMA (50): ${sma_value:,.2f} ({'UP' if sma_slope_up else 'DOWN' if sma_slope_down else 'FLAT'})")
    print(f"ATR (14): ${atr_value:,.2f} ({(atr_value/current_price)*100:.2f}% of price)")
    print(f"RSI (14): {rsi_value:.1f} ({'BULLISH' if rsi_up_bias else 'BEARISH'})")
    print()
    print(f"📈 UPPER BRACKET: ${upper_bracket:,.2f} (need +{distance_to_upper_pct:.2f}% to reach)")
    print(f"📉 LOWER BRACKET: ${lower_bracket:,.2f} (need -{distance_to_lower_pct:.2f}% to reach)")
    print()

    # Check BUY conditions
    buy_price_met = current_price > upper_bracket
    buy_sma_met = sma_slope_up
    buy_rsi_met = rsi_up_bias
    buy_ready = buy_price_met and buy_sma_met and buy_rsi_met

    print(f"🟢 BUY SIGNAL CONDITIONS:")
    print(f"   Price > Upper Bracket: {'✅' if buy_price_met else '❌'} (${current_price:,.2f} {'>' if buy_price_met else '<='} ${upper_bracket:,.2f})")
    print(f"   SMA Uptrend: {'✅' if buy_sma_met else '❌'}")
    print(f"   RSI > 50: {'✅' if buy_rsi_met else '❌'} ({rsi_value:.1f})")
    print(f"   → BUY SIGNAL: {'🚀 READY' if buy_ready else '⏸️  NOT READY'}")
    print()

    # Check SELL conditions
    sell_price_met = current_price < lower_bracket
    sell_sma_met = sma_slope_down
    sell_rsi_met = rsi_down_bias
    sell_ready = sell_price_met and sell_sma_met and sell_rsi_met

    print(f"🔴 SELL SIGNAL CONDITIONS:")
    print(f"   Price < Lower Bracket: {'✅' if sell_price_met else '❌'} (${current_price:,.2f} {'<' if sell_price_met else '>='} ${lower_bracket:,.2f})")
    print(f"   SMA Downtrend: {'✅' if sell_sma_met else '❌'}")
    print(f"   RSI < 50: {'✅' if sell_rsi_met else '❌'} ({rsi_value:.1f})")
    print(f"   → SELL SIGNAL: {'🔴 READY' if sell_ready else '⏸️  NOT READY'}")
    print()

    # Failure reasons
    if not sell_ready:
        failures = []
        if not sell_price_met:
            failures.append(f"Price ${distance_to_lower_pct:.2f}% ABOVE lower bracket (needs breakdown)")
        if not sell_sma_met:
            failures.append(f"SMA trending {'UP' if sma_slope_up else 'SIDEWAYS'} (need downtrend)")
        if not sell_rsi_met:
            failures.append(f"RSI {rsi_value:.1f} > 50 (need <50)")

        print(f"❌ SELL BLOCKED BY:")
        for failure in failures:
            print(f"   • {failure}")

    # Historical SELL signals
    print(f"\n📜 RECENT SIGNAL HISTORY (last 20 bars):")
    for i in range(-20, 0):
        idx = i
        if abs(idx) > len(close):
            continue

        p = close[idx]
        s = sma[idx]
        r = rsi[idx]
        a = atr[idx]

        ub = s + (multiplier * a)
        lb = s - (multiplier * a)

        s_slope = s > sma[idx-1]

        if p < lb and not s_slope and r < 50:
            print(f"   Bar {len(close)+idx}: 🔴 SELL SIGNAL @ ${p:,.2f} (RSI {r:.1f})")
        elif p > ub and s_slope and r > 50:
            print(f"   Bar {len(close)+idx}: 🟢 BUY SIGNAL @ ${p:,.2f} (RSI {r:.1f})")

    return {
        'symbol': symbol,
        'sell_ready': sell_ready,
        'buy_ready': buy_ready,
        'distance_to_sell': distance_to_lower_pct,
        'rsi': rsi_value,
        'sma_trend': 'UP' if sma_slope_up else 'DOWN' if sma_slope_down else 'FLAT'
    }

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔍 CHECKING WHY SELL SIGNALS NOT GENERATING")
    print("="*80)

    symbols = ['ETHUSDT', 'SOLUSDT', 'BTCUSDT']
    results = []

    for symbol in symbols:
        result = check_strategy_conditions(symbol, timeframe='1h')
        if result:
            results.append(result)

    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)

    for r in results:
        print(f"\n{r['symbol']}:")
        print(f"  SELL Ready: {'🔴 YES' if r['sell_ready'] else '❌ NO'}")
        print(f"  BUY Ready: {'🟢 YES' if r['buy_ready'] else '❌ NO'}")
        print(f"  Distance to SELL: {r['distance_to_sell']:.2f}% (need breakdown)")
        print(f"  RSI: {r['rsi']:.1f} ({'Bearish <50' if r['rsi'] < 50 else 'Bullish >50'})")
        print(f"  SMA Trend: {r['sma_trend']}")
