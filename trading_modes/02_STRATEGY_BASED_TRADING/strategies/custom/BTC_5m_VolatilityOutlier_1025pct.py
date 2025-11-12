from src.strategies.base_strategy import BaseStrategy
import talib
import pandas as pd
import numpy as np

class BTC_5m_VolatilityOutlier(BaseStrategy):
    """
    VolatilityOutlier strategy optimized for BTC 5m

    Original backtest return: 1025.92%
    Recommended pair: BTC
    Recommended timeframe: 5m
    """

    def __init__(self):
        super().__init__(f"BTC 5m VolatilityOutlier (1025.9% backtest)")
        self.target_pair = "BTC"
        self.target_timeframe = "5m"

    def generate_signals(self, token_address, market_data):
        """
        Generate live trading signals

        Args:
            token_address: Token to analyze
            market_data: DataFrame with OHLCV data

        Returns:
            dict with 'action', 'confidence', 'reasoning'
        """
        try:
            # Extract OHLCV arrays
            high = market_data['High'].values
            low = market_data['Low'].values
            close = market_data['Close'].values
            open_price = market_data['Open'].values
            volume = market_data['Volume'].values if 'Volume' in market_data.columns else None

            # Check if we have enough data
            if len(close) < 1000:
                return {
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': 'Not enough data for indicators'
                }

            # Calculate indicators (EXTRACT FROM init() METHOD)
            def compute_vol(prices):
                rets = pd.Series(prices).pct_change()
                return rets.rolling(window=14, min_periods=14).std() * 100
            
            vol_series = compute_vol(close)
            
            def compute_p90(vols):
                return pd.Series(vols).rolling(window=10000, min_periods=1000).quantile(0.9)
            
            p90_series = compute_p90(vol_series)
            
            atr = talib.ATR(high, low, close, timeperiod=14)
            sma_vol = talib.SMA(vol_series.values, timeperiod=5)

            # Check if we have enough data
            if len(close) < 50:
                return {
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': 'Not enough data for indicators'
                }

            vol = vol_series.iloc[-1]
            sma = sma_vol[-1]
            p90 = p90_series.iloc[-1]
            atr_val = atr[-1]
            current_price = close[-1]
            
            if pd.isna(vol) or pd.isna(sma) or pd.isna(p90) or pd.isna(atr_val):
                return {
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': 'Indicators not ready (NaN values)'
                }
            
            # BEARISH ENTRY CONDITIONS (EXTRACT FROM next() METHOD)
            # Look for: self.sell() or self.position.size == 0 with bearish logic
            if vol > sma and vol > p90:
                sl = current_price + (2 * atr_val)
                tp = current_price - (4 * atr_val)
                return {
                    'action': 'SELL',
                    'confidence': 85,
                    'reasoning': f'Volatility Outlier SHORT ENTRY at {current_price:.2f}! Vol: {vol:.2f} > SMA: {sma:.2f} & > P90: {p90:.2f} | SL: {sl:.2f} TP: {tp:.2f}'
                }
            
            # EXIT CONDITIONS (EXTRACT FROM next() METHOD)
            # Look for: position closing logic
            elif vol < sma:
                return {
                    'action': 'CLOSE',
                    'confidence': 90,
                    'reasoning': f'Volatility Contraction EXIT! Covering at {current_price:.2f}. Vol: {vol:.2f} < SMA: {sma:.2f}'
                }

            # NO SIGNAL
            return {
                'action': 'NOTHING',
                'confidence': 0,
                'reasoning': 'No setup detected'
            }

        except Exception as e:
            return {
                'action': 'NOTHING',
                'confidence': 0,
                'reasoning': f'Error calculating indicators: {str(e)}'
            }