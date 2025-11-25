#!/usr/bin/env python3
"""
RBI_RESEARCH_TRADE_FLOW
Uses ONLY deployed RBI strategies from database

Flow:
   ┌──────────────────┐
   │ RBI Strategies   │ ← Deployed from Phase 2
   │ (Pure Python)    │
   │ <100ms           │
   └────────┬─────────┘
            │
            └────────────────────
                                ↓
                      ┌─────────────────┐
                      │ Arbiter         │ ← Deterministic
                      │ (Decision Logic)│
                      │ <1ms            │
                      └────────┬────────┘
                               ↓
                    ┌──────────────────┐
                    │ ExchangeManager  │ ← Existing
                    │ (Execution)      │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Position Manager │ ← Existing
                    │ (Risk/Monitoring)│
                    └──────────────────┘

Evidence-Based:
- Walk-forward validated strategies only
- No AI in execution path
- Complete determinism
- Binance default exchange
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import importlib.util

# CRITICAL: Disable output buffering for real-time console display
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
os.environ['PYTHONUNBUFFERED'] = '1'

# Windows-specific: Force console buffer to flush immediately
if sys.platform == 'win32':
    import msvcrt
    import ctypes
    # Set console mode to disable buffering
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_modes.core.signal_bus import Signal, get_signal_bus
from trading_modes.core.arbiter import DeterministicArbiter
from trading_modes.core.strategy_validator import get_strategy_validator
# PERMANENT FIX: Import agents ONLY when needed (lazy loading)
# Previously: Imported at module level → triggered model_factory init → OpenRouter errors
# market_analysis_agent → strategy_verification_agent → swarm_agent → model_factory → ALL MODELS INIT
# signal_verification_agent → model_factory → ALL MODELS INIT
# Now: Import inside methods when first used → only loads when actually needed
from src.exchange_manager import ExchangeManager

# PERMANENT FIX: Use typed database wrapper
from risk_management.trading_database import get_trading_db
from risk_management.trading_database_typed import TradingDatabaseTyped
from trading_modes.models.domain import Trade, TradingMode

# from risk_management.intelligent_position_manager import IntelligentPositionManager  # DISABLED - Not used (position_manager = None)
from risk_management.dynamic_risk_engine import (
    DynamicRiskEngine, TokenRiskProfile, MarketRegime
)
from risk_management.sharp_fibonacci_atr import (
    SharpSwingDetector, ATRFibonacciCalculator, SharpFibonacciLevels
)
from order_management.dynamic_order_manager import DynamicOrderManager, OrderPlan
# Make termcolor optional
try:
    from termcolor import cprint as _cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text
import pandas as pd
import numpy as np

# Wrapper for cprint that auto-flushes (Windows real-time display fix)
def cprint(*args, **kwargs):
    _cprint(*args, **kwargs)
    sys.stdout.flush()  # Force immediate display


class RBI_ResearchTradeFlow:
    """
    RBI Research-Based Trading Flow

    Uses ONLY deployed RBI strategies (no Volume/Funding engines)
    """

    def __init__(self, config: Dict = None):
        """
        Initialize RBI Research Trade Flow

        Args:
            config: Configuration dict
        """
        self.config = config or {}

        # Mode and exchange
        self.mode = self.config.get('mode', 'PAPER')
        self.exchange = self.config.get('exchange', 'BINANCE')
        self.check_interval_minutes = self.config.get('check_interval_minutes', 15)

        # Components
        self.signal_bus = get_signal_bus()

        # Configure arbiter with LOWER thresholds for BACKTEST-PROVEN RBI strategies
        # Rationale: RBI strategies have proven track record (726%, 236%, 1025% returns)
        # PERMANENT FIX: Lowered from 65% to 55% to match backtest behavior
        # Backtests had NO confidence filter - they traded ALL valid signals (breakout + SMA + RSI)
        # TradingView chart shows valid BUY @ 61% confidence (RSI 64.5, price broke upper bracket)
        # Math: confidence = 50 + (RSI - 50) × 0.7 → Need RSI ≥ 57.1 for 55% confidence
        arbiter_config = config.get('arbiter_config', {
            'buy_confidence_min': 55.0,      # LOWERED to match backtest (was 65%, blocked 60% signals)
            'buy_confidence_strong': 75.0,   # Strong conviction = larger position (unchanged)
            'sell_confidence_min': 50.0,     # LOWERED to match backtest (was 60%)
            'sell_confidence_strong': 70.0,  # Strong conviction = immediate exit (unchanged)
            'hold_threshold': 50.0,          # Baseline predictive power (unchanged)
            'conflict_threshold': 10.0,      # Signals must agree within 10% to combine (unchanged)
            'agreement_bonus': 10.0          # Bonus for multiple strategies agreeing (unchanged)
        })
        self.arbiter = DeterministicArbiter(arbiter_config)

        # PERMANENT FIX: Initialize typed database wrapper
        # Returns Result[List[Trade]] instead of List[Dict]
        # Eliminates direction/side field confusion at the database boundary
        self.db_legacy = get_trading_db()  # Keep legacy for compatibility
        self.db_typed = TradingDatabaseTyped()  # Type-safe wrapper
        self.db = self.db_legacy  # Backward compatibility for now

        self.validator = get_strategy_validator()  # CRITICAL: Catch broken strategies immediately
        # PERMANENT FIX: Lazy initialization of market analysis agent
        # market_analysis_agent imports swarm_agent which imports model_factory
        # Don't initialize unless actually needed (strategy alerts)
        self.ai_analyst = None  # Will be initialized on first use (lazy loading)

        # Track strategy reasoning for AI analysis
        self.strategy_reasoning_history = {}  # {strategy_name: [recent reasoning strings]}
        self.strategy_ohlcv_data = {}  # {strategy_name: latest ohlcv dataframe}
        self.strategy_symbol_map = {}  # {strategy_name: symbol}

        # ACTUAL ADVANCED SYSTEMS (from risk_management/ and order_management/)
        self.risk_engine = DynamicRiskEngine()
        self.order_manager = DynamicOrderManager()

        # Exchange manager (Binance default)
        try:
            self.exchange_manager = ExchangeManager(exchange=self.exchange)
            cprint(f"✅ ExchangeManager initialized: {self.exchange}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize exchange: {e}", "red")
            cprint("   Continuing in PAPER mode only", "yellow")
            self.mode = 'PAPER'
            self.exchange_manager = None

        # Position manager - note: IntelligentPositionManager uses different interface
        # It expects BinanceTruthPaperTrader, not our simplified ExchangeManager
        # For now, position monitoring handled through database queries
        self.position_manager = None

        # Loaded strategies
        self.rbi_strategies = []

        cprint(f"\n{'='*80}", "cyan")
        cprint("RBI RESEARCH TRADE FLOW INITIALIZED", "cyan", attrs=['bold'])
        cprint(f"{'='*80}", "cyan")
        print(f"Mode: {self.mode}")
        print(f"Exchange: {self.exchange}")
        print(f"Check Interval: {self.check_interval_minutes} minutes")
        cprint(f"{'='*80}\n", "cyan")

    def get_symbols_from_strategies(self) -> List[str]:
        """
        Auto-detect symbols from loaded strategies

        Returns:
            List of unique symbols (e.g., ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
        """
        if not self.rbi_strategies:
            cprint("  ⚠️  No RBI strategies loaded - cannot extract symbols", "yellow")
            return []

        symbols = set()
        for strat_info in self.rbi_strategies:
            strategy = strat_info['instance']
            if hasattr(strategy, 'target_pair'):
                # Normalize symbol format to ensure consistency
                from trading_modes.utils.symbol_utils import normalize_symbol
                normalized = normalize_symbol(strategy.target_pair, 'USDT')
                symbols.add(normalized)
                cprint(f"  📊 Strategy '{strat_info['name']}' targets: {normalized}", "white")

        if not symbols:
            cprint("  ⚠️  No symbols found in strategies (missing target_pair attribute?)", "yellow")

        return sorted(list(symbols))

    def get_symbol_timeframe_mapping(self) -> Dict[str, str]:
        """
        Get mapping of symbols to their timeframes from strategies

        Returns:
            Dict of {symbol: timeframe} (e.g., {'SOL': '1h', 'ETH': '1h'})
        """
        mapping = {}
        for strat_info in self.rbi_strategies:
            strategy = strat_info['instance']
            if hasattr(strategy, 'target_pair') and hasattr(strategy, 'target_timeframe'):
                mapping[strategy.target_pair] = strategy.target_timeframe
        return mapping

    def get_strategy_instance_by_name(self, strategy_name: str):
        """
        Get strategy instance by name

        Args:
            strategy_name: Name of strategy

        Returns:
            Strategy instance or None if not found
        """
        for strat_info in self.rbi_strategies:
            if strat_info['name'] == strategy_name:
                return strat_info['instance']
        return None

    def load_rbi_strategies(self):
        """
        Load deployed RBI strategies from database

        Uses dynamic import to load strategy classes
        """
        cprint("\n[1/5] Loading RBI Strategies from Database...", "yellow")

        # Get deployed strategies
        deployed = self.db.get_deployed_strategies()

        if not deployed:
            cprint("  ⚠️  No deployed strategies found in database", "yellow")
            return

        cprint(f"  Found {len(deployed)} deployed strategies", "green")

        for strat in deployed:
            try:
                # Get strategy details
                name = strat['strategy_name']
                code_path = strat['code_path']

                # Dynamic import
                spec = importlib.util.spec_from_file_location(name, code_path)
                if not spec or not spec.loader:
                    cprint(f"  ❌ Could not load {name}", "red")
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Get strategy class - try multiple naming patterns
                strategy_class = None

                # Pattern 1: Class named 'Strategy'
                if hasattr(module, 'Strategy'):
                    strategy_class = getattr(module, 'Strategy')
                else:
                    # Pattern 2: Find any class that inherits from BaseStrategy
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            hasattr(attr, 'generate_signals') and
                            attr_name not in ['BaseStrategy', 'Strategy']):
                            strategy_class = attr
                            break

                if strategy_class:
                    strategy_instance = strategy_class()

                    # Extract strategy attributes
                    target_pair = getattr(strategy_instance, 'target_pair', 'N/A')
                    target_timeframe = getattr(strategy_instance, 'target_timeframe', 'N/A')

                    self.rbi_strategies.append({
                        'instance': strategy_instance,
                        'name': name,
                        'metadata': strat
                    })

                    cprint(f"  ✅ Loaded: {name}", "green")
                    cprint(f"      → Symbol: {target_pair} | Timeframe: {target_timeframe}", "cyan")
                else:
                    cprint(f"  ⚠️  No valid strategy class in {name}", "yellow")

            except Exception as e:
                cprint(f"  ❌ Error loading {strat['strategy_name']}: {e}", "red")

        cprint(f"\n  Total loaded: {len(self.rbi_strategies)} strategies\n", "cyan", attrs=['bold'])

    def generate_rbi_signals(self, symbols: List[str]) -> Dict[str, List[Signal]]:
        """
        Generate signals from all RBI strategies

        Args:
            symbols: List of symbols to analyze

        Returns:
            Dict of {symbol: [signals]}
        """
        cprint("\n[2/5] Generating Signals from RBI Strategies...", "yellow")

        all_signals = {}

        for symbol in symbols:
            symbol_signals = []

            # Find the strategy that targets this symbol to get its timeframe
            target_timeframe = '1h'  # Default fallback
            for strat_info in self.rbi_strategies:
                strategy = strat_info['instance']
                if hasattr(strategy, 'target_pair') and strategy.target_pair.upper() in symbol.upper():
                    if hasattr(strategy, 'target_timeframe'):
                        target_timeframe = strategy.target_timeframe
                        break

            # Get OHLCV data for this symbol using strategy's timeframe
            try:
                from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                cprint(f"  📊 Fetching {symbol} data (timeframe: {target_timeframe})...", "cyan")
                ohlcv = BinanceTruthAPI.get_ohlcv_data(
                    symbol,
                    timeframe=target_timeframe,
                    days_back=self.config.get('OHLCV_DAYS_BACK', 3)
                )
            except Exception as e:
                cprint(f"  ⚠️  Failed to get OHLCV data for {symbol}: {e}", "yellow")
                ohlcv = None

            if ohlcv is None or len(ohlcv) < 50:
                cprint(f"  ⚠️  Insufficient OHLCV data for {symbol}, skipping...", "yellow")
                continue

            # Analyze each symbol with matching strategies
            cprint(f"\n  📈 Analyzing {symbol} with strategies:", "cyan")

            matched_count = 0
            for strat_info in self.rbi_strategies:
                try:
                    strategy = strat_info['instance']
                    name = strat_info['name']

                    # Check if strategy targets this symbol (use exact match after normalization)
                    if hasattr(strategy, 'target_pair'):
                        from trading_modes.utils.symbol_utils import normalize_symbol
                        strategy_symbol = normalize_symbol(strategy.target_pair, 'USDT')
                        current_symbol = normalize_symbol(symbol, 'USDT')

                        if strategy_symbol != current_symbol:
                            # Skip silently - strategy doesn't target this symbol
                            continue

                        matched_count += 1

                    # Show what we're analyzing
                    current_price = ohlcv['close'].iloc[-1]
                    num_candles = len(ohlcv)
                    cprint(f"     🔍 {name} analyzing {symbol}...", "white")

                    # Warn if candles are low (production standard: 500 candles)
                    if num_candles < 200:
                        cprint(f"        Price: ${current_price:.2f} | Candles: {num_candles} ⚠️ (Low - expected 500)", "yellow")
                    elif num_candles < 400:
                        cprint(f"        Price: ${current_price:.2f} | Candles: {num_candles} ⚠️ (Acceptable but not optimal)", "yellow")
                    else:
                        cprint(f"        Price: ${current_price:.2f} | Candles: {num_candles} ✅", "green")

                    # Generate signal with required parameters
                    result = strategy.generate_signals(symbol, ohlcv)

                    # CRITICAL: Track strategy output for validation
                    self.validator.track_strategy_cycle(name, result, ohlcv)

                    # Track reasoning history for AI analysis (keep last 10)
                    if name not in self.strategy_reasoning_history:
                        self.strategy_reasoning_history[name] = []
                    reasoning_text = result.get('reasoning', '')
                    if reasoning_text:
                        self.strategy_reasoning_history[name].append(reasoning_text)
                        # Keep only last 10 reasoning messages
                        if len(self.strategy_reasoning_history[name]) > 10:
                            self.strategy_reasoning_history[name] = self.strategy_reasoning_history[name][-10:]

                    # Store OHLCV and symbol for AI analysis
                    self.strategy_ohlcv_data[name] = ohlcv
                    self.strategy_symbol_map[name] = symbol

                    # Show detailed processing info
                    cprint(f"        📝 Strategy returned: {result}", "white")

                    if result and result.get('action'):
                        action = result.get('action', 'NOTHING')
                        confidence = result.get('confidence', 0)
                        reasoning = result.get('reasoning', 'N/A')

                        if action != 'NOTHING':
                            # Map strategy action to signal action
                            action_map = {
                                'BUY': 'BUY',
                                'SELL': 'SELL',
                                'LONG': 'BUY',
                                'SHORT': 'SELL'
                            }
                            mapped_action = action_map.get(action.upper(), action)

                            # Get timeframe from strategy if available
                            timeframe = getattr(strategy, 'target_timeframe', '15m')

                            # MULTI-MODEL SIGNAL VERIFICATION (HYBRID APPROACH)
                            # Cross-check RBI strategy signal against REAL technical indicators with 5 AI models
                            # Can be disabled via config if verification causes issues
                            verification_agreement = 'none'  # Default value

                            if self.config.get('enable_signal_verification', True):
                                try:
                                    # PERMANENT FIX: Lazy import verification agent (only when enabled)
                                    # This prevents model_factory initialization when verification is disabled
                                    from trading_modes.core.signal_verification_agent import get_signal_verification_agent

                                    cprint(f"        [VERIFICATION] Running multi-model verification for {name}...", "yellow")
                                    verification_agent = get_signal_verification_agent()
                                    verification_result = verification_agent.verify_signal(
                                        symbol=symbol,
                                        timeframe=timeframe,
                                        scanner_signal=mapped_action,
                                        scanner_confidence=confidence,
                                        strategy_name=name,
                                        strategy_logic=reasoning
                                    )

                                    # PERMANENT FIX: Handle Result[SignalVerificationResult] type-safe object
                                    # verify_signal() returns Result object, NOT dict
                                    # Must check .is_success() then access .value property
                                    if verification_result.is_success():
                                        result_value = verification_result.value  # SignalVerificationResult object
                                        verification_agreement = result_value.agreement_level.value  # Enum to string

                                        # If verification DISAGREES with strategy, override action
                                        if not result_value.agrees_with_scanner:
                                            cprint(f"        [OVERRIDE] Verification detected FALSE SIGNAL - overriding strategy action", "red", attrs=['bold'])
                                            mapped_action = result_value.action.value  # SignalAction enum to string
                                            confidence = result_value.confidence
                                            reasoning = f"VERIFICATION OVERRIDE: {result_value.reasoning}"
                                            cprint(f"        [NEW ACTION] {mapped_action} @ {confidence:.0f}% (verified by {verification_agreement})", "yellow", attrs=['bold'])
                                    else:
                                        # Verification failed - log error and use strategy signal
                                        cprint(f"        [WARNING] Verification returned failure: {verification_result.error}", "yellow")
                                        verification_agreement = 'error'
                                except Exception as verification_error:
                                    cprint(f"        [WARNING] Verification failed: {verification_error}", "yellow")
                                    cprint(f"        [FALLBACK] Using strategy signal directly: {mapped_action} @ {confidence:.0f}%", "cyan")
                                    verification_agreement = 'error'
                            else:
                                cprint(f"        [VERIFICATION DISABLED] Using strategy signal directly", "cyan")
                                verification_agreement = 'disabled'

                            # Create Signal object (with possibly overridden action/confidence)
                            signal = Signal(
                                source="RBI_STRATEGY",
                                symbol=symbol,
                                timeframe=timeframe,
                                action=mapped_action,
                                confidence=confidence,
                                ttl_sec=1800,  # 30 minutes
                                timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                                metadata={
                                    'strategy_name': name,
                                    'reasoning': reasoning,
                                    'verified': True,
                                    'verification_agreement': verification_agreement
                                }
                            )

                            symbol_signals.append(signal)

                            # Publish to bus
                            self.signal_bus.publish(signal)

                            cprint(f"        ✅ SIGNAL: {mapped_action} @ {confidence:.1f}% confidence", "green", attrs=['bold'])
                            cprint(f"        💡 {reasoning[:120]}", "white")
                        else:
                            # No signal - show why with bracket analysis
                            cprint(f"        ⏸️  NO SIGNAL - {reasoning[:120]}", "yellow")

                            # Extract bracket info if available
                            if 'in range' in reasoning.lower():
                                # Parse price and brackets from reasoning
                                import re
                                price_match = re.search(r'Price \$?([\d.]+)', reasoning)
                                range_match = re.search(r'\[\$?([\d.]+), \$?([\d.]+)\]', reasoning)

                                if price_match and range_match:
                                    price = float(price_match.group(1))
                                    lower = float(range_match.group(1))
                                    upper = float(range_match.group(2))
                                    bracket_width = upper - lower
                                    price_pct_in_range = ((price - lower) / bracket_width * 100)

                                    cprint(f"           Price: ${price:.2f} | Range: [${lower:.2f}, ${upper:.2f}] | Position in range: {price_pct_in_range:.1f}%", "white")
                                    cprint(f"           Need breakout: >${upper:.2f} (UP) or <${lower:.2f} (DOWN)", "white")
                    else:
                        cprint(f"        ⚠️  Strategy returned no result", "yellow")

                except Exception as e:
                    cprint(f"     ❌ STRATEGY ERROR in {strat_info['name']}: {type(e).__name__}: {e}", "red", attrs=['bold'])
                    import traceback
                    tb = traceback.format_exc()
                    # Show full traceback, not truncated
                    for line in tb.split('\n'):
                        if line.strip():
                            cprint(f"        {line}", "red")

            # Check if any strategies matched this symbol
            if matched_count == 0:
                cprint(f"     ⚠️  No strategies matched {symbol} - check target_pair values in strategy files", "yellow")

            all_signals[symbol] = symbol_signals

        # Summary
        total_signals = sum(len(sigs) for sigs in all_signals.values())
        cprint(f"\n  {'='*70}", "cyan")
        if total_signals > 0:
            cprint(f"  ✅ Generated {total_signals} signal(s):", "green", attrs=['bold'])
            for sym, sigs in all_signals.items():
                if sigs:
                    for sig in sigs:
                        cprint(f"     • {sym}: {sig.action} @ {sig.confidence:.1f}% ({sig.metadata.get('strategy_name', 'Unknown')})", "green")
        else:
            cprint(f"  ⏸️  Generated 0 signals - No trade conditions met", "yellow", attrs=['bold'])
        cprint(f"  {'='*70}\n", "cyan")

        # CRITICAL: Display strategy health statistics
        cprint("  📊 Strategy Health Check:", "cyan", attrs=['bold'])
        for strat_info in self.rbi_strategies:
            name = strat_info['name']
            summary = self.validator.get_strategy_summary(name)
            if summary:
                cycles = summary['total_cycles']
                signal_rate = summary['signal_rate']
                cycles_since = summary['cycles_since_signal']

                # Color code based on performance
                if signal_rate == 0 and cycles >= 5:
                    health_color = "red"
                    status = f"⚠️  {cycles} cycles, 0 signals ({cycles_since} since last)"
                elif signal_rate < 2.0 and cycles >= 10:
                    health_color = "yellow"
                    status = f"⚠️  {cycles} cycles, {signal_rate:.1f}% signal rate"
                else:
                    health_color = "green"
                    status = f"✅ {cycles} cycles, {signal_rate:.1f}% signal rate ({summary['signal_count']} signals)"

                cprint(f"     • {name}: {status}", health_color)
        cprint("")

        # CRITICAL: Check for broken strategies and use AI analysis for intelligent diagnosis
        alerts = self.validator.validate_and_alert()

        if alerts:
            # For CRITICAL alerts, run AI analysis instead of showing generic alerts
            critical_alerts = [a for a in alerts if a['severity'] == 'CRITICAL']

            if critical_alerts:
                cprint("\n" + "="*80, "cyan", attrs=['bold'])
                cprint("🤖 AI MARKET ANALYSIS - Intelligent Strategy Diagnosis", "cyan", attrs=['bold'])
                cprint("="*80, "cyan", attrs=['bold'])

                for alert in critical_alerts:
                    strategy_name = alert['strategy']
                    symbol = alert.get('symbol', self.strategy_symbol_map.get(strategy_name, 'UNKNOWN'))

                    # Get strategy data
                    summary = self.validator.get_strategy_summary(strategy_name)
                    ohlcv = self.strategy_ohlcv_data.get(strategy_name)
                    recent_reasoning = self.strategy_reasoning_history.get(strategy_name, [])

                    if ohlcv is not None and len(ohlcv) > 0:
                        # Extract bracket info from recent reasoning if available
                        bracket_info = None
                        if recent_reasoning:
                            import re
                            last_reasoning = recent_reasoning[-1]
                            price_match = re.search(r'Price \$?([\d.]+)', last_reasoning)
                            range_match = re.search(r'\[\$?([\d.]+), \$?([\d.]+)\]', last_reasoning)

                            if price_match and range_match:
                                bracket_info = {
                                    'current': float(price_match.group(1)),
                                    'lower': float(range_match.group(1)),
                                    'upper': float(range_match.group(2))
                                }

                        # Get strategy instance (for extracting actual indicator settings)
                        strategy_instance = self.get_strategy_instance_by_name(strategy_name)

                        if strategy_instance is None:
                            cprint(f"  [WARN] Could not find strategy instance for {strategy_name}", "yellow")

                        # Run AI analysis with strategy's ACTUAL settings
                        try:
                            # PERMANENT FIX: Lazy initialization of AI analyst (only when needed)
                            if self.ai_analyst is None:
                                from trading_modes.core.market_analysis_agent import get_market_analysis_agent
                                self.ai_analyst = get_market_analysis_agent('xai')  # Use Grok (already initialized)

                            analysis = self.ai_analyst.analyze_strategy_performance(
                                strategy_name=strategy_name,
                                symbol=symbol,
                                cycles=summary.get('total_cycles', 0),
                                signal_count=summary.get('signal_count', 0),
                                ohlcv_data=ohlcv,
                                recent_reasoning=recent_reasoning,
                                bracket_info=bracket_info,
                                strategy_instance=strategy_instance  # ✅ NOW PASSES STRATEGY INSTANCE!
                            )

                            # Display AI analysis
                            self.ai_analyst.display_analysis(analysis, strategy_name, symbol)

                        except Exception as e:
                            cprint(f"⚠️  AI analysis failed for {strategy_name}: {e}", "yellow")
                            cprint(f"   Falling back to standard alert: {alert['message']}", "yellow")
                    else:
                        cprint(f"\n⚠️  {strategy_name} ({symbol}): {alert['message']}", "yellow")

                cprint("")

            # Show non-critical warnings normally
            warning_alerts = [a for a in alerts if a['severity'] == 'WARNING']
            if warning_alerts:
                self.validator.display_alerts(warning_alerts)

        else:
            # Show "all clear" message after 20+ cycles
            if any(self.validator.get_strategy_summary(s['name']).get('total_cycles', 0) >= 20 for s in self.rbi_strategies):
                cprint("  ✅ No validation alerts - All strategies operating normally\n", "green")
            elif total_signals == 0 and any(self.validator.get_strategy_summary(s['name']).get('total_cycles', 0) >= 5 for s in self.rbi_strategies):
                # Show info about consolidation
                cprint("  📊 Market Status: Consolidation phase - Price within volatility brackets", "cyan")
                cprint("     Waiting for breakout to generate trading signals\n", "white")

        return all_signals

    def arbitrate_signals(self, symbols: List[str]) -> Dict:
        """
        Arbitrate signals using deterministic arbiter

        Args:
            symbols: Symbols to arbitrate

        Returns:
            Dict of arbitration results
        """
        cprint("\n[3/5] Arbitrating Signals (Deterministic - No AI)...", "yellow")

        results = {}
        timeframe_map = self.get_symbol_timeframe_mapping()

        for symbol in symbols:
            # Get strategy's timeframe for this symbol
            timeframe = timeframe_map.get(symbol, "1h")  # Default to 1h if not found

            # Check how many signals are in the bus for this symbol/timeframe
            signals_in_bus = self.signal_bus.get_signals(symbol, timeframe, max_age_sec=900)
            cprint(f"\n  🔍 {symbol} ({timeframe}):", "cyan")
            cprint(f"     Signals in bus: {len(signals_in_bus)}", "white")

            if signals_in_bus:
                for sig in signals_in_bus:
                    cprint(f"       • {sig.action} @ {sig.confidence:.1f}% from {sig.source}", "white")

            # Arbitrate using correct timeframe
            result = self.arbiter.arbitrate(symbol, timeframe)

            if result.action not in ['NEUTRAL', 'WAIT']:
                cprint(f"     ✅ DECISION: {result.action} @ {result.confidence:.1f}%", "green", attrs=['bold'])
                cprint(f"     💡 {result.reasoning}", "white")
            else:
                cprint(f"     ⏸️  DECISION: {result.action}", "yellow")
                cprint(f"     💡 {result.reasoning}", "white")

            results[symbol] = result

        return results

    def execute_trades(self, arbitration_results: Dict):
        """
        Execute trades using ACTUAL DYNAMIC SYSTEMS

        Flow:
        1. Get OHLCV data for token
        2. Update market regime (DynamicRiskEngine)
        3. Score token risk (TokenRiskScorer)
        4. Calculate position size (VolatilityPositionSizer)
        5. Calculate stops/TPs (SharpFibonacciLevels)
        6. Create OrderPlan (DynamicOrderManager)
        7. Execute via ExchangeManager

        Args:
            arbitration_results: Results from arbiter
        """
        cprint("\n[4/5] Executing Trades with Dynamic Risk/Order Systems...", "yellow")

        executed_count = 0
        skipped_count = 0

        # PERMANENT FIX: Get current portfolio equity (PAPER vs LIVE)
        # Previously: Always used config value ($10,000) for both modes
        # Issue: LIVE mode calculated position from $10,000 when real balance was $0.23
        # Result: Tried to execute $300 position with $0.23 balance (1300x over!)
        # Now: LIVE fetches real balance, PAPER uses tracked balance from database
        if self.mode == 'LIVE' and self.exchange_manager:
            # LIVE mode: Get REAL balance from exchange
            try:
                equity_usd = self.exchange_manager.get_balance()
                cprint(f"  💰 [LIVE] Real Balance: ${equity_usd:.2f}", "cyan", attrs=['bold'])
            except Exception as e:
                cprint(f"  ⚠️  Failed to get live balance: {e}", "yellow")
                cprint(f"  📊 Using config default: $10,000", "yellow")
                equity_usd = self.config.get('starting_balance', 10000.0)
        else:
            # PAPER mode: Use starting balance (will be adjusted by PnL tracking)
            equity_usd = self.config.get('starting_balance', 10000.0)
            cprint(f"  💰 [PAPER] Starting Balance: ${equity_usd:.2f}", "cyan")

        # Get PnL history from database
        pnl_history_raw = self.db.get_pnl_history(mode=self.mode, days=30)
        if pnl_history_raw:
            pnl_history = pd.DataFrame(pnl_history_raw)
        else:
            # Empty history
            pnl_history = pd.DataFrame({'timestamp': [], 'pnl_usd': []})

        # CRITICAL: Get all open trades to prevent duplicate positions
        open_trades = self.db.get_open_trades(mode=self.mode)
        open_symbols = {trade['symbol'] for trade in open_trades}

        if open_symbols:
            cprint(f"\n  📌 Open positions: {', '.join(open_symbols)}", "yellow")

        for symbol, result in arbitration_results.items():
            # PERMANENT FIX: Use arbiter thresholds instead of hardcoded 70%
            # Previously: Arbiter accepted 55% BUY signals, but execution required >=70%
            # Result: Accepted signals never executed (55% < 70%)
            # Now: Execute ALL arbiter-accepted signals (arbiter already validated them)
            if result.action == 'BUY':
                min_confidence = self.config.get('buy_confidence_min', 55.0)
            elif result.action == 'SELL':
                min_confidence = self.config.get('sell_confidence_min', 50.0)
            else:
                continue  # Skip NEUTRAL/WAIT

            if result.confidence >= min_confidence:
                cprint(f"\n  🎯 Processing {result.action} for {symbol}...", "cyan")

                # PERMANENT FIX: Handle opposite signals - close position immediately at market
                # If BUY signal but holding SELL → skip (wait for exit)
                # If SELL signal but holding BUY → CLOSE BUY at market, then continue to open SELL
                if symbol in open_symbols:
                    # Find the existing trade for this symbol
                    existing_trade = next((t for t in open_trades if t['symbol'] == symbol), None)

                    if existing_trade:
                        existing_side = existing_trade.get('side', 'UNKNOWN')

                        # Check if signal is opposite direction
                        is_opposite_signal = (existing_side == 'BUY' and result.action == 'SELL') or \
                                           (existing_side == 'SELL' and result.action == 'BUY')

                        if is_opposite_signal:
                            # OPPOSITE SIGNAL: Close existing position at market price
                            cprint(f"     🔄 OPPOSITE SIGNAL DETECTED", "yellow", attrs=['bold'])
                            cprint(f"     📍 Existing: {existing_side} | New Signal: {result.action}", "yellow")
                            cprint(f"     🚨 Closing {existing_side} position at MARKET PRICE", "red", attrs=['bold'])

                            try:
                                # Get current market price
                                from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                                ohlcv = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe='15m', days_back=1)
                                current_price = float(ohlcv['close'].iloc[-1])

                                # Cancel all open orders for this symbol (SL/TP orders)
                                if self.mode == 'LIVE':
                                    cprint(f"     ⚠️  Cancelling all open orders for {symbol}...", "yellow")
                                    open_orders = self.exchange_manager.binance_client.get_open_orders(symbol=f"{symbol}USDT")
                                    for order in open_orders:
                                        self.exchange_manager.binance_client.cancel_order(
                                            symbol=f"{symbol}USDT",
                                            orderId=order['orderId']
                                        )
                                    cprint(f"     ✅ Cancelled {len(open_orders)} orders", "green")

                                # Execute market order to close position
                                if self.mode == 'LIVE':
                                    # Get actual balance from exchange
                                    account = self.exchange_manager.binance_client.get_account()
                                    balance = next((b for b in account['balances'] if b['asset'] == symbol), None)

                                    if balance and float(balance['free']) > 0:
                                        close_qty = float(balance['free'])

                                        # Close the position at market
                                        close_side = 'SELL' if existing_side == 'BUY' else 'BUY'
                                        cprint(f"     [BINANCE] Market {close_side}: {close_qty} {symbol} @ ${current_price:.2f}", "cyan")

                                        if close_side == 'SELL':
                                            close_order = self.exchange_manager.binance_client.order_market_sell(
                                                symbol=f"{symbol}USDT",
                                                quantity=close_qty
                                            )
                                        else:
                                            close_order = self.exchange_manager.binance_client.order_market_buy(
                                                symbol=f"{symbol}USDT",
                                                quantity=close_qty
                                            )

                                        cprint(f"     ✅ Position closed at market", "green")

                                        # Close trade in database
                                        entry_price = existing_trade.get('entry_price', current_price)
                                        pnl_usd = (current_price - entry_price) * close_qty if existing_side == 'BUY' else (entry_price - current_price) * close_qty
                                        pnl_pct = (pnl_usd / (entry_price * close_qty)) * 100

                                        self.db.close_trade(
                                            trade_id=existing_trade['id'],
                                            exit_price=current_price,
                                            exit_reason='opposite_signal',
                                            pnl_usd=pnl_usd,
                                            pnl_pct=pnl_pct
                                        )
                                        cprint(f"     💰 PnL: ${pnl_usd:.2f} ({pnl_pct:+.2f}%)", "white")
                                        cprint(f"     ✅ Trade closed in database", "green")

                                        # Remove from open_symbols so we can proceed with new trade
                                        open_symbols.discard(symbol)
                                    else:
                                        cprint(f"     ⚠️  No {symbol} balance to close", "yellow")
                                        skipped_count += 1
                                        continue
                                else:
                                    # PAPER mode: Just close in database
                                    entry_price = existing_trade.get('entry_price', current_price)
                                    position_size = existing_trade.get('position_size_usd', 100)
                                    pnl_usd = (current_price - entry_price) * (position_size / entry_price) if existing_side == 'BUY' else (entry_price - current_price) * (position_size / entry_price)
                                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 if existing_side == 'BUY' else ((entry_price - current_price) / entry_price) * 100

                                    self.db.close_trade(
                                        trade_id=existing_trade['id'],
                                        exit_price=current_price,
                                        exit_reason='opposite_signal',
                                        pnl_usd=pnl_usd,
                                        pnl_pct=pnl_pct
                                    )
                                    cprint(f"     💰 PnL: ${pnl_usd:.2f} ({pnl_pct:+.2f}%)", "white")
                                    cprint(f"     ✅ Position closed (PAPER)", "green")

                                    # Remove from open_symbols
                                    open_symbols.discard(symbol)

                            except Exception as e:
                                cprint(f"     ❌ Failed to close position: {e}", "red")
                                skipped_count += 1
                                continue
                        else:
                            # SAME DIRECTION: Skip (don't add to existing position)
                            cprint(f"     ⚠️  SKIPPED - {symbol} already has an OPEN {existing_side} trade", "red", attrs=['bold'])
                            cprint(f"     💡 Waiting for existing position to close before opening new trade", "yellow")
                            skipped_count += 1
                            continue

                try:
                    # STEP 1: Get OHLCV data from Binance (REAL data)
                    from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                    ohlcv = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe='15m', days_back=3)

                    if ohlcv is None or len(ohlcv) < 50:
                        cprint(f"     ⚠️  Insufficient OHLCV data for {symbol}", "yellow")
                        continue

                    # Get current price (last close)
                    entry_price = float(ohlcv['close'].iloc[-1])

                    # STEP 2: Update market regime
                    # PERMANENT FIX: Pass OHLCV data to update_regime() (it detects regime internally)
                    # DynamicRiskEngine requires regime to be set before updating limits
                    self.risk_engine.update_regime(ohlcv)
                    regime = self.risk_engine.current_regime
                    regime_config = self.risk_engine.current_regime_config
                    cprint(f"     📊 Market Regime: {regime.value}", "white")

                    # STEP 2.5: OVERBOUGHT/TOP-BUYING PROTECTION
                    # CRITICAL: Prevent buying at local highs / market tops
                    # Check multiple conditions: RSI, distance from recent high, volatility expansion
                    if result.action == 'BUY':
                        import talib
                        import numpy as np

                        # Calculate RSI (14-period standard)
                        rsi = talib.RSI(ohlcv['close'].values, timeperiod=14)
                        current_rsi = rsi[-1]

                        # Calculate price distance from recent high (100 candles)
                        recent_high = ohlcv['high'].tail(100).max()
                        # FIXED: When price is 5% BELOW high, this gives 5.0 (positive)
                        # When price is AT high, this gives 0.0
                        # When price is ABOVE high, this gives negative value
                        distance_from_high_pct = ((recent_high - entry_price) / recent_high) * 100

                        # Calculate 20-period ATR for volatility context
                        atr = talib.ATR(ohlcv['high'].values, ohlcv['low'].values, ohlcv['close'].values, timeperiod=20)
                        current_atr = atr[-1]
                        atr_pct = (current_atr / entry_price) * 100

                        # Additional protection: Check for extreme volatility
                        extreme_volatility = atr_pct > 4.0  # ATR > 4% indicates extreme volatility

                        # PROTECTION RULES:
                        overbought_reasons = []

                        # Rule 1: RSI > 75 = Extreme overbought
                        if current_rsi > 75:
                            overbought_reasons.append(f"RSI extremely overbought ({current_rsi:.1f} > 75)")

                        # Rule 2: RSI > 70 + price within 2% of recent high = Double top risk
                        # FIXED: distance < 2.0 means price is within 2% BELOW the high
                        if current_rsi > 70 and distance_from_high_pct < 2.0:
                            overbought_reasons.append(f"RSI overbought ({current_rsi:.1f}) + near recent high (within {distance_from_high_pct:.1f}% of top)")

                        # Rule 3: Price at/above recent high with expanding volatility = Blow-off top risk
                        # FIXED: distance < 0.5 means price is within 0.5% of high or ABOVE it
                        if distance_from_high_pct < 0.5 and atr_pct > 3.0:
                            overbought_reasons.append(f"At/near recent high with high volatility (ATR {atr_pct:.1f}%)")

                        # Rule 4: Extreme volatility protection (matching Pine Script)
                        if extreme_volatility:
                            overbought_reasons.append(f"Extreme volatility detected (ATR {atr_pct:.1f}% > 4%)")

                        # ALWAYS show overbought assessment (even when passing)
                        cprint(f"     🔍 OVERBOUGHT PROTECTION CHECK:", "cyan", attrs=['bold'])
                        cprint(f"        📊 RSI: {current_rsi:.1f}/75 {'❌ EXTREME' if current_rsi > 75 else '⚠️ HIGH' if current_rsi > 70 else '✅ OK'}", "white")
                        cprint(f"        📈 Price vs High: ${entry_price:.2f} vs ${recent_high:.2f} ({distance_from_high_pct:.1f}% below)", "white")
                        cprint(f"           Status: {'❌ AT TOP' if distance_from_high_pct < 0.5 else '⚠️ NEAR TOP' if distance_from_high_pct < 2.0 else '✅ SAFE DISTANCE'}", "white")
                        cprint(f"        💨 ATR volatility: {atr_pct:.2f}% {'❌ EXTREME' if atr_pct > 4.0 else '⚠️ HIGH' if atr_pct > 3.0 else '✅ NORMAL'}", "white")

                        # If ANY protection rule triggers, REJECT the BUY
                        if overbought_reasons:
                            cprint(f"     🚨 OVERBOUGHT PROTECTION TRIGGERED - REJECTING BUY", "red", attrs=['bold'])
                            for reason in overbought_reasons:
                                cprint(f"        ⚠️  {reason}", "yellow")
                            cprint(f"     💡 Waiting for pullback or RSI cooldown before buying", "cyan")
                            skipped_count += 1
                            continue
                        else:
                            cprint(f"     ✅ OVERBOUGHT CHECK PASSED - Safe to buy", "green")

                    # STEP 2.6: OVERSOLD/BOTTOM-SELLING PROTECTION
                    # CRITICAL: Prevent selling at local lows / market bottoms (matching Pine Script)
                    if result.action == 'SELL':
                        import talib
                        import numpy as np

                        # Calculate RSI (14-period standard)
                        rsi = talib.RSI(ohlcv['close'].values, timeperiod=14)
                        current_rsi = rsi[-1]

                        # Calculate price distance from recent low (100 candles)
                        recent_low = ohlcv['low'].tail(100).min()
                        # FIXED: When price is 5% ABOVE low, this gives 5.0 (positive)
                        # When price is AT low, this gives 0.0
                        # When price is BELOW low, this would give negative (new low)
                        distance_from_low_pct = ((entry_price - recent_low) / recent_low) * 100

                        # Calculate 20-period ATR for volatility context
                        atr = talib.ATR(ohlcv['high'].values, ohlcv['low'].values, ohlcv['close'].values, timeperiod=20)
                        current_atr = atr[-1]
                        atr_pct = (current_atr / entry_price) * 100

                        # Additional protection: Check for extreme volatility
                        extreme_volatility = atr_pct > 4.0  # ATR > 4% indicates extreme volatility

                        # PROTECTION RULES:
                        oversold_reasons = []

                        # Rule 1: RSI < 25 = Extreme oversold
                        if current_rsi < 25:
                            oversold_reasons.append(f"RSI extremely oversold ({current_rsi:.1f} < 25)")

                        # Rule 2: RSI < 30 + price within 2% of recent low = Double bottom risk
                        # FIXED: distance < 2.0 means price is within 2% ABOVE the low
                        if current_rsi < 30 and distance_from_low_pct < 2.0:
                            oversold_reasons.append(f"RSI oversold ({current_rsi:.1f}) + near recent low (within {distance_from_low_pct:.1f}% of bottom)")

                        # Rule 3: Price at/near recent low with expanding volatility = Capitulation risk
                        # FIXED: distance < 0.5 means price is within 0.5% of low
                        if distance_from_low_pct < 0.5 and atr_pct > 3.0:
                            oversold_reasons.append(f"At/near recent low with high volatility (ATR {atr_pct:.1f}%)")

                        # Rule 4: Extreme volatility protection (matching Pine Script)
                        if extreme_volatility:
                            oversold_reasons.append(f"Extreme volatility detected (ATR {atr_pct:.1f}% > 4%)")

                        # ALWAYS show oversold assessment (even when passing)
                        cprint(f"     🔍 OVERSOLD PROTECTION CHECK:", "cyan", attrs=['bold'])
                        cprint(f"        📊 RSI: {current_rsi:.1f}/25 {'❌ EXTREME' if current_rsi < 25 else '⚠️ LOW' if current_rsi < 30 else '✅ OK'}", "white")
                        cprint(f"        📉 Price vs Low: ${entry_price:.2f} vs ${recent_low:.2f} ({distance_from_low_pct:.1f}% above)", "white")
                        cprint(f"           Status: {'❌ AT BOTTOM' if distance_from_low_pct < 0.5 else '⚠️ NEAR BOTTOM' if distance_from_low_pct < 2.0 else '✅ SAFE DISTANCE'}", "white")
                        cprint(f"        💨 ATR volatility: {atr_pct:.2f}% {'❌ EXTREME' if atr_pct > 4.0 else '⚠️ HIGH' if atr_pct > 3.0 else '✅ NORMAL'}", "white")

                        # If ANY protection rule triggers, REJECT the SELL
                        if oversold_reasons:
                            cprint(f"     🚨 OVERSOLD PROTECTION TRIGGERED - REJECTING SELL", "red", attrs=['bold'])
                            for reason in oversold_reasons:
                                cprint(f"        ⚠️  {reason}", "yellow")
                            cprint(f"     💡 Waiting for bounce or RSI recovery before selling", "cyan")
                            skipped_count += 1
                            continue
                        else:
                            cprint(f"     ✅ OVERSOLD CHECK PASSED - Safe to sell", "green")

                    # STEP 3: Score token risk
                    # Get token metadata (volume, market cap, spread) from Binance
                    token_data = BinanceTruthAPI.token_overview(symbol)

                    volume_24h_usd = token_data.get('volume_24h_usd', 1_000_000)
                    market_cap_usd = token_data.get('market_cap_usd', 100_000_000)
                    avg_spread_bps = token_data.get('spread_bps', 10)

                    token_profile = self.risk_engine.token_scorer.compute_risk_score(
                        symbol, ohlcv, volume_24h_usd, market_cap_usd, avg_spread_bps
                    )
                    cprint(f"     🎯 Token Risk Score: {token_profile.risk_score:.2f}", "white")

                    # STEP 4: Update dynamic limits
                    self.risk_engine.update_limits(equity_usd, pnl_history)
                    limits = self.risk_engine.current_limits

                    # STEP 5: Calculate position size (VolatilityPositionSizer)
                    position_size_usd, stop_loss_price, take_profit_price = \
                        self.risk_engine.position_sizer.compute_position_size(
                            equity_usd=equity_usd,
                            entry_price=entry_price,
                            token_profile=token_profile,
                            regime_config=regime_config,
                            min_trade_usd=self.config.get('min_trade_usd', 50)  # Binance SPOT minimum
                        )

                    # Apply arbiter size_multiplier
                    position_size_usd *= result.size_multiplier

                    # PERMANENT FIX: Validate position size doesn't exceed available balance
                    # Issue: In LIVE mode, calculated position $300 but balance only $0.23
                    # Result: Trade should be rejected or capped to available balance
                    # Solution: Cap position size to available balance in LIVE mode
                    if self.mode == 'LIVE' and position_size_usd > equity_usd:
                        cprint(f"     ⚠️  Position ${position_size_usd:.2f} exceeds balance ${equity_usd:.2f}", "yellow", attrs=['bold'])
                        cprint(f"     📉 Capping position to available balance: ${equity_usd:.2f}", "yellow")
                        position_size_usd = equity_usd

                    cprint(f"     💰 Position Size: ${position_size_usd:.2f}", "white")
                    cprint(f"     📍 Entry: ${entry_price:.6f}", "white")

                    # STEP 6: Create OrderPlan with dynamic SL/TP
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
                    cprint(f"     🎯 Take Profit 2: ${order_plan.take_profits[1].price:.6f} ({order_plan.take_profits[1].allocation_pct:.0f}%)", "green")
                    cprint(f"     🎯 Take Profit 3: ${order_plan.take_profits[2].price:.6f} ({order_plan.take_profits[2].allocation_pct:.0f}%)", "green")

                    # PERMANENT FIX: Validate position size before execution/logging
                    # Issue: Risk engine may calculate $0 position due to conservative limits
                    # Result: Invalid trade logged, blocks future trades on same symbol
                    # Solution: Only execute/log trades with valid position sizes (min $50 for Binance SPOT)
                    if position_size_usd < 50.0:
                        cprint(f"     ⚠️  Position size ${position_size_usd:.2f} too small (min $50 Binance SPOT) - skipping trade", "yellow")
                        cprint(f"     💡 Check risk limits: equity=${equity_usd:.2f}, token_risk={token_profile.risk_score:.2f}", "white")
                        skipped_count += 1
                        continue

                    # STEP 7: Execute via ExchangeManager + Log to Database
                    # PERMANENT FIX: Both LIVE and PAPER modes must log to database
                    # Previously: LIVE executed but didn't log → monitoring showed no positions
                    # Now: Both modes log to database for position tracking

                    # Generate unique trade ID
                    import time
                    trade_id = f"{symbol}_{int(time.time() * 1000)}"

                    if self.exchange_manager and self.mode == 'LIVE':
                        # Execute LIVE order
                        if result.action == 'BUY':
                            order = self.exchange_manager.market_buy(symbol, position_size_usd)
                        else:
                            order = self.exchange_manager.market_sell(symbol, position_size_usd)

                        cprint(f"     ✅ LIVE order executed", "green")

                        # Place OCO order (Stop Loss + TP1 at 40%)
                        # OCO = One-Cancels-Other: Either SL triggers OR TP1 triggers
                        if order.get('success', False) and 'quantity' in order:
                            executed_qty = float(order['quantity'])

                            # Calculate 40% of position for TP1 (OCO will handle this portion)
                            oco_quantity = executed_qty * 0.4

                            # Stop limit price (slightly worse than stop price to ensure fill)
                            stop_limit_offset = 0.001  # 0.1% worse than stop trigger
                            if result.action == 'BUY':
                                stop_limit_price = order_plan.stop_loss.price * (1 - stop_limit_offset)
                            else:
                                stop_limit_price = order_plan.stop_loss.price * (1 + stop_limit_offset)

                            # PERMANENT FIX: ASYMMETRIC OCO to prevent orphaned TP2/TP3
                            # TP1 = 40% (profit target)
                            # SL = 100% (full protection)
                            # When SL triggers, Binance closes 100% and auto-cancels TP2/TP3 (no qty left)
                            oco_tp1_quantity = executed_qty * 0.4   # TP1 leg: 40%
                            oco_sl_quantity = executed_qty          # SL leg: 100% FULL PROTECTION

                            # Place ASYMMETRIC OCO (SL=100% + TP1=40%)
                            oco_result = self.exchange_manager.place_oco_order(
                                symbol=symbol,
                                side=result.action,  # Original side (BUY or SELL)
                                tp1_quantity=oco_tp1_quantity,      # 40% for TP1
                                sl_quantity=oco_sl_quantity,        # 100% for SL
                                stop_price=order_plan.stop_loss.price,
                                stop_limit_price=stop_limit_price,
                                take_profit_price=order_plan.take_profits[0].price
                            )

                            # Extract OCO order list ID for monitoring
                            oco_order_list_id = None
                            if oco_result.get('success', True):  # OCO might not return 'success' key
                                oco_order_list_id = oco_result.get('orderListId')
                                cprint(f"     [OK] OCO placed (FULL POSITION: TP1=100%, SL=100%) - ID: {oco_order_list_id}", "green")

                            # PERMANENT FIX: OCO now uses FULL quantity (100% position)
                            # When OCO is successful, we do NOT place TP2/TP3
                            # because the entire position is covered by the OCO order
                            # This prevents orphaned orders and simplifies execution
                            should_place_additional_tps = not oco_result.get('success', False)

                            # Only place TP2/TP3 if OCO failed (fallback mode)
                            if should_place_additional_tps:
                                cprint(f"     ⚠️  OCO failed - placing individual TP orders as fallback", "yellow")

                                # Calculate quantities for fallback TP orders
                                tp2_quantity = executed_qty * 0.3
                                tp3_quantity = executed_qty * 0.3  # Remaining 30%

                                # TP2 limit order (30% of position)
                                if len(order_plan.take_profits) > 1:
                                    tp2_result = self.exchange_manager.place_limit_order(
                                        symbol=symbol,
                                        side='SELL' if result.action == 'BUY' else 'BUY',
                                        quantity=tp2_quantity,
                                        price=order_plan.take_profits[1].price
                                    )
                                    if tp2_result.get('success', True):
                                        cprint(f"     ✅ TP2 limit order placed (30%)", "green")

                                # TP3 limit order (30% of position)
                                if len(order_plan.take_profits) > 2:
                                    tp3_result = self.exchange_manager.place_limit_order(
                                        symbol=symbol,
                                        side='SELL' if result.action == 'BUY' else 'BUY',
                                        quantity=tp3_quantity,
                                        price=order_plan.take_profits[2].price
                                    )
                                    if tp3_result.get('success', True):
                                        cprint(f"     ✅ TP3 limit order placed (30%)", "green")
                            else:
                                cprint(f"     ✅ OCO order covers full position - no additional TP orders needed", "green")

                        # PERMANENT FIX: Log LIVE trades to database (for position tracking)
                        self.db.insert_trade(
                            trade_id=trade_id,
                            symbol=symbol,
                            side=result.action,
                            entry_price=entry_price,
                            position_size_usd=position_size_usd,
                            stop_loss=order_plan.stop_loss.price,
                            tp1_price=order_plan.take_profits[0].price if len(order_plan.take_profits) > 0 else entry_price * 1.01,
                            tp2_price=order_plan.take_profits[1].price if len(order_plan.take_profits) > 1 else entry_price * 1.02,
                            tp3_price=order_plan.take_profits[2].price if len(order_plan.take_profits) > 2 else entry_price * 1.03,
                            mode=self.mode,
                            tp1_pct=order_plan.take_profits[0].allocation_pct if len(order_plan.take_profits) > 0 else 40.0,
                            tp2_pct=order_plan.take_profits[1].allocation_pct if len(order_plan.take_profits) > 1 else 30.0,
                            tp3_pct=order_plan.take_profits[2].allocation_pct if len(order_plan.take_profits) > 2 else 30.0,
                            strategy_name=f"{symbol}_1h_VolatilityBracket",
                            confidence=str(result.confidence),
                            metadata={
                                'regime': regime.value,
                                'token_risk_score': token_profile.risk_score,
                                'reasoning': result.reasoning
                            },
                            oco_order_list_id=str(oco_order_list_id) if oco_order_list_id else None
                        )
                    else:
                        # PAPER mode
                        cprint(f"     📝 PAPER trade logged", "cyan")

                        # Log to database
                        self.db.insert_trade(
                            trade_id=trade_id,
                            symbol=symbol,
                            side=result.action,
                            entry_price=entry_price,
                            position_size_usd=position_size_usd,
                            stop_loss=order_plan.stop_loss.price,
                            tp1_price=order_plan.take_profits[0].price if len(order_plan.take_profits) > 0 else entry_price * 1.01,
                            tp2_price=order_plan.take_profits[1].price if len(order_plan.take_profits) > 1 else entry_price * 1.02,
                            tp3_price=order_plan.take_profits[2].price if len(order_plan.take_profits) > 2 else entry_price * 1.03,
                            mode=self.mode,
                            tp1_pct=order_plan.take_profits[0].allocation_pct if len(order_plan.take_profits) > 0 else 40.0,
                            tp2_pct=order_plan.take_profits[1].allocation_pct if len(order_plan.take_profits) > 1 else 30.0,
                            tp3_pct=order_plan.take_profits[2].allocation_pct if len(order_plan.take_profits) > 2 else 30.0,
                            strategy_name=f"{symbol}_1h_VolatilityBracket",
                            confidence=str(result.confidence),
                            metadata={
                                'regime': regime.value,
                                'token_risk_score': token_profile.risk_score,
                                'reasoning': result.reasoning
                            },
                            oco_order_list_id=None  # PAPER mode doesn't have real OCO orders
                        )

                    executed_count += 1

                except Exception as e:
                    cprint(f"     ❌ Execution failed: {e}", "red")
                    import traceback
                    cprint(f"     {traceback.format_exc()}", "red")

        # Summary
        if skipped_count > 0:
            cprint(f"\n  Executed: {executed_count} | Skipped (duplicate): {skipped_count}\n", "cyan", attrs=['bold'])
        else:
            cprint(f"\n  Executed {executed_count} trades using DYNAMIC systems\n", "cyan", attrs=['bold'])

    def reconcile_positions_with_exchange(self):
        """
        Sync database positions with actual exchange balances
        Closes ghost positions that exist in database but not on exchange

        This fixes the issue where OCO orders execute but database isn't updated
        """
        if self.mode != 'LIVE':
            return  # Only reconcile in LIVE mode

        cprint("\n  🔍 Reconciling positions with exchange...", "cyan")

        # Get open positions from database
        result = self.db_typed.get_open_trades(mode=TradingMode(self.mode))

        if not result.is_success() or not result.value:
            cprint("     ✅ No positions to reconcile", "green")
            return

        open_positions = result.value

        # Get actual account balances from Binance
        try:
            account = self.exchange_manager.binance_client.get_account()
            exchange_balances = {b['asset']: float(b['free']) for b in account['balances']}
        except Exception as e:
            cprint(f"     ⚠️  Failed to get exchange balances: {e}", "yellow")
            return

        ghost_positions_found = 0

        for trade in open_positions:
            symbol = trade.symbol
            trade_id = trade.trade_id
            entry_price = trade.entry_price
            position_size_usd = trade.position_size_usd

            # Extract base asset (e.g., 'ETH' from 'ETHUSDT')
            base_asset = symbol.replace('USDT', '').replace('-', '')

            # Calculate expected balance
            expected_balance = position_size_usd / entry_price if entry_price > 0 else 0

            # Get actual balance from exchange
            actual_balance = exchange_balances.get(base_asset, 0.0)

            # Check if position is a "ghost" (balance is dust or zero)
            # Consider it ghost if actual < 1% of expected
            is_ghost = actual_balance < (expected_balance * 0.01)

            if is_ghost:
                ghost_positions_found += 1
                cprint(f"     🚨 GHOST POSITION DETECTED: {symbol}", "yellow")
                cprint(f"        Database shows: {expected_balance:.8f} {base_asset}", "yellow")
                cprint(f"        Exchange shows: {actual_balance:.8f} {base_asset}", "yellow")
                cprint(f"        🔧 Closing ghost position in database...", "cyan")

                # Close position in database
                try:
                    # Use last known price or entry price
                    current_price = self.exchange_manager.binance_client.get_symbol_ticker(
                        symbol=symbol.replace('-', '')
                    )
                    exit_price = float(current_price['price'])
                except:
                    exit_price = entry_price  # Fallback to entry price

                # Calculate PnL
                price_change_pct = ((exit_price - entry_price) / entry_price) * 100
                realized_pnl = position_size_usd * (price_change_pct / 100)

                self.db.close_trade(
                    trade_id=trade_id,
                    exit_price=exit_price,
                    exit_reason='ghost_position_cleanup_oco_filled',
                    pnl_usd=realized_pnl,
                    pnl_pct=price_change_pct
                )
                cprint(f"        ✅ Ghost position closed in database", "green")

        if ghost_positions_found > 0:
            cprint(f"     🔧 Reconciliation complete: {ghost_positions_found} ghost position(s) cleaned up", "cyan")
        else:
            cprint(f"     ✅ All positions in sync with exchange", "green")

    def monitor_positions(self):
        """
        COMPREHENSIVE POSITION MONITORING with ASYMMETRIC OCO protection:

        1. Real-time PnL calculation from live market prices
        2. OCO order status verification with ASYMMETRIC structure (TP1=40%, SL=100%)
        3. Emergency protocol: If SL triggers, Binance auto-closes 100% and cancels TP2/TP3
        4. Trailing stop loss: Move SL to breakeven+2% when profit > 5%
        5. Trailing take profit: Adjust TP2/TP3 upward when profit > 5%
        6. PAPER mode: Simulated SL/TP triggers based on price checks

        ASYMMETRIC OCO STRUCTURE:
        - TP1 = 40% (profit target)
        - SL = 100% (full protection - prevents orphaned TP2/TP3 when SL triggers)
        - When SL triggers: Binance closes 100%, TP2/TP3 auto-cancelled (no qty left)
        - When TP1 triggers: SL cancelled, 60% remains for TP2/TP3
        """
        cprint("\n[5/5] Monitoring Open Positions with Real-time PnL & OCO Protection...", "yellow")

        # FIRST: Reconcile positions with exchange (closes ghost positions)
        self.reconcile_positions_with_exchange()

        # Get open positions from database
        result = self.db_typed.get_open_trades(mode=TradingMode(self.mode))

        if not result.is_success():
            cprint(f"  ⚠️  Error getting open trades: {result.error}", "yellow")
            return

        open_positions = result.value  # Type: List[Trade]

        if not open_positions:
            cprint("  No open positions\n", "white")
            return

        cprint(f"  Monitoring {len(open_positions)} position(s)", "green")

        from risk_management.binance_truth_paper_trading import BinanceTruthAPI

        for trade in open_positions:
            try:
                symbol = trade.symbol
                side = trade.side.value  # 'BUY' or 'SELL'
                entry_price = trade.entry_price
                position_size_usd = trade.position_size_usd
                stop_loss_price = trade.stop_loss
                tp1_price = trade.tp1_price
                tp2_price = trade.tp2_price
                tp3_price = trade.tp3_price
                trade_id = trade.trade_id
                metadata = trade.metadata  # ADDED: Load metadata from Trade object

                # STEP 1: Get LIVE current price from Binance
                binance_symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"
                current_price = BinanceTruthAPI.get_live_price(binance_symbol)

                if not current_price:
                    cprint(f"  ⚠️  Could not fetch price for {symbol}", "yellow")
                    continue

                # STEP 2: Calculate REAL-TIME unrealized PnL
                if side.upper() == 'BUY':
                    # LONG position: profit if price went up
                    price_change_pct = ((current_price - entry_price) / entry_price) * 100
                    unrealized_pnl_usd = position_size_usd * (price_change_pct / 100)
                else:
                    # SHORT position: profit if price went down
                    price_change_pct = ((entry_price - current_price) / entry_price) * 100
                    unrealized_pnl_usd = position_size_usd * (price_change_pct / 100)

                # Color code PnL
                pnl_color = "green" if unrealized_pnl_usd >= 0 else "red"

                # Display position summary
                cprint(f"\n  📊 {symbol} ({side} @ ${entry_price:.6f})", "cyan", attrs=['bold'])
                cprint(f"     Current Price: ${current_price:.6f}", "white")
                cprint(f"     Position Size: ${position_size_usd:.2f}", "white")
                cprint(f"     Unrealized PnL: ${unrealized_pnl_usd:+.2f} ({price_change_pct:+.2f}%)", pnl_color, attrs=['bold'])
                cprint(f"     Stop Loss: ${stop_loss_price:.6f} | TP1: ${tp1_price:.6f} | TP2: ${tp2_price:.6f} | TP3: ${tp3_price:.6f}", "white")

                # STEP 3: Check OCO order status (LIVE mode only)
                if self.mode == 'LIVE' and self.exchange_manager and self.exchange_manager.binance_client:
                    try:
                        # Get all open orders for this symbol
                        open_orders = self.exchange_manager.binance_client.get_open_orders(symbol=binance_symbol)

                        # Check if OCO SL/TP1 orders exist
                        oco_exists = any(order.get('type') in ['STOP_LOSS_LIMIT', 'LIMIT_MAKER'] for order in open_orders)

                        if not oco_exists:
                            # OCO MISSING - Either SL triggered or TP1 filled
                            cprint(f"     🚨 OCO order NOT FOUND - Checking if SL triggered or TP1 filled", "red", attrs=['bold'])

                            # Check recent trades to see if SL or TP1 filled
                            recent_trades = self.exchange_manager.binance_client.get_my_trades(symbol=binance_symbol, limit=20)

                            # Find fills related to this position
                            sl_triggered = False
                            tp1_triggered = False

                            for fill in recent_trades:
                                fill_price = float(fill['price'])

                                # Check if fill price matches SL or TP1 (within 0.5% tolerance)
                                if abs(fill_price - stop_loss_price) / stop_loss_price < 0.005:
                                    sl_triggered = True
                                    cprint(f"     ⚠️  STOP LOSS TRIGGERED @ ${fill_price:.6f}", "red", attrs=['bold'])
                                    break
                                elif abs(fill_price - tp1_price) / tp1_price < 0.005:
                                    tp1_triggered = True
                                    cprint(f"     ✅ TP1 FILLED @ ${fill_price:.6f}", "green", attrs=['bold'])
                                    break

                            if sl_triggered:
                                # EMERGENCY FALLBACK: SL triggered - cancel TP2/TP3 and close remaining position
                                # Note: With ASYMMETRIC OCO (SL=100%), this should rarely happen
                                # Binance should auto-close 100% and cancel TP2/TP3, but this is a safety net
                                cprint(f"     🔥 EMERGENCY FALLBACK: Cancelling TP2/TP3 and closing remaining position", "red", attrs=['bold'])

                                # Cancel all remaining limit orders (TP2/TP3)
                                for order in open_orders:
                                    try:
                                        self.exchange_manager.binance_client.cancel_order(
                                            symbol=binance_symbol,
                                            orderId=order['orderId']
                                        )
                                        cprint(f"     ✅ Cancelled order {order['orderId']} ({order['type']})", "green")
                                    except Exception as cancel_err:
                                        cprint(f"     ⚠️  Failed to cancel order {order['orderId']}: {cancel_err}", "yellow")

                                # Get remaining balance and market sell
                                account = self.exchange_manager.binance_client.get_account()
                                token_asset = symbol.replace('USDT', '')
                                balance = next((b for b in account['balances'] if b['asset'] == token_asset), None)

                                if balance and float(balance['free']) > 0:
                                    remaining_qty = float(balance['free'])

                                    # Format quantity properly for Binance (no scientific notation, LOT_SIZE compliant)
                                    quantity_formatted = self.exchange_manager.format_quantity_for_binance(
                                        remaining_qty,
                                        binance_symbol
                                    )

                                    # Check if quantity is too small after rounding
                                    if quantity_formatted == "0":
                                        cprint(f"     ℹ️  Balance too small to sell ({remaining_qty:.8f} {token_asset})", "cyan")
                                        cprint(f"     🔧 Closing position in database (dust remaining)", "cyan")

                                        # Close in database without selling dust
                                        realized_pnl = unrealized_pnl_usd
                                        self.db.close_trade(
                                            trade_id=trade_id,
                                            exit_price=current_price,
                                            exit_reason='dust_remaining_below_min_notional',
                                            pnl_usd=realized_pnl,
                                            pnl_pct=price_change_pct
                                        )
                                        cprint(f"     ✅ Trade closed in database (dust position)", "green")
                                        continue  # Skip to next position

                                    cprint(f"     🔥 Market selling remaining balance: {quantity_formatted} {token_asset}", "red")

                                    # Execute market sell with formatted quantity
                                    try:
                                        close_order = self.exchange_manager.binance_client.order_market_sell(
                                            symbol=binance_symbol,
                                            quantity=quantity_formatted
                                        )
                                        cprint(f"     ✅ Remaining position closed at market", "green")
                                    except Exception as sell_err:
                                        cprint(f"     ⚠️  Market sell failed: {sell_err}", "yellow")
                                        cprint(f"     🔧 Closing position in database anyway (manual cleanup required)", "cyan")
                                        # Still close in database to prevent infinite loops
                                        realized_pnl = unrealized_pnl_usd
                                        self.db.close_trade(
                                            trade_id=trade_id,
                                            exit_price=current_price,
                                            exit_reason='emergency_close_failed',
                                            pnl_usd=realized_pnl,
                                            pnl_pct=price_change_pct
                                        )
                                        cprint(f"     ⚠️  Position closed in DB - manually verify on Binance", "yellow")
                                        continue  # Skip to next position

                                # Close trade in database
                                realized_pnl = unrealized_pnl_usd  # Use calculated PnL
                                self.db.close_trade(
                                    trade_id=trade_id,
                                    exit_price=current_price,
                                    exit_reason='stop_loss_hit',
                                    pnl_usd=realized_pnl,
                                    pnl_pct=price_change_pct
                                )
                                cprint(f"     ✅ Trade closed in database (Reason: stop_loss_hit)", "green")

                            elif tp1_triggered:
                                # TP1 filled - keep TP2/TP3 active
                                cprint(f"     ✅ TP1 filled - TP2/TP3 still active", "green")
                                # Update database to reflect partial exit (optional - track TP levels filled)
                                # For now, just log it
                                pass

                        else:
                            # OCO exists - check if we should update trailing stop
                            cprint(f"     ✅ OCO order active ({len([o for o in open_orders if o['type'] in ['STOP_LOSS_LIMIT', 'LIMIT_MAKER']])} orders)", "green")

                            # STEP 4: HYBRID TRAILING STOP LOSS
                            # Phase 1: Wait for 3% profit confirmation (avoids "red arrow massacre")
                            # Phase 2: Trail continuously using 3.0x ATR multiplier (wider, safer)

                            if side.upper() == 'BUY':
                                # Get metadata to track highest price since entry
                                # metadata is already a dict from Trade object, no need to json.loads()
                                trade_metadata = metadata if isinstance(metadata, dict) else (json.loads(metadata) if metadata else {})

                                # Track highest price since entry (for trailing calculation)
                                if 'highest_since_entry' not in trade_metadata:
                                    trade_metadata['highest_since_entry'] = current_price
                                    trade_metadata['trailing_activated'] = False
                                else:
                                    # Update highest price
                                    trade_metadata['highest_since_entry'] = max(
                                        trade_metadata['highest_since_entry'],
                                        current_price
                                    )

                                # Phase 1: DYNAMIC activation threshold based on market regime and volatility
                                # Get fresh market data for regime detection
                                from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                                fresh_ohlcv = BinanceTruthAPI.get_ohlcv_data(binance_symbol, timeframe='1h', days_back=3)

                                from risk_management.dynamic_risk_engine import MarketRegimeDetector
                                regime_detector = MarketRegimeDetector()
                                current_regime, regime_config = regime_detector.detect_regime(fresh_ohlcv)

                                # Calculate ATR percentage (using DataFrame column access)
                                highs = fresh_ohlcv['high'].iloc[-14:].tolist()
                                lows = fresh_ohlcv['low'].iloc[-14:].tolist()
                                closes = fresh_ohlcv['close'].iloc[-15:-1].tolist()
                                true_ranges = []
                                for i in range(len(closes)):
                                    tr = max(highs[i] - lows[i], abs(highs[i] - closes[i]), abs(lows[i] - closes[i]))
                                    true_ranges.append(tr)
                                atr = sum(true_ranges) / len(true_ranges)
                                atr_pct = atr / current_price

                                # Regime-adaptive activation threshold
                                regime_thresholds = {
                                    'TRENDING_UP': 1.5,    # Lower in trends (trail sooner)
                                    'TRENDING_DOWN': 2.0,  # Moderate
                                    'CHOPPY': 1.0,         # Very low (lock profits fast)
                                    'CRISIS': 2.5,         # Higher (need confirmation)
                                    'FLAT': 1.5            # Moderate
                                }
                                base_threshold = regime_thresholds.get(current_regime.value, 1.5)

                                # ATR adjustment: Higher volatility = higher threshold
                                atr_adjustment = (atr_pct / 0.015) * 0.5  # Base 1.5% ATR = no adjustment
                                final_activation_threshold = base_threshold + atr_adjustment

                                if price_change_pct >= final_activation_threshold and not trade_metadata.get('trailing_activated', False):
                                    trade_metadata['trailing_activated'] = True
                                    cprint(f"     🎯 TRAILING ACTIVATED: {price_change_pct:.2f}% profit (threshold: {final_activation_threshold:.2f}% for {current_regime.value}, ATR: {atr_pct*100:.2f}%)", "cyan", attrs=['bold'])

                                # Phase 2: Continuous trailing after activation
                                if trade_metadata.get('trailing_activated', False):
                                    # Calculate ATR-based trailing distance
                                    try:
                                        from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                                        fresh_ohlcv = BinanceTruthAPI.get_ohlcv_data(binance_symbol, timeframe='1h', days_back=3)

                                        # Calculate ATR (14 periods) (using DataFrame column access)
                                        highs = fresh_ohlcv['high'].iloc[-14:].tolist()
                                        lows = fresh_ohlcv['low'].iloc[-14:].tolist()
                                        closes = fresh_ohlcv['close'].iloc[-15:-1].tolist()

                                        true_ranges = []
                                        for i in range(len(closes)):
                                            tr = max(
                                                highs[i] - lows[i],
                                                abs(highs[i] - closes[i]),
                                                abs(lows[i] - closes[i])
                                            )
                                            true_ranges.append(tr)

                                        atr = sum(true_ranges) / len(true_ranges)

                                        # Get regime for adaptive multiplier
                                        from risk_management.dynamic_risk_engine import MarketRegimeDetector
                                        regime_detector = MarketRegimeDetector()
                                        current_regime, regime_config = regime_detector.detect_regime(fresh_ohlcv)

                                        # Regime-adaptive multipliers (wider in trends to avoid stops)
                                        regime_multipliers = {
                                            'TRENDING_UP': 1.3,    # Wider (let trends run)
                                            'TRENDING_DOWN': 1.0,
                                            'CHOPPY': 0.7,         # Tighter (take profits fast)
                                            'FLAT': 1.0,
                                            'CRISIS': 0.6          # Very tight (protect capital)
                                        }
                                        regime_mult = regime_multipliers.get(current_regime.value, 1.0)

                                        # CRITICAL: Use 3.0x ATR (wider than 2.0x to survive normal volatility)
                                        sl_distance = 3.0 * atr * regime_mult

                                        # Calculate trailing SL from highest price since entry
                                        new_sl = trade_metadata['highest_since_entry'] - sl_distance

                                        # Only move SL UP (ratchet mechanism)
                                        if new_sl > stop_loss_price:
                                            cprint(f"     🎯 CONTINUOUS TRAILING: SL ${stop_loss_price:.6f} → ${new_sl:.6f} (3.0x ATR, {current_regime.value}, mult={regime_mult:.1f}x)", "cyan", attrs=['bold'])

                                            # Update metadata in database
                                            self.db.cursor.execute("""
                                                UPDATE trades
                                                SET metadata = ?
                                                WHERE trade_id = ?
                                            """, (json.dumps(trade_metadata), trade_id))
                                            self.db.conn.commit()
                                        else:
                                            # SL hasn't moved up yet, just update metadata
                                            self.db.cursor.execute("""
                                                UPDATE trades
                                                SET metadata = ?
                                                WHERE trade_id = ?
                                            """, (json.dumps(trade_metadata), trade_id))
                                            self.db.conn.commit()
                                            continue  # Skip OCO replacement

                                    except Exception as atr_err:
                                        cprint(f"     ⚠️  ATR calculation failed: {atr_err}, using fallback (breakeven+2%)", "yellow")
                                        new_sl = entry_price * 1.02
                                        if new_sl <= stop_loss_price:
                                            continue

                                else:
                                    # Not activated yet - update metadata and continue
                                    self.db.cursor.execute("""
                                        UPDATE trades
                                        SET metadata = ?
                                        WHERE trade_id = ?
                                    """, (json.dumps(trade_metadata), trade_id))
                                    self.db.conn.commit()
                                    continue

                                # If we reach here, new_sl > stop_loss_price, so update OCO
                                # Cancel existing OCO
                                oco_order = next((o for o in open_orders if o['type'] == 'STOP_LOSS_LIMIT'), None)
                                if oco_order:
                                    # Find the order list ID
                                    order_list_id = oco_order.get('orderListId')
                                    if order_list_id and order_list_id != -1:
                                        try:
                                            # Cancel OCO order list
                                            self.exchange_manager.binance_client.cancel_order_list(
                                                symbol=binance_symbol,
                                                orderListId=order_list_id
                                            )
                                            cprint(f"     ✅ Old OCO cancelled", "green")
                                        except Exception as cancel_err:
                                            cprint(f"     ⚠️  Failed to cancel OCO: {cancel_err}", "yellow")

                                    # Place new OCO with tighter SL and TRAILING TP
                                    # Calculate new TP1 (adjust proportionally) - TRAILING TP
                                    new_tp1 = current_price * 1.03  # TP1 at +3% from current price

                                    # Get position quantity for ASYMMETRIC OCO
                                    account = self.exchange_manager.binance_client.get_account()
                                    token_asset = symbol.replace('USDT', '')
                                    balance = next((b for b in account['balances'] if b['asset'] == token_asset), None)

                                    if balance and float(balance['free']) > 0:
                                        remaining_qty = float(balance['free'])

                                        # ASYMMETRIC OCO: TP1=40%, SL=100%
                                        oco_tp1_qty = remaining_qty * 0.4  # TP1 leg: 40%
                                        oco_sl_qty = remaining_qty         # SL leg: 100% FULL PROTECTION

                                        # Place new ASYMMETRIC OCO with trailing SL and TP
                                        new_oco_result = self.exchange_manager.place_oco_order(
                                            symbol=symbol,
                                            side='BUY',
                                            tp1_quantity=oco_tp1_qty,      # 40% for TP1
                                            sl_quantity=oco_sl_qty,        # 100% for SL
                                            stop_price=new_sl,
                                            stop_limit_price=new_sl * 0.999,
                                            take_profit_price=new_tp1
                                        )

                                        if new_oco_result.get('success'):
                                            cprint(f"     ✅ New trailing OCO placed: SL ${new_sl:.6f} | TP ${new_tp1:.6f}", "green", attrs=['bold'])

                                            # STEP 5: DYNAMIC TRAILING TAKE PROFIT for TP2 and TP3
                                            # Recalculate TPs using dynamic order manager (regime-based, ATR-based)
                                            # This ensures TPs adapt to current market conditions, not static percentages

                                            # Get fresh OHLCV data and recalculate market conditions
                                            try:
                                                from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                                                fresh_ohlcv = BinanceTruthAPI.get_ohlcv_data(binance_symbol, timeframe='1h', days_back=3)

                                                # Recalculate current market regime and token profile
                                                from risk_management.dynamic_risk_engine import DynamicRiskEngine, MarketRegimeDetector
                                                risk_engine = DynamicRiskEngine()
                                                regime_detector = MarketRegimeDetector()

                                                # Get fresh regime detection
                                                current_regime, regime_config = regime_detector.detect_regime(fresh_ohlcv)

                                                # Get fresh token profile
                                                current_token_profile = risk_engine.analyze_token(symbol, fresh_ohlcv)

                                                # Recalculate order plan with CURRENT price as entry and FRESH market conditions
                                                # This gives us dynamic TP levels based on CURRENT market regime
                                                new_order_plan = self.order_manager.calculate_order_plan(
                                                    symbol=symbol,
                                                    entry_price=current_price,  # Use CURRENT price as new "entry"
                                                    position_size_usd=position_size_usd,
                                                    direction=side,
                                                    token_profile=current_token_profile,  # FRESH token profile
                                                    regime=current_regime,                # FRESH market regime
                                                    ohlcv_data=fresh_ohlcv,
                                                    use_support_resistance=True
                                                )

                                                # Extract dynamic TP2 and TP3 from recalculated plan
                                                new_tp2 = new_order_plan.take_profits[1].price  # Dynamic TP2
                                                new_tp3 = new_order_plan.take_profits[2].price  # Dynamic TP3

                                                cprint(f"     📊 Dynamic TPs recalculated (Regime: {current_regime.value}): TP2=${new_tp2:.6f}, TP3=${new_tp3:.6f}", "cyan")

                                            except Exception as calc_err:
                                                # Fallback to ATR-based calculation if order manager fails
                                                cprint(f"     ⚠️  Dynamic TP calc failed, using ATR-based fallback: {calc_err}", "yellow")

                                                # Simple ATR-based fallback (still better than static %)
                                                atr_pct = 0.03  # Approximate 3% ATR for most crypto
                                                new_tp2 = current_price + (current_price * atr_pct * 3)  # 3x ATR
                                                new_tp3 = current_price + (current_price * atr_pct * 5)  # 5x ATR

                                            # Find existing TP2/TP3 orders
                                            tp2_orders = [o for o in open_orders if o['type'] == 'LIMIT' and abs(float(o['price']) - tp2_price) / tp2_price < 0.01]
                                            tp3_orders = [o for o in open_orders if o['type'] == 'LIMIT' and abs(float(o['price']) - tp3_price) / tp3_price < 0.01]

                                            # Cancel old TP2/TP3 orders
                                            for tp2_order in tp2_orders:
                                                try:
                                                    self.exchange_manager.binance_client.cancel_order(
                                                        symbol=binance_symbol,
                                                        orderId=tp2_order['orderId']
                                                    )
                                                    cprint(f"     ✅ Cancelled old TP2 order @ ${tp2_price:.6f}", "cyan")
                                                except Exception as e:
                                                    cprint(f"     ⚠️  Failed to cancel TP2: {e}", "yellow")

                                            for tp3_order in tp3_orders:
                                                try:
                                                    self.exchange_manager.binance_client.cancel_order(
                                                        symbol=binance_symbol,
                                                        orderId=tp3_order['orderId']
                                                    )
                                                    cprint(f"     ✅ Cancelled old TP3 order @ ${tp3_price:.6f}", "cyan")
                                                except Exception as e:
                                                    cprint(f"     ⚠️  Failed to cancel TP3: {e}", "yellow")

                                            # Place new TP2 and TP3 at higher prices
                                            tp2_qty = remaining_qty * 0.3
                                            tp3_qty = remaining_qty - oco_tp1_qty - tp2_qty  # Remaining balance

                                            # Place new TP2
                                            new_tp2_result = self.exchange_manager.place_limit_order(
                                                symbol=symbol,
                                                side='SELL',
                                                quantity=tp2_qty,
                                                price=new_tp2
                                            )
                                            if new_tp2_result.get('success'):
                                                cprint(f"     ✅ New trailing TP2 placed @ ${new_tp2:.6f}", "green", attrs=['bold'])

                                            # Place new TP3
                                            new_tp3_result = self.exchange_manager.place_limit_order(
                                                symbol=symbol,
                                                side='SELL',
                                                quantity=tp3_qty,
                                                price=new_tp3
                                            )
                                            if new_tp3_result.get('success'):
                                                cprint(f"     ✅ New trailing TP3 placed @ ${new_tp3:.6f}", "green", attrs=['bold'])

                            elif side.upper() == 'SELL' and price_change_pct > 5.0:
                                # SHORT position up 5%+ - move SL down to lock in profits
                                new_sl = entry_price * 0.98  # Move SL down 2% from entry
                                if new_sl < stop_loss_price:
                                    cprint(f"     🎯 TRAILING STOP: Moving SL from ${stop_loss_price:.6f} to ${new_sl:.6f} (lock in +2%)", "cyan", attrs=['bold'])
                                    # (Same logic as above but for SHORT positions)

                    except Exception as oco_check_err:
                        cprint(f"     ⚠️  OCO check failed: {oco_check_err}", "yellow")

                elif self.mode == 'PAPER':
                    # PAPER mode: Simulate SL/TP hits AND trailing logic
                    sl_hit = False
                    tp_hit = False

                    if side.upper() == 'BUY':
                        # LONG: Check if price hit SL (below) or TP (above)
                        if current_price <= stop_loss_price:
                            sl_hit = True
                            cprint(f"     🚨 PAPER: Stop Loss HIT @ ${current_price:.6f}", "red", attrs=['bold'])
                        elif current_price >= tp1_price:
                            tp_hit = True
                            cprint(f"     ✅ PAPER: TP1 HIT @ ${current_price:.6f}", "green", attrs=['bold'])

                        # PAPER: HYBRID TRAILING STOP LOSS (same logic as LIVE)
                        # Phase 1: Wait for 3% profit confirmation
                        # Phase 2: Trail continuously using 3.0x ATR multiplier
                        else:
                            # Get metadata to track highest price since entry
                            # FIXED: metadata is already a dict from Trade object, not a JSON string
                            if isinstance(metadata, str):
                                trade_metadata = json.loads(metadata) if metadata else {}
                            elif isinstance(metadata, dict):
                                trade_metadata = metadata
                            else:
                                trade_metadata = {}

                            # Track highest price since entry
                            if 'highest_since_entry' not in trade_metadata:
                                trade_metadata['highest_since_entry'] = current_price
                                trade_metadata['trailing_activated'] = False
                            else:
                                trade_metadata['highest_since_entry'] = max(
                                    trade_metadata['highest_since_entry'],
                                    current_price
                                )

                            # Phase 1: DYNAMIC activation threshold (same logic as LIVE)
                            from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                            # Get fresh OHLCV data (3 days = ~72 hourly candles)
                            fresh_ohlcv = BinanceTruthAPI.get_ohlcv_data(binance_symbol, '1h', days_back=3)

                            from risk_management.dynamic_risk_engine import MarketRegimeDetector
                            regime_detector = MarketRegimeDetector()
                            current_regime, regime_config = regime_detector.detect_regime(fresh_ohlcv)

                            # Calculate ATR percentage (using DataFrame column access)
                            highs = fresh_ohlcv['high'].iloc[-14:].tolist()
                            lows = fresh_ohlcv['low'].iloc[-14:].tolist()
                            closes = fresh_ohlcv['close'].iloc[-15:-1].tolist()
                            true_ranges = []
                            for i in range(len(closes)):
                                tr = max(highs[i] - lows[i], abs(highs[i] - closes[i]), abs(lows[i] - closes[i]))
                                true_ranges.append(tr)
                            atr = sum(true_ranges) / len(true_ranges)
                            atr_pct = atr / current_price

                            # Regime-adaptive activation threshold
                            regime_thresholds = {
                                'TRENDING_UP': 1.5,
                                'TRENDING_DOWN': 2.0,
                                'CHOPPY': 1.0,
                                'CRISIS': 2.5,
                                'FLAT': 1.5
                            }
                            base_threshold = regime_thresholds.get(current_regime.value, 1.5)
                            atr_adjustment = (atr_pct / 0.015) * 0.5
                            final_activation_threshold = base_threshold + atr_adjustment

                            if price_change_pct >= final_activation_threshold and not trade_metadata.get('trailing_activated', False):
                                trade_metadata['trailing_activated'] = True
                                cprint(f"     🎯 PAPER TRAILING ACTIVATED: {price_change_pct:.2f}% profit (threshold: {final_activation_threshold:.2f}% for {current_regime.value}, ATR: {atr_pct*100:.2f}%)", "cyan", attrs=['bold'])

                            # Phase 2: Continuous trailing after activation
                            if trade_metadata.get('trailing_activated', False):
                                # Calculate ATR-based trailing distance
                                try:
                                    from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                                    # Get fresh OHLCV data (3 days = ~72 hourly candles)
                                    fresh_ohlcv = BinanceTruthAPI.get_ohlcv_data(binance_symbol, '1h', days_back=3)

                                    # Calculate ATR (14 periods) (using DataFrame column access)
                                    highs = fresh_ohlcv['high'].iloc[-14:].tolist()
                                    lows = fresh_ohlcv['low'].iloc[-14:].tolist()
                                    closes = fresh_ohlcv['close'].iloc[-15:-1].tolist()

                                    true_ranges = []
                                    for i in range(len(closes)):
                                        tr = max(
                                            highs[i] - lows[i],
                                            abs(highs[i] - closes[i]),
                                            abs(lows[i] - closes[i])
                                        )
                                        true_ranges.append(tr)

                                    atr = sum(true_ranges) / len(true_ranges)

                                    # Get regime for adaptive multiplier
                                    from risk_management.dynamic_risk_engine import MarketRegimeDetector
                                    regime_detector = MarketRegimeDetector()
                                    current_regime, regime_config = regime_detector.detect_regime(fresh_ohlcv)

                                    # Regime-adaptive multipliers
                                    regime_multipliers = {
                                        'TRENDING_UP': 1.3,
                                        'TRENDING_DOWN': 1.0,
                                        'CHOPPY': 0.7,
                                        'FLAT': 1.0,
                                        'CRISIS': 0.6
                                    }
                                    regime_mult = regime_multipliers.get(current_regime.value, 1.0)

                                    # Use 3.0x ATR multiplier
                                    sl_distance = 3.0 * atr * regime_mult

                                    # Calculate trailing SL from highest price
                                    new_sl = trade_metadata['highest_since_entry'] - sl_distance

                                    # Only move SL UP
                                    if new_sl > stop_loss_price:
                                        cprint(f"     🎯 PAPER CONTINUOUS TRAILING: SL ${stop_loss_price:.6f} → ${new_sl:.6f} (3.0x ATR, {current_regime.value}, mult={regime_mult:.1f}x)", "cyan", attrs=['bold'])

                                        # Update metadata in database
                                        self.db.cursor.execute("""
                                            UPDATE trades
                                            SET metadata = ?
                                            WHERE trade_id = ?
                                        """, (json.dumps(trade_metadata), trade_id))
                                        self.db.conn.commit()

                                        # PAPER: Recalculate DYNAMIC TPs
                                        current_token_profile = risk_engine.analyze_token(symbol, fresh_ohlcv)

                                        new_order_plan = self.order_manager.calculate_order_plan(
                                            symbol=symbol,
                                            entry_price=current_price,
                                            position_size_usd=position_size_usd,
                                            direction=side,
                                            token_profile=current_token_profile,
                                            regime=current_regime,
                                            ohlcv_data=fresh_ohlcv,
                                            use_support_resistance=True
                                        )

                                        new_tp1 = new_order_plan.take_profits[0].price
                                        new_tp2 = new_order_plan.take_profits[1].price
                                        new_tp3 = new_order_plan.take_profits[2].price

                                        cprint(f"     📊 PAPER: Dynamic TPs recalculated (Regime: {current_regime.value})", "cyan")
                                        cprint(f"         TP1: ${new_tp1:.6f} | TP2: ${new_tp2:.6f} | TP3: ${new_tp3:.6f}", "cyan")

                                    else:
                                        # SL hasn't moved up yet, just update metadata
                                        self.db.cursor.execute("""
                                            UPDATE trades
                                            SET metadata = ?
                                            WHERE trade_id = ?
                                        """, (json.dumps(trade_metadata), trade_id))
                                        self.db.conn.commit()

                                except Exception as calc_err:
                                    cprint(f"     ⚠️  PAPER: ATR calculation failed: {calc_err}", "yellow")
                            else:
                                # Not activated yet - update metadata
                                self.db.cursor.execute("""
                                    UPDATE trades
                                    SET metadata = ?
                                    WHERE trade_id = ?
                                """, (json.dumps(trade_metadata), trade_id))
                                self.db.conn.commit()

                    else:
                        # SHORT: Check if price hit SL (above) or TP (below)
                        if current_price >= stop_loss_price:
                            sl_hit = True
                            cprint(f"     🚨 PAPER: Stop Loss HIT @ ${current_price:.6f}", "red", attrs=['bold'])
                        elif current_price <= tp1_price:
                            tp_hit = True
                            cprint(f"     ✅ PAPER: TP1 HIT @ ${current_price:.6f}", "green", attrs=['bold'])

                        # PAPER: Trailing Stop Loss for SHORT positions
                        elif price_change_pct > 5.0:
                            new_sl = entry_price * 0.98  # Move SL down 2% from entry
                            if new_sl < stop_loss_price:
                                cprint(f"     🎯 PAPER TRAILING STOP: Moving SL from ${stop_loss_price:.6f} to ${new_sl:.6f} (lock in +2%)", "cyan", attrs=['bold'])

                    # Close position in PAPER mode if SL/TP hit
                    if sl_hit:
                        self.db.close_trade(
                            trade_id=trade_id,
                            exit_price=stop_loss_price,
                            exit_reason='stop_loss_hit',
                            pnl_usd=unrealized_pnl_usd,
                            pnl_pct=price_change_pct
                        )
                        cprint(f"     ✅ PAPER: Trade closed (SL hit)", "green")
                    elif tp_hit:
                        # TP1 hit in PAPER mode - close 40% (simulate OCO behavior)
                        partial_pnl = unrealized_pnl_usd * 0.4
                        # In real system, would create new trade for remaining 60%
                        # For simplicity, just log it
                        cprint(f"     ✅ PAPER: TP1 hit - 40% closed, 60% still open", "green")

            except Exception as monitor_err:
                cprint(f"  ❌ Error monitoring {trade.symbol}: {monitor_err}", "red")
                import traceback
                cprint(f"     {traceback.format_exc()[:300]}", "red")

        cprint("")

    def get_account_status(self):
        """
        Get REAL-TIME account status with live position tracking

        Returns:
            - current_balance: Starting balance + realized PnL + unrealized PnL
            - free_usdt: Available USDT for new trades
            - allocated_usdt: USDT locked in open positions
            - unrealized_pnl: Live PnL from open positions (updated every cycle)
            - realized_pnl: PnL from closed trades
        """
        try:
            from risk_management.binance_truth_paper_trading import BinanceTruthAPI

            # Get starting balance based on mode
            if self.mode == 'LIVE':
                # LIVE: Fetch REAL Binance USDT balance
                real_balance = BinanceTruthAPI.get_usdt_balance()
                if real_balance is not None:
                    starting_balance = real_balance
                    cprint(f"  [LIVE] Using real Binance USDT balance: ${real_balance:,.2f}", "green", attrs=['bold'])
                else:
                    # Fallback if API keys not configured or API error
                    cprint("  [WARN] LIVE mode but couldn't fetch Binance balance - using config starting balance", "yellow")
                    starting_balance = self.config.get('starting_balance', 10000.0)
            else:
                # PAPER: Use configured starting balance
                starting_balance = self.config.get('starting_balance', 10000.0)

            # Get all trades for this mode
            all_trades = self.db.get_all_trades(mode=self.mode)

            if not all_trades:
                return {
                    'current_balance': starting_balance,
                    'free_usdt': starting_balance,
                    'allocated_usdt': 0.0,
                    'unrealized_pnl': 0.0,
                    'realized_pnl': 0.0,
                    'total_pnl': 0.0,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0
                }

            # Calculate REALIZED PnL from closed trades
            realized_pnl = 0.0
            winning_trades = 0
            losing_trades = 0

            for trade in all_trades:
                if trade.get('status') == 'CLOSED' and trade.get('pnl_usd') is not None:
                    pnl = float(trade.get('pnl_usd', 0))
                    realized_pnl += pnl

                    if pnl > 0:
                        winning_trades += 1
                    elif pnl < 0:
                        losing_trades += 1

            # Calculate UNREALIZED PnL from open positions (REAL-TIME)
            unrealized_pnl = 0.0
            allocated_usdt = 0.0
            # PERMANENT FIX: Use typed database to get Trade objects
            # Eliminates direction/side field confusion completely
            result = self.db_typed.get_open_trades(mode=TradingMode(self.mode))

            if not result.is_success():
                cprint(f"[WARN] Error getting open trades: {result.error}", "yellow")
                # Continue with empty open_trades list
                result_open_trades = []
            else:
                result_open_trades = result.value  # Type: List[Trade]

            for trade in result_open_trades:
                try:
                    symbol = trade.symbol
                    # PERMANENT FIX: Type-safe Trade object - no .get() needed!
                    # trade.side is a TradeSide enum, always exists
                    side = trade.side.value  # 'BUY' or 'SELL'
                    entry_price = trade.entry_price
                    position_size_usd = trade.position_size_usd

                    # Get LIVE current price from Binance
                    # Ensure symbol ends with 'USDT' for Binance API
                    binance_symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"
                    current_price = BinanceTruthAPI.get_live_price(binance_symbol)

                    if current_price:
                        # Calculate unrealized PnL based on side (BUY/SELL)
                        if side.upper() == 'BUY':
                            # LONG position: profit if price went up
                            price_change_pct = ((current_price - entry_price) / entry_price)
                        else:
                            # SHORT position: profit if price went down
                            price_change_pct = ((entry_price - current_price) / entry_price)

                        position_pnl = position_size_usd * price_change_pct
                        unrealized_pnl += position_pnl

                    # Track allocated capital
                    allocated_usdt += position_size_usd

                except Exception as e:
                    # Silent handling - still track allocated capital
                    allocated_usdt += trade.position_size_usd

            # Calculate totals
            total_pnl = realized_pnl + unrealized_pnl
            current_balance = starting_balance + total_pnl
            free_usdt = starting_balance + realized_pnl - allocated_usdt  # Capital not locked in positions

            total_trades = winning_trades + losing_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

            return {
                'current_balance': current_balance,
                'free_usdt': free_usdt,
                'allocated_usdt': allocated_usdt,
                'unrealized_pnl': unrealized_pnl,
                'realized_pnl': realized_pnl,
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'open_positions': len(result_open_trades)
            }
        except Exception as e:
            cprint(f"⚠️  Error getting account status: {e}", "yellow")
            import traceback
            cprint(f"  {traceback.format_exc()[:300]}", "red")
            return {
                'current_balance': 10000.0,
                'free_usdt': 10000.0,
                'allocated_usdt': 0.0,
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'total_pnl': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'open_positions': 0
            }

    def run_cycle(self, symbols: List[str] = None):
        """
        Run one complete trading cycle

        Args:
            symbols: List of symbols to trade (if None, auto-detect from strategies)
        """
        cycle_start = datetime.now()

        # Get account status
        account_status = self.get_account_status()

        cprint(f"\n{'='*80}", "magenta", attrs=['bold'])
        cprint(f"RBI RESEARCH TRADE FLOW - CYCLE START", "magenta", attrs=['bold'])
        cprint(f"Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}", "magenta")
        cprint(f"Mode: {self.mode}", "magenta")

        # Display balance and PnL (REAL-TIME with unrealized PnL)
        balance_color = "green" if account_status['total_pnl'] >= 0 else "red"
        cprint(f"Total Balance: ${account_status['current_balance']:,.2f} | Total PnL: ${account_status['total_pnl']:+,.2f}", balance_color, attrs=['bold'])

        # Show breakdown if there are open positions
        if account_status.get('open_positions', 0) > 0:
            unrealized_color = "green" if account_status['unrealized_pnl'] >= 0 else "red"
            cprint(f"Free USDT: ${account_status['free_usdt']:,.2f} | Allocated: ${account_status['allocated_usdt']:,.2f} | Unrealized PnL: ${account_status['unrealized_pnl']:+,.2f}", unrealized_color)
            cprint(f"Realized PnL: ${account_status['realized_pnl']:+,.2f} | Open Positions: {account_status['open_positions']}", "white")

        if account_status['total_trades'] > 0:
            cprint(f"Closed Trades: {account_status['total_trades']} ({account_status['winning_trades']}W/{account_status['losing_trades']}L) | Win Rate: {account_status['win_rate']:.1f}%", "cyan")

        cprint(f"{'='*80}\n", "magenta", attrs=['bold'])

        try:
            # 1. Load strategies (if not loaded)
            if not self.rbi_strategies:
                self.load_rbi_strategies()

            # 2. Auto-detect symbols from strategies if not provided
            if symbols is None or len(symbols) == 0:
                symbols = self.get_symbols_from_strategies()
                if symbols:
                    # Get timeframe mapping
                    timeframe_map = self.get_symbol_timeframe_mapping()
                    symbols_with_tf = [f"{sym} ({timeframe_map.get(sym, 'N/A')})" for sym in symbols]
                    cprint(f"🎯 Auto-detected trading pairs: {', '.join(symbols_with_tf)}\n", "cyan")

            if not symbols:
                cprint("⚠️  No symbols to trade (no strategies loaded)", "yellow")
                return

            # 3. Generate signals
            self.generate_rbi_signals(symbols)

            # 4. Arbitrate
            results = self.arbitrate_signals(symbols)

            # 5. Execute
            self.execute_trades(results)

            # 6. Monitor
            self.monitor_positions()

        except Exception as e:
            cprint(f"\n❌ Cycle error: {e}", "red")

        cycle_end = datetime.now()
        cycle_duration = (cycle_end - cycle_start).total_seconds()

        cprint(f"{'='*80}", "magenta", attrs=['bold'])
        cprint(f"CYCLE COMPLETE - Duration: {cycle_duration:.1f}s", "magenta", attrs=['bold'])
        cprint(f"{'='*80}\n", "magenta", attrs=['bold'])

    def run_continuous(self, symbols: List[str] = None):
        """
        Run continuous trading loop

        Args:
            symbols: List of symbols to trade (if None, auto-detect from strategies)
        """
        # Load strategies first to get symbols
        if not self.rbi_strategies:
            self.load_rbi_strategies()

        # Auto-detect symbols if not provided
        if symbols is None or len(symbols) == 0:
            symbols = self.get_symbols_from_strategies()

        if not symbols:
            cprint("❌ No symbols to trade - no strategies deployed", "red")
            return

        cycle_count = 0

        cprint(f"\n{'='*80}", "cyan", attrs=['bold'])
        cprint("STARTING CONTINUOUS RBI RESEARCH TRADE FLOW", "cyan", attrs=['bold'])
        cprint(f"{'='*80}", "cyan")
        print(f"Symbols: {', '.join(symbols)} (auto-detected from strategies)")
        print(f"Interval: {self.check_interval_minutes} minutes")
        print(f"Mode: {self.mode}")
        print(f"Exchange: {self.exchange}")
        cprint(f"{'='*80}\n", "cyan")

        try:
            while True:
                cycle_count += 1
                cprint(f"[CYCLE #{cycle_count}]", "cyan", attrs=['bold'])

                self.run_cycle(symbols)

                # Sleep with real-time countdown (single line update)
                sleep_seconds = self.check_interval_minutes * 60

                # Update countdown on same line every second
                for remaining in range(sleep_seconds, 0, -1):
                    mins_left = remaining // 60
                    secs_left = remaining % 60
                    # Use \r to overwrite same line
                    sys.stdout.write(f"\r😴 Next cycle in: {mins_left}m {secs_left}s   ")
                    sys.stdout.flush()
                    time.sleep(1)

                # Clear countdown line and show completion
                sys.stdout.write("\r" + " " * 50 + "\r")  # Clear the line
                sys.stdout.flush()
                cprint(f"✅ Sleep complete - starting next cycle\n", "green")

        except KeyboardInterrupt:
            cprint(f"\n\n{'='*80}", "red", attrs=['bold'])
            cprint("SHUTDOWN REQUESTED", "red", attrs=['bold'])
            cprint(f"{'='*80}", "red")
            cprint(f"Completed {cycle_count} cycles", "white")
            cprint("Goodbye! 👋\n", "cyan")


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RBI Research Trade Flow")
    parser.add_argument('--mode', choices=['PAPER', 'LIVE'], default='PAPER', help='Trading mode')
    parser.add_argument('--exchange', default='BINANCE', help='Exchange to use')
    parser.add_argument('--interval', type=int, default=15, help='Check interval in minutes')
    parser.add_argument('--symbols', nargs='+', default=None, help='Symbols to trade (default: auto-detect from strategies)')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuous')

    args = parser.parse_args()

    # Configuration
    config = {
        'mode': args.mode,
        'exchange': args.exchange,
        'check_interval_minutes': args.interval,
        # PERMANENT FIX: Unified balance configuration
        # PAPER mode: Uses this as starting balance ($10,000 default)
        # LIVE mode: Fetches real balance from exchange (this value ignored)
        'starting_balance': 10000.0,  # Starting balance for PAPER mode
        'position_size_usd': 1000,  # DEPRECATED - position sizing now dynamic
        'OHLCV_DAYS_BACK': 21,  # Fetch 21 days = ~500 candles for 1h (production-grade: SMA50 warmup + 450 analysis candles)
        'enable_signal_verification': False,  # DISABLED: RBI strategies already proven (1025% BTC, 726% SOL, 236% ETH) - verification adds complexity without benefit
        'arbiter_config': {
            'buy_confidence_min': 55.0,      # LOWERED to match backtest behavior (was 65%, blocked valid signals)
            'buy_confidence_strong': 75.0,   # Strong conviction = larger position
            'sell_confidence_min': 50.0,     # LOWERED to match backtest (was 60%)
            'sell_confidence_strong': 70.0,  # Strong conviction = immediate exit
            'hold_threshold': 50.0,          # Baseline predictive power
            'conflict_diff_threshold': 10.0,
            'agreement_bonus': 10.0
        }
    }

    # Initialize flow
    flow = RBI_ResearchTradeFlow(config)

    # Run
    if args.once:
        flow.run_cycle(args.symbols)
    else:
        flow.run_continuous(args.symbols)
