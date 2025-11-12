"""
🌙 Moon Dev's Unified Configuration File
Built with love by Moon Dev 🚀

IMPORTANT: This is the SINGLE unified config.py (NOT config_master.py)
User requirement: "name it config.py not config_master to avoid mulplie broken script issue"
"""

# ==================================================
# 🎯 TRADING MODE CONFIGURATION
# ==================================================
# User requirement: "i need a config or env where all turn on and off each trade mode"

TRADING_MODES = {
    'ai_swarm': {
        'enabled': False,  # 6-model AI consensus (expensive, 60 sec/token)
        'tokens': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
        'models': ['claude', 'gpt4', 'deepseek', 'groq', 'gemini', 'ollama']
    },
    'strategy_based': {
        'enabled': True,  # Python strategies + AI validation (cheap, 5-10 sec/token)
        'strategies': ['adaptive_reversal', 'volatility_bracket'],  # RBI "hit" strategies
        'tokens': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
        'use_ai_validation': True
    },
    'copybot': {
        'enabled': False,  # Follow whale wallets (30-45 sec/portfolio)
        'whale_wallets': [
            # Add wallet addresses here
        ],
        'copy_threshold_usd': 100  # Only copy trades above this size
    },
    'rbi_research': {
        'enabled': True,  # Automated strategy factory (6 min/strategy one-time)
        'run_continuously': True,  # Keep generating and testing new strategies
        'auto_deploy_threshold': 100,  # Auto-deploy strategies with >100% return
        'test_parallel': True  # Test on BTC/ETH/SOL simultaneously
    }
}

# ==================================================
# 💱 EXCHANGE CONFIGURATION
# ==================================================
# User requirement: "Use binance has main exchange and main to get candle, order, market and other you need"

EXCHANGE_CONFIG = {
    'binance': {
        'enabled': True,  # PRIMARY exchange (main for candles, orders, market data)
        'spot': True,  # Enable SPOT trading
        'futures': True,  # Enable Futures trading
        'default_leverage': 5,  # Leverage for futures (1-125)
        'testnet': False  # Use real API (not testnet)
    },
    'hyperliquid': {
        'enabled': True,  # SECONDARY exchange
        'symbols': ['BTC', 'ETH', 'SOL'],
        'leverage': 5,
        'testnet': False
    },
    'solana': {
        'enabled': False,  # Disabled by default (Binance is primary)
        'usdc_address': "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        'sol_address': "So11111111111111111111111111111111111111111"
    }
}

# Active exchange selector (for backward compatibility)
EXCHANGE = 'binance'  # Options: 'binance', 'hyperliquid', 'solana'

# ==================================================
# 💰 TRADING CONFIGURATION
# ==================================================

# Token Lists
MONITORED_TOKENS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']  # Binance format
HYPERLIQUID_SYMBOLS = ['BTC', 'ETH', 'SOL']  # Hyperliquid format
SOLANA_EXCLUDED_TOKENS = [
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "So11111111111111111111111111111111111111111"   # SOL
]

def get_active_tokens():
    """Returns the appropriate token/symbol list based on active exchange"""
    if EXCHANGE == 'binance':
        return MONITORED_TOKENS
    elif EXCHANGE == 'hyperliquid':
        return HYPERLIQUID_SYMBOLS
    else:
        return MONITORED_TOKENS

# Position Sizing
usd_size = 25  # Size of position to hold
max_usd_order_size = 3  # Max order size
tx_sleep = 30  # Sleep between transactions
slippage = 199  # Slippage settings (199 = 1.99%)

# ==================================================
# 🛡️ RISK MANAGEMENT
# ==================================================

RISK_LIMITS = {
    # Portfolio-level limits
    'max_loss_usd': 50,  # Stop trading if lose $50 in 12 hours
    'max_gain_usd': 100,  # Stop trading if gain $100 in 12 hours
    'max_loss_gain_check_hours': 12,

    # Position-level limits
    'max_position_percentage': 30,  # Max 30% in single position
    'cash_percentage': 20,  # Keep 20% in USDC/cash
    'minimum_balance_usd': 100,  # Emergency threshold

    # Percentage-based limits (alternative)
    'use_percentage': False,  # Use USD limits (not percentage)
    'max_loss_percent': 5,
    'max_gain_percent': 5,

    # AI Override System
    'use_ai_confirmation': True,  # AI decides if limits should close positions
    'ai_override_confidence_threshold': 90  # Need 90% confidence to override
}

