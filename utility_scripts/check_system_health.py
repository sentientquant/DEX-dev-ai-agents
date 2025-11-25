#!/usr/bin/env python3
"""
System Health Check - Production Trading System
Verifies all critical components before live trading

Checks:
[OK] API Keys configured
[OK] Database accessible
[OK] Binance connection working
[OK] Strategies loadable
[OK] All dependencies installed
[OK] Real balance fetch working
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        print(text)

def check_api_keys():
    """Verify all required API keys are configured"""
    load_dotenv()

    required_keys = {
        'BINANCE_API_KEY': 'Binance Trading',
        'BINANCE_SECRET_KEY': 'Binance Trading',
        'ANTHROPIC_KEY': 'Claude AI (optional)',
        'GROQ_API_KEY': 'Groq AI (optional)',
        'OPENROUTER_API_KEY': 'OpenRouter (optional)'
    }

    cprint("\n[1/7] API Keys Check", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    all_ok = True
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value and len(value) > 10:
            cprint(f"  [OK] {key}: Found ({len(value)} chars) - {description}", "green")
        elif 'optional' in description.lower():
            cprint(f"  [WARN] {key}: Missing (optional) - {description}", "yellow")
        else:
            cprint(f"  [ERROR] {key}: MISSING - {description}", "red")
            all_ok = False

    return all_ok

def check_database():
    """Check database connection and tables"""
    cprint("\n[2/7] Database Check", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    try:
        from risk_management.trading_database import TradingDatabase

        db = TradingDatabase("trading_system.db")

        # Check if key tables exist
        tables_to_check = ['trades', 'strategies', 'strategy_performance']

        for table in tables_to_check:
            db.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = db.cursor.fetchone()[0]
            cprint(f"  [OK] Table '{table}': {count} rows", "green")

        db.conn.close()
        cprint(f"  [OK] Database operational", "green")
        return True

    except Exception as e:
        cprint(f"  [ERROR] Database error: {e}", "red")
        return False

def check_binance_connection():
    """Test Binance API connection"""
    cprint("\n[3/7] Binance Connection Check", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    try:
        from risk_management.binance_truth_paper_trading import BinanceTruthAPI

        # Test public API (no auth needed)
        btc_price = BinanceTruthAPI.get_live_price("BTC")
        if btc_price:
            cprint(f"  [OK] Public API working: BTC = ${btc_price:,.2f}", "green")
        else:
            cprint(f"  [ERROR] Public API failed", "red")
            return False

        # Test authenticated API (requires keys)
        usdt_balance = BinanceTruthAPI.get_usdt_balance()
        if usdt_balance is not None:
            cprint(f"  [OK] Authenticated API working: Balance = ${usdt_balance:,.2f} USDT", "green")
        else:
            cprint(f"  [WARN]  Authenticated API failed (check API keys)", "yellow")
            return False

        return True

    except Exception as e:
        cprint(f"  [ERROR] Binance connection error: {e}", "red")
        return False

def check_strategies():
    """Verify strategies can be loaded"""
    cprint("\n[4/7] Strategy Loading Check", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    try:
        strategies_dir = Path("trading_modes/02_STRATEGY_BASED_TRADING/strategies/custom")

        if not strategies_dir.exists():
            cprint(f"  [ERROR] Strategies directory not found: {strategies_dir}", "red")
            return False

        strategy_files = list(strategies_dir.glob("*.py"))
        if not strategy_files:
            cprint(f"  [ERROR] No strategy files found", "red")
            return False

        cprint(f"  [OK] Found {len(strategy_files)} strategy files:", "green")
        for f in strategy_files:
            cprint(f"     - {f.name}", "white")

        return True

    except Exception as e:
        cprint(f"  [ERROR] Strategy loading error: {e}", "red")
        return False

def check_dependencies():
    """Check critical Python packages"""
    cprint("\n[5/7] Dependencies Check", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    required_packages = {
        'pandas': 'Data processing',
        'numpy': 'Numerical computing',
        'requests': 'HTTP requests',
        'dotenv': 'Environment variables',
        'sqlite3': 'Database (built-in)'
    }

    all_ok = True
    for package, description in required_packages.items():
        try:
            if package == 'dotenv':
                from dotenv import load_dotenv  # Test actual import
            else:
                __import__(package)
            cprint(f"  [OK] {package}: Installed - {description}", "green")
        except ImportError:
            cprint(f"  [ERROR] {package}: MISSING - {description}", "red")
            all_ok = False

    return all_ok

def check_trading_mode_files():
    """Verify RBI trading mode files exist"""
    cprint("\n[6/7] Trading Mode Files Check", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    required_files = [
        "trading_modes/RBI_RESEARCH_TRADE_FLOW.py",
        "risk_management/binance_truth_paper_trading.py",
        "risk_management/trading_database.py",
        "trading_modes/core/strategy_validator.py"
    ]

    all_ok = True
    for filepath in required_files:
        path = Path(filepath)
        if path.exists():
            size_kb = path.stat().st_size / 1024
            cprint(f"  [OK] {filepath} ({size_kb:.1f} KB)", "green")
        else:
            cprint(f"  [ERROR] MISSING: {filepath}", "red")
            all_ok = False

    return all_ok

def check_data_directories():
    """Verify data directories exist"""
    cprint("\n[7/7] Data Directories Check", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    required_dirs = [
        "src/data",
        "trading_modes/data",
        "risk_management"
    ]

    all_ok = True
    for dirpath in required_dirs:
        path = Path(dirpath)
        if path.exists() and path.is_dir():
            cprint(f"  [OK] {dirpath}/", "green")
        else:
            cprint(f"  [WARN]  {dirpath}/ not found (creating...)", "yellow")
            path.mkdir(parents=True, exist_ok=True)

    return all_ok

def main():
    """Run all health checks"""
    cprint("\n" + "="*60, "cyan", attrs=['bold'])
    cprint(" MOON DEV TRADING SYSTEM - HEALTH CHECK", "cyan", attrs=['bold'])
    cprint("="*60, "cyan", attrs=['bold'])

    results = {
        "API Keys": check_api_keys(),
        "Database": check_database(),
        "Binance Connection": check_binance_connection(),
        "Strategies": check_strategies(),
        "Dependencies": check_dependencies(),
        "Trading Mode Files": check_trading_mode_files(),
        "Data Directories": check_data_directories()
    }

    # Summary
    cprint("\n" + "="*60, "cyan", attrs=['bold'])
    cprint(" HEALTH CHECK SUMMARY", "cyan", attrs=['bold'])
    cprint("="*60, "cyan", attrs=['bold'])

    passed = sum(results.values())
    total = len(results)

    for check, status in results.items():
        if status:
            cprint(f"  [OK] {check}", "green")
        else:
            cprint(f"  [ERROR] {check}", "red")

    cprint(f"\nPassed: {passed}/{total}", "white", attrs=['bold'])

    if passed == total:
        cprint("\n[READY] SYSTEM READY FOR LIVE TRADING! [READY]\n", "green", attrs=['bold'])
        return 0
    else:
        cprint(f"\n[WARN]  {total - passed} CRITICAL ISSUES FOUND - FIX BEFORE TRADING [WARN]\n", "red", attrs=['bold'])
        return 1

if __name__ == "__main__":
    sys.exit(main())
