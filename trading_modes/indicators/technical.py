"""
Version-agnostic technical indicator calculations

Eliminates dependency on pandas_ta/talib column naming conventions.
All indicators return consistent dict format regardless of library version.

Previously:
    bb_result = pandas_ta.bbands(close, length=20, std=2.0)
    bb_upper = bb_result['BBU_20_2.0']  # KeyError on version change!

Now:
    bb = TechnicalIndicators.bollinger_bands(close, period=20, std_dev=2.0)
    bb_upper = bb['upper']  # Always 'upper', never breaks
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class TechnicalIndicators:
    """
    All technical indicators in one place
    Pure pandas/numpy operations - no external library dependencies
    """

    @staticmethod
    def bollinger_bands(
        close: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate Bollinger Bands

        Args:
            close: Closing prices
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            {'upper': float, 'middle': float, 'lower': float}

        Raises:
            ValueError: If insufficient data or NaN result
        """
        if len(close) < period:
            raise ValueError(
                f"Insufficient data for BB calculation: need {period}+ bars, got {len(close)}"
            )

        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        upper = sma.iloc[-1] + (std_dev * std.iloc[-1])
        middle = sma.iloc[-1]
        lower = sma.iloc[-1] - (std_dev * std.iloc[-1])

        # Validate
        if pd.isna(upper) or pd.isna(middle) or pd.isna(lower):
            raise ValueError(
                f"BB calculation failed - NaN result (check data quality)"
            )

        return {
            'upper': float(upper),
            'middle': float(middle),
            'lower': float(lower)
        }

    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index

        Args:
            close: Closing prices
            period: RSI period

        Returns:
            RSI value (0-100)

        Raises:
            ValueError: If insufficient data or NaN result
        """
        if len(close) < period + 1:
            raise ValueError(
                f"Insufficient data for RSI calculation: need {period + 1}+ bars, got {len(close)}"
            )

        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()  # type: ignore[operator]
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()  # type: ignore[operator]

        # Avoid division by zero
        loss = loss.replace(0, 1e-10)

        rs = gain / loss
        rsi_value = 100 - (100 / (1 + rs.iloc[-1]))

        if pd.isna(rsi_value):
            raise ValueError(
                f"RSI calculation failed - NaN result (check data quality)"
            )

        return float(rsi_value)

    @staticmethod
    def sma(close: pd.Series, period: int) -> float:
        """
        Calculate Simple Moving Average

        Args:
            close: Closing prices
            period: SMA period

        Returns:
            SMA value

        Raises:
            ValueError: If insufficient data or NaN result
        """
        if len(close) < period:
            raise ValueError(
                f"Insufficient data for SMA calculation: need {period}+ bars, got {len(close)}"
            )

        sma_value = close.rolling(window=period).mean().iloc[-1]

        if pd.isna(sma_value):
            raise ValueError(
                f"SMA calculation failed - NaN result (check data quality)"
            )

        return float(sma_value)

    @staticmethod
    def ema(close: pd.Series, period: int) -> float:
        """
        Calculate Exponential Moving Average

        Args:
            close: Closing prices
            period: EMA period

        Returns:
            EMA value

        Raises:
            ValueError: If insufficient data or NaN result
        """
        if len(close) < period:
            raise ValueError(
                f"Insufficient data for EMA calculation: need {period}+ bars, got {len(close)}"
            )

        ema_value = close.ewm(span=period, adjust=False).mean().iloc[-1]

        if pd.isna(ema_value):
            raise ValueError(
                f"EMA calculation failed - NaN result (check data quality)"
            )

        return float(ema_value)

    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> float:
        """
        Calculate Average True Range

        Args:
            high: High prices
            low: Low prices
            close: Closing prices
            period: ATR period

        Returns:
            ATR value

        Raises:
            ValueError: If insufficient data or NaN result
        """
        if len(close) < period + 1:
            raise ValueError(
                f"Insufficient data for ATR calculation: need {period + 1}+ bars, got {len(close)}"
            )

        high_low = high - low
        high_close = (high - close.shift()).abs()
        low_close = (low - close.shift()).abs()

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr_value = true_range.rolling(window=period).mean().iloc[-1]

        if pd.isna(atr_value):
            raise ValueError(
                f"ATR calculation failed - NaN result (check data quality)"
            )

        return float(atr_value)

    @staticmethod
    def macd(
        close: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            close: Closing prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period

        Returns:
            {'macd': float, 'signal': float, 'histogram': float}

        Raises:
            ValueError: If insufficient data or NaN result
        """
        required_bars = slow_period + signal_period
        if len(close) < required_bars:
            raise ValueError(
                f"Insufficient data for MACD calculation: need {required_bars}+ bars, got {len(close)}"
            )

        fast_ema = close.ewm(span=fast_period, adjust=False).mean()
        slow_ema = close.ewm(span=slow_period, adjust=False).mean()

        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        macd_val = float(macd_line.iloc[-1])
        signal_val = float(signal_line.iloc[-1])
        hist_val = float(histogram.iloc[-1])

        if pd.isna(macd_val) or pd.isna(signal_val) or pd.isna(hist_val):
            raise ValueError(
                f"MACD calculation failed - NaN result (check data quality)"
            )

        return {
            'macd': macd_val,
            'signal': signal_val,
            'histogram': hist_val
        }

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Dict[str, float]:
        """
        Calculate Stochastic Oscillator

        Args:
            high: High prices
            low: Low prices
            close: Closing prices
            period: Lookback period
            smooth_k: %K smoothing
            smooth_d: %D smoothing

        Returns:
            {'k': float, 'd': float}  # Both 0-100

        Raises:
            ValueError: If insufficient data or NaN result
        """
        required_bars = period + smooth_k + smooth_d
        if len(close) < required_bars:
            raise ValueError(
                f"Insufficient data for Stochastic calculation: need {required_bars}+ bars, got {len(close)}"
            )

        # Calculate %K
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()

        k_raw = 100 * (close - lowest_low) / (highest_high - lowest_low)
        k = k_raw.rolling(window=smooth_k).mean()

        # Calculate %D
        d = k.rolling(window=smooth_d).mean()

        k_val = float(k.iloc[-1])
        d_val = float(d.iloc[-1])

        if pd.isna(k_val) or pd.isna(d_val):
            raise ValueError(
                f"Stochastic calculation failed - NaN result (check data quality)"
            )

        return {
            'k': k_val,
            'd': d_val
        }

    @staticmethod
    def adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> float:
        """
        Calculate Average Directional Index (trend strength)

        Args:
            high: High prices
            low: Low prices
            close: Closing prices
            period: ADX period

        Returns:
            ADX value (0-100, >25 = trending)

        Raises:
            ValueError: If insufficient data or NaN result
        """
        required_bars = period * 2
        if len(close) < required_bars:
            raise ValueError(
                f"Insufficient data for ADX calculation: need {required_bars}+ bars, got {len(close)}"
            )

        # Calculate +DM and -DM
        high_diff = high.diff()
        low_diff = -low.diff()

        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)  # type: ignore[operator]
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)  # type: ignore[operator]

        # Calculate ATR
        high_low = high - low
        high_close = (high - close.shift()).abs()
        low_close = (low - close.shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean()

        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # Calculate DX and ADX
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        adx_value = dx.rolling(window=period).mean().iloc[-1]

        if pd.isna(adx_value):
            raise ValueError(
                f"ADX calculation failed - NaN result (check data quality)"
            )

        return float(adx_value)

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> float:
        """
        Calculate On-Balance Volume

        Args:
            close: Closing prices
            volume: Volume data

        Returns:
            Current OBV value

        Raises:
            ValueError: If data lengths don't match or NaN result
        """
        if len(close) != len(volume):
            raise ValueError(
                f"Close and volume lengths must match: {len(close)} != {len(volume)}"
            )

        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        obv_value = float(obv.iloc[-1])

        if pd.isna(obv_value):
            raise ValueError(
                f"OBV calculation failed - NaN result (check data quality)"
            )

        return obv_value

    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> float:
        """
        Calculate Volume-Weighted Average Price

        Args:
            high: High prices
            low: Low prices
            close: Closing prices
            volume: Volume data

        Returns:
            VWAP value

        Raises:
            ValueError: If data lengths don't match or NaN result
        """
        if not (len(high) == len(low) == len(close) == len(volume)):
            raise ValueError("All price series must have same length")

        typical_price = (high + low + close) / 3
        vwap_value = (typical_price * volume).cumsum().iloc[-1] / volume.cumsum().iloc[-1]

        if pd.isna(vwap_value):
            raise ValueError(
                f"VWAP calculation failed - NaN result (check data quality)"
            )

        return float(vwap_value)
