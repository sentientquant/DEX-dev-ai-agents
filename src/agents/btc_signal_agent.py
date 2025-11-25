#!/usr/bin/env python3
"""
BTCUSDT SIGNAL AGENT - SWARM + STRUCTURED PROMPT

Made for Moon Dev

What this agent does:
- Pulls BTCUSDT OHLCV from Binance (4h, 1h, 15m)
- Computes simple indicators (EMA, RSI, ATR, Bollinger, volume vs average)
- Builds a compact technical snapshot JSON
- Uses SwarmAgent with a STRICT JSON prompt:
    {
      "signal": "LONG | SHORT | FLAT",
      "confidence": 0-100,
      "timeframe": "15m",
      "reason_summary": "...",
      "reasons": ["...", "..."]
    }
- Picks a primary model's JSON output (e.g. Claude) as the official signal
- Applies post-rules (minimum confidence, safety → FLAT)
- Logs everything to src/data/btc_signal_agent

Usage:
    python src/agents/btc_signal_agent.py --once    # run once
    python src/agents/btc_signal_agent.py           # loop every 15m

You can adapt it to Hyperliquid later by swapping the data source.
"""

import os
import sys
import json
import time
import math
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
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

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import Swarm Agent
from src.agents.swarm_agent import SwarmAgent

# ============================================================================
# CONFIG
# ============================================================================

BINANCE_BASE = "https://api.binance.com"  # Spot; change if you want futures
SYMBOL = "BTCUSDT"

TIMEFRAMES = {
    "4h": {"binance_interval": "4h", "limit": 200},
    "1h": {"binance_interval": "1h", "limit": 200},
    "15m": {"binance_interval": "15m", "limit": 200},
}

# LLM / Signal config
PRIMARY_PROVIDER = "claude"        # one of the SWARM_MODELS keys
MIN_CONFIDENCE = 55               # below this → FLAT
DEFAULT_TIMEFRAME = "15m"
DEFAULT_HORIZON = "next 4–8 candles on the 15m chart"

# Logging
DATA_DIR = Path(project_root) / "src" / "data" / "btc_signal_agent"
SIGNAL_LOG = DATA_DIR / "btc_signals.jsonl"

# Run interval
CHECK_INTERVAL_SECONDS = 15 * 60  # 15 minutes


# ============================================================================
# UTILITIES: INDICATORS
# ============================================================================

def ema(values: List[float], period: int) -> List[float]:
    """Simple EMA implementation."""
    if not values:
        return []
    ema_values = []
    k = 2 / (period + 1)
    for i, price in enumerate(values):
        if i == 0:
            ema_values.append(price)
        else:
            ema_values.append(price * k + ema_values[-1] * (1 - k))
    return ema_values


def rsi(values: List[float], period: int = 14) -> List[float]:
    """Wilder's RSI."""
    if len(values) < period + 1:
        return [50.0] * len(values)

    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsis = [50.0] * (period)  # pad initial

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rs = float('inf')
            rsi_val = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs))

        rsis.append(rsi_val)

    # align length with prices
    return [50.0] + rsis  # add one at start to match length


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    """Average True Range."""
    if len(closes) < period + 1:
        return [0.0] * len(closes)

    trs = []
    for i in range(len(closes)):
        if i == 0:
            tr = highs[i] - lows[i]
        else:
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
        trs.append(tr)

    atrs = []
    first_atr = sum(trs[1:period + 1]) / period
    atrs = [0.0] * (period)  # pad initial
    atrs.append(first_atr)

    for i in range(period + 1, len(trs)):
        prev_atr = atrs[-1]
        curr_atr = (prev_atr * (period - 1) + trs[i]) / period
        atrs.append(curr_atr)

    # pad if necessary
    while len(atrs) < len(closes):
        atrs.insert(0, 0.0)

    return atrs


def sma(values: List[float], period: int) -> List[float]:
    """Simple moving average."""
    if len(values) < period:
        return [sum(values) / len(values)] * len(values) if values else []
    out = []
    for i in range(len(values)):
        if i < period - 1:
            out.append(sum(values[:i + 1]) / (i + 1))
        else:
            window = values[i - period + 1:i + 1]
            out.append(sum(window) / period)
    return out


