#!/usr/bin/env python3
"""
SCANNER_SWARM_TRADE_FLOW - ALTCOINS ONLY
Evidence-Based Scanner → AI Swarm Validation → Dynamic Risk → Execute

NEW CLEAN FLOW (NO Funding Rate, NO BTC/ETH/SOL engines)

Flow:
 ┌──────────────────┐
 │ Scanner Database │  ← Evidence-Based (12 filters)
 │ STRONG tokens    │     RSI, volume, momentum, liquidity
 │ (≥75/100 score)  │     NO AI, deterministic
 └────────┬─────────┘
          │
          ↓
 ┌──────────────────┐
 │ Swarm Agent      │  ← AI Validation (Multi-Model)
 │ (4-5 AI models)  │     DeepSeek, Claude, Grok, Qwen, GLM
 │ Consensus        │     Parallel queries → consensus summary
 └────────┬─────────┘
          │
          ↓
 ┌──────────────────┐
 │ Dynamic Risk     │  ← Regime detection, token scoring
 │ Engine           │     Position sizing based on risk
 └────────┬─────────┘
          │
          ↓
 ┌──────────────────┐
 │ Order Manager    │  ← SL/TP based on support/resistance
 │ (OCO orders)     │     Momentum-aware exits
 └────────┬─────────┘
          │
          ↓
     EXECUTE TRADES

Usage:
  # Single cycle test
  python trading_modes/SCANNER_SWARM_TRADE_FLOW.py --once

  # Continuous monitoring (RBI-style)
  python trading_modes/SCANNER_SWARM_TRADE_FLOW.py --monitor

  # Multiple workers
  python trading_modes/SCANNER_SWARM_TRADE_FLOW.py --monitor --workers 2

  # LIVE mode
  python trading_modes/SCANNER_SWARM_TRADE_FLOW.py --mode LIVE --monitor
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
import requests
import threading
from queue import Queue
from threading import Lock
import hashlib

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix Windows Unicode encoding issues
from src.utils.windows_unicode_fix import fix_windows_unicode
from src.unified_config import get_config
fix_windows_unicode()

from src.exchange_manager import ExchangeManager
from risk_management.trading_database import get_trading_db
from risk_management.dynamic_risk_engine import DynamicRiskEngine
from order_management.dynamic_order_manager import DynamicOrderManager
from trading_modes.core.altcoin_database import get_pairs_db
from trading_modes.core.arbiter import ArbitrationResult, DeterministicArbiter
from trading_modes.core.signal_bus import Signal, get_signal_bus
from trading_modes.core.signal_verification_agent import get_signal_verification_agent
import pandas as pd

cprint("\n" + "="*80, "cyan", attrs=['bold'])
cprint("SCANNER SWARM TRADE FLOW", "cyan", attrs=['bold'])
cprint("Scanner → Swarm Agent → Dynamic Risk → Execute", "cyan")
cprint("="*80 + "\n", "cyan")

# Global lock for console output (thread-safe printing)
console_lock = Lock()


def get_qualified_symbols_from_scanner(max_symbols=3, method='combined', fallback_symbols=None, mode='PAPER'):
    """
    Get qualified trading symbols from scanner database
    FILTERS OUT symbols with existing open trades

    Args:
        max_symbols: Maximum number of symbols to return (default: 3)
        method: 'scanner', 'active', or 'combined' (default: 'combined')
        fallback_symbols: Symbols to use if scanner has no results (default: [])
        mode: Trading mode to check for open trades (default: 'PAPER')

    Returns:
        List of token symbols (without USDT suffix)
    """
    if fallback_symbols is None:
        fallback_symbols = []

    try:
        db = get_pairs_db()
        trading_db = get_trading_db()

        # Get symbols with open trades
        open_trades = trading_db.get_open_trades(mode=mode)
        open_symbols = {trade['symbol'].replace('USDT', '') for trade in open_trades}

        if open_symbols:
            cprint(f"[FILTER] Excluding {len(open_symbols)} symbols with open trades: {', '.join(list(open_symbols)[:5])}", "yellow")

        if method == 'combined':
            # Scanner STRONG + Currently Active
            scanner_picks = db.get_cached_scanner_results(max_age_hours=6)
            scanner_symbols = {r['symbol'] for r in scanner_picks if r['classification'] == 'STRONG'}

            active_pairs = db.get_active_pairs(min_volume=10_000_000, max_age_hours=2)
            active_symbols = {p['symbol'] for p in active_pairs}

            # Intersection: Scanner STRONG + Active
            qualified_symbols = scanner_symbols & active_symbols

            # CRITICAL: Filter out symbols with open trades
            qualified_symbols = {s for s in qualified_symbols if s.replace('USDT', '') not in open_symbols}

            cprint(f"[COMBINED] Scanner STRONG: {len(scanner_symbols)}, Active: {len(active_symbols)}, "
                   f"After filtering open trades: {len(qualified_symbols)}", "cyan")

            if not qualified_symbols:
                cprint("[WARN] No intersection (or all filtered out), using scanner STRONG picks only", "yellow")
                qualified_symbols = {s for s in scanner_symbols if s.replace('USDT', '') not in open_symbols}

            if qualified_symbols:
                # Sort by scanner score
                qualified_with_data = [r for r in scanner_picks if r['symbol'] in qualified_symbols]
                qualified_with_data.sort(key=lambda x: x['score'], reverse=True)
                symbols = [p['symbol'].replace('USDT', '') for p in qualified_with_data[:max_symbols]]
                cprint(f"[QUALIFIED] Using {len(symbols)} tokens: {', '.join(symbols)}", "green", attrs=['bold'])
                return symbols

        # If no results
        if fallback_symbols:
            cprint(f"[WARN] No scanner results, using fallback: {', '.join(fallback_symbols)}", "yellow")
        return fallback_symbols

    except Exception as e:
        cprint(f"[ERROR] Failed to get symbols from scanner: {e}", "red")
        return fallback_symbols


def get_symbol_hash(symbols: list) -> str:
    """Generate hash for symbol list (for deduplication)"""
    symbol_str = '|'.join(sorted(symbols))
    return hashlib.md5(symbol_str.encode()).hexdigest()


def scanner_monitor_thread(symbol_queue: Queue, processed_symbols: set, queue_lock: Lock, stop_flag: dict, config: dict):
    """
    Producer thread - UNIFIED SCANNER: Scans Binance + monitors database for STRONG signals
    """
    db = get_pairs_db()
    check_interval_seconds = config.get('scanner_check_interval_seconds', 60)
    max_symbols = config.get('max_symbols', 3)
    scanner_method = config.get('scanner_method', 'combined')
    mode = config.get('mode', 'PAPER')

    with console_lock:
        cprint("🔍 UNIFIED Scanner Monitor Started (Built-in Scanning)", "cyan", attrs=['bold'])
        cprint(f"   Check Interval: {check_interval_seconds}s", "cyan")
        cprint(f"   Method: {scanner_method}", "cyan")
        cprint(f"   Max Symbols: {max_symbols}", "cyan")
        cprint(f"   Auto-Scan: Enabled (scans Binance every cycle)\n", "green")

    scan_cycle = 0

    while not stop_flag.get('stop', False):
        try:
            scan_cycle += 1

            # UNIFIED APPROACH: Run built-in scanner every cycle
            with console_lock:
                cprint(f"\n{'='*60}", "cyan")
                cprint(f"SCANNER CYCLE #{scan_cycle} - {datetime.now().strftime('%H:%M:%S')}", "cyan", attrs=['bold'])
                cprint(f"{'='*60}", "cyan")

            # Import and run the scanner directly
            try:
                from trading_modes.binance_altcoin_scanner import BinanceAltcoinScanner

                with console_lock:
                    cprint("  [SCAN] Running built-in Binance altcoin scanner...", "yellow")

                # Initialize scanner and run complete workflow
                scanner = BinanceAltcoinScanner()

                # Step 1: Get all USDT pairs
                all_pairs = scanner.get_all_usdt_pairs()

                if all_pairs:
                    # Step 2: Pre-filter
                    filtered = scanner.pre_filter(all_pairs)

                    if filtered:
                        # Step 3: Score tokens
                        scored = scanner.score_all_tokens(filtered)

                        if scored:
                            # Step 4: Save results (automatically caches to database)
                            scanner.save_results(scored)

                            # Extract STRONG results
                            strong_count = sum(1 for t in scored if t['classification'] == 'STRONG')

                            with console_lock:
                                cprint(f"  [OK] Scanner complete: {strong_count} STRONG signals found", "green")

                                # Show top 5
                                strong_tokens = [t for t in scored if t['classification'] == 'STRONG'][:5]
                                if strong_tokens:
                                    top_symbols = [t['symbol'] for t in strong_tokens]
                                    cprint(f"       Top 5: {', '.join(top_symbols)}", "white")
                        else:
                            with console_lock:
                                cprint(f"  [INFO] No tokens scored above threshold", "yellow")
                    else:
                        with console_lock:
                            cprint(f"  [INFO] No tokens passed pre-filter", "yellow")
                else:
                    with console_lock:
                        cprint(f"  [WARN] Failed to fetch Binance pairs", "yellow")

            except Exception as scan_error:
                import traceback
                with console_lock:
                    cprint(f"  [ERROR] Scanner failed: {scan_error}", "red")
                    cprint(f"  {traceback.format_exc()}", "red")
                    cprint(f"  [INFO] Will retry next cycle", "yellow")

            # Get qualified symbols from scanner (filters out symbols with open trades)
            symbols = get_qualified_symbols_from_scanner(
                max_symbols=max_symbols,
                method=scanner_method,
                fallback_symbols=[],
                mode=mode
            )

            if symbols:
                symbol_hash = get_symbol_hash(symbols)

                # Check if this symbol combination is new (thread-safe)
                with queue_lock:
                    already_processed = symbol_hash in processed_symbols

                if not already_processed:
                    # Queue new symbol combination
                    symbol_queue.put(symbols)
                    with queue_lock:
                        processed_symbols.add(symbol_hash)

                    with console_lock:
                        cprint(f"🆕 NEW SYMBOLS QUEUED: {', '.join(symbols)}", "green", attrs=['bold'])
                else:
                    with console_lock:
                        cprint(f"⏭️  No change in symbols: {', '.join(symbols)}", "white")

            # Wait before next check
            time.sleep(check_interval_seconds)

        except Exception as e:
            with console_lock:
                cprint(f"❌ Scanner monitor error: {e}", "red")
            time.sleep(check_interval_seconds)


def trading_worker_thread(worker_id: int, symbol_queue: Queue, processed_symbols: set, queue_lock: Lock,
                         stats: dict, stop_flag: dict, flow_instance):
    """
    Consumer thread - processes new symbols by running trading cycles
    """
    with console_lock:
        cprint(f"🤖 Worker Thread {worker_id} Started", "cyan")

    while not stop_flag.get('stop', False):
        try:
            # Get symbols from queue (timeout 1 second to check stop_flag)
            try:
                symbols = symbol_queue.get(timeout=1)
            except:
                continue  # Queue empty, check again

            with console_lock:
                stats['active'] += 1
                cprint(f"\n🚀 Worker {worker_id} processing: {', '.join(symbols)}", "cyan", attrs=['bold'])

            # Run trading cycle
            start_time = datetime.now()
            try:
                flow_instance.run_cycle(symbols)
                success = True
            except Exception as e:
                with console_lock:
                    cprint(f"❌ Cycle error: {e}", "red")
                success = False

            total_time = (datetime.now() - start_time).total_seconds()

            # Update stats
            with console_lock:
                stats['completed'] += 1
                stats['active'] -= 1

                if success:
                    stats['successful'] += 1
                    cprint(f"\n{'='*60}", "green")
                    cprint(f"✅ Worker {worker_id} COMPLETED ({stats['completed']} total) - {total_time:.1f}s",
                           "green", attrs=['bold'])
                else:
                    stats['failed'] += 1
                    cprint(f"\n{'='*60}", "red")
                    cprint(f"❌ Worker {worker_id} FAILED ({stats['failed']} failed) - {total_time:.1f}s", "red")

                cprint(f"{'='*60}\n", "white")

        except Exception as e:
            with console_lock:
                cprint(f"❌ Worker {worker_id} error: {e}", "red")


class ScannerSwarmTradeFlow:
    """
    Scanner → Swarm Agent → Dynamic Risk → Execute

    Clean flow for altcoin trading:
    1. Scanner finds STRONG tokens (evidence-based)
    2. Swarm Agent validates with multiple AI models
    3. Dynamic Risk Engine calculates position size
    4. Order Manager sets SL/TP
    5. Execute trade
    """

    def __init__(self, config: Dict):
        self.config = config
        self.mode = config.get('mode', 'PAPER')
        self.exchange = config.get('exchange', 'BINANCE')
        self.check_interval_minutes = config.get('check_interval_minutes', 15)

        # Components
        self.db = get_trading_db()
        self.risk_engine = DynamicRiskEngine()
        self.order_manager = DynamicOrderManager()

        # Signal bus and arbiter (UNIFIED approach)
        self.signal_bus = get_signal_bus()
        arbiter_config = config.get('arbiter_config', {
            'buy_confidence_min': 75.0,      # Higher bar for entering positions (capital risk)
            'buy_confidence_strong': 85.0,   # Strong conviction = larger position
            'sell_confidence_min': 65.0,     # Lower bar for protecting capital (loss prevention)
            'sell_confidence_strong': 80.0,  # Strong conviction = immediate exit
            'hold_threshold': 50.0,          # Baseline predictive power
            'conflict_threshold': 10.0,
            'agreement_bonus': 10.0
        })
        self.arbiter = DeterministicArbiter(arbiter_config)

        # Exchange manager
        try:
            self.exchange_manager = ExchangeManager(exchange=self.exchange)
            cprint(f"✅ ExchangeManager initialized: {self.exchange}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize exchange: {e}", "red")
            cprint("   Continuing in PAPER mode only", "yellow")
            self.mode = 'PAPER'
            self.exchange_manager = None

        cprint(f"\n{'='*80}", "cyan")
        cprint("SCANNER SWARM TRADE FLOW INITIALIZED", "cyan", attrs=['bold'])
        cprint(f"{'='*80}", "cyan")
        print(f"Mode: {self.mode}")
        print(f"Exchange: {self.exchange}")
        print(f"Check Interval: {self.check_interval_minutes} minutes")
        cprint(f"{'='*80}\n", "cyan")

    def run_cycle(self, symbols):
        """Run one complete cycle"""
        cycle_start = datetime.now()

        cprint(f"\n{'='*80}", "cyan", attrs=['bold'])
        cprint("SCANNER SWARM FLOW - CYCLE START", "cyan", attrs=['bold'])
        cprint(f"Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}", "cyan")
        cprint(f"{'='*80}\n", "cyan", attrs=['bold'])

        try:
            # STEP 0: Position Monitoring (Check SL/TP FIRST before opening new trades)
            cprint("[0/6] Position Monitoring (Check SL/TP)...", "yellow")

            from trading_modes.core.position_monitor import PositionMonitor
            monitor = PositionMonitor()
            closed_count = monitor.check_and_close_positions(mode=self.mode, verbose=True)

            if closed_count > 0:
                cprint(f"\n  ✅ Closed {closed_count} positions (SL/TP hit)", "green", attrs=['bold'])

            # STEP 1: Filter out symbols with existing open trades
            cprint("\n[1/6] Trade Deduplication Check...", "yellow")

            # Get all open trades for current mode
            open_trades = self.db.get_open_trades(mode=self.mode)

            # Create dict of symbol -> trade info for open trades
            open_symbols = {}
            for trade in open_trades:
                symbol_base = trade['symbol'].replace('USDT', '')
                open_symbols[symbol_base] = {
                    'trade_id': trade['trade_id'],
                    'entry_time': trade['timestamp'],
                    'side': trade['side'],
                    'position_size_usd': trade['position_size_usd']
                }

            # Filter symbols - remove any with open trades
            filtered_symbols = []
            skipped_symbols = []

            for symbol in symbols:
                symbol_base = symbol.replace('USDT', '')

                if symbol_base in open_symbols:
                    trade_info = open_symbols[symbol_base]
                    entry_time = trade_info['entry_time']

                    # Calculate how long trade has been open
                    if isinstance(entry_time, str):
                        entry_dt = datetime.fromisoformat(entry_time)
                    else:
                        entry_dt = entry_time

                    hours_open = (datetime.now() - entry_dt).total_seconds() / 3600

                    skipped_symbols.append(symbol_base)
                    cprint(f"     ⏭️  SKIP {symbol_base}: Open trade exists (opened {hours_open:.1f}h ago, ${trade_info['position_size_usd']:.2f} {trade_info['side']})", "yellow")
                else:
                    filtered_symbols.append(symbol)

            # Show summary
            if skipped_symbols:
                cprint(f"\n     ✅ Processing: {len(filtered_symbols)} symbols", "green")
                cprint(f"     ⏭️  Skipped: {len(skipped_symbols)} symbols (open trades exist)", "yellow")
            else:
                cprint(f"     ✅ All {len(filtered_symbols)} symbols clear (no open trades)", "green")

            # If all symbols filtered out, exit cycle early
            if not filtered_symbols:
                cprint(f"\n❌ No symbols to process (all have open trades)", "red")
                cprint("   Waiting for existing trades to close before opening new positions...", "yellow")
                return

            # Update symbols list to only include non-open-trade symbols
            symbols = filtered_symbols

            # CIRCUIT BREAKER: Stop opening new trades if we have 5+ positions
            MAX_OPEN_TRADES = 5
            current_open_count = len(open_symbols)

            if current_open_count >= MAX_OPEN_TRADES:
                cprint(f"\n⚠️  CIRCUIT BREAKER ACTIVATED", "yellow", attrs=['bold'])
                cprint(f"   Current open trades: {current_open_count}/{MAX_OPEN_TRADES}", "yellow")
                cprint(f"   Reason: Maximum position limit reached", "yellow")
                cprint(f"   Action: Skipping AI analysis and new trade entry", "yellow")
                cprint(f"   Cost Saved: ~${len(symbols) * 2:.2f} (AI calls avoided)", "green")
                cprint(f"   Note: Existing positions will continue to be monitored", "cyan")
                cprint(f"\n   Waiting for trades to close before accepting new signals...", "white")
                return

            # Step 2: Scanner-based analysis (Evidence-based, NO AI)
            cprint("\n[2/6] Scanner-Based Analysis (Evidence-Based, NO AI)...", "yellow")
            cprint(f"     Symbols: {', '.join(symbols)}", "cyan")
            cprint("     Scanner qualification: STRONG (score ≥75/100)", "cyan")
            cprint("     Filters: RSI trend, volume-price correlation, momentum, liquidity, etc.", "cyan")

            # Step 3: Independent AI Validation (GATHER REAL MARKET DATA)
            cprint("\n[3/6] Independent AI Validation (Real Market Analysis)...", "yellow")

            # Import swarm agent and market data API
            from src.agents.swarm_agent import SwarmAgent
            from risk_management.binance_truth_paper_trading import BinanceTruthAPI

            # Query swarm for each symbol WITH REAL MARKET DATA
            swarm_results = {}
            try:
                swarm = SwarmAgent()

                for symbol in symbols:
                    cprint(f"\n  [DATA] Gathering market data for {symbol}...", "cyan")

                    # GATHER REAL MARKET DATA (user requirement)
                    try:
                        # Get current price and 24h stats
                        ticker = BinanceTruthAPI.token_overview(symbol)
                        current_price = ticker.get('price_usd', 0)
                        volume_24h = ticker.get('volume_24h_usd', 0)
                        price_change_24h = ticker.get('price_change_24h_pct', 0)

                        # Get OHLCV for technical indicators
                        ohlcv = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe='15m', days_back=3)

                        if ohlcv is None or len(ohlcv) < 50:
                            cprint(f"  ⚠️  Insufficient data for {symbol}, skipping AI validation", "yellow")
                            continue

                        # Calculate RSI
                        delta = ohlcv['close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = 100 - (100 / (1 + rs))
                        current_rsi = rsi.iloc[-1]

                        # Calculate MACD
                        exp1 = ohlcv['close'].ewm(span=12, adjust=False).mean()
                        exp2 = ohlcv['close'].ewm(span=26, adjust=False).mean()
                        macd = exp1 - exp2
                        signal = macd.ewm(span=9, adjust=False).mean()
                        macd_histogram = macd - signal
                        current_macd_hist = macd_histogram.iloc[-1]

                        # Volume trend (current vs 20-period average)
                        avg_volume = ohlcv['volume'].rolling(window=20).mean().iloc[-1]
                        current_volume = ohlcv['volume'].iloc[-1]
                        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

                    except Exception as e:
                        cprint(f"  ⚠️  Error fetching data for {symbol}: {e}", "yellow")
                        continue

                    # INDEPENDENT AI PROMPT (NO BIAS - user requirement)
                    prompt = f"""INDEPENDENT trading analysis for {symbol}.

