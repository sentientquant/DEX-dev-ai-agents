"""
Base Strategy Class for RBI Trading System
All custom strategies inherit from this
"""

import pandas as pd
from typing import Dict


class BaseStrategy:
    """
    Base class for all trading strategies

    Strategies must implement generate_signals() method
    """

    target_pair: str = None
    target_timeframe: str = None

    def __init__(self, name: str):
        self.name = name

    def generate_signals(self, symbol: str, ohlcv: pd.DataFrame) -> Dict:
        """
        Generate trading signals from OHLCV data

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            ohlcv: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']

        Returns:
            {
                'action': 'BUY' | 'SELL' | 'NOTHING',
                'confidence': 0-100,
                'reasoning': 'explanation of signal'
            }
        """
        raise NotImplementedError("Subclasses must implement generate_signals()")
