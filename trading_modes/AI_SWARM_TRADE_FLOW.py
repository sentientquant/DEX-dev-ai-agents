#!/usr/bin/env python3
"""
AI_SWARM_TRADE_FLOW_STR - BTC, ETH, SOL ONLY
Uses ONLY Volume + Funding engines (NO RBI strategies)

NOTE: This file trades BTC, ETH, SOL ONLY (major coins, hardcoded)
      For ALTCOINS, use AI_SWARM_TRADE_FLOW.py (uses scanner)

Flow:
 ┌──────────────────┐  ┌──────────────┐
 │  Volume Agent    │  │ Funding Agent│
 │  (Statistical)   │  │ (Rule-based) │
 │  <100ms          │  │ <100ms       │
 └────────┬─────────┘  └────────┬─────┘
          │                     │
          └─────────────────────┘
                    ↓
           ┌─────────────────┐
           │ Fusion Layer    │
           │ (Decision Logic)│
           │ <1ms            │
           └────────┬────────┘
                    ↓
           ┌─────────────────┐
           │ Dynamic Risk    │ ← ACTUAL SYSTEM
           │ + Order Manager │    (Evidence-based)
           │ <10ms           │
           └────────┬────────┘
                    ↓
              EXECUTE TRADES

See: trading_modes/COMPLETE_SYSTEM_DOCUMENTATION.md for full details
Run: python trading_modes/AI_SWARM_TRADE_FLOW.py --mode PAPER
"""

import sys
import time
from pathlib import Path
from datetime import datetime
# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text
from typing import Dict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_modes.core.signal_bus import get_signal_bus
from trading_modes.core.arbiter import DeterministicArbiter
from src.agents.master_trading_agent_two_engine import run_trading_cycle
from src.exchange_manager import ExchangeManager
from risk_management.trading_database import get_trading_db
from risk_management.intelligent_position_manager import IntelligentPositionManager
from risk_management.dynamic_risk_engine import DynamicRiskEngine
from order_management.dynamic_order_manager import DynamicOrderManager
import pandas as pd

cprint("\n" + "="*80, "cyan", attrs=['bold'])
cprint("AI_SWARM_TRADE_FLOW", "cyan", attrs=['bold'])
cprint("Volume + Funding Engines + Dynamic Risk/Order Systems", "cyan")
cprint("="*80 + "\n", "cyan")


