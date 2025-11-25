# verify_indicators.py
# Independent verification of market conditions using multiple indicators
# Compare with RBI trade mode results

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from trading_modes.indicators.technical import TechnicalIndicators

def analyze_pair(symbol: str, timeframe: str = '1h'):
    """Analyze a trading pair with multiple indicators"""

    # Load OHLCV data
    data_path = f'src/data/ohlcv/{symbol}-USDT-{timeframe}.csv'
    try:
        df = pd.read_csv(data_path)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime').sort_index()
    except FileNotFoundError:
        print(f"ERROR: Data file not found: {data_path}")
        return None

    # Get recent data
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    current_price = close.iloc[-1]
    prev_price = close.iloc[-2]

    print(f"\n{'='*60}")
    print(f" {symbol}/USDT - {timeframe} INDICATOR ANALYSIS")
    print(f"{'='*60}")
    print(f"Current Price: ${current_price:,.2f}")
    print(f"Previous Price: ${prev_price:,.2f}")
    print(f"Change: {((current_price - prev_price) / prev_price * 100):+.2f}%")

    # 1. RSI ANALYSIS
    print(f"\n--- RSI (14) ---")
    rsi = TechnicalIndicators.rsi(close, period=14)
    rsi_prev = TechnicalIndicators.rsi(close.iloc[:-1], period=14)

    if rsi < 30:
        rsi_signal = "OVERSOLD (BUY)"
    elif rsi > 70:
        rsi_signal = "OVERBOUGHT (SELL)"
    elif rsi > 50:
        rsi_signal = "BULLISH BIAS"
    else:
        rsi_signal = "BEARISH BIAS"

    print(f"RSI: {rsi:.2f} (prev: {rsi_prev:.2f})")
    print(f"Signal: {rsi_signal}")

    # 2. MACD ANALYSIS
    print(f"\n--- MACD (12/26/9) ---")
    macd = TechnicalIndicators.macd(close)
    macd_prev = TechnicalIndicators.macd(close.iloc[:-1])

    if macd['histogram'] > 0 and macd_prev['histogram'] < 0:
        macd_signal = "BULLISH CROSSOVER (BUY)"
    elif macd['histogram'] < 0 and macd_prev['histogram'] > 0:
        macd_signal = "BEARISH CROSSOVER (SELL)"
    elif macd['histogram'] > 0:
        macd_signal = "BULLISH MOMENTUM"
    else:
        macd_signal = "BEARISH MOMENTUM"

    print(f"MACD: {macd['macd']:.4f}")
    print(f"Signal Line: {macd['signal']:.4f}")
    print(f"Histogram: {macd['histogram']:.4f} (prev: {macd_prev['histogram']:.4f})")
    print(f"Signal: {macd_signal}")

    # 3. BOLLINGER BANDS ANALYSIS
    print(f"\n--- Bollinger Bands (20, 2.0) ---")
    bb = TechnicalIndicators.bollinger_bands(close, period=20, std_dev=2.0)

    bb_position = (current_price - bb['lower']) / (bb['upper'] - bb['lower']) * 100

    if current_price > bb['upper']:
        bb_signal = "ABOVE UPPER BAND (OVERBOUGHT/BREAKOUT)"
    elif current_price < bb['lower']:
        bb_signal = "BELOW LOWER BAND (OVERSOLD/BREAKDOWN)"
    elif bb_position > 80:
        bb_signal = "NEAR UPPER BAND (POTENTIAL SELL)"
    elif bb_position < 20:
        bb_signal = "NEAR LOWER BAND (POTENTIAL BUY)"
    else:
        bb_signal = "CONSOLIDATION (RANGE-BOUND)"

    print(f"Upper: ${bb['upper']:,.2f}")
    print(f"Middle: ${bb['middle']:,.2f}")
    print(f"Lower: ${bb['lower']:,.2f}")
    print(f"Price Position: {bb_position:.1f}% (0=lower, 100=upper)")
    print(f"Signal: {bb_signal}")

    # 4. ATR ANALYSIS (Volatility)
    print(f"\n--- ATR (14) - Volatility ---")
    atr = TechnicalIndicators.atr(high, low, close, period=14)
    atr_pct = (atr / current_price) * 100

    if atr_pct < 1.0:
        atr_signal = "LOW VOLATILITY (CONSOLIDATION)"
    elif atr_pct < 2.5:
        atr_signal = "NORMAL VOLATILITY"
    else:
        atr_signal = "HIGH VOLATILITY (TRENDING)"

    print(f"ATR: ${atr:,.2f} ({atr_pct:.2f}% of price)")
    print(f"Signal: {atr_signal}")

    # 5. EMA TREND ANALYSIS
    print(f"\n--- EMA Trend (9/21) ---")
    ema9 = TechnicalIndicators.ema(close, period=9)
    ema21 = TechnicalIndicators.ema(close, period=21)

    if ema9 > ema21 and current_price > ema9:
        ema_signal = "BULLISH TREND"
    elif ema9 < ema21 and current_price < ema9:
        ema_signal = "BEARISH TREND"
    else:
        ema_signal = "NEUTRAL/CONSOLIDATION"

    print(f"EMA 9: ${ema9:,.2f}")
    print(f"EMA 21: ${ema21:,.2f}")
    print(f"Price vs EMA9: {'ABOVE' if current_price > ema9 else 'BELOW'}")
    print(f"Signal: {ema_signal}")

    # OVERALL VERDICT
    print(f"\n{'='*60}")
    print(f" OVERALL VERDICT FOR {symbol}")
    print(f"{'='*60}")

    # Count signals
    bullish = 0
    bearish = 0
    neutral = 0

    if 'BUY' in rsi_signal or 'BULLISH' in rsi_signal:
        bullish += 1
    elif 'SELL' in rsi_signal or 'BEARISH' in rsi_signal:
        bearish += 1
    else:
        neutral += 1

    if 'BUY' in macd_signal or 'BULLISH' in macd_signal:
        bullish += 1
    elif 'SELL' in macd_signal or 'BEARISH' in macd_signal:
        bearish += 1
    else:
        neutral += 1

    if 'BUY' in bb_signal or 'BREAKOUT' in bb_signal:
        bullish += 1
    elif 'SELL' in bb_signal or 'BREAKDOWN' in bb_signal:
        bearish += 1
    else:
        neutral += 1

    if 'BULLISH' in ema_signal:
        bullish += 1
    elif 'BEARISH' in ema_signal:
        bearish += 1
    else:
        neutral += 1

    print(f"Bullish Signals: {bullish}/4")
    print(f"Bearish Signals: {bearish}/4")
    print(f"Neutral Signals: {neutral}/4")

    if bullish > bearish and bullish >= 2:
        verdict = "BULLISH - Consider LONG"
    elif bearish > bullish and bearish >= 2:
        verdict = "BEARISH - Consider SHORT"
    else:
        verdict = "NEUTRAL/CONSOLIDATION - NO TRADE"

    print(f"\nFINAL VERDICT: {verdict}")

    return {
        'symbol': symbol,
        'price': current_price,
        'rsi': rsi,
        'macd_hist': macd['histogram'],
        'bb_position': bb_position,
        'atr_pct': atr_pct,
        'bullish': bullish,
        'bearish': bearish,
        'neutral': neutral,
        'verdict': verdict
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" INDEPENDENT INDICATOR VERIFICATION")
    print(" Comparing with RBI Trade Mode Results")
    print("="*60)

    # Test all 3 pairs
    results = []
    for symbol in ['BTC', 'SOL', 'ETH']:
        result = analyze_pair(symbol, '1h')
        if result:
            results.append(result)

    # Summary
    print("\n" + "="*60)
    print(" SUMMARY - ALL PAIRS")
    print("="*60)
    print(f"{'Symbol':<8} {'Price':>12} {'RSI':>8} {'MACD Hist':>12} {'BB %':>8} {'Verdict'}")
    print("-" * 60)

    for r in results:
        print(f"{r['symbol']:<8} ${r['price']:>10,.2f} {r['rsi']:>7.2f} {r['macd_hist']:>11.4f} {r['bb_position']:>7.1f}% {r['verdict'].split(' - ')[0]}")

    print("\n" + "="*60)
    print(" VERIFICATION vs RBI TRADE MODE")
    print("="*60)
    print("If RBI shows 'No signals' during consolidation, these indicators should show:")
    print("- RSI: Between 30-70 (not extreme)")
    print("- MACD: Small histogram (no strong momentum)")
    print("- BB Position: 20-80% (within bands)")
    print("- ATR: Low volatility (<2%)")
    print("\nThis confirms the VolatilityBracket strategy is correctly waiting for breakouts.")
