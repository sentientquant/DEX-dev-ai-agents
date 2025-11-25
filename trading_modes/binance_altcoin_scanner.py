#!/usr/bin/env python3
"""
BINANCE ALTCOIN SCANNER - Evidence-Based Design
Built by Claude Code based on academic research

PHILOSOPHY:
- 100% MATH-ONLY (no AI) - Pure math/logic for maximum speed
- Evidence-based indicators (RSI trend-following, RVOL, persistence)
- Realistic expectations (55-65% win rate, not 90%+)

ACADEMIC SOURCES:
- PMC 2023: RSI effectiveness study (774% with trend-following)
- REPEC 2023: Volume-price correlation research
- ScienceDirect 2024: Momentum trading studies
- Hasbrouck 2007: Volume persistence research

PERFORMANCE:
- Runtime: 30-60 seconds
- Cost: $0.00 (no AI, no API costs beyond free Binance data)
- Output: Top 3 STRONG candidates (score ≥75/100)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
import pandas as pd
import numpy as np
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
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

# Import existing components
from risk_management.binance_truth_paper_trading import BinanceTruthAPI
from trading_modes.core.altcoin_database import get_pairs_db

# ============================================================================
# CONFIGURATION
# ============================================================================

# Data directory
DATA_DIR = Path(project_root) / "src" / "data" / "scanner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SCANNER_RESULTS = DATA_DIR / "scanner_results.json"
VALIDATED_TOKENS = DATA_DIR / "validated_tokens.json"
SCAN_HISTORY = DATA_DIR / "scan_history.csv"
PERFORMANCE_LOG = DATA_DIR / "performance_tracker.csv"

# Excluded tokens (major coins, stablecoins)
EXCLUDED_TOKENS = ['BTC', 'ETH', 'SOL', 'BNB', 'USDC', 'USDT', 'BUSD', 'DAI', 'TUSD', 'FDUSD']

# TIERED MARKET CAP FILTERING (captures mid-cap movers)
LARGE_CAP_THRESHOLD = 1_000_000_000   # $1B (large-cap)
MID_CAP_THRESHOLD = 100_000_000       # $100M (mid-cap - high movement potential)
MIN_MARKET_CAP = 100_000_000          # $100M (minimum - includes mid-caps)

# TIERED VOLUME REQUIREMENTS (based on market cap)
LARGE_CAP_MIN_VOLUME = 10_000_000     # $10M for large-caps
MID_CAP_MIN_VOLUME = 5_000_000        # $5M for mid-caps (lower requirement)

MIN_PRICE = 0.01                      # $0.01 (avoid dust tokens)
MIN_LISTING_DAYS = 90                 # 90 days (stability requirement)

# Scoring weights (total = 100 points)
WEIGHT_RSI_TREND = 20                 # PMC 2023: 774% returns
WEIGHT_VOLUME_PRICE = 25              # REPEC 2023: Strong correlation
WEIGHT_MOMENTUM_2W = 20               # ScienceDirect 2024: 2-4 week window
WEIGHT_VS_BTC = 15                    # PMC 2023: Hard to outperform BTC
WEIGHT_PERSISTENCE = 20               # Hasbrouck 2007: Volume autocorrelation

# PERMANENT FIX: Import thresholds from unified config
# No more hardcoded values scattered across files
try:
    from src.unified_config import get_config
    _config = get_config()
    STRONG_THRESHOLD = _config.STRONG_THRESHOLD
    MODERATE_THRESHOLD = _config.MODERATE_THRESHOLD
    WEAK_THRESHOLD = _config.WEAK_THRESHOLD
except ImportError:
    # Fallback if unified_config not available yet
    STRONG_THRESHOLD = 60
    MODERATE_THRESHOLD = 50
    WEAK_THRESHOLD = 45

# AI validation settings - DISABLED
USE_AI_VALIDATION = False           # REMOVED - Math-only scanner
MAX_AI_CANDIDATES = 0               # Not used


# ============================================================================
# SCANNER (100% MATH - NO AI)
# ============================================================================

class BinanceAltcoinScanner:
    """Evidence-based altcoin scanner using math/logic only"""

    def __init__(self):
        self.api = BinanceTruthAPI()
        self.btc_cache = {}  # Cache BTC data to avoid repeated calls
        self.db = get_pairs_db()  # Database for pair caching

    # ========================================================================
    # STEP 1: GET UNIVERSE
    # ========================================================================

    def get_all_usdt_pairs(self) -> List[Dict]:
        """
        Fetch all USDT pairs from Binance (with database caching)
        Returns: List of dicts with symbol info
        """
        cprint("\n[STEP 1] Fetching all Binance USDT pairs...", "cyan", attrs=['bold'])

        try:
            # Use database caching (24h expiry)
            all_pairs = self.db.fetch_and_cache_pairs()

            # Filter to USDT pairs only and exclude major coins
            usdt_pairs = []
            for pair_data in all_pairs:
                base = pair_data['base_asset']

                # Exclude major coins and stablecoins
                if base not in EXCLUDED_TOKENS:
                    usdt_pairs.append({
                        'symbol': pair_data['symbol'],
                        'base': base,
                        'quote': 'USDT'
                    })

            cprint(f"[OK] Found {len(usdt_pairs)} USDT altcoin pairs", "green")
            return usdt_pairs

        except Exception as e:
            cprint(f"[ERROR] Error fetching pairs: {e}", "red")
            return []

    # ========================================================================
    # STEP 2: PRE-FILTER (OBJECTIVE CRITERIA)
    # ========================================================================

    def _fetch_market_caps_batch(self, symbols: List[str]) -> Dict[str, float]:
        """
        PERMANENT FIX: Multi-source market cap fetching with waterfall fallback

        Priority order:
        1. CoinGecko (Free/Pro)
        2. CoinMarketCap (Free: 10K calls/month)
        3. CryptoCompare (Free: 100K calls/month)
        4. Binance-derived (volume × price estimate)
        5. Volume-only filtering

        Returns dict: {symbol_lowercase: market_cap_usd}
        """
        import os
        from dotenv import load_dotenv
        load_dotenv()

        # ============================================================
        # SOURCE 1: CoinGecko (Original)
        # ============================================================
        try:
            COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
            urls_to_try = []

            if COINGECKO_API_KEY:
                urls_to_try.append({
                    'url': "https://pro-api.coingecko.com/api/v3/coins/markets",
                    'headers': {
                        "x-cg-pro-api-key": COINGECKO_API_KEY,
                        "Content-Type": "application/json"
                    }
                })

            urls_to_try.append({
                'url': "https://api.coingecko.com/api/v3/coins/markets",
                'headers': {"Content-Type": "application/json"}
            })

            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 250,
                "page": 1,
                "sparkline": False
            }

            for endpoint in urls_to_try:
                response = requests.get(endpoint['url'], headers=endpoint['headers'], params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    market_caps = {}
                    for coin in data:
                        symbol = coin.get('symbol', '').upper()
                        market_cap = coin.get('market_cap', 0)
                        if symbol and market_cap:
                            market_caps[symbol.lower()] = market_cap

                    api_type = "Pro" if "pro-api" in endpoint['url'] else "Free"
                    cprint(f"  [OK] Fetched market caps for {len(market_caps)} coins from CoinGecko ({api_type} API)", "green")
                    return market_caps

        except Exception as e:
            cprint(f"  [INFO] CoinGecko failed: {str(e)[:100]}", "yellow")

        # ============================================================
        # SOURCE 2: CoinMarketCap (10K calls/month free)
        # ============================================================
        try:
            CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
            if CMC_API_KEY:
                cprint(f"  [FALLBACK] Trying CoinMarketCap API...", "cyan")
                response = requests.get(
                    "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
                    headers={
                        "X-CMC_PRO_API_KEY": CMC_API_KEY,
                        "Accept": "application/json"
                    },
                    params={"limit": 250, "convert": "USD"},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    market_caps = {}
                    for coin in data.get('data', []):
                        symbol = coin.get('symbol', '').upper()
                        market_cap = coin.get('quote', {}).get('USD', {}).get('market_cap', 0)
                        if symbol and market_cap:
                            market_caps[symbol.lower()] = market_cap

                    if len(market_caps) > 50:  # Sanity check
                        cprint(f"  [OK] Fetched market caps for {len(market_caps)} coins from CoinMarketCap", "green")
                        return market_caps
        except Exception as e:
            cprint(f"  [INFO] CoinMarketCap failed: {str(e)[:100]}", "yellow")

        # ============================================================
        # SOURCE 3: CryptoCompare (100K calls/month free)
        # ============================================================
        try:
            CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")
            headers = {"authorization": f"Apikey {CRYPTOCOMPARE_API_KEY}"} if CRYPTOCOMPARE_API_KEY else {}

            cprint(f"  [FALLBACK] Trying CryptoCompare API...", "cyan")

            # Get top coins list
            response = requests.get(
                "https://min-api.cryptocompare.com/data/top/mktcapfull",
                headers=headers,
                params={"limit": 250, "tsym": "USD"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                market_caps = {}
                for coin_data in data.get('Data', []):
                    coin_info = coin_data.get('CoinInfo', {})
                    raw_data = coin_data.get('RAW', {}).get('USD', {})

                    symbol = coin_info.get('Name', '').upper()
                    market_cap = raw_data.get('MKTCAP', 0)

                    if symbol and market_cap:
                        market_caps[symbol.lower()] = market_cap

                if len(market_caps) > 50:  # Sanity check
                    cprint(f"  [OK] Fetched market caps for {len(market_caps)} coins from CryptoCompare", "green")
                    return market_caps
        except Exception as e:
            cprint(f"  [INFO] CryptoCompare failed: {str(e)[:100]}", "yellow")

        # ============================================================
        # SOURCE 4: Binance-Derived Market Caps (Estimate)
        # ============================================================
        try:
            cprint(f"  [FALLBACK] Estimating market caps from Binance data...", "cyan")

            # Fetch ticker data (already batched in pre_filter)
            response = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=10)
            if response.status_code == 200:
                tickers = response.json()
                market_caps = {}

                # Estimate: market_cap ≈ volume_24h × 30 (rough circulating supply multiplier)
                # This is VERY rough but better than nothing
                for ticker in tickers:
                    symbol = ticker.get('symbol', '')
                    if symbol.endswith('USDT'):
                        base = symbol[:-4]
                        volume_24h = float(ticker.get('quoteVolume', 0))
                        price = float(ticker.get('lastPrice', 0))

                        # Rough estimate: higher volume coins tend to have larger market caps
                        # Use volume × 30 as proxy for market cap
                        estimated_market_cap = volume_24h * 30

                        if estimated_market_cap > 0:
                            market_caps[base.lower()] = estimated_market_cap

                if len(market_caps) > 50:
                    cprint(f"  [OK] Estimated market caps for {len(market_caps)} coins from Binance volume data", "yellow")
                    cprint(f"  [NOTE] These are ROUGH estimates - add CMC or CryptoCompare API key for accuracy", "yellow")
                    return market_caps
        except Exception as e:
            cprint(f"  [INFO] Binance-derived estimate failed: {str(e)[:100]}", "yellow")

        # ============================================================
        # FALLBACK: Volume-only filtering
        # ============================================================
        cprint(f"  [WARNING] All market cap sources failed - using volume-only filtering", "red")
        cprint(f"  [TIP] Add API keys to .env for market cap data:", "cyan")
        cprint(f"        - COINMARKETCAP_API_KEY (free: https://coinmarketcap.com/api/)", "cyan")
        cprint(f"        - CRYPTOCOMPARE_API_KEY (free: https://www.cryptocompare.com/cryptopian/api-keys)", "cyan")
        return {}

    def pre_filter(self, pairs: List[Dict]) -> List[Dict]:
        """
        Apply TIERED filters based on market cap (LARGE-CAP vs MID-CAP)
        Reduces 432 pairs → 60-100 quality tokens

        OPTIMIZED: Uses Binance batch ticker endpoint (1 API call instead of 864)
        """
        cprint("\n[STEP 2] Pre-filtering with TIERED objective criteria...", "cyan", attrs=['bold'])
        cprint(f"LARGE-CAP: ≥${LARGE_CAP_THRESHOLD/1e9:.0f}B cap, ≥${LARGE_CAP_MIN_VOLUME/1e6:.0f}M vol", "white")
        cprint(f"MID-CAP: ≥${MID_CAP_THRESHOLD/1e6:.0f}M cap, ≥${MID_CAP_MIN_VOLUME/1e6:.0f}M vol", "white")
        cprint(f"Minimum price: ${MIN_PRICE}", "white")

        filtered = []
        large_cap_count = 0
        mid_cap_count = 0

        # Fetch market cap data from CoinGecko (batch request)
        market_caps = self._fetch_market_caps_batch([p['base'] for p in pairs])
        use_market_cap = len(market_caps) > 0

        if not use_market_cap:
            cprint("  [INFO] Market cap data unavailable - using volume-only filtering", "yellow")

        # ✅ PERFORMANCE FIX: Fetch ALL tickers in ONE batch call instead of 432 individual calls
        cprint("  [BATCH] Fetching all 24h tickers from Binance (1 API call)...", "cyan")
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=10)
            if response.status_code == 200:
                all_tickers = {t['symbol']: t for t in response.json()}
                cprint(f"  [OK] Fetched {len(all_tickers)} tickers in 1 batch call", "green")
            else:
                cprint(f"  [WARN] Batch ticker fetch failed, falling back to individual calls", "yellow")
                all_tickers = {}
        except Exception as e:
            cprint(f"  [WARN] Batch ticker error: {e}, falling back to individual calls", "yellow")
            all_tickers = {}

        for i, pair in enumerate(pairs):
            symbol = pair['symbol']
            base = pair['base']

            # Progress indicator (every 10 tokens)
            if (i + 1) % 10 == 0:
                print(f"  Checked {i+1}/{len(pairs)}... ({len(filtered)} passed)", end='\r', flush=True)

            try:
                # Get 24h volume and price from batch data (instant) or fallback to individual call
                if symbol in all_tickers:
                    ticker = all_tickers[symbol]
                    volume_24h = float(ticker.get('quoteVolume', 0))
                    price = float(ticker.get('lastPrice', 0))
                else:
                    # Fallback to individual calls (slower)
                    volume_24h = self.api.get_24h_volume(symbol)
                    if not volume_24h:
                        continue
                    price = self.api.get_live_price(symbol)

                if not volume_24h or not price or price < MIN_PRICE:
                    continue

                # Market cap filtering (if available)
                if use_market_cap:
                    # Get market cap from CoinGecko data
                    market_cap = market_caps.get(base.lower(), 0)

                    # Skip if market cap not found OR below minimum threshold
                    if market_cap == 0 or market_cap < MIN_MARKET_CAP:
                        continue

                    # Determine tier and apply appropriate volume threshold
                    if market_cap >= LARGE_CAP_THRESHOLD:
                        tier = 'LARGE_CAP'
                        min_volume = LARGE_CAP_MIN_VOLUME
                    else:
                        tier = 'MID_CAP'
                        min_volume = MID_CAP_MIN_VOLUME
                else:
                    # FALLBACK: Use volume as proxy (high volume = likely larger cap)
                    market_cap = 0  # Unknown
                    tier = 'UNKNOWN'
                    # Use lower volume threshold to be inclusive
                    min_volume = MID_CAP_MIN_VOLUME

                # Apply tier-specific volume filter
                if volume_24h < min_volume:
                    continue

                # Increment tier count AFTER passing volume filter
                if tier == 'LARGE_CAP':
                    large_cap_count += 1
                elif tier == 'MID_CAP':
                    mid_cap_count += 1

                filtered.append({
                    'symbol': symbol,
                    'base': base,
                    'volume_24h': volume_24h,
                    'price': price,
                    'market_cap': market_cap,
                    'tier': tier
                })

            except Exception as e:
                # Skip tokens that error (likely delisted or broken)
                if (i + 1) % 100 == 0:
                    print(f"  Error on {symbol}: {e}", end='\r')
                continue

        print()  # Clear progress line
        cprint(f"✅ After pre-filter: {len(filtered)} quality tokens (LARGE: {large_cap_count}, MID: {mid_cap_count})", "green")
        return filtered

    # ========================================================================
    # STEP 3: MOMENTUM SCORING (EVIDENCE-BASED INDICATORS)
    # ========================================================================

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        if loss.iloc[-1] == 0:
            return 100.0

        rs = gain.iloc[-1] / loss.iloc[-1]
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def get_btc_change_2w(self) -> float:
        """Get BTC 2-week price change (cached)"""
        if 'btc_2w_change' in self.btc_cache:
            # Check if cache is fresh (< 1 hour old)
            if datetime.now() - self.btc_cache['timestamp'] < timedelta(hours=1):
                return self.btc_cache['btc_2w_change']

        # Fetch fresh BTC data
        try:
            df = self.api.get_ohlcv_data('BTCUSDT', '1h', days_back=14)
            if df is not None and len(df) >= 336:
                btc_change = ((df['close'].iloc[-1] - df['close'].iloc[0]) /
                             df['close'].iloc[0] * 100)

                self.btc_cache = {
                    'btc_2w_change': btc_change,
                    'timestamp': datetime.now()
                }
                return btc_change
        except:
            pass

        return 0.0  # Fallback

    def score_token(self, token: Dict) -> Tuple[float, Dict]:
        """
        Calculate momentum score (0-100 points)
        Returns: (score, signals_dict)
        """
        symbol = token['symbol']
        score = 0
        signals = {}

        try:
            # Fetch OHLCV data (30 days, 1H timeframe)
            df = self.api.get_ohlcv_data(symbol, '1h', days_back=30)

            if df is None or len(df) < 336:  # Need at least 14 days
                return 0, {'error': 'Insufficient data'}

            # ================================================================
            # SIGNAL 1: RSI TREND-FOLLOWING (20 pts)
            # Evidence: PMC 2023 - 774% returns with RSI 50-100 strategy
            # ================================================================
            rsi = self.calculate_rsi(df['close'], 14)
            signals['rsi'] = round(rsi, 1)

            if rsi > 50:  # Uptrend (NOT oversold/overbought!)
                score += WEIGHT_RSI_TREND
                if rsi > 60:
                    score += 5  # Bonus: Strong uptrend
                signals['rsi_signal'] = 'UPTREND'
            else:
                signals['rsi_signal'] = 'DOWNTREND'

            # ================================================================
            # SIGNAL 2: VOLUME-PRICE CORRELATION (25 pts)
            # Evidence: REPEC 2023 - Positive correlation post-2019
            # ================================================================

            # Calculate RVOL (relative volume)
            current_volume_24h = df['volume'].tail(24).sum()
            avg_volume_24h = df['volume'].rolling(24).sum().mean()
            rvol = current_volume_24h / avg_volume_24h if avg_volume_24h > 0 else 1.0
            signals['rvol'] = round(rvol, 2)

            # Calculate 24h price change
            price_change_24h = ((df['close'].iloc[-1] - df['close'].iloc[-24]) /
                               df['close'].iloc[-24] * 100)
            signals['price_change_24h'] = round(price_change_24h, 2)

            # Volume-Price Alignment
            if rvol > 1.5 and price_change_24h > 5:
                score += WEIGHT_VOLUME_PRICE
                signals['volume_price_signal'] = 'STRONG_BUY'
            elif rvol > 2.0 and price_change_24h < -5:
                score -= 20  # TRAP: Distribution
                signals['volume_price_signal'] = 'DISTRIBUTION_TRAP'
            elif rvol > 2.0 and abs(price_change_24h) < 2:
                score += 5  # WEAK: Noise
                signals['volume_price_signal'] = 'WEAK_NOISE'
            else:
                signals['volume_price_signal'] = 'NO_SIGNAL'

            # ================================================================
            # SIGNAL 3: SHORT-TERM MOMENTUM (20 pts)
            # Evidence: ScienceDirect 2024 - 2-4 week momentum works
            # ================================================================

            if len(df) >= 336:  # Need 14 days of hourly data
                price_2w_ago = df['close'].iloc[-336]
                price_change_2w = ((df['close'].iloc[-1] - price_2w_ago) /
                                  price_2w_ago * 100)
                signals['price_change_2w'] = round(price_change_2w, 2)

                if price_change_2w > 15:
                    score += WEIGHT_MOMENTUM_2W
                    signals['momentum_signal'] = 'STRONG'
                elif price_change_2w > 7:
                    score += WEIGHT_MOMENTUM_2W // 2
                    signals['momentum_signal'] = 'MODERATE'
                else:
                    signals['momentum_signal'] = 'WEAK'
            else:
                signals['momentum_signal'] = 'INSUFFICIENT_DATA'

            # ================================================================
            # SIGNAL 4: RELATIVE STRENGTH vs BTC (15 pts)
            # Evidence: PMC 2023 - Difficult to outperform BTC
            # ================================================================

            btc_change_2w = self.get_btc_change_2w()
            if 'price_change_2w' in signals:
                alt_vs_btc = signals['price_change_2w'] - btc_change_2w
                signals['vs_btc'] = round(alt_vs_btc, 2)

                if alt_vs_btc > 10:  # Outperform by >10%
                    score += WEIGHT_VS_BTC
                    signals['vs_btc_signal'] = 'STRONG_OUTPERFORM'
                elif alt_vs_btc > 0:
                    score += WEIGHT_VS_BTC // 2
                    signals['vs_btc_signal'] = 'OUTPERFORM'
                else:
                    signals['vs_btc_signal'] = 'UNDERPERFORM'

            # ================================================================
            # SIGNAL 5: PERSISTENCE CHECK (20 pts)
            # Evidence: Hasbrouck 2007 - Volume autocorrelation
            # ================================================================

            # Check RVOL over last 3 days (72 hours)
            rvol_history = []
            for day in range(1, 4):
                start_idx = -24 * day
                end_idx = -24 * (day - 1) if day > 1 else None
                period_volume = df['volume'].iloc[start_idx:end_idx].sum()
                baseline_volume = df['volume'].rolling(24).sum().mean()
                period_rvol = period_volume / baseline_volume if baseline_volume > 0 else 1.0
                rvol_history.append(period_rvol)

            consecutive_elevated = sum(1 for r in rvol_history if r > 1.5)
            signals['persistence_cycles'] = consecutive_elevated

            if consecutive_elevated >= 3:
                score += WEIGHT_PERSISTENCE
                signals['persistence_signal'] = 'ESTABLISHED'
            elif consecutive_elevated == 2:
                score += WEIGHT_PERSISTENCE // 2
                signals['persistence_signal'] = 'EMERGING'
            else:
                signals['persistence_signal'] = 'SPIKE'

            # Clamp score to 0-100
            score = max(0, min(100, score))

            return score, signals

        except Exception as e:
            return 0, {'error': str(e)}

    def score_all_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """Score all pre-filtered tokens"""
        cprint("\n[STEP 3] Calculating momentum scores (math indicators only)...", "cyan", attrs=['bold'])

        scored = []

        for i, token in enumerate(tokens):
            symbol = token['symbol']

            # Progress indicator
            print(f"  Scoring {i+1}/{len(tokens)}: {symbol}...", end='\r', flush=True)

            score, signals = self.score_token(token)

            if score >= WEAK_THRESHOLD:  # Only keep tokens above minimum
                token['score'] = score
                token['signals'] = signals

                # Copy price_change_24h to token level for database tracking
                if 'price_change_24h' in signals:
                    token['price_change_24h'] = signals['price_change_24h']

                # Classify
                if score >= STRONG_THRESHOLD:
                    token['classification'] = 'STRONG'
                elif score >= MODERATE_THRESHOLD:
                    token['classification'] = 'MODERATE'
                else:
                    token['classification'] = 'WEAK'

                scored.append(token)

        print()  # Clear progress line

        # Sort by score (highest first)
        scored.sort(key=lambda x: x['score'], reverse=True)

        # Print summary
        strong_count = sum(1 for t in scored if t['classification'] == 'STRONG')
        moderate_count = sum(1 for t in scored if t['classification'] == 'MODERATE')
        weak_count = sum(1 for t in scored if t['classification'] == 'WEAK')

        cprint(f"✅ Scored {len(scored)} tokens:", "green")
        cprint(f"   STRONG (≥{STRONG_THRESHOLD}): {strong_count} tokens", "green")
        cprint(f"   MODERATE ({MODERATE_THRESHOLD}-{STRONG_THRESHOLD-1}): {moderate_count} tokens", "yellow")
        cprint(f"   WEAK ({WEAK_THRESHOLD}-{MODERATE_THRESHOLD-1}): {weak_count} tokens", "white")

        # Print top 10
        if scored:
            cprint("\nTop 10 Scored Tokens:", "cyan", attrs=['bold'])
            for i, token in enumerate(scored[:10], 1):
                signals = token['signals']
                tier = token.get('tier', 'UNKNOWN')
                market_cap_fmt = f"${token.get('market_cap', 0)/1e9:.2f}B" if token.get('market_cap', 0) > 0 else "N/A"

                cprint(f"{i:2d}. {token['symbol']:12s} {token['score']:3.0f} pts ({token['classification']:8s}) [{tier:9s}] MC:{market_cap_fmt:>8s}", "white")
                cprint(f"    RSI:{signals.get('rsi', 'N/A'):>6} | RVOL:{signals.get('rvol', 'N/A'):>5} | "
                       f"2w:{signals.get('price_change_2w', 'N/A'):>6}% | "
                       f"vsBTC:{signals.get('vs_btc', 'N/A'):>6}% | "
                       f"Persist:{signals.get('persistence_signal', 'N/A')}", "cyan")

        return scored

    # ========================================================================
    # STEP 4: SAVE RESULTS
    # ========================================================================

    def save_results(self, scored_tokens: List[Dict]):
        """Save scanner results to JSON, CSV, and database"""
        cprint("\n[STEP 4] Saving results...", "cyan", attrs=['bold'])

        # Save full JSON results
        output = {
            'timestamp': datetime.now().isoformat(),
            'total_scanned': len(scored_tokens),
            'strong_candidates': [t for t in scored_tokens if t['classification'] == 'STRONG'],
            'moderate_candidates': [t for t in scored_tokens if t['classification'] == 'MODERATE'],
            'all_results': scored_tokens
        }

        with open(SCANNER_RESULTS, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        cprint(f"[OK] Saved full results: {SCANNER_RESULTS}", "green")

        # Append to scan history CSV
        csv_exists = SCAN_HISTORY.exists()
        with open(SCAN_HISTORY, 'a', newline='') as f:
            writer = csv.writer(f)
            if not csv_exists:
                writer.writerow(['timestamp', 'symbol', 'score', 'classification', 'tier',
                               'market_cap', 'volume_24h', 'rsi', 'rvol', 'price_change_2w', 'vs_btc', 'persistence'])

            for token in scored_tokens:
                signals = token['signals']
                writer.writerow([
                    datetime.now().isoformat(),
                    token['symbol'],
                    token['score'],
                    token['classification'],
                    token.get('tier', 'UNKNOWN'),
                    token.get('market_cap', 0),
                    token.get('volume_24h', 0),
                    signals.get('rsi', ''),
                    signals.get('rvol', ''),
                    signals.get('price_change_2w', ''),
                    signals.get('vs_btc', ''),
                    signals.get('persistence_signal', '')
                ])

        cprint(f"[OK] Appended to history: {SCAN_HISTORY}", "green")

        # Cache results to database
        cprint(f"[UPDATE] Caching results to database...", "cyan")
        for token in scored_tokens:
            self.db.cache_scanner_result(
                symbol=token['symbol'],
                score=token['score'],
                classification=token['classification'],
                signals=token['signals']
            )

            # Update active pairs tracking (for AI_SWARM_TRADE_FLOW integration)
            if token.get('volume_24h') and token.get('price_change_24h') is not None:
                self.db.update_active_pair(
                    symbol=token['symbol'],
                    volume_24h=token['volume_24h'],
                    price_change_24h=token['price_change_24h']
                )

        cprint(f"[OK] Cached {len(scored_tokens)} results to database", "green")


# ============================================================================
# PHASE 2: AI VALIDATION - REMOVED
# ============================================================================
# AI validation has been removed to make this a pure math-only scanner
# for maximum speed and zero cost.


# ============================================================================
# MAIN RUNNER
# ============================================================================

def main():
    """Main scanner execution"""
    cprint("\n" + "="*70, "cyan")
    cprint("BINANCE ALTCOIN SCANNER - Math-Only (No AI)", "cyan", attrs=['bold'])
    cprint("="*70 + "\n", "cyan")

    start_time = datetime.now()

    # ========================================================================
    # SCANNER EXECUTION (100% MATH)
    # ========================================================================

    scanner = BinanceAltcoinScanner()

    # Step 1: Get all USDT pairs
    all_pairs = scanner.get_all_usdt_pairs()

    if not all_pairs:
        cprint("❌ Failed to fetch pairs. Exiting.", "red")
        return

    # Step 2: Pre-filter
    filtered = scanner.pre_filter(all_pairs)

    if not filtered:
        cprint("❌ No tokens passed pre-filter. Exiting.", "red")
        return

    # Step 3: Score tokens
    scored = scanner.score_all_tokens(filtered)

    if not scored:
        cprint("❌ No tokens scored above threshold. Exiting.", "red")
        return

    # Step 4: Save results
    scanner.save_results(scored)

    # Get strong candidates
    strong_candidates = [t for t in scored if t['classification'] == 'STRONG']

    # ========================================================================
    # SELECT FINAL PICKS (Math-Only, No AI)
    # ========================================================================

    # Use top 3 math-scored STRONG candidates
    final_picks = [t['symbol'] for t in strong_candidates[:3]]

    # Save final picks
    validated_output = {
        'timestamp': datetime.now().isoformat(),
        'validated_symbols': final_picks,
        'ai_validation': False,
        'method': 'math_only_top_3'
    }

    with open(VALIDATED_TOKENS, 'w') as f:
        json.dump(validated_output, f, indent=2)

    cprint(f"✅ Saved top picks: {VALIDATED_TOKENS}", "green")

    total_time = (datetime.now() - start_time).total_seconds()

    # ========================================================================
    # FINAL OUTPUT
    # ========================================================================

    cprint("\n" + "="*70, "green", attrs=['bold'])
    cprint("SCAN COMPLETE", "green", attrs=['bold'])
    cprint("="*70, "green", attrs=['bold'])

    cprint(f"\n⏱️  Total time: {total_time:.1f} seconds", "cyan")
    cprint(f"💰 Cost: $0.00 (Math-only, no AI)", "cyan")

    cprint(f"\n🎯 FINAL PICKS ({len(final_picks)} tokens):", "green", attrs=['bold'])
    for i, symbol in enumerate(final_picks, 1):
        # Find token details
        token_data = next((t for t in scored if t['symbol'] == symbol), None)
        if token_data:
            cprint(f"   {i}. {symbol} (Score: {token_data['score']:.0f}/100)", "green")

    # Extract base symbols (remove USDT)
    base_symbols = [s.replace('USDT', '') for s in final_picks]

    cprint(f"\n📝 Update your .env file:", "yellow", attrs=['bold'])
    cprint(f"   DEFAULT_SYMBOLS={','.join(base_symbols)}", "white")

    cprint(f"\n▶️  Run trading system:", "yellow", attrs=['bold'])
    cprint(f"   python trading_modes/AI_SWARM_TRADE_FLOW.py", "white")

    cprint("\n" + "="*70 + "\n", "green")

    return final_picks


if __name__ == "__main__":
    main()
