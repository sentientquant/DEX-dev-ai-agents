"""
Auto-Converted RBI Strategy: VolatilityBracket
Source: T05_VolatilityBracket_BT.py
Target: BTC 1h
Backtest Return: 1025.00%
Sharpe: 0.52
Trades: 15

STRATEGY LOGIC:
- Uses ATR brackets for volatility-based entries
- Requires trend confirmation (SMA slope) + RSI bias
- Trailing stops based on ATR
- Exits on bracket pullback
"""

from src.strategies.base_strategy import BaseStrategy
import talib
import pandas as pd
import numpy as np


class Strategy(BaseStrategy):
    """
    VolatilityBracket - ATR-powered bracket strategy
    """

    target_pair = "BTCUSDT"  # Standardized: full pair format
    target_timeframe = "1h"

    # Strategy parameters (from backtest)
    atr_period = 14
    multiplier = 1.5  # For brackets
    ma_period = 50  # For trend confirmation
    rsi_period = 14
    min_atr_pct = 0.005  # Min ATR as 0.5% of price
    max_atr_pct = 0.03  # Max ATR as 3% of price

    def __init__(self):
        super().__init__(name="VolatilityBracket_BTC_1h")
        self.prev_sma = None

    def generate_signals(self, symbol: str, ohlcv: pd.DataFrame) -> dict:
        """
        Generate trading signals from LIVE market data

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            ohlcv: DataFrame with ['open', 'high', 'low', 'close', 'volume']

        Returns:
            {
                'action': 'BUY' | 'SELL' | 'NOTHING',
                'confidence': 0-100,
                'reasoning': 'explanation'
            }
        """
        try:
            # Check if this strategy targets this symbol
            if self.target_pair.upper() not in symbol.upper():
                return {
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': f'Strategy targets {self.target_pair}, not {symbol}'
                }

            # Extract OHLCV arrays (handle both lowercase and uppercase column names)
            high = ohlcv['high'].values if 'high' in ohlcv.columns else ohlcv['High'].values
            low = ohlcv['low'].values if 'low' in ohlcv.columns else ohlcv['Low'].values
            close = ohlcv['close'].values if 'close' in ohlcv.columns else ohlcv['Close'].values
            open_price = ohlcv['open'].values if 'open' in ohlcv.columns else ohlcv['Open'].values
            volume = ohlcv['volume'].values if 'volume' in ohlcv.columns else (ohlcv['Volume'].values if 'Volume' in ohlcv.columns else None)

            # Minimum data check
            if len(close) < max(self.atr_period, self.ma_period, self.rsi_period) + 10:
                return {
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': 'Insufficient data for indicators'
                }

            # Calculate indicators
            atr = talib.ATR(high, low, close, timeperiod=self.atr_period)
            sma = talib.SMA(close, timeperiod=self.ma_period)
            rsi = talib.RSI(close, timeperiod=self.rsi_period)

            # Current values (most recent bar)
            current_price = close[-1]
            atr_value = atr[-1]
            sma_value = sma[-1]
            rsi_value = rsi[-1]

            # Check for NaN values
            if np.isnan(atr_value) or np.isnan(sma_value) or np.isnan(rsi_value):
                return {
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': 'Indicators not ready (NaN values)'
                }

            # PERMANENT FIX: Calculate Keltner Channels anchored to SMA (statistical boundary)
            # This is the CORRECT formula that produced 1025% backtest returns
            # Brackets represent statistical volatility zones, NOT moving price levels
            upper_bracket = sma_value + (self.multiplier * atr_value)
            lower_bracket = sma_value - (self.multiplier * atr_value)

            # Check ATR thresholds (volatility filter)
            atr_pct = atr_value / current_price
            if atr_pct < self.min_atr_pct or atr_pct > self.max_atr_pct:
                return {
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': f'ATR {atr_pct*100:.2f}% out of range ({self.min_atr_pct*100:.1f}%-{self.max_atr_pct*100:.1f}%)'
                }

            # PERMANENT FIX: Calculate SMA slope from array data (stateless)
            # Don't rely on self.prev_sma which is None on each new instance
            # Compare last two SMA values directly from the indicator array
            prev_sma_value = sma[-2] if len(sma) > 1 else sma_value
            sma_slope_up = sma_value > prev_sma_value
            sma_slope_down = sma_value < prev_sma_value

            # RSI bias
            rsi_up_bias = rsi_value > 50
            rsi_down_bias = rsi_value < 50

            # LONG ENTRY LOGIC
            if (current_price > upper_bracket and sma_slope_up and rsi_up_bias):
                confidence = min(85, int(50 + (rsi_value - 50) * 0.7))  # Scale confidence with RSI
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'reasoning': f'Price ${current_price:.4f} broke upper bracket ${upper_bracket:.4f}, SMA uptrend, RSI {rsi_value:.1f} bullish'
                }

            # SHORT ENTRY LOGIC
            elif (current_price < lower_bracket and sma_slope_down and rsi_down_bias):
                confidence = min(85, int(50 + (50 - rsi_value) * 0.7))  # Scale confidence with RSI
                return {
                    'action': 'SELL',
                    'confidence': confidence,
                    'reasoning': f'Price ${current_price:.4f} broke lower bracket ${lower_bracket:.4f}, SMA downtrend, RSI {rsi_value:.1f} bearish'
                }

            # NO SIGNAL - Build detailed debug reasoning showing ALL conditions
            failed_conditions = []

            # Check LONG conditions
            if current_price > upper_bracket:
                if not sma_slope_up:
                    failed_conditions.append(f"SMA not rising (${sma_value:.2f} vs prev ${prev_sma_value:.2f})")
                if not rsi_up_bias:
                    failed_conditions.append(f"RSI not bullish ({rsi_value:.1f} < 50)")
            # Check SHORT conditions
            elif current_price < lower_bracket:
                if not sma_slope_down:
                    failed_conditions.append(f"SMA not falling (${sma_value:.2f} vs prev ${prev_sma_value:.2f})")
                if not rsi_down_bias:
                    failed_conditions.append(f"RSI not bearish ({rsi_value:.1f} > 50)")
            else:
                # Price in consolidation
                distance_to_upper = ((upper_bracket - current_price) / current_price) * 100
                distance_to_lower = ((current_price - lower_bracket) / current_price) * 100
                failed_conditions.append(f"Price in range (need +{distance_to_upper:.2f}% UP or -{distance_to_lower:.2f}% DOWN)")

            reason = f"No setup: Price ${current_price:.4f}, RSI {rsi_value:.1f}"
            if failed_conditions:
                reason += f" | Failed: {', '.join(failed_conditions)}"

            return {
                'action': 'NOTHING',
                'confidence': 0,
                'reasoning': reason
            }

        except Exception as e:
            return {
                'action': 'NOTHING',
                'confidence': 0,
                'reasoning': f'Error: {str(e)}'
            }
