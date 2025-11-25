# DEX AI Trading Agents

A comprehensive AI-powered cryptocurrency trading system with multiple specialized agents for various trading strategies and market analysis.

## Project Structure

```
DEX-dev-ai-agents/
├── src/                          # Main source code
│   ├── agents/                   # Trading agent implementations
│   │   ├── archive/             # Archived agent versions
│   │   ├── base_agent.py        # Base agent class
│   │   ├── trading_agent.py     # Main trading agent
│   │   ├── sentiment_agent.py   # Sentiment analysis agent
│   │   ├── whale_agent.py       # Whale tracking agent
│   │   └── ... (other agents)
│   ├── config.py                # System configuration
│   └── data/                    # Data storage and processing
│
├── config/                       # Configuration files
│   ├── requirements.txt         # Python dependencies
│   ├── requirements_typecheck.txt # Type checking dependencies
│   ├── mypy.ini                 # MyPy configuration
│   ├── .pre-commit-config.yaml  # Pre-commit hooks
│   └── AI_MODELS_CONFIGURATION.md # AI model settings
│
├── documentation/                # All project documentation
│   ├── architecture/            # System architecture docs
│   │   ├── ARCHITECTURAL_REFACTORING_COMPLETE.md
│   │   ├── ARCHITECTURE_PERMANENT_FIXES.md
│   │   ├── PHASE_3_COMPLETE.md
│   │   ├── FULL_FIX_COMPLETE_PHASE_1-2.md
│   │   └── COMPLETE_SIGNAL_TO_EXECUTION_FLOW.md
│   ├── guides/                  # User guides and setup instructions
│   │   ├── QUICK_START_GUIDE.md
│   │   ├── BINANCE_API_SETUP_GUIDE.md
│   │   ├── TESTING_GUIDE.md
│   │   ├── PRODUCTION_SCRIPTS_README.md
│   │   └── RUN FLOW.txt
│   └── status_reports/          # System status and fix reports
│       ├── COMPLETE_SYSTEM_STATUS.md
│       ├── CURRENT_SYSTEM_STATUS.md
│       ├── FIXES_APPLIED_SUMMARY.md
│       └── ... (other status reports)
│
├── utility_scripts/             # Utility and maintenance scripts
│   ├── check_system_health.py  # System health monitoring
│   ├── close_open_trades.py    # Emergency trade closure
│   ├── diagnose_binance_api.py # API diagnostic tool
│   ├── emergency_stop.py       # Emergency system shutdown
│   ├── generate_trade_report.py # Trade reporting
│   ├── monitor_live_trading.py # Live trading monitor
│   └── verify_indicators.py    # Indicator verification
│
├── tests/                       # Test files
│   ├── test_database.py
│   ├── test_domain_models.py
│   ├── test_indicators.py
│   └── test_volatility_bracket_fix.py
│
├── trading_modes/               # Different trading mode implementations
├── risk_management/             # Risk management modules
├── order_management/            # Order execution and management
├── market_analysis/             # Market analysis tools
├── shared/                      # Shared utilities and helpers
├── scripts/                     # Build and deployment scripts
├── examples/                    # Example usage and demos
├── results/                     # Trading results and backtests
│
├── database/                    # Database storage (gitignored)
├── logs/                        # System logs (gitignored)
├── temp_data/                   # Temporary data files
│
├── .env                         # Environment variables (gitignored)
├── .gitignore                   # Git ignore rules
└── trading_system.db*           # Active database files (in use)
```

## Quick Start

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r config/requirements.txt
   ```

2. **Configure API Keys**
   - Copy `.env.example` to `.env`
   - Add your API keys for exchanges and services
   - See [documentation/guides/BINANCE_API_SETUP_GUIDE.md](documentation/guides/BINANCE_API_SETUP_GUIDE.md)

3. **Run System Health Check**
   ```bash
   python utility_scripts/check_system_health.py
   ```

4. **Start Trading Agent**
   ```bash
   python src/agents/trading_agent.py
   ```

## Key Features

- **Multi-Agent System**: Specialized agents for different trading strategies
- **Real-time Market Analysis**: Live data processing and signal generation
- **Risk Management**: Comprehensive risk controls and position sizing
- **Exchange Integration**: Support for multiple cryptocurrency exchanges
- **Sentiment Analysis**: Social media and news sentiment tracking
- **Whale Tracking**: Large transaction monitoring and analysis
- **Automated Trading**: Autonomous trade execution based on signals
- **Backtesting**: Historical strategy testing and optimization

## Available Agents

- **Trading Agent**: Main trading execution agent
- **Sentiment Agent**: Social sentiment analysis
- **Whale Agent**: Whale wallet tracking
- **Research Agent**: Market research and analysis
- **Sniper Agent**: Fast entry/exit opportunities
- **Liquidation Agent**: Liquidation cascade detection
- **Funding Agent**: Funding rate arbitrage
- **And many more...** (see `src/agents/` directory)

## Utility Scripts

Located in `utility_scripts/`:

- `check_system_health.py` - Monitor system health and status
- `emergency_stop.py` - Emergency shutdown all trading
- `close_open_trades.py` - Close all open positions
- `monitor_live_trading.py` - Real-time trading monitor
- `generate_trade_report.py` - Generate performance reports
- `diagnose_binance_api.py` - Diagnose API connectivity issues

## Documentation

All documentation is organized in the `documentation/` directory:

- **Architecture**: System design and technical architecture
- **Guides**: Setup, configuration, and usage guides
- **Status Reports**: System status, fixes, and updates

Start with [documentation/guides/QUICK_START_GUIDE.md](documentation/guides/QUICK_START_GUIDE.md)

## Configuration

Configuration files are in the `config/` directory:

- `requirements.txt` - Python package dependencies
- `mypy.ini` - Type checking configuration
- `.pre-commit-config.yaml` - Git hooks configuration
- `AI_MODELS_CONFIGURATION.md` - AI model settings and parameters

## Testing

Run tests from the project root:

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_database.py

# Run with coverage
python -m pytest --cov=src tests/
```

See [documentation/guides/TESTING_GUIDE.md](documentation/guides/TESTING_GUIDE.md) for details.

## Safety Features

- **Emergency Stop**: Immediate system shutdown
- **Position Limits**: Maximum position size controls
- **Loss Limits**: Daily/weekly loss limits
- **API Safeguards**: Rate limiting and error handling
- **Database Backups**: Automatic state persistence

## Project Status

This is a production-ready crypto trading system. Check [documentation/status_reports/CURRENT_SYSTEM_STATUS.md](documentation/status_reports/CURRENT_SYSTEM_STATUS.md) for latest updates.

## Important Notes

- **Database Files**: The active `trading_system.db*` files remain in root as they are actively in use
- **No Mock Data**: All agents use real API data (no placeholders or dummy data)
- **Production Grade**: Built for real-world trading with proper error handling
- **Environment Variables**: All sensitive keys in `.env` file (never committed)

## Support & Issues

For issues, feature requests, or questions:
1. Check existing documentation in `documentation/`
2. Review status reports for known issues
3. Run diagnostic scripts in `utility_scripts/`

## License

[Add your license information here]

## Disclaimer

**Trading cryptocurrency involves substantial risk of loss. This software is provided as-is without any guarantees. Use at your own risk. Always test thoroughly with small amounts before scaling up.**