# Legacy variables (for backward compatibility)
MAX_LOSS_USD = RISK_LIMITS['max_loss_usd']
MAX_GAIN_USD = RISK_LIMITS['max_gain_usd']
MAX_LOSS_GAIN_CHECK_HOURS = RISK_LIMITS['max_loss_gain_check_hours']
MAX_POSITION_PERCENTAGE = RISK_LIMITS['max_position_percentage']
CASH_PERCENTAGE = RISK_LIMITS['cash_percentage']
MINIMUM_BALANCE_USD = RISK_LIMITS['minimum_balance_usd']
USE_PERCENTAGE = RISK_LIMITS['use_percentage']
MAX_LOSS_PERCENT = RISK_LIMITS['max_loss_percent']
MAX_GAIN_PERCENT = RISK_LIMITS['max_gain_percent']
USE_AI_CONFIRMATION = RISK_LIMITS['use_ai_confirmation']

# ==================================================
# 📊 MARKET ANALYSIS AGENTS
# ==================================================
# User requirement: "we have MARKET ANALYSIS AGENTS agent (funding, liqulidation, chartanalsysis, tiktok, whale, sentient agent and Polymarket Agent)"

MARKET_ANALYSIS = {
    'funding_agent': {
        'enabled': True,
        'check_interval_minutes': 15,
        'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    },
    'liquidation_agent': {
        'enabled': True,
        'check_interval_minutes': 15,
        'track_levels': True  # Track liquidation clusters
    },
    'chartanalysis_agent': {
        'enabled': True,
        'timeframes': ['15m', '1h', '4h'],
        'indicators': ['RSI', 'MACD', 'BB', 'Volume']
    },
    'whale_agent': {
        'enabled': True,
        'track_wallets': True,
        'min_trade_size_usd': 100000  # $100k+ trades
    },
    'sentiment_agent': {
        'enabled': True,
        'sources': ['twitter', 'reddit', 'tiktok'],
        'tokens': ['BTC', 'ETH', 'SOL'],
        'check_interval_minutes': 15
    },
    'tiktok_sentiment_agent': {
        'enabled': True,
        'hashtags': ['crypto', 'bitcoin', 'ethereum', 'solana'],
        'check_interval_minutes': 30
    },
    'polymarket_agent': {
        'enabled': True,
        'mode': 'sentiment',  # NOT trading - sentiment/macro analysis only
        'markets': ['crypto', 'finance', 'politics'],
        'check_interval_minutes': 60
    }
}

# Sentiment Agent Configuration
SENTIMENT_TOKENS = MARKET_ANALYSIS['sentiment_agent']['tokens']
SENTIMENT_TWEETS_PER_TOKEN = 20
SENTIMENT_REDDIT_POSTS_PER_TOKEN = 20
SENTIMENT_TWITTER_ROTATION_DAYS = 10
SENTIMENT_TWITTER_BUDGET_PER_ACCOUNT = 100
SENTIMENT_SUBREDDITS = {
    'BTC': ['Bitcoin', 'CryptoCurrency', 'BitcoinMarkets'],
    'ETH': ['ethereum', 'ethtrader', 'CryptoCurrency'],
    'SOL': ['solana', 'CryptoCurrency', 'SolanaMarkets']
}
SENTIMENT_CHECK_INTERVAL_MINUTES = 15

# ==================================================
# 🤖 AI MODEL SETTINGS
# ==================================================

AI_MODEL = "claude-3-haiku-20240307"  # Default fast model
AI_MAX_TOKENS = 1024
AI_TEMPERATURE = 0.7

# Model selection by agent type
AI_MODELS = {
    'trading': 'claude-3-haiku-20240307',  # Fast decisions
    'research': 'deepseek',  # Deep reasoning
    'sentiment': 'groq',  # Fast inference
    'risk': 'claude-3-sonnet-20240229',  # Balanced
    'strategy': 'gpt-4o',  # Strategy evaluation
}

# ==================================================
# 📈 DATA COLLECTION SETTINGS
# ==================================================

DAYSBACK_4_DATA = 3
DATA_TIMEFRAME = '1H'  # 1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 8H, 12H, 1D, 3D, 1W, 1M
SAVE_OHLCV_DATA = False  # Save data permanently or use temp

# ==================================================
# ⚙️ SYSTEM SETTINGS
# ==================================================

SLEEP_BETWEEN_RUNS_MINUTES = 15  # How long to sleep between agent runs
SLEEP_AFTER_CLOSE = 600  # Prevent overtrading after closing position
MIN_TRADES_LAST_HOUR = 2  # Minimum trades for token overview

# Transaction settings (Solana-specific)
PRIORITY_FEE = 100000  # ~0.02 USD at current SOL prices
orders_per_open = 3  # Multiple orders for better fill rates

# Strategy Agent Settings
ENABLE_STRATEGIES = TRADING_MODES['strategy_based']['enabled']
STRATEGY_MIN_CONFIDENCE = 0.7  # Minimum confidence to act on strategy signals

# ==================================================
# 🎬 CONTENT CREATION (OPTIONAL)
# ==================================================

REALTIME_CLIPS_ENABLED = False
REALTIME_CLIPS_OBS_FOLDER = '/Volumes/Moon 26/OBS'
REALTIME_CLIPS_AUTO_INTERVAL = 120
REALTIME_CLIPS_LENGTH = 2
REALTIME_CLIPS_AI_MODEL = 'groq'
REALTIME_CLIPS_AI_MODEL_NAME = None
REALTIME_CLIPS_TWITTER = True

# ==================================================
# 🔧 LEGACY VARIABLES (BACKWARD COMPATIBILITY)
# ==================================================

# Solana-specific (kept for backward compatibility)
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL_ADDRESS = "So11111111111111111111111111111111111111111"
EXCLUDED_TOKENS = SOLANA_EXCLUDED_TOKENS
symbol = '9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump'
address = '4wgfCBf2WwLSRKLef9iW7JXZ2AfkxUxGM4XcKpHm3Sin'
tokens_to_trade = MONITORED_TOKENS

# Market maker settings
buy_under = .0946
sell_over = 1

# HyperLiquid Configuration
HYPERLIQUID_LEVERAGE = EXCHANGE_CONFIG['hyperliquid']['leverage']

# Token to Exchange Mapping (for future hybrid trading)
TOKEN_EXCHANGE_MAP = {
    'BTC': 'binance',
    'ETH': 'binance',
    'SOL': 'binance',
    'BTC/USDT': 'binance',
    'ETH/USDT': 'binance',
    'SOL/USDT': 'binance',
}

# Future variables (not active yet)
STOPLOSS_PRICE = 1
BREAKOUT_PRICE = .0001
sell_at_multiple = 3
USDC_SIZE = 1
limit = 49

# ==================================================
# 🎯 HELPER FUNCTIONS
# ==================================================

def get_active_trading_modes():
    """Returns list of enabled trading modes"""
    return [mode for mode, config in TRADING_MODES.items() if config['enabled']]

def get_active_exchanges():
    """Returns list of enabled exchanges"""
    return [ex for ex, config in EXCHANGE_CONFIG.items() if config['enabled']]

def get_active_market_analysis_agents():
    """Returns list of enabled market analysis agents"""
    return [agent for agent, config in MARKET_ANALYSIS.items() if config['enabled']]

def is_mode_enabled(mode: str) -> bool:
    """Check if a trading mode is enabled"""
    return TRADING_MODES.get(mode, {}).get('enabled', False)

def is_exchange_enabled(exchange: str) -> bool:
    """Check if an exchange is enabled"""
    return EXCHANGE_CONFIG.get(exchange, {}).get('enabled', False)

def is_agent_enabled(agent: str) -> bool:
    """Check if a market analysis agent is enabled"""
    return MARKET_ANALYSIS.get(agent, {}).get('enabled', False)

# ==================================================
# 📋 SYSTEM STATUS REPORT
# ==================================================

def print_config_status():
    """Print current configuration status"""
    print("=" * 60)
    print("MOON DEV'S TRADING SYSTEM CONFIGURATION")
    print("=" * 60)

    print("\nACTIVE TRADING MODES:")
    for mode in get_active_trading_modes():
        print(f"   [+] {mode.upper()}")

    print("\nACTIVE EXCHANGES:")
    for exchange in get_active_exchanges():
        print(f"   [+] {exchange.upper()}")

    print("\nACTIVE MARKET ANALYSIS:")
    for agent in get_active_market_analysis_agents():
        print(f"   [+] {agent}")

    print("\nRISK LIMITS:")
    print(f"   Max Loss (12h): ${RISK_LIMITS['max_loss_usd']}")
    print(f"   Max Gain (12h): ${RISK_LIMITS['max_gain_usd']}")
    print(f"   Min Balance: ${RISK_LIMITS['minimum_balance_usd']}")
    print(f"   AI Override: {RISK_LIMITS['use_ai_confirmation']}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Test config when run directly
    print_config_status()
