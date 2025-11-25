"""
Check if strategies are deployed in database
"""
import sys
sys.path.insert(0, r'c:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents')

from risk_management.trading_database_typed import TradingDatabase
from termcolor import cprint

db = TradingDatabase()

print("="*80)
print("CHECKING DEPLOYED STRATEGIES IN DATABASE")
print("="*80)

# Query deployed strategies
strategies = db.get_deployed_strategies()

if not strategies:
    print("\nNO DEPLOYED STRATEGIES FOUND IN DATABASE")
    print("\nThis is ROOT CAUSE #1: Empty strategy list")
    print("\nYou need to deploy strategies to the database first.")
    sys.exit(1)

print(f"\nFound {len(strategies)} deployed strategy(ies):\n")

for i, strat in enumerate(strategies, 1):
    print(f"{i}. Strategy Name: {strat.get('strategy_name', 'N/A')}")
    print(f"   Code Path: {strat.get('code_path', 'N/A')}")
    print(f"   Deployed At: {strat.get('deployed_timestamp', 'N/A')}")
    print(f"   Config: {strat.get('config_json', 'N/A')}")
    print()

print("="*80)
