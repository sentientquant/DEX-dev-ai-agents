#!/usr/bin/env python3
"""
Complete Strategy Validation and Trading Script

FLOW:
1. Validate existing converted strategies
2. Deploy to database if validation passes
3. Run paper trading with full risk monitoring
4. Execute on Binance if profitable

Evidence-Based Permanent Solutions (NO QUICK FIXES)
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from risk_management.trading_database import get_trading_db
from risk_management.strategy_validator import StrategyValidator
from risk_management.integrated_paper_trading import IntegratedPaperTradingSystem


class StrategyValidationAndTrading:
    """Complete validation, deployment, and trading pipeline"""

    def __init__(self):
        self.db = get_trading_db()
        self.validator = StrategyValidator(tolerance_pct=20.0, auto_debug=True)
        self.paper_system = IntegratedPaperTradingSystem(balance_usd=500.0, max_positions=3)

        # Strategies to validate
        self.strategies_to_validate = [
            {
                'name': 'BTC_5m_VolatilityOutlier',
                'path': 'trading_modes/02_STRATEGY_BASED_TRADING/strategies/custom/BTC_5m_VolatilityOutlier_1025pct.py',
                'token': 'BTC',
                'timeframe': '5m',
                'data_file': 'src/data/ohlcv/BTC-USDT-5m.csv',
                'original_metrics': {
                    'return_pct': 1025.92,
                    'sharpe_ratio': 0.48,
                    'total_trades': 14,
                    'win_rate': 50.0,
                    'max_drawdown': 15.0
                }
            },
            {
                'name': 'BTC_4h_VerticalBullish',
                'path': 'trading_modes/02_STRATEGY_BASED_TRADING/strategies/custom/BTC_4h_VerticalBullish_977pct.py',
                'token': 'BTC',
                'timeframe': '4h',
                'data_file': 'src/data/ohlcv/BTC-USDT-4h.csv',
                'original_metrics': {
                    'return_pct': 977.76,
                    'sharpe_ratio': 0.80,
                    'total_trades': 111,
                    'win_rate': 55.0,
                    'max_drawdown': 20.0
                }
            }
        ]

        print("="*80)
        print("STRATEGY VALIDATION AND TRADING SYSTEM")
        print("="*80)
        print(f"Database: {self.db.db_path}")
        print(f"Strategies to validate: {len(self.strategies_to_validate)}")
        print("="*80)

    def validate_strategy(self, strategy_info: dict) -> bool:
        """
        Validate a single strategy

        Returns: True if passed, False if failed
        """
        print(f"\n{'='*80}")
        print(f"VALIDATING: {strategy_info['name']}")
        print(f"{'='*80}")
        print(f"Token: {strategy_info['token']}")
        print(f"Timeframe: {strategy_info['timeframe']}")
        print(f"Data file: {strategy_info['data_file']}")
        print(f"Original return: {strategy_info['original_metrics']['return_pct']:.2f}%")

        # Check if data file exists
        data_file_path = project_root / strategy_info['data_file']
        if not data_file_path.exists():
            print(f"\nERROR: Data file not found: {data_file_path}")
            return False

        # Check if strategy file exists
        strategy_file_path = project_root / strategy_info['path']
        if not strategy_file_path.exists():
            print(f"\nERROR: Strategy file not found: {strategy_file_path}")
            return False

        # Validate with auto-debug
        try:
            passed, metrics, message = self.validator.validate_with_auto_debug(
                strategy_name=strategy_info['name'],
                strategy_code_path=str(strategy_file_path),
                original_metrics=strategy_info['original_metrics'],
                data_file=str(data_file_path),
                symbol=strategy_info['token'],
                timeframe=strategy_info['timeframe']
            )

            print(f"\n{'='*80}")
            print(f"VALIDATION RESULT: {message}")
            print(f"{'='*80}")

            if passed:
                print(f"PASSED - Validation return: {metrics.get('return_pct', 0):.2f}%")
                return True
            else:
                print(f"FAILED - Validation return: {metrics.get('return_pct', 0):.2f}%")
                return False

        except Exception as e:
            print(f"\nERROR during validation: {e}")
            import traceback
            traceback.print_exc()
            return False

    def deploy_strategy(self, strategy_info: dict) -> bool:
        """Deploy validated strategy to database"""
        print(f"\nDeploying {strategy_info['name']} to database...")

        try:
            # Insert strategy
            self.db.insert_strategy(
                strategy_name=strategy_info['name'],
                source_type="CONVERTED",
                source_url=strategy_info['path'],
                backtest_return=strategy_info['original_metrics']['return_pct'],
                backtest_sharpe=strategy_info['original_metrics']['sharpe_ratio'],
                backtest_max_drawdown=strategy_info['original_metrics']['max_drawdown'],
                backtest_win_rate=strategy_info['original_metrics']['win_rate'],
                backtest_trades=strategy_info['original_metrics']['total_trades'],
                code_path=strategy_info['path']
            )

            # Add token assignment
            data_file_path = project_root / strategy_info['data_file']
            self.db.add_strategy_token(
                strategy_name=strategy_info['name'],
                token=strategy_info['token'],
                timeframe=strategy_info['timeframe'],
                data_file=str(data_file_path),
                backtest_return=strategy_info['original_metrics']['return_pct'],
                backtest_sharpe=strategy_info['original_metrics']['sharpe_ratio'],
                backtest_trades=strategy_info['original_metrics']['total_trades'],
                is_primary=True
            )

            # Mark as validated
            self.db.update_strategy_token_validation(
                strategy_name=strategy_info['name'],
                token=strategy_info['token'],
                timeframe=strategy_info['timeframe'],
                validation_return=strategy_info['original_metrics']['return_pct'],  # Will be updated after validation
                validation_passed=True
            )

            # Deploy
            self.db.deploy_strategy(strategy_info['name'])

            print(f"  DEPLOYED: {strategy_info['name']}")
            return True

        except Exception as e:
            print(f"  ERROR deploying: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_validation_and_deployment(self):
        """Validate and deploy all strategies"""
        print(f"\n{'='*80}")
        print(f"STEP 1: VALIDATION AND DEPLOYMENT")
        print(f"{'='*80}\n")

        deployed_count = 0
        failed_count = 0

        for strategy_info in self.strategies_to_validate:
            # Validate
            passed = self.validate_strategy(strategy_info)

            if passed:
                # Deploy
                success = self.deploy_strategy(strategy_info)
                if success:
                    deployed_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1

        print(f"\n{'='*80}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"Deployed: {deployed_count}")
        print(f"Failed: {failed_count}")

        return deployed_count > 0

    def run_paper_trading_cycle(self):
        """Run one cycle of paper trading with deployed strategies"""
        print(f"\n{'='*80}")
        print(f"STEP 2: PAPER TRADING")
        print(f"{'='*80}\n")

        # Get deployed strategies
        deployed_strategies = self.db.get_deployed_strategies()

        if not deployed_strategies:
            print("No deployed strategies found!")
            return False

        print(f"Found {len(deployed_strategies)} deployed strategies:")
        for strat in deployed_strategies:
            print(f"  - {strat['strategy_name']}")

        # Generate signals for BTC (example)
        print(f"\nGenerating signals for BTC...")

        try:
            # Import strategy agent
            sys.path.insert(0, str(project_root / "trading_modes" / "02_STRATEGY_BASED_TRADING"))
            from strategy_agent import StrategyAgent

            agent = StrategyAgent()
            signals = agent.get_signals('BTC')

            if signals and len(signals) > 0:
                print(f"\nGenerated {len(signals)} signals:")
                for signal in signals:
                    print(f"  {signal['strategy_name']}: {signal['direction']} (confidence: {signal.get('signal', 0)*100:.1f}%)")

                # Execute strongest signal
                strongest_signal = max(signals, key=lambda x: x.get('signal', 0))

                if strongest_signal['direction'] in ['BUY', 'SELL']:
                    print(f"\nExecuting: {strongest_signal['strategy_name']} - {strongest_signal['direction']}")

                    # Execute through paper trading system
                    position_size = 500 * 0.33  # 33% of balance
                    success, msg = self.paper_system.execute_trade(
                        symbol='BTC',
                        side=strongest_signal['direction'],
                        position_size_usd=position_size
                    )

                    if success:
                        print(f"\n  PAPER TRADE EXECUTED: {msg}")
                    else:
                        print(f"\n  PAPER TRADE FAILED: {msg}")
            else:
                print("No signals generated")

            return True

        except Exception as e:
            print(f"\nERROR in paper trading: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self):
        """Run complete validation and trading pipeline"""
        try:
            # Step 1: Validate and deploy
            has_deployed = self.run_validation_and_deployment()

            if not has_deployed:
                print("\nNo strategies deployed - cannot proceed to trading")
                return

            # Step 2: Run paper trading
            self.run_paper_trading_cycle()

            print(f"\n{'='*80}")
            print(f"COMPLETE - Ready for continuous trading")
            print(f"{'='*80}")
            print(f"\nNext steps:")
            print(f"1. Review paper trading results")
            print(f"2. If profitable, enable live trading in config")
            print(f"3. Run main_orchestrator.py for continuous operation")

        except KeyboardInterrupt:
            print(f"\n\nShutdown requested by user")
        except Exception as e:
            print(f"\nCRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    print(f"\nStarting at {datetime.now()}\n")

    system = StrategyValidationAndTrading()
    system.run()

    print(f"\nFinished at {datetime.now()}")


if __name__ == "__main__":
    main()