def stddev(values: List[float], period: int) -> List[float]:
    """Rolling standard deviation."""
    if len(values) < period:
        mean = sum(values) / len(values) if values else 0.0
        return [0.0 if not values else math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))] * len(values)
    out = []
    for i in range(len(values)):
        if i < period - 1:
            window = values[:i + 1]
        else:
            window = values[i - period + 1:i + 1]
        m = sum(window) / len(window)
        var = sum((v - m) ** 2 for v in window) / len(window)
        out.append(math.sqrt(var))
    return out


# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_ohlcv_binance(symbol: str, interval: str, limit: int = 200) -> List[Dict[str, Any]]:
    """
    Fetch OHLCV candles from Binance.
    Returns: list of dicts with time, open, high, low, close, volume.
    """
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Binance API error {resp.status_code}: {resp.text}")

    data = resp.json()
    candles = []
    for k in data:
        candles.append({
            "open_time": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
            "close_time": int(k[6])
        })
    return candles


# ============================================================================
# SNAPSHOT CREATION
# ============================================================================

def detect_trend(closes: List[float], ema_short: List[float], ema_long: List[float]) -> str:
    """Very simple trend label based on EMAs and slope."""
    if len(closes) < 5:
        return "unknown"

    price = closes[-1]
    es = ema_short[-5:]
    el = ema_long[-5:]

    es_slope = es[-1] - es[0]
    el_slope = el[-1] - el[0]

    if price > el[-1] and es[-1] > el[-1] and es_slope > 0 and el_slope > 0:
        return "uptrend"
    if price < el[-1] and es[-1] < el[-1] and es_slope < 0 and el_slope < 0:
        return "downtrend"
    return "range_or_pullback"


def bollinger_position(close: float, mid: float, upper: float, lower: float) -> str:
    if upper == lower:
        return "middle"
    if close >= upper:
        return "upper_band"
    if close <= lower:
        return "lower_band"
    if close > mid:
        return "upper_half"
    return "lower_half"


def volume_vs_average(volumes: List[float], period: int = 20) -> float:
    if not volumes:
        return 1.0
    if len(volumes) < period:
        avg = sum(volumes) / len(volumes)
    else:
        avg = sum(volumes[-period:]) / period
    if avg == 0:
        return 1.0
    return volumes[-1] / avg


