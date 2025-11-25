#!/usr/bin/env python3
"""
Paper Trading with Full Risk Management

FLOW (as per user request):
1. Generate signals using deployed strategies
2. If BUY/SELL signal → place order on PAPER TRADING
3. Monitor with FULL RISK MANAGEMENT
4. Track performance for BINANCE LIVE decision

NO PLACEHOLDERS - PERMANENT SOLUTION
"""

import os
import sys
import io
from pathlib import Path
from datetime import datetime
import importlib.util
import pandas as pd
import numpy as np

# Fix Windows encoding (only if not already wrapped)
if os.name == 'nt' and not isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass  # Already wrapped or not needed

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from risk_management.trading_database import get_trading_db
from risk_management.integrated_paper_trading import IntegratedPaperTradingSystem


class PaperTradingWithRisk:
    """Paper trading with full risk management and monitoring"""

    def __init__(self):
        self.db = get_trading_db()
        self.paper_system = IntegratedPaperTradingSystem(
            balance_usd=500.0,  # Start with $500 paper balance
            max_positions=3
        )

        # Risk parameters (as per user's config requirements)
        self.max_position_size_usd = 100.0  # Max $100 per position
        self.max_loss_per_trade_pct = 5.0   # Max 5% loss per trade
        self.min_confidence = 70             # Minimum 70% confidence to trade

    def load_strategy(self, strategy_path: str, strategy_name: str):
        """Load strategy module from file path"""
        spec = importlib.util.spec_from_file_location(strategy_name, strategy_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the strategy class (should inherit from BaseStrategy)
        for item_name in dir(module):
            item = getattr(module, item_name)
            if isinstance(item, type) and item_name != 'BaseStrategy':
                if hasattr(item, 'generate_signals'):
                    return item()

        raise ValueError(f"No strategy class found in {strategy_path}")

    def get_binance_data(self, symbol: str, timeframe: str, limit: int = 1000):
        """Get real Binance data for the symbol and timeframe"""
        import ccxt

        exchange = ccxt.binance({
            'enableRateLimit': True,
        })

        # Map timeframes to CCXT format
        timeframe_map = {
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }

        ccxt_timeframe = timeframe_map.get(timeframe, '1h')

        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, ccxt_timeframe, limit=limit)

        # Convert to DataFrame with CAPITAL column names (strategies expect this)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        return df

    def generate_signal(self, strategy, token: str, timeframe: str):
        """Generate trading signal using strategy"""

        print(f"\n{'='*80}")
        print(f"GENERATING SIGNAL: {strategy.name}")
        print(f"Token: {token} | Timeframe: {timeframe}")
        print(f"{'='*80}")

        try:
            # Get real Binance data
            symbol = f"{token}/USDT"
            market_data = self.get_binance_data(symbol, timeframe, limit=1000)

            print(f"  Market data fetched: {len(market_data)} candles")
            print(f"  Current price: ${market_data['Close'].iloc[-1]:.2f}")

            # Generate signal
            signal = strategy.generate_signals(token, market_data)

            print(f"\n  SIGNAL GENERATED:")
            print(f"    Action: {signal['action']}")
            print(f"    Confidence: {signal['confidence']}%")
            print(f"    Reasoning: {signal['reasoning']}")

            return signal, market_data['Close'].iloc[-1]

        except Exception as e:
            print(f"  ERROR generating signal: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None

    def execute_paper_trade(self, signal, current_price: float, token: str, strategy_name: str):
        """Execute trade on paper trading system with risk management"""

        if signal is None or signal['action'] == 'NOTHING':
            print(f"  No trade executed (signal: {signal['action'] if signal else 'None'})")
            return False

        # Risk check 0: Check if we already have an open position for this token (PREVENT DUPLICATES)
        open_trades = self.db.get_open_trades(mode='paper')
        for trade in open_trades:
            if trade['symbol'] == token and trade['side'] == signal['action']:
                print(f"  RISK BLOCK: Already have open {signal['action']} position for {token}")
                print(f"    Existing Trade ID: {trade['trade_id']}")
                print(f"    Entry Price: ${trade['entry_price']:.2f}")
                print(f"    Position Size: ${trade['position_size_usd']:.2f}")
                return False

        # Risk check 1: Confidence threshold
        if signal['confidence'] < self.min_confidence:
            print(f"  RISK BLOCK: Confidence {signal['confidence']}% < {self.min_confidence}% threshold")
            return False

        # Risk check 2: Position size limit
        position_size = min(self.max_position_size_usd, self.paper_system.paper_trader.balance * 0.2)  # Max 20% of balance

        print(f"\n  {'='*80}")
        print(f"  EXECUTING PAPER TRADE")
        print(f"  {'='*80}")
        print(f"    Symbol: {token}/USDT")
        print(f"    Side: {signal['action']}")
        print(f"    Entry Price: ${current_price:.2f}")
        print(f"    Position Size: ${position_size:.2f}")
        print(f"    Confidence: {signal['confidence']}%")

        # Calculate stop loss and take profit
        if signal['action'] == 'BUY':
            stop_loss = current_price * 0.95  # 5% stop loss
            take_profit = current_price * 1.10  # 10% take profit
        elif signal['action'] == 'SELL':
            stop_loss = current_price * 1.05  # 5% stop loss (higher for short)
            take_profit = current_price * 0.90  # 10% take profit (lower for short)
        else:
            print(f"  ERROR: Invalid action {signal['action']}")
            return False

        print(f"    Stop Loss: ${stop_loss:.2f}")
        print(f"    Take Profit: ${take_profit:.2f}")

        # Execute on paper trading system
        try:
            success, message = self.paper_system.execute_trade(
                symbol=token,  # Just the token symbol (e.g., 'BTC')
                side=signal['action'],  # 'BUY' or 'SELL'
                position_size_usd=position_size,
                strategy_name=strategy_name  # Store strategy name in database
            )

            if success:
                print(f"  ✅ PAPER TRADE EXECUTED SUCCESSFULLY!")
                print(f"    {message}")
                return True
            else:
                print(f"  ❌ PAPER TRADE FAILED: {message}")
                return False

        except Exception as e:
            print(f"  ERROR executing paper trade: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def monitor_positions(self):
        """Monitor all open paper trading positions with risk management"""

        print(f"\n{'='*80}")
        print(f"MONITORING PAPER TRADING POSITIONS")
        print(f"{'='*80}")

        # Get open positions from database
        open_positions = self.db.get_open_trades(mode='paper')

        if not open_positions:
            print("  No open positions")
            return

        print(f"  Open Positions: {len(open_positions)}")
        print(f"  Paper Balance: ${self.paper_system.paper_trader.balance:.2f}")

        for pos in open_positions:
            print(f"\n  Position: {pos['symbol']}")
            print(f"    Side: {pos['side']}")
            print(f"    Entry: ${pos['entry_price']:.2f}")
            print(f"    Size: ${pos['position_size_usd']:.2f}")
            print(f"    Stop Loss: ${pos['stop_loss']:.2f}")
            # Handle both single take_profit and multi-level tp1/tp2/tp3
            if 'take_profit' in pos and pos['take_profit']:
                print(f"    Take Profit: ${pos['take_profit']:.2f}")
            elif 'tp1_price' in pos and pos['tp1_price']:
                print(f"    TP1: ${pos['tp1_price']:.2f} ({pos.get('tp1_pct', 0):.1f}%)")
                print(f"    TP2: ${pos.get('tp2_price', 0):.2f} ({pos.get('tp2_pct', 0):.1f}%)")
                print(f"    TP3: ${pos.get('tp3_price', 0):.2f} ({pos.get('tp3_pct', 0):.1f}%)")
            print(f"    Strategy: {pos.get('strategy_name', 'N/A')}")

            # Calculate and display REAL-TIME PnL
            try:
                # Get current price from Binance
                symbol = f"{pos['symbol']}/USDT"
                current_data = self.get_binance_data(symbol, '1h', limit=1)
                current_price = current_data['Close'].iloc[-1]

                # Calculate unrealized PnL
                if pos['side'] == 'BUY':
                    pnl_pct = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
                else:  # SELL (short)
                    pnl_pct = ((pos['entry_price'] - current_price) / pos['entry_price']) * 100

                pnl_usd = (pnl_pct / 100) * pos['position_size_usd']

                # Color-coded display
                pnl_color = "green" if pnl_usd >= 0 else "red"
                pnl_symbol = "+" if pnl_usd >= 0 else ""

                print(f"    Current Price: ${current_price:.2f}")
                print(f"    Unrealized PnL: ${pnl_symbol}{pnl_usd:.2f} ({pnl_symbol}{pnl_pct:.2f}%)")

                # Check if TP or SL hit
                if pos['side'] == 'BUY':
                    if current_price >= pos.get('tp1_price', float('inf')):
                        print(f"    🎯 TP1 HIT! Target: ${pos['tp1_price']:.2f}")
                    elif current_price <= pos['stop_loss']:
                        print(f"    🛑 STOP LOSS HIT! SL: ${pos['stop_loss']:.2f}")
                else:  # SELL
                    if current_price <= pos.get('tp1_price', 0):
                        print(f"    🎯 TP1 HIT! Target: ${pos['tp1_price']:.2f}")
                    elif current_price >= pos['stop_loss']:
                        print(f"    🛑 STOP LOSS HIT! SL: ${pos['stop_loss']:.2f}")

            except Exception as e:
                print(f"    ERROR calculating PnL: {str(e)}")

    def get_performance_summary(self):
        """Get paper trading performance summary"""

        print(f"\n{'='*80}")
        print(f"PAPER TRADING PERFORMANCE SUMMARY")
        print(f"{'='*80}")

        # Get closed paper trades from database (status = 'closed')
        all_trades = self.db.get_trades_by_strategy('', limit=1000)  # Get all trades
        closed_trades = [t for t in all_trades if t.get('status') == 'closed' and t.get('mode') == 'paper']

        if not closed_trades:
            print("  No closed trades yet")
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'ready_for_live': False
            }

        total_trades = len(closed_trades)
        winning_trades = sum(1 for t in closed_trades if t['pnl_usd'] > 0)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = sum(t['pnl_usd'] for t in closed_trades)

        print(f"  Total Trades: {total_trades}")
        print(f"  Winning Trades: {winning_trades}")
        print(f"  Win Rate: {win_rate:.2f}%")
        print(f"  Total PnL: ${total_pnl:.2f}")
        print(f"  Current Balance: ${self.paper_system.paper_trader.balance:.2f}")

        # Decision criteria for BINANCE LIVE
        ready_for_live = (
            total_trades >= 5 and  # At least 5 trades
            win_rate >= 50.0 and   # At least 50% win rate
            total_pnl > 0          # Profitable overall
        )

        print(f"\n  READY FOR BINANCE LIVE: {'YES ✅' if ready_for_live else 'NO ❌'}")

        if not ready_for_live:
            print(f"    Criteria:")
            print(f"      - Trades >= 5: {'✅' if total_trades >= 5 else '❌'} ({total_trades})")
            print(f"      - Win Rate >= 50%: {'✅' if win_rate >= 50 else '❌'} ({win_rate:.2f}%)")
            print(f"      - Total PnL > 0: {'✅' if total_pnl > 0 else '❌'} (${total_pnl:.2f})")

        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'ready_for_live': ready_for_live
        }

    def run(self):
        """Run paper trading with deployed strategies"""

        print(f"\n{'='*80}")
        print(f"PAPER TRADING WITH FULL RISK MANAGEMENT")
        print(f"{'='*80}")
        print(f"Started: {datetime.now()}")
        print(f"Paper Balance: ${self.paper_system.paper_trader.balance:.2f}")
        print(f"Max Positions: {self.paper_system.paper_trader.max_positions}")
        print(f"Max Position Size: ${self.max_position_size_usd:.2f}")

        # Get deployed strategies from database
        deployed = self.db.get_deployed_strategies()

        if not deployed:
            print("\n❌ No deployed strategies found!")
            print("   Please run deploy_strategies_direct.py first")
            return

        print(f"\nDeployed Strategies: {len(deployed)}")
        for strat in deployed:
            print(f"  - {strat['strategy_name']}")

        # Generate signals for each strategy
        for strat in deployed:
            strategy_name = strat['strategy_name']
            code_path = strat['code_path']

            # Extract token and timeframe from strategy name
            # Format: BTC_5m_VolatilityOutlier_1025pct
            parts = strategy_name.split('_')
            token = parts[0]  # BTC
            timeframe = parts[1]  # 5m

            print(f"\n{'='*80}")
            print(f"STRATEGY: {strategy_name}")
            print(f"{'='*80}")

            try:
                # Load strategy
                strategy = self.load_strategy(code_path, strategy_name)
                print(f"  Strategy loaded: {strategy.name}")

                # Generate signal
                signal, current_price = self.generate_signal(strategy, token, timeframe)

                # Execute paper trade if signal generated
                if signal and signal['action'] != 'NOTHING':
                    self.execute_paper_trade(signal, current_price, token, strategy_name)

            except Exception as e:
                print(f"  ERROR processing strategy: {str(e)}")
                import traceback
                traceback.print_exc()

        # Monitor positions
        self.monitor_positions()

        # Get performance summary
        performance = self.get_performance_summary()

        print(f"\n{'='*80}")
        print(f"PAPER TRADING SESSION COMPLETE")
        print(f"{'='*80}")
        print(f"Ended: {datetime.now()}")

        return performance


if __name__ == "__main__":
    paper_trading = PaperTradingWithRisk()
    paper_trading.run()