class AI_SwarmTradeFlow:
    """
    AI Swarm Trade Flow with ACTUAL dynamic systems

    Flow:
    1. Run Volume + Funding engines (generates signals to Signal Bus)
    2. Arbiter combines signals (weighted voting, NO AI)
    3. Dynamic Risk Engine (regime detection, token scoring, position sizing)
    4. Dynamic Order Manager (momentum-aware SL/TP with OCO)
    5. Execute via ExchangeManager
    6. Monitor via IntelligentPositionManager
    """

    def __init__(self, config: Dict):
        self.config = config
        self.mode = config.get('mode', 'PAPER')
        self.exchange = config.get('exchange', 'BINANCE')
        self.check_interval_minutes = config.get('check_interval_minutes', 15)

        # Components
        self.signal_bus = get_signal_bus()
        self.arbiter = DeterministicArbiter(config.get('arbiter_config'))
        self.db = get_trading_db()

        # ACTUAL ADVANCED SYSTEMS
        self.risk_engine = DynamicRiskEngine()
        self.order_manager = DynamicOrderManager()

        # Exchange manager
        try:
            self.exchange_manager = ExchangeManager(exchange=self.exchange)
            cprint(f"✅ ExchangeManager initialized: {self.exchange}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize exchange: {e}", "red")
            cprint("   Continuing in PAPER mode only", "yellow")
            self.mode = 'PAPER'
            self.exchange_manager = None

        # Position manager - uses different interface, monitoring via database
        self.position_manager = None

        cprint(f"\n{'='*80}", "cyan")
        cprint("AI SWARM TRADE FLOW INITIALIZED", "cyan", attrs=['bold'])
        cprint(f"{'='*80}", "cyan")
        print(f"Mode: {self.mode}")
        print(f"Exchange: {self.exchange}")
        print(f"Check Interval: {self.check_interval_minutes} minutes")
        cprint(f"{'='*80}\n", "cyan")

    def get_account_status(self):
        """
        Get current balance and PnL

        Returns real-time balance:
        - LIVE mode: Fetches actual Binance USDT balance
        - PAPER mode: Tracks starting balance + PnL from database
        """
        try:
            from risk_management.binance_truth_paper_trading import BinanceTruthAPI

            # Calculate PnL from closed trades
            all_trades = self.db.get_all_trades(mode=self.mode)

            total_pnl = 0.0
            winning_trades = 0
            losing_trades = 0

            for trade in all_trades:
                if trade.get('status') == 'CLOSED' and trade.get('pnl_usd') is not None:
                    pnl = float(trade.get('pnl_usd', 0))
                    total_pnl += pnl
                    if pnl > 0:
                        winning_trades += 1
                    elif pnl < 0:
                        losing_trades += 1

            total_trades = winning_trades + losing_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

            # Determine current balance based on mode
            if self.mode == 'LIVE':
                # LIVE: Fetch real Binance USDT balance
                real_balance = BinanceTruthAPI.get_usdt_balance()
                if real_balance is not None:
                    current_balance = real_balance
                else:
                    # Fallback if API keys not configured
                    cprint("  [WARN] LIVE mode but Binance API keys not configured - using PAPER balance tracking", "yellow")
                    starting_balance = self.config.get('starting_balance', 10000.0)
                    current_balance = starting_balance + total_pnl
            else:
                # PAPER: Track balance from starting point + PnL
                starting_balance = self.config.get('starting_balance', 10000.0)
                current_balance = starting_balance + total_pnl

            return {
                'current_balance': current_balance,
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate
            }
        except Exception as e:
            cprint(f"  [ERROR] Failed to get account status: {e}", "red")
            return {
                'current_balance': 10000.0,
                'total_pnl': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0
            }

    def run_cycle(self, symbols):
        """Run one complete cycle"""
        cycle_start = datetime.now()
        account_status = self.get_account_status()

        cprint(f"\n{'='*80}", "cyan", attrs=['bold'])
        cprint("AI SWARM FLOW - CYCLE START", "cyan", attrs=['bold'])
        cprint(f"Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}", "cyan")
        cprint(f"Mode: {self.mode}", "cyan")

        balance_color = "green" if account_status['total_pnl'] >= 0 else "red"
        cprint(f"Balance: ${account_status['current_balance']:,.2f} | PnL: ${account_status['total_pnl']:+,.2f}", balance_color, attrs=['bold'])

        if account_status['total_trades'] > 0:
            cprint(f"Trades: {account_status['total_trades']} ({account_status['winning_trades']}W/{account_status['losing_trades']}L) | Win Rate: {account_status['win_rate']:.1f}%", "cyan")

        cprint(f"{'='*80}\n", "cyan", attrs=['bold'])

        try:
            # Step 1: Run Volume + Funding engines
            cprint("[1/4] Running Volume + Funding Engines...", "yellow")
            run_trading_cycle()

            # Step 2: Arbitrate signals
            cprint("\n[2/4] Arbitrating Signals (Deterministic - No AI)...", "yellow")
            results = {}
            for symbol in symbols:
                result = self.arbiter.arbitrate(symbol, "15m")
                if result.action not in ['NEUTRAL', 'WAIT']:
                    cprint(f"  ✅ {symbol}: {result.action} ({result.confidence:.1f}%)", "green")
                    cprint(f"     {result.reasoning}", "white")
                else:
                    cprint(f"  ⏸️  {symbol}: {result.action} - {result.reasoning}", "yellow")
                results[symbol] = result

            # Step 3: Execute with dynamic systems
            cprint("\n[3/4] Executing with Dynamic Risk/Order Systems...", "yellow")
            self._execute_trades_dynamic(results)

            # Step 4: Monitor positions
            cprint("\n[4/4] Monitoring Positions...", "yellow")
            if self.position_manager:
                self.position_manager.monitor_all_positions()
                cprint("  ✅ Position monitoring complete", "green")
            else:
                # Fallback to database query
                open_positions = self.db.get_open_trades(mode=self.mode)
                if open_positions:
                    cprint(f"  Monitoring {len(open_positions)} positions", "green")
                    for pos in open_positions:
                        cprint(f"    • {pos['symbol']}: ${pos['position_size_usd']:.2f}", "white")
                else:
                    cprint("  No open positions", "white")

        except Exception as e:
            cprint(f"\n❌ Cycle error: {e}", "red")
            import traceback
            cprint(f"{traceback.format_exc()}", "red")

        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()

        cprint(f"{'='*80}", "cyan", attrs=['bold'])
        cprint(f"CYCLE COMPLETE - Duration: {duration:.1f}s", "cyan", attrs=['bold'])
        cprint(f"{'='*80}\n", "cyan", attrs=['bold'])

    def _execute_trades_dynamic(self, arbitration_results: Dict):
        """Execute trades using ACTUAL dynamic systems (same as RBI flow)"""
        executed_count = 0
        skipped_count = 0

        # Get current portfolio equity
        equity_usd = self.config.get('equity_usd', 10000.0)

        # Get PnL history from database
        pnl_history_raw = self.db.get_pnl_history(mode=self.mode, days=30)
        if pnl_history_raw:
            pnl_history = pd.DataFrame(pnl_history_raw)
        else:
            pnl_history = pd.DataFrame({'timestamp': [], 'pnl_usd': []})

        # CRITICAL: Get all open trades to prevent duplicate positions
        open_trades = self.db.get_open_trades(mode=self.mode)
        open_symbols = {trade['symbol'] for trade in open_trades}

        if open_symbols:
            cprint(f"\n  📌 Open positions: {', '.join(open_symbols)}", "yellow")

        for symbol, result in arbitration_results.items():
            if result.action in ['BUY', 'SELL'] and result.confidence >= 70:
                cprint(f"\n  🎯 Processing {result.action} for {symbol}...", "cyan")

                # CRITICAL: Skip if token already has an open trade
                if symbol in open_symbols:
                    cprint(f"     ⚠️  SKIPPED - {symbol} already has an OPEN trade", "red", attrs=['bold'])
                    cprint(f"     💡 Waiting for existing position to close before opening new trade", "yellow")
                    skipped_count += 1
                    continue

                try:
                    # Get OHLCV data from Binance (REAL data)
                    from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                    ohlcv = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe='15m', days_back=21)  # 500+ candles for production-grade analysis

                    if ohlcv is None or len(ohlcv) < 50:
                        cprint(f"     ⚠️  Insufficient OHLCV data for {symbol}", "yellow")
                        continue

                    entry_price = float(ohlcv['close'].iloc[-1])

                    # Update market regime
                    regime, regime_config = self.risk_engine.regime_detector.detect_regime(ohlcv)
                    cprint(f"     📊 Market Regime: {regime.value}", "white")

                    # Score token risk from Binance
                    token_data = BinanceTruthAPI.token_overview(symbol)
                    volume_24h_usd = token_data.get('volume_24h_usd', 1_000_000)
                    market_cap_usd = token_data.get('market_cap_usd', 100_000_000)
                    avg_spread_bps = token_data.get('spread_bps', 10)

                    token_profile = self.risk_engine.token_scorer.compute_risk_score(
                        symbol, ohlcv, volume_24h_usd, market_cap_usd, avg_spread_bps
                    )
                    cprint(f"     🎯 Token Risk Score: {token_profile.risk_score:.2f}", "white")

                    # Update dynamic limits
                    self.risk_engine.update_limits(equity_usd, pnl_history)

                    # Calculate position size
                    position_size_usd, _, _ = self.risk_engine.position_sizer.compute_position_size(
                        equity_usd=equity_usd,
                        entry_price=entry_price,
                        token_profile=token_profile,
                        regime_config=regime_config,
                        min_trade_usd=self.config.get('min_trade_usd', 100)
                    )

                    # Apply arbiter size_multiplier
                    position_size_usd *= result.size_multiplier

                    cprint(f"     💰 Position Size: ${position_size_usd:.2f}", "white")
                    cprint(f"     📍 Entry: ${entry_price:.6f}", "white")

                    # Create OrderPlan with dynamic SL/TP
                    order_plan = self.order_manager.calculate_order_plan(
                        symbol=symbol,
                        entry_price=entry_price,
                        position_size_usd=position_size_usd,
                        direction=result.action,
                        token_profile=token_profile,
                        regime=regime,
                        ohlcv_data=ohlcv,
                        use_support_resistance=True
                    )

                    cprint(f"     🛑 Stop Loss: ${order_plan.stop_loss.price:.6f} ({order_plan.stop_loss.rationale})", "red")
                    cprint(f"     🎯 Take Profit 1: ${order_plan.take_profits[0].price:.6f} ({order_plan.take_profits[0].allocation_pct:.0f}%)", "green")

                    # Execute
                    if self.exchange_manager and self.mode == 'LIVE':
                        if result.action == 'BUY':
                            order = self.exchange_manager.market_buy(symbol, position_size_usd)
                        else:
                            order = self.exchange_manager.market_sell(symbol, position_size_usd)
                        cprint(f"     ✅ LIVE order executed", "green")
                    else:
                        cprint(f"     📝 PAPER trade logged", "cyan")
                        self.db.log_trade(
                            mode=self.mode,
                            symbol=symbol,
                            direction=result.action,
                            entry_price=entry_price,
                            position_size_usd=position_size_usd,
                            stop_loss=order_plan.stop_loss.price,
                            take_profit=order_plan.take_profits[0].price,
                            confidence=result.confidence,
                            metadata={
                                'regime': regime.value,
                                'token_risk_score': token_profile.risk_score,
                                'order_plan': order_plan.__dict__
                            }
                        )

                    executed_count += 1

                except Exception as e:
                    cprint(f"     ❌ Execution failed: {e}", "red")

        # Summary
        if skipped_count > 0:
            cprint(f"\n  Executed: {executed_count} | Skipped (duplicate): {skipped_count}\n", "cyan", attrs=['bold'])
        else:
            cprint(f"\n  Executed {executed_count} trades using DYNAMIC systems\n", "cyan", attrs=['bold'])

    def run_continuous(self, symbols):
        """Run continuous trading loop"""
        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                cprint(f"[CYCLE #{cycle_count}]", "cyan", attrs=['bold'])

                self.run_cycle(symbols)

                cprint(f"😴 Sleeping {self.check_interval_minutes} minutes...\n", "yellow")
                time.sleep(self.check_interval_minutes * 60)

        except KeyboardInterrupt:
            cprint(f"\n\n{'='*80}", "red", attrs=['bold'])
            cprint("SHUTDOWN", "red", attrs=['bold'])
            cprint(f"Completed {cycle_count} cycles\n", "white")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Swarm Trade Flow")
    parser.add_argument('--mode', choices=['PAPER', 'LIVE'], default='PAPER')
    parser.add_argument('--exchange', default='BINANCE')
    parser.add_argument('--interval', type=int, default=15, help='Minutes')
    parser.add_argument('--symbols', nargs='+', default=['BTC', 'ETH', 'SOL'])
    parser.add_argument('--once', action='store_true')

    args = parser.parse_args()

    config = {
        'mode': args.mode,
        'exchange': args.exchange,
        'check_interval_minutes': args.interval,
        'starting_balance': 10000.0,  # Starting balance for tracking
        'equity_usd': 10000,
        'min_trade_usd': 100,
        'arbiter_config': {
            'min_confidence': 70.0,
            'source_weights': {
                'FUSION': 1.0,
                'VOLUME_ENGINE': 0.8,
                'FUNDING_ENGINE': 0.8
            }
        }
    }

    cprint(f"Mode: {args.mode}", "white")
    cprint(f"Exchange: {args.exchange}", "white")
    cprint(f"Symbols: {', '.join(args.symbols)}", "white")
    cprint(f"Interval: {args.interval} minutes\n", "white")

    flow = AI_SwarmTradeFlow(config)

    if args.once:
        flow.run_cycle(args.symbols)
    else:
        flow.run_continuous(args.symbols)
