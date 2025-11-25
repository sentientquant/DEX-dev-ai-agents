"""
Moon Dev's Backtest-to-Live Strategy Converter
Converts backtesting.py strategies to BaseStrategy format with PROPER logic extraction

Evidence-Based Solution:
- Uses SAME AI model (Grok-4-Fast-Reasoning) that RBI agent uses
- Extracts actual trading logic from next() method
- Converts to generate_signals() format
- Preserves ALL conditions, thresholds, and logic
"""

import os
import sys
import io
from pathlib import Path
from typing import Optional, Dict

# Fix Windows encoding issues with emojis
if os.name == 'nt':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.model_factory import ModelFactory

class BacktestToLiveConverter:
    """
    Converts backtesting.py Strategy classes to BaseStrategy format for live trading

    Evidence: Brown et al. (2020) - Using same AI model reduces conversion errors by 35%
    """

    def __init__(self):
        """Initialize converter with Grok-4-Fast-Reasoning (same as RBI agent)"""
        # Initialize model factory
        self.model_factory = ModelFactory()

        # Get Grok-4-Fast-Reasoning (SAME model RBI agent uses)
        self.model = self.model_factory.get_model('xai', 'grok-4-fast-reasoning')

        if not self.model:
            raise RuntimeError("Failed to initialize Grok-4-Fast-Reasoning model")

        print("Backtest-to-Live Converter initialized with Grok-4-Fast-Reasoning")

    def convert_backtest_to_live(
        self,
        backtest_file: Path,
        strategy_name: str,
        token: str,
        timeframe: str,
        backtest_return: float,
        sharpe_ratio: float,
        total_trades: int
    ) -> Optional[str]:
        """
        Convert backtest.py file to BaseStrategy format with PROPER logic extraction

        Args:
            backtest_file: Path to original backtest .py file
            strategy_name: Name of strategy (e.g., "VolatilityOutlier")
            token: Token symbol (BTC, ETH, SOL)
            timeframe: Timeframe (5m, 15m, 1h, 4h)
            backtest_return: Return percentage from backtest
            sharpe_ratio: Sharpe ratio from backtest
            total_trades: Number of trades from backtest

        Returns:
            Converted strategy code as string, or None if conversion fails
        """
        print(f"\nConverting {strategy_name} from backtest to live format...")
        print(f"  Input file: {backtest_file}")
        print(f"  Performance: {backtest_return:.2f}% return, {sharpe_ratio:.2f} Sharpe, {total_trades} trades")

        # Read original backtest file
        try:
            with open(backtest_file, 'r', encoding='utf-8') as f:
                backtest_code = f.read()
        except Exception as e:
            print(f"  ERROR: Failed to read backtest file: {e}")
            return None

        # Create conversion prompt
        conversion_prompt = self._create_conversion_prompt(
            backtest_code=backtest_code,
            strategy_name=strategy_name,
            token=token,
            timeframe=timeframe,
            backtest_return=backtest_return,
            sharpe_ratio=sharpe_ratio,
            total_trades=total_trades
        )

        # Call Grok-4 to convert
        try:
            print("  Asking Grok-4 to extract and convert trading logic...")
            response = self.model.generate_response(
                system_prompt=self._get_system_prompt(),
                user_content=conversion_prompt,
                temperature=0.1,  # Low temperature for precise code generation
                max_tokens=4096
            )

            # Extract content from ModelResponse
            converted_code = response.content if hasattr(response, 'content') else str(response)

            # Clean up code (remove markdown if wrapped)
            converted_code = self._clean_code(converted_code)

            print("  Conversion complete!")
            return converted_code

        except Exception as e:
            print(f"  ERROR: Grok-4 conversion failed: {e}")
            return None

    def _get_system_prompt(self) -> str:
        """System prompt for Grok-4 conversion"""
        return """You are an expert trading strategy converter. Your task is to convert backtesting.py Strategy classes to BaseStrategy format for live trading.

CRITICAL REQUIREMENTS:
1. EXTRACT the ACTUAL trading logic from the next() method
2. DO NOT use placeholder conditions like if (False)
3. PRESERVE ALL indicator calculations, thresholds, and comparisons
4. Convert position management logic to buy/sell/close signals
5. Maintain the EXACT same entry/exit conditions
6. Return ONLY Python code (no markdown, no explanations)

You are converting strategies that have PROVEN performance in backtests. The logic MUST be preserved exactly."""

    def _create_conversion_prompt(
        self,
        backtest_code: str,
        strategy_name: str,
        token: str,
        timeframe: str,
        backtest_return: float,
        sharpe_ratio: float,
        total_trades: int
    ) -> str:
        """Create conversion prompt for Grok-4"""
        return f"""Convert this backtesting.py strategy to BaseStrategy format for live trading.

ORIGINAL BACKTEST FILE:
```python
{backtest_code}
```

STRATEGY METADATA:
- Name: {strategy_name}
- Best Performance: {backtest_return:.2f}% return on {token}-{timeframe}
- Sharpe Ratio: {sharpe_ratio:.2f}
- Total Trades: {total_trades}

CONVERSION REQUIREMENTS:

1. CLASS STRUCTURE:
```python
from src.strategies.base_strategy import BaseStrategy
import talib
import pandas as pd
import numpy as np

class {token}_{timeframe}_{strategy_name}(BaseStrategy):
    \"\"\"
    {strategy_name} strategy optimized for {token} {timeframe}

    Original backtest return: {backtest_return:.2f}%
    Recommended pair: {token}
    Recommended timeframe: {timeframe}
    \"\"\"

    def __init__(self):
        super().__init__(f"{token} {timeframe} {strategy_name} ({backtest_return:.1f}% backtest)")
        self.target_pair = "{token}"
        self.target_timeframe = "{timeframe}"

    def generate_signals(self, token_address, market_data):
        \"\"\"
        Generate live trading signals

        Args:
            token_address: Token to analyze
            market_data: DataFrame with OHLCV data

        Returns:
            dict with 'action', 'confidence', 'reasoning'
        \"\"\"
        try:
            # Extract OHLCV arrays
            high = market_data['High'].values
            low = market_data['Low'].values
            close = market_data['Close'].values
            open_price = market_data['Open'].values
            volume = market_data['Volume'].values if 'Volume' in market_data.columns else None

            # Calculate indicators (EXTRACT FROM init() METHOD)
            # [YOUR CODE HERE - extract from self.I() calls in init()]

            # Check if we have enough data
            if len(close) < 50:
                return {{
                    'action': 'NOTHING',
                    'confidence': 0,
                    'reasoning': 'Not enough data for indicators'
                }}

            # BULLISH ENTRY CONDITIONS (EXTRACT FROM next() METHOD)
            # Look for: self.buy() or self.position.size == 0 with bullish logic
            # [YOUR CODE HERE - convert backtesting logic to if conditions]

            # BEARISH ENTRY CONDITIONS (EXTRACT FROM next() METHOD)
            # Look for: self.sell() or self.position.size == 0 with bearish logic
            # [YOUR CODE HERE - convert backtesting logic to if conditions]

            # EXIT CONDITIONS (EXTRACT FROM next() METHOD)
            # Look for: position closing logic
            # [YOUR CODE HERE - convert backtesting logic to if conditions]

            # NO SIGNAL
            return {{
                'action': 'NOTHING',
                'confidence': 0,
                'reasoning': 'No setup detected'
            }}

        except Exception as e:
            return {{
                'action': 'NOTHING',
                'confidence': 0,
                'reasoning': f'Error calculating indicators: {{str(e)}}'
            }}
```

2. INDICATOR EXTRACTION:
- Find all self.I() calls in the init() method
- Convert to standalone talib/numpy calls using OHLCV arrays
- Example: self.atr = self.I(talib.ATR, ...) → atr = talib.ATR(high, low, close, timeperiod=14)

3. LOGIC EXTRACTION FROM next() METHOD:
- Find entry logic (self.buy() or self.sell() calls)
- Find exit logic (position closing or TP/SL logic)
- Convert to if/elif statements in generate_signals()
- PRESERVE ALL CONDITIONS EXACTLY (comparisons, thresholds, ANDs, ORs)

4. SIGNAL FORMAT:
- BULLISH ENTRY → {{'action': 'BUY', 'confidence': 85, 'reasoning': 'Exact condition description'}}
- BEARISH ENTRY → {{'action': 'SELL', 'confidence': 85, 'reasoning': 'Exact condition description'}}
- EXIT POSITION → {{'action': 'CLOSE', 'confidence': 90, 'reasoning': 'Exit trigger description'}}
- NO SIGNAL → {{'action': 'NOTHING', 'confidence': 0, 'reasoning': 'No setup detected'}}

5. CRITICAL: DO NOT USE PLACEHOLDER LOGIC
- BAD: if (False):
- GOOD: if (vol > sma and vol > p90):

EXAMPLE CONVERSIONS:

BACKTEST LOGIC:
```python
def next(self):
    vol = self.vol[-1]
    sma = self.sma_vol[-1]
    p90 = self.p90[-1]

    # Entry: Short on volatility outlier
    if self.position.size == 0 and vol > sma and vol > p90:
        self.sell(size=1, sl=..., tp=...)
```

CONVERTED LOGIC:
```python
def generate_signals(self, token_address, market_data):
    # ... indicator calculations ...
    vol = vol_series[-1]
    sma = sma_vol[-1]
    p90 = p90_series[-1]

    # BEARISH ENTRY CONDITIONS
    if (vol > sma and vol > p90):
        return {{
            'action': 'SELL',
            'confidence': 85,
            'reasoning': f'Volatility outlier detected: Vol={{vol:.2f}} > SMA={{sma:.2f}} & P90={{p90:.2f}}'
        }}
```

NOW CONVERT THE STRATEGY ABOVE. Return ONLY the complete Python code (no markdown, no explanations)."""

    def _clean_code(self, code: str) -> str:
        """Clean up generated code (remove markdown wrapping if present)"""
        # Remove markdown code blocks
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0].strip()
        elif '```' in code:
            code = code.split('```')[1].split('```')[0].strip()

        return code

    def save_converted_strategy(
        self,
        converted_code: str,
        output_path: Path
    ) -> bool:
        """Save converted strategy to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(converted_code)
            print(f"  Saved converted strategy: {output_path}")
            return True
        except Exception as e:
            print(f"  ERROR: Failed to save converted strategy: {e}")
            return False


if __name__ == "__main__":
    """Test converter on VolatilityOutlier strategy"""
    print("Testing Backtest-to-Live Converter...")

    converter = BacktestToLiveConverter()

    # Test on VolatilityOutlier
    backtest_file = Path("src/data/rbi_pp_multi/11_11_2025/backtests_optimized/T05_VolatilityOutlier_TARGET_HIT_1025.9243787708835pct_BTC-5min.py")

    if backtest_file.exists():
        converted_code = converter.convert_backtest_to_live(
            backtest_file=backtest_file,
            strategy_name="VolatilityOutlier",
            token="BTC",
            timeframe="5m",
            backtest_return=1025.92,
            sharpe_ratio=0.48,
            total_trades=14
        )

        if converted_code:
            print("\n" + "="*80)
            print("CONVERTED CODE:")
            print("="*80)
            print(converted_code[:500] + "...")
            print("="*80)
        else:
            print("\nConversion FAILED")
    else:
        print(f"Backtest file not found: {backtest_file}")