CURRENT MARKET DATA:
- Price: ${current_price:.6f}
- 24h Change: {price_change_24h:+.2f}%
- 24h Volume: ${volume_24h:,.0f}
- RSI (14): {current_rsi:.1f}
- MACD Histogram: {current_macd_hist:.6f}
- Volume vs Avg: {volume_ratio:.2f}x

PROVIDE YOUR INDEPENDENT RECOMMENDATION:

1. Signal: BUY, SELL, or NEUTRAL
2. Confidence: 0-100%
3. Key Reasoning: 2-3 sentences

IMPORTANT:
- Be contrarian if data doesn't support bullish bias
- RSI >70 = overbought risk
- MACD negative = bearish momentum
- Low volume = weak conviction
- Don't just agree - provide real analysis"""

                    cprint(f"  [AI] Independent analysis for {symbol}...", "cyan")
                    result = swarm.query(prompt, system_prompt="You are an independent crypto trading analyst. Provide objective analysis based ONLY on the market data provided. Be contrarian when appropriate.")

                    # Extract consensus
                    consensus = result.get("consensus_summary", "No consensus available")
                    swarm_results[symbol] = {
                        'consensus': consensus,
                        'responses': result.get('responses', {}),
                        'timestamp': datetime.now(),
                        'market_data': {
                            'price': current_price,
                            'rsi': current_rsi,
                            'macd_hist': current_macd_hist,
                            'volume_ratio': volume_ratio,
                            'price_change_24h': price_change_24h
                        }
                    }

                    cprint(f"  [AI VERDICT] {symbol}: {consensus}", "green")

            except Exception as e:
                cprint(f"  [WARN] AI validation unavailable: {e}", "yellow")
                cprint("  [INFO] Proceeding with scanner confidence only", "yellow")

            # Step 4: PUBLISH SIGNALS TO BUS AND ARBITRATE
            cprint("\n[4/6] Publishing Signals & Arbitration (Deterministic Arbiter)...", "yellow")

            import re

            for symbol in symbols:
                # Get AI analysis if available
                swarm_data = swarm_results.get(symbol, {})
                consensus = swarm_data.get('consensus', '')
                market_data = swarm_data.get('market_data', {})
                responses = swarm_data.get('responses', {})

                # Scanner signal (always STRONG/BUY for these symbols)
                scanner_signal = "BUY"
                scanner_confidence = 75  # STRONG qualification minimum

                # Parse individual AI model signals (NOT summary text)
                ai_signals = []
                ai_confidences = []

                for model_name, response_data in responses.items():
                    response = response_data.get('response', '')

                    # Extract explicit signal declarations
                    if 'Signal: BUY' in response or 'Signal: **BUY' in response or '**Signal: BUY' in response:
                        ai_signals.append('BUY')
                    elif 'Signal: SELL' in response or 'Signal: **SELL' in response or '**Signal: SELL' in response:
                        ai_signals.append('SELL')
                    elif 'Signal: NEUTRAL' in response or 'Signal: **NEUTRAL' in response or '**Signal: NEUTRAL' in response:
                        ai_signals.append('NEUTRAL')

                    # Extract confidence (0-100%)
                    conf_match = re.search(r'Confidence:?\s*(\d{1,3})%', response)
                    if conf_match:
                        ai_confidences.append(int(conf_match.group(1)))

                # Determine consensus via VOTING
                buy_count = ai_signals.count('BUY')
                sell_count = ai_signals.count('SELL')
                neutral_count = ai_signals.count('NEUTRAL')
                total_models = len(ai_signals)

                if total_models >= 3:
                    if buy_count >= 3:  # Majority (3/5 models)
                        ai_signal = "BUY"
                    elif sell_count >= 3:
                        ai_signal = "SELL"
                    else:
                        ai_signal = "NEUTRAL"  # Default to caution
                else:
                    ai_signal = "NEUTRAL"  # Insufficient data

                # CRITICAL FIX: Calculate confidence based on vote agreement
                # Unanimous NEUTRAL (5/5 or 4/5) should have HIGH confidence to veto Scanner
                avg_confidence = sum(ai_confidences) / len(ai_confidences) if ai_confidences else 50

                if ai_signal == "NEUTRAL":
                    # Strong NEUTRAL consensus when few/zero BUY votes
                    if buy_count == 0 and sell_count == 0:
                        # Unanimous NEUTRAL (5/5) = 95% confidence veto
                        ai_confidence = 95.0
                    elif buy_count == 0 and neutral_count >= 3:
                        # Strong NEUTRAL (0 BUY, 3+ NEUTRAL) = 85% confidence veto
                        ai_confidence = 85.0
                    elif neutral_count >= 3:
                        # Majority NEUTRAL = 75% confidence
                        ai_confidence = 75.0
                    else:
                        # Weak NEUTRAL = use average
                        ai_confidence = avg_confidence
                else:
                    # For BUY/SELL, use average confidence as before
                    ai_confidence = avg_confidence

                # Apply text-based confidence penalties
                consensus_lower = consensus.lower()
                if 'weak' in consensus_lower:
                    ai_confidence -= 15
                if 'lacking' in consensus_lower or 'lacks' in consensus_lower:
                    ai_confidence -= 10

                # Volume divergence veto rules (CRITICAL)
                volume_ratio = market_data.get('volume_ratio', 1.0)
                rsi = market_data.get('rsi', 50)
                macd_hist = market_data.get('macd_hist', 0)

                # PERMANENT FIX: Volume thresholds from unified config
                config = get_config()
                volume_veto = config.VOLUME_RATIO_VETO
                volume_warning = config.VOLUME_RATIO_WARNING
                confidence_penalty = config.VOLUME_WARNING_CONFIDENCE_PENALTY

                # Hard veto: Volume below threshold = manipulation risk
                if volume_ratio < volume_veto:
                    cprint(f"\n  [VETO] {symbol}: Volume {volume_ratio:.2f}x < {volume_veto}x threshold - SKIP", "red", attrs=['bold'])
                    continue  # Skip to next symbol

                # Volume warning: Below warning threshold
                if volume_veto <= volume_ratio < volume_warning:
                    ai_confidence *= confidence_penalty  # Configurable confidence reduction

                # Negative MACD override
                if macd_hist < 0 and rsi > 35 and ai_signal == "BUY":
                    ai_signal = "NEUTRAL"  # Downgrade to neutral

                # Display signal analysis
                cprint(f"\n  [SIGNALS] {symbol}:", "cyan", attrs=['bold'])
                cprint(f"     Scanner: {scanner_signal} @ {scanner_confidence}%", "white")
                cprint(f"     AI Votes: {buy_count} BUY, {neutral_count} NEUTRAL, {sell_count} SELL ({total_models} models)", "white")
                cprint(f"     AI Consensus: {ai_signal} @ {ai_confidence:.0f}%", "white")
                cprint(f"     Market: Vol {volume_ratio:.2f}x, RSI {rsi:.1f}, MACD {macd_hist:.6f}", "white")

                # MULTI-MODEL SIGNAL VERIFICATION (HYBRID APPROACH)
                # Cross-check Scanner signal against REAL technical indicators with 5 AI models
                cprint(f"\n  [VERIFICATION] Running multi-model verification...", "yellow")
                verification_agent = get_signal_verification_agent()
                verification_result_obj = verification_agent.verify_signal(
                    symbol=symbol,
                    timeframe="15m",
                    scanner_signal=scanner_signal,
                    scanner_confidence=scanner_confidence,
                    strategy_name="Scanner_Swarm"
                )

                # Extract result from Result object
                if verification_result_obj.is_failure():
                    cprint(f"  [WARN] Verification failed: {verification_result_obj.error}", "yellow")
                    # Continue with scanner signal
                else:
                    verification_result = verification_result_obj.value

                    # If verification DISAGREES with scanner, override AI signal
                    if not verification_result['agrees_with_scanner']:
                        cprint(f"  [OVERRIDE] Verification agent detected FALSE SIGNAL - overriding AI consensus", "red", attrs=['bold'])
                        ai_signal = verification_result['action']
                        ai_confidence = verification_result['confidence']
                        cprint(f"  [NEW CONSENSUS] {ai_signal} @ {ai_confidence:.0f}% (verified by {verification_result['agreement_level']})", "yellow", attrs=['bold'])

                # PUBLISH SIGNALS TO BUS (for arbiter)
                # Publish Scanner signal
                scanner_sig = Signal(
                    source="SCANNER",
                    symbol=symbol,
                    timeframe="15m",
                    action=scanner_signal,
                    confidence=scanner_confidence,
                    ttl_sec=1800,
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    metadata={'source': 'scanner_database', 'classification': 'STRONG'}
                )
                self.signal_bus.publish(scanner_sig)

                # Publish Swarm signal (CRITICAL FIX: Publish NEUTRAL signals too for conflict detection)
                # NEUTRAL signals MUST be published so arbiter sees Scanner BUY vs Swarm NEUTRAL conflicts
                if ai_signal != 'SKIP':  # Publish BUY, SELL, and NEUTRAL (but not SKIP)
                    swarm_sig = Signal(
                        source="SWARM",
                        symbol=symbol,
                        timeframe="15m",
                        action=ai_signal,  # Can be BUY, SELL, or NEUTRAL
                        confidence=ai_confidence,
                        ttl_sec=1800,
                        timestamp=datetime.utcnow().isoformat() + 'Z',
                        metadata={
                            'consensus': consensus,
                            'ai_votes': {'BUY': buy_count, 'NEUTRAL': neutral_count, 'SELL': sell_count},
                            'market_data': market_data
                        }
                    )
                    self.signal_bus.publish(swarm_sig)

            # Step 5: ARBITRATE USING DETERMINISTIC ARBITER
            cprint("\n[5/6] Arbitrating Signals (Deterministic Arbiter)...", "yellow")

            results = {}
            for symbol in symbols:
                result = self.arbiter.arbitrate(symbol, "15m")

                cprint(f"\n  [ARBITER] {symbol}:", "cyan", attrs=['bold'])
                cprint(f"     Decision: {result.action}", "white")
                cprint(f"     Confidence: {result.confidence:.1f}%", "white")
                cprint(f"     Size Multiplier: {result.size_multiplier:.2f}x", "white")
                cprint(f"     Reasoning: {result.reasoning}", "white")

                if result.action not in ['NEUTRAL', 'WAIT']:
                    results[symbol] = result

            # Step 6: Execute with Dynamic Risk + Order Management
            cprint("\n[6/6] Executing with Dynamic Risk/Order Systems...", "yellow")
            self._execute_trades_dynamic(results)

            # Step 7: Display Open Positions
            cprint("\n[7/7] Open Positions Summary...", "yellow")
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
        """Execute trades using Dynamic Risk + Order Management"""
        executed_count = 0

        # Get current portfolio equity
        equity_usd = self.config.get('equity_usd', 10000.0)

        # Get PnL history from database
        pnl_history_raw = self.db.get_pnl_history(mode=self.mode, days=30)
        if pnl_history_raw:
            pnl_history = pd.DataFrame(pnl_history_raw)
        else:
            pnl_history = pd.DataFrame({'timestamp': [], 'pnl_usd': []})

        for symbol, result in arbitration_results.items():
            if result.action in ['BUY', 'SELL'] and result.confidence >= 70:
                cprint(f"\n  🎯 Processing {result.action} for {symbol}...", "cyan")

                try:
                    # Get OHLCV data from Binance (REAL data)
                    from risk_management.binance_truth_paper_trading import BinanceTruthAPI
                    ohlcv = BinanceTruthAPI.get_ohlcv_data(symbol, timeframe='15m', days_back=3)

                    if ohlcv is None or len(ohlcv) < 50:
                        cprint(f"     ⚠️  Insufficient OHLCV data for {symbol}", "yellow")
                        continue

                    entry_price = float(ohlcv['close'].iloc[-1])

                    # Update market regime (MUST call this first!)
                    self.risk_engine.update_regime(ohlcv)
                    regime = self.risk_engine.current_regime
                    regime_config = self.risk_engine.current_regime_config
                    cprint(f"     📊 Market Regime: {regime.value}", "white")

                    # Score token risk from Binance
                    token_data = BinanceTruthAPI.token_overview(symbol)
                    volume_24h_usd = token_data.get('volume_24h_usd', 1_000_000)
                    market_cap_usd = token_data.get('market_cap_usd', 100_000_000)
                    avg_spread_bps = token_data.get('spread_bps', 10)

                    # Update token profile (stores in risk_engine.token_profiles)
                    self.risk_engine.update_token_profile(
                        symbol, ohlcv, volume_24h_usd, market_cap_usd, avg_spread_bps
                    )
                    token_profile = self.risk_engine.token_profiles[symbol]
                    cprint(f"     🎯 Token Risk Score: {token_profile.risk_score:.2f}", "white")

                    # Update dynamic limits (MUST call after update_regime!)
                    self.risk_engine.update_limits(equity_usd, pnl_history)

                    # Calculate position size using DynamicRiskEngine (uses stored token_profile and regime_config)
                    position_size_usd, _, _ = self.risk_engine.get_position_sizing(
                        symbol=symbol,
                        equity_usd=equity_usd,
                        entry_price=entry_price,
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
                        # Generate trade ID
                        import uuid
                        trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

                        # Get TP prices (handle single or multiple TPs)
                        tp1_price = order_plan.take_profits[0].price if len(order_plan.take_profits) > 0 else entry_price * 1.05
                        tp2_price = order_plan.take_profits[1].price if len(order_plan.take_profits) > 1 else entry_price * 1.10
                        tp3_price = order_plan.take_profits[2].price if len(order_plan.take_profits) > 2 else entry_price * 1.15

                        # Get TP allocations
                        tp1_pct = order_plan.take_profits[0].allocation_pct if len(order_plan.take_profits) > 0 else 50.0
                        tp2_pct = order_plan.take_profits[1].allocation_pct if len(order_plan.take_profits) > 1 else 30.0
                        tp3_pct = order_plan.take_profits[2].allocation_pct if len(order_plan.take_profits) > 2 else 20.0

                        cprint(f"     📝 PAPER trade logged", "cyan")
                        self.db.insert_trade(
                            trade_id=trade_id,
                            symbol=symbol,
                            side=result.action,
                            entry_price=entry_price,
                            position_size_usd=position_size_usd,
                            stop_loss=order_plan.stop_loss.price,
                            tp1_price=tp1_price,
                            tp2_price=tp2_price,
                            tp3_price=tp3_price,
                            tp1_pct=tp1_pct,
                            tp2_pct=tp2_pct,
                            tp3_pct=tp3_pct,
                            mode=self.mode,
                            strategy_name="SCANNER_SWARM_AI",
                            confidence=str(result.confidence),
                            metadata={
                                'regime': regime.value,
                                'token_risk_score': token_profile.risk_score,
                                'swarm_consensus': result.metadata.get('swarm_consensus'),
                                'scanner_score': result.metadata.get('scanner_score', 'N/A'),
                                'order_plan_rationale': order_plan.stop_loss.rationale
                            }
                        )

                    executed_count += 1

                except Exception as e:
                    cprint(f"     ❌ Execution failed: {e}", "red")

        cprint(f"\n  Executed {executed_count} trades using DYNAMIC systems\n", "cyan", attrs=['bold'])

    def run_continuous_monitored(self, num_workers=1):
        """
        Run continuous monitoring mode (RBI-style scanner monitoring)
        """
        cprint(f"\n{'='*80}", "magenta", attrs=['bold'])
        cprint("CONTINUOUS MONITORING MODE", "magenta", attrs=['bold'])
        cprint(f"{'='*80}", "magenta", attrs=['bold'])
        cprint(f"Workers: {num_workers}", "white")
        cprint(f"Scanner Check Interval: {self.config.get('scanner_check_interval_seconds', 60)}s", "white")
        cprint(f"Scanner Method: {self.config.get('scanner_method', 'combined')}", "white")
        cprint(f"Max Symbols: {self.config.get('max_symbols', 3)}", "white")
        cprint(f"{'='*80}\n", "magenta", attrs=['bold'])

        # Thread-safe data structures
        symbol_queue = Queue()
        processed_symbols = set()
        queue_lock = Lock()
        stop_flag = {'stop': False}
        stats = {
            'completed': 0,
            'successful': 0,
            'failed': 0,
            'active': 0
        }

        # Start monitor thread (producer)
        monitor = threading.Thread(
            target=scanner_monitor_thread,
            args=(symbol_queue, processed_symbols, queue_lock, stop_flag, self.config),
            daemon=True
        )
        monitor.start()

        # Start worker threads (consumers)
        workers = []
        for i in range(num_workers):
            worker = threading.Thread(
                target=trading_worker_thread,
                args=(i + 1, symbol_queue, processed_symbols, queue_lock, stats, stop_flag, self),
                daemon=True
            )
            worker.start()
            workers.append(worker)

        # Main thread monitors stats (DISABLED - interrupts scanner output)
        try:
            while True:
                time.sleep(30)  # Check every 30 seconds but don't print
                # Stats printing disabled to prevent interrupting scanner output
                # Stats are still tracked in background and shown at shutdown

        except KeyboardInterrupt:
            cprint(f"\n\n{'='*80}", "red", attrs=['bold'])
            cprint("SHUTTING DOWN CONTINUOUS MONITORING", "red", attrs=['bold'])
            cprint(f"{'='*80}", "red", attrs=['bold'])

            # Signal threads to stop
            stop_flag['stop'] = True

            # Wait for threads to finish
            cprint("Waiting for threads to finish...", "yellow")
            monitor.join(timeout=5)
            for worker in workers:
                worker.join(timeout=5)

            # Final stats
            cprint(f"\n{'='*80}", "green", attrs=['bold'])
            cprint("FINAL STATS", "green", attrs=['bold'])
            cprint(f"{'='*80}", "green")
            cprint(f"Completed Cycles: {stats['completed']}", "white")
            cprint(f"Successful: {stats['successful']}", "green")
            cprint(f"Failed: {stats['failed']}", "red")
            cprint(f"{'='*80}\n", "green", attrs=['bold'])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scanner Swarm Trade Flow")
    parser.add_argument('--mode', choices=['PAPER', 'LIVE'], default='PAPER')
    parser.add_argument('--exchange', default='BINANCE')
    parser.add_argument('--scanner-method', choices=['scanner', 'active', 'combined'], default='combined')
    parser.add_argument('--max-symbols', type=int, default=3)
    parser.add_argument('--once', action='store_true', help='Run single cycle and exit')
    parser.add_argument('--monitor', action='store_true', help='Continuous monitoring mode (RBI-style)')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker threads for monitoring mode')
    parser.add_argument('--scanner-check-interval', type=int, default=60, help='Scanner check interval in seconds')

    args = parser.parse_args()

    config = {
        'mode': args.mode,
        'exchange': args.exchange,
        'equity_usd': 10000,
        'min_trade_usd': 100,
        'scanner_check_interval_seconds': args.scanner_check_interval,
        'scanner_method': args.scanner_method,
        'max_symbols': args.max_symbols,
        'arbiter_config': {
            'buy_confidence_min': 75.0,      # Higher bar for entering positions (capital risk)
            'buy_confidence_strong': 85.0,   # Strong conviction = larger position
            'sell_confidence_min': 65.0,     # Lower bar for protecting capital (loss prevention)
            'sell_confidence_strong': 80.0,  # Strong conviction = immediate exit
            'hold_threshold': 50.0,          # Baseline predictive power
            'conflict_threshold': 10.0,
            'agreement_bonus': 10.0
        }
    }

    cprint(f"Mode: {args.mode}", "white")
    cprint(f"Exchange: {args.exchange}", "white")

    # UNIFIED APPROACH: Run scanner first (unless in monitor mode where it runs continuously)
    if args.once:
        cprint("\n🔍 Running built-in scanner first...\n", "cyan", attrs=['bold'])
        try:
            from trading_modes.binance_altcoin_scanner import BinanceAltcoinScanner

            scanner = BinanceAltcoinScanner()

            # Run complete scanner workflow
            all_pairs = scanner.get_all_usdt_pairs()
            if all_pairs:
                filtered = scanner.pre_filter(all_pairs)
                if filtered:
                    scored = scanner.score_all_tokens(filtered)
                    if scored:
                        scanner.save_results(scored)
                        strong_count = sum(1 for t in scored if t['classification'] == 'STRONG')
                        cprint(f"\n✅ Scanner complete: {strong_count} STRONG signals cached to database\n", "green")
                    else:
                        cprint("\n[WARN] No tokens scored above threshold\n", "yellow")
                else:
                    cprint("\n[WARN] No tokens passed pre-filter\n", "yellow")
            else:
                cprint("\n[ERROR] Failed to fetch Binance pairs\n", "red")

        except Exception as e:
            import traceback
            cprint(f"\n[ERROR] Scanner failed: {e}", "red")
            cprint(f"{traceback.format_exc()}", "red")

    # Get symbols from scanner (filters out symbols with open trades)
    symbols = get_qualified_symbols_from_scanner(
        max_symbols=args.max_symbols,
        method=args.scanner_method,
        fallback_symbols=[],
        mode=args.mode
    )

    if not symbols and not args.monitor:
        cprint("[ERROR] No symbols from scanner database after scanning", "red")
        cprint("This usually means no STRONG signals found in current market conditions", "yellow")
        sys.exit(1)

    flow = ScannerSwarmTradeFlow(config)

    if args.monitor:
        # Continuous monitoring mode
        cprint("\n⚡ Starting CONTINUOUS MONITORING MODE...\n", "magenta", attrs=['bold'])
        flow.run_continuous_monitored(num_workers=args.workers)
    elif args.once and symbols:
        # Single cycle
        cprint(f"Symbols: {', '.join(symbols)}\n", "green")
        flow.run_cycle(symbols)
    else:
        cprint("[ERROR] No symbols available", "red")
        sys.exit(1)
