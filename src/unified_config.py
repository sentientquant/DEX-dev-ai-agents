"""
🌙 Moon Dev's Unified Configuration System
Built with love by Moon Dev 🚀

PERMANENT SOLUTION to configuration sprawl.
All settings in ONE place with validation, type safety, and environment variable override.

This replaces:
- src/config.py (trading parameters)
- trading_modes/trading_modes_config.py (environment-driven config)
- trading_modes/scanner_config.py (scanner thresholds)
"""

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from typing import List, Dict, Optional, Any
from enum import Enum
import os
from pathlib import Path


class TradingMode(str, Enum):
    """Trading mode options"""
    PAPER = "PAPER"
    LIVE = "LIVE"


class ScannerMethod(str, Enum):
    """Scanner method options"""
    COMBINED = "combined"
    TOP_GAINERS = "top_gainers"
    VOLUME_SURGE = "volume_surge"


class UnifiedConfig(BaseSettings):
    """
    Unified configuration for entire trading system.

    Features:
    - Type safety with pydantic
    - Automatic environment variable loading
    - Validation on load
    - Single source of truth
    - No more hardcoded thresholds scattered across 20+ files
    """

    # =================================================================
    # SCANNER CONFIGURATION
    # =================================================================

    # Signal Thresholds (previously in scanner_config.py)
    STRONG_THRESHOLD: int = Field(
        default=60,
        description="Minimum score for STRONG signals (lowered from 70 for low volatility)",
        ge=0, le=100
    )
    MODERATE_THRESHOLD: int = Field(
        default=50,
        description="Minimum score for MODERATE signals",
        ge=0, le=100
    )
    WEAK_THRESHOLD: int = Field(
        default=40,
        description="Minimum score for WEAK signals",
        ge=0, le=100
    )

    # Volume Thresholds (previously hardcoded in multiple files)
    VOLUME_RATIO_VETO: float = Field(
        default=0.3,
        description="Hard veto: Volume < this ratio = skip (lowered from 0.5 for low volatility)",
        ge=0.0, le=5.0
    )
    VOLUME_RATIO_WARNING: float = Field(
        default=0.6,
        description="Volume warning threshold (lowered from 0.8)",
        ge=0.0, le=5.0
    )
    VOLUME_WARNING_CONFIDENCE_PENALTY: float = Field(
        default=0.8,
        description="Confidence multiplier for low volume (0.8 = 20% reduction)",
        ge=0.0, le=1.0
    )
    RVOL_ELEVATED_THRESHOLD: float = Field(
        default=1.5,
        description="Relative volume elevated threshold",
        ge=1.0
    )
    RVOL_HIGH_THRESHOLD: float = Field(
        default=2.0,
        description="Relative volume high threshold",
        ge=1.0
    )

    # RSI Thresholds (previously hardcoded across multiple files)
    RSI_OVERSOLD: int = Field(default=30, ge=0, le=100)
    RSI_OVERBOUGHT: int = Field(default=70, ge=0, le=100)
    RSI_UPTREND_THRESHOLD: int = Field(default=50, ge=0, le=100)
    RSI_STRONG_UPTREND: int = Field(default=60, ge=0, le=100)

    # Market Cap Filtering (previously in scanner_config.py)
    LARGE_CAP_MIN: int = Field(
        default=1_000_000_000,
        description="Minimum market cap for LARGE tier ($1B)",
        ge=0
    )
    MID_CAP_MIN: int = Field(
        default=100_000_000,
        description="Minimum market cap for MID tier ($100M)",
        ge=0
    )
    MIN_24H_VOLUME_USD: int = Field(
        default=1_000_000,
        description="Minimum 24h volume ($1M)",
        ge=0
    )

    # =================================================================
    # RISK MANAGEMENT
    # =================================================================

    CASH_PERCENTAGE: float = Field(
        default=0.05,
        description="Percentage of balance per trade (5%)",
        ge=0.01, le=1.0
    )
    MAX_POSITION_PERCENTAGE: float = Field(
        default=0.15,
        description="Maximum position size as % of balance (15%)",
        ge=0.01, le=1.0
    )
    MAX_LOSS_USD: int = Field(
        default=500,
        description="Stop trading if loss exceeds this ($500)",
        ge=0
    )
    MAX_GAIN_USD: int = Field(
        default=2000,
        description="Take profit if gain exceeds this ($2000)",
        ge=0
    )
    MINIMUM_BALANCE_USD: int = Field(
        default=100,
        description="Stop trading if balance falls below this ($100)",
        ge=0
    )

    # Stop Loss / Take Profit
    DEFAULT_STOP_LOSS_PCT: float = Field(
        default=0.02,
        description="Default stop loss percentage (2%)",
        ge=0.0, le=1.0
    )
    DEFAULT_TAKE_PROFIT_PCT: float = Field(
        default=0.05,
        description="Default take profit percentage (5%)",
        ge=0.0, le=1.0
    )

    # =================================================================
    # AI SWARM VERIFICATION
    # =================================================================

    # Consensus Thresholds (previously hardcoded in signal_verification_agent.py)
    UNANIMOUS_CONFIDENCE: float = Field(
        default=95.0,
        description="Confidence when all 5 models agree",
        ge=0.0, le=100.0
    )
    STRONG_MAJORITY_CONFIDENCE: float = Field(
        default=85.0,
        description="Confidence when 4/5 models agree",
        ge=0.0, le=100.0
    )
    MAJORITY_CONFIDENCE: float = Field(
        default=75.0,
        description="Confidence when 3/5 models agree",
        ge=0.0, le=100.0
    )

    # =================================================================
    # TRADING MODE
    # =================================================================

    TRADING_MODE: TradingMode = Field(
        default=TradingMode.PAPER,
        description="PAPER or LIVE trading mode"
    )
    SCANNER_METHOD: ScannerMethod = Field(
        default=ScannerMethod.COMBINED,
        description="Scanner method to use"
    )

    # =================================================================
    # EXCHANGE & API SETTINGS
    # =================================================================

    # API Keys (from environment variables)
    BINANCE_API_KEY: Optional[str] = Field(default=None, env="BINANCE_API_KEY")
    BINANCE_API_SECRET: Optional[str] = Field(default=None, env="BINANCE_API_SECRET")
    COINGECKO_API_KEY: Optional[str] = Field(default=None, env="COINGECKO_API_KEY")
    ANTHROPIC_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_KEY")
    OPENAI_KEY: Optional[str] = Field(default=None, env="OPENAI_KEY")
    DEEPSEEK_KEY: Optional[str] = Field(default=None, env="DEEPSEEK_KEY")
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    GEMINI_KEY: Optional[str] = Field(default=None, env="GEMINI_KEY")

    # AI Model Settings
    AI_MODEL_PROVIDER: str = Field(
        default="anthropic",
        description="Default AI model provider"
    )
    AI_MODEL_NAME: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Default AI model name"
    )
    AI_MAX_TOKENS: int = Field(default=4096, ge=100, le=100000)
    AI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)

    # =================================================================
    # MONITORING & LOGGING
    # =================================================================

    SLEEP_BETWEEN_RUNS_MINUTES: int = Field(
        default=15,
        description="Sleep duration between main loop iterations",
        ge=1
    )
    SCANNER_INTERVAL_HOURS: int = Field(
        default=4,
        description="How often to run full scanner (hours)",
        ge=1
    )
    MONITOR_INTERVAL_MINUTES: int = Field(
        default=15,
        description="How often to monitor active positions (minutes)",
        ge=1
    )

    # =================================================================
    # DATABASE
    # =================================================================

    DATABASE_PATH: str = Field(
        default="trading_system.db",
        description="Path to main trading database"
    )
    SCANNER_DATABASE_PATH: str = Field(
        default="src/data/scanner/altcoin_pairs.db",
        description="Path to scanner cache database"
    )

    # =================================================================
    # POSITION LIMITS
    # =================================================================

    MAX_SYMBOLS: int = Field(
        default=5,
        description="Maximum number of concurrent positions",
        ge=1, le=50
    )
    MONITORED_TOKENS: List[str] = Field(
        default_factory=lambda: ["BTC", "ETH", "SOL"],
        description="Tokens to always monitor"
    )
    EXCLUDED_TOKENS: List[str] = Field(
        default_factory=lambda: [],
        description="Tokens to never trade"
    )

    # =================================================================
    # VALIDATORS (Pydantic v2 syntax)
    # =================================================================

    @model_validator(mode='after')
    def validate_thresholds(self) -> 'UnifiedConfig':
        """Validate threshold relationships (Pydantic v2 cross-field validation)"""
        # MODERATE < STRONG
        if self.MODERATE_THRESHOLD >= self.STRONG_THRESHOLD:
            raise ValueError("MODERATE_THRESHOLD must be less than STRONG_THRESHOLD")

        # WEAK < MODERATE
        if self.WEAK_THRESHOLD >= self.MODERATE_THRESHOLD:
            raise ValueError("WEAK_THRESHOLD must be less than MODERATE_THRESHOLD")

        # VOLUME_WARNING > VOLUME_VETO
        if self.VOLUME_RATIO_WARNING <= self.VOLUME_RATIO_VETO:
            raise ValueError("VOLUME_RATIO_WARNING must be greater than VOLUME_RATIO_VETO")

        # MAX_POSITION reasonable given CASH_PERCENTAGE * MAX_SYMBOLS
        max_reasonable = self.CASH_PERCENTAGE * self.MAX_SYMBOLS
        if self.MAX_POSITION_PERCENTAGE > max_reasonable:
            raise ValueError(
                f"MAX_POSITION_PERCENTAGE ({self.MAX_POSITION_PERCENTAGE}) exceeds reasonable limit "
                f"({max_reasonable:.2f} = {self.CASH_PERCENTAGE} * {self.MAX_SYMBOLS})"
            )

        return self

    class ConfigDict:
        """Pydantic v2 config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        validate_assignment = True  # Validate on attribute assignment


# =================================================================
# SINGLETON INSTANCE
# =================================================================

# Load configuration once at import
_config: Optional[UnifiedConfig] = None

def get_config() -> UnifiedConfig:
    """
    Get singleton configuration instance.

    Usage:
        from src.unified_config import get_config

        config = get_config()

        # Access settings
        if config.TRADING_MODE == TradingMode.LIVE:
            print(f"LIVE trading with max symbols: {config.MAX_SYMBOLS}")

        # Update settings (validated automatically)
        config.STRONG_THRESHOLD = 65

        # Environment variables override defaults
        # Set STRONG_THRESHOLD=70 in .env to override
    """
    global _config
    if _config is None:
        _config = UnifiedConfig()
    return _config


# =================================================================
# BACKWARD COMPATIBILITY EXPORTS
# =================================================================

# Export commonly used values for backward compatibility with old code
config = get_config()

# Export individual values (for old imports like "from src.config import STRONG_THRESHOLD")
STRONG_THRESHOLD = config.STRONG_THRESHOLD
MODERATE_THRESHOLD = config.MODERATE_THRESHOLD
WEAK_THRESHOLD = config.WEAK_THRESHOLD
VOLUME_RATIO_VETO = config.VOLUME_RATIO_VETO
VOLUME_RATIO_WARNING = config.VOLUME_RATIO_WARNING
CASH_PERCENTAGE = config.CASH_PERCENTAGE
MAX_POSITION_PERCENTAGE = config.MAX_POSITION_PERCENTAGE
MAX_LOSS_USD = config.MAX_LOSS_USD
MAX_GAIN_USD = config.MAX_GAIN_USD
MINIMUM_BALANCE_USD = config.MINIMUM_BALANCE_USD
MAX_SYMBOLS = config.MAX_SYMBOLS
TRADING_MODE = config.TRADING_MODE
AI_MODEL_PROVIDER = config.AI_MODEL_PROVIDER
AI_MODEL_NAME = config.AI_MODEL_NAME