def build_timeframe_snapshot(candles: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
    """Build a compact snapshot for a single timeframe."""
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    vols = [c["volume"] for c in candles]

    price = closes[-1]
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    rsi14 = rsi(closes, 14)
    atr14 = atr(highs, lows, closes, 14)
    bb_mid = sma(closes, 20)
    bb_std = stddev(closes, 20)
    bb_upper = [m + 2 * s for m, s in zip(bb_mid, bb_std)]
    bb_lower = [m - 2 * s for m, s in zip(bb_mid, bb_std)]
    vol_vs_avg = volume_vs_average(vols, 20)

    trend = detect_trend(closes, ema50, ema200)
    bb_pos = bollinger_position(price, bb_mid[-1], bb_upper[-1], bb_lower[-1])

    snapshot = {
        "timeframe": label,
        "price": price,
        "trend": trend,
        "ema_20": ema20[-1],
        "ema_50": ema50[-1],
        "ema_200": ema200[-1],
        "price_vs_ema_50": "above" if price > ema50[-1] else "below",
        "price_vs_ema_200": "above" if price > ema200[-1] else "below",
        "rsi_14": rsi14[-1],
        "atr_14": atr14[-1],
        "bb_position": bb_pos,
        "volume_vs_20_sma": vol_vs_avg,
    }

    return snapshot


def build_btc_snapshot() -> Dict[str, Any]:
    """Fetch OHLCV for all timeframes and build a multi-TF snapshot."""
    tf_data = {}
    for tf, cfg in TIMEFRAMES.items():
        cprint(f"📡 Fetching {SYMBOL} {tf} data from Binance...", "cyan")
        candles = fetch_ohlcv_binance(SYMBOL, cfg["binance_interval"], cfg["limit"])
        tf_data[tf] = candles
        cprint(f"✅ Got {len(candles)} candles for {tf}", "green")

    # Build per-timeframe snapshots
    snapshots = {}
    for tf, candles in tf_data.items():
        snapshots[tf] = build_timeframe_snapshot(candles, tf)

    # Last candle time (from 15m)
    last_ts = tf_data["15m"][-1]["close_time"]

    snapshot = {
        "symbol": SYMBOL,
        "time_generated_utc": datetime.utcfromtimestamp(last_ts / 1000).isoformat() + "Z",
        "timeframes": snapshots,
        # Hooks for later:
        "funding_and_sentiment": {
            "funding_rate": None,
            "funding_context": "not_provided",
            "open_interest_change_24h": None,
            "liquidation_heat": "not_provided"
        }
    }
    return snapshot


# ============================================================================
# LLM PROMPTS
# ============================================================================

def build_system_prompt() -> str:
    return (
        "You are a disciplined BTCUSDT trading signal engine.\n"
        "Your job is to turn a multi-timeframe technical snapshot into a SINGLE clear trading signal.\n"
        "You MUST:\n"
        "- Use ONLY the data provided (no outside data, no news, no macro).\n"
        "- Choose exactly one of these signals: LONG, SHORT, or FLAT (no trade).\n"
        "- Output VALID JSON ONLY, matching the schema. No extra text.\n"
        "- Keep reasons short, technical, and directly tied to the snapshot.\n"
        "- If the picture is mixed/uncertain, prefer FLAT with low confidence.\n"
    )


def build_user_prompt(snapshot: Dict[str, Any]) -> str:
    snapshot_json = json.dumps(snapshot, indent=2)
    prompt = f"""
You are analysing BTCUSDT.

Trading framework:
- Market: BTCUSDT (Binance)
- Primary timeframe: {DEFAULT_TIMEFRAME}
- Context timeframes: 1h and 4h
- Signal horizon: {DEFAULT_HORIZON}
- Style: short-term technical, no macro narrative, no news.

Here is the technical snapshot (precomputed indicators):

SNAPSHOT_JSON:
{snapshot_json}

Requirements:
1. Decide the trading signal for BTCUSDT on the {DEFAULT_TIMEFRAME} timeframe:
   - "LONG"  = open or maintain a long bias
   - "SHORT" = open or maintain a short bias
   - "FLAT"  = stay out / no new trade

2. Set a confidence from 0 to 100:
   - 0–39: weak / noisy → usually FLAT
   - 40–69: moderate edge
   - 70–100: strong edge and clean confluence

3. Provide:
   - a short one-sentence summary
   - 2–5 bullet-point reasons linking directly to the snapshot data
     (trend, EMAs, RSI, ATR/volatility, Bollinger position, volume vs average)

4. Output ONLY this JSON object, nothing else:

{{
  "signal": "LONG" | "SHORT" | "FLAT",
  "confidence": 0-100,
  "timeframe": "{DEFAULT_TIMEFRAME}",
  "reason_summary": "one-sentence summary of the setup and risk",
  "reasons": [
    "reason 1",
    "reason 2",
    "reason 3"
  ]
}}

Do NOT include any text before or after the JSON. Only return the JSON object.
"""
    return prompt.strip()


# ============================================================================
# JSON PARSING / POST-PROCESSING
# ============================================================================

def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Try to extract a JSON object from a model's text."""
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to grab from first { to last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return None
    return None


def apply_post_rules(signal_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Apply your own guard rails (confidence floor, safety)."""
    sig = signal_obj.get("signal", "FLAT")
    conf = signal_obj.get("confidence", 0)

    # Enforce type
    if sig not in ["LONG", "SHORT", "FLAT"]:
        sig = "FLAT"

    # Confidence floor
    if not isinstance(conf, (int, float)):
        conf = 0
    conf = max(0, min(100, int(conf)))

    if conf < MIN_CONFIDENCE:
        sig = "FLAT"

    signal_obj["signal"] = sig
    signal_obj["confidence"] = conf
    return signal_obj


# ============================================================================
# BTC SIGNAL AGENT
# ============================================================================

class BtcSignalAgent:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.swarm = SwarmAgent()
        cprint(f"\n[INIT] BTCUSDT Signal Agent initialised", "cyan")

    def generate_signal(self) -> Dict[str, Any]:
        """Main call: build snapshot, query swarm, return processed signal dict."""
        # 1. Build technical snapshot
        snapshot = build_btc_snapshot()

        # 2. Build prompts
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(snapshot)

        # 3. Call Swarm
        cprint("\n🤖 Querying AI Swarm for BTCUSDT signal...", "cyan", attrs=['bold'])
        result = self.swarm.query(prompt=user_prompt, system_prompt=system_prompt)

        # 4. Pick primary provider output (e.g. Claude) as the JSON we parse
        responses = result.get("responses", {})
        if PRIMARY_PROVIDER not in responses or not responses[PRIMARY_PROVIDER].get("success"):
            # Fallback: pick any successful provider
            cprint(f"[WARN] Primary provider '{PRIMARY_PROVIDER}' failed or missing. Falling back.", "yellow")
            primary_text = None
            for prov, data in responses.items():
                if data.get("success") and data.get("response"):
                    PRIMARY = prov
                    primary_text = data["response"]
                    cprint(f"[INFO] Using provider '{prov}' as fallback", "yellow")
                    break
        else:
            primary_text = responses[PRIMARY_PROVIDER]["response"]

        if not primary_text:
            raise RuntimeError("No successful model response for signal generation.")

        # 5. Parse JSON
        signal_obj = extract_json_block(primary_text)
        if not signal_obj:
            raise RuntimeError("Failed to parse JSON from model response.")

        # 6. Post-process rules
        signal_obj = apply_post_rules(signal_obj)

        # 7. Attach snapshot + swarm metadata for logging
        wrapper = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "symbol": SYMBOL,
            "raw_snapshot": snapshot,
            "signal": signal_obj,
            "swarm_consensus_summary": result.get("consensus_summary"),
            "swarm_metadata": result.get("metadata"),
        }

        # 8. Log
        self._log_signal(wrapper)

        return wrapper

    def _log_signal(self, entry: Dict[str, Any]):
        with open(SIGNAL_LOG, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
        cprint(f"[LOG] Signal logged to {SIGNAL_LOG}", "blue")

    def run_once(self):
        """Run a single signal generation cycle."""
        try:
            wrapper = self.generate_signal()
            sig = wrapper["signal"]["signal"]
            conf = wrapper["signal"]["confidence"]
            summary = wrapper["signal"]["reason_summary"]

            cprint("\n" + "=" * 80, "green", attrs=['bold'])
            cprint("🎯 BTCUSDT SIGNAL (15m)", "green", attrs=['bold'])
            cprint("=" * 80, "green", attrs=['bold'])
            cprint(f"Signal      : {sig}", "yellow")
            cprint(f"Confidence  : {conf}", "yellow")
            cprint(f"Summary     : {summary}", "yellow")
            cprint("Reasons:", "yellow")
            for r in wrapper["signal"].get("reasons", []):
                cprint(f"  - {r}", "white")
            cprint("=" * 80 + "\n", "green", attrs=['bold'])
        except Exception as e:
            cprint(f"[ERROR] BTCUSDT signal generation failed: {e}", "red")

    def run_forever(self):
        """Run every CHECK_INTERVAL_SECONDS."""
        cprint("\n" + "=" * 80, "magenta")
        cprint("🤖 BTCUSDT SIGNAL AGENT - CONTINUOUS MODE 🤖", "magenta", attrs=['bold'])
        cprint("=" * 80, "magenta")
        cprint(f"Symbol    : {SYMBOL}", "cyan")
        cprint(f"Interval  : every {CHECK_INTERVAL_SECONDS // 60} minutes", "cyan")
        cprint(f"Log file  : {SIGNAL_LOG}", "cyan")
        cprint("=" * 80 + "\n", "magenta")

        iteration = 0
        try:
            while True:
                iteration += 1
                cprint(f"\n🔄 RUN #{iteration}", "cyan", attrs=['bold'])
                self.run_once()
                cprint(f"⏳ Sleeping {CHECK_INTERVAL_SECONDS // 60} minutes...\n", "yellow")
                time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            cprint("\n👋 BTCUSDT Signal Agent stopped by user.", "yellow", attrs=['bold'])


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    agent = BtcSignalAgent()
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        agent.run_once()
    else:
        agent.run_forever()


if __name__ == "__main__":
    main()
