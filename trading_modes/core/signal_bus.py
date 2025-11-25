#!/usr/bin/env python3
"""
SIGNAL BUS - Unified Messaging System
Lightweight in-memory message broker for trading signals

Evidence-Based Design:
- Hohpe & Woolf (2003): Enterprise Integration Patterns
- Pub/Sub pattern for decoupling
- TTL-based message expiry
- Thread-safe operations
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import json


@dataclass
class Signal:
    """
    Normalized signal message

    All signal sources (RBI, Volume, Funding, Fusion) produce this format
    """
    source: str  # "RBI_STRATEGY" | "VOLUME_ENGINE" | "FUNDING_ENGINE" | "FUSION"
    symbol: str  # "BTC", "ETH", "SOL"
    timeframe: str  # "15m", "1H", "4H"
    action: str  # "BUY", "SELL", "NEUTRAL", "STRONG_BUY", "STRONG_SELL"
    confidence: float  # 0-100
    ttl_sec: int  # Time to live in seconds
    timestamp: str  # ISO8601 format
    metadata: Dict  # Strategy-specific data

    def is_expired(self) -> bool:
        """Check if signal has expired"""
        signal_time = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        age_seconds = (datetime.utcnow() - signal_time.replace(tzinfo=None)).total_seconds()
        return age_seconds > self.ttl_sec

    def age_seconds(self) -> float:
        """Get age of signal in seconds"""
        signal_time = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        return (datetime.utcnow() - signal_time.replace(tzinfo=None)).total_seconds()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Signal':
        """Create from dictionary"""
        return cls(**data)


class SignalBus:
    """
    In-memory signal message bus

    Thread-safe, TTL-aware, topic-based pub/sub
    """

    def __init__(self):
        """Initialize signal bus"""
        self._signals: Dict[str, List[Signal]] = defaultdict(list)
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List] = defaultdict(list)

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        print("[OK] Signal Bus initialized")

    def publish(self, signal: Signal):
        """
        Publish signal to bus

        Args:
            signal: Signal object to publish
        """
        with self._lock:
            topic = f"{signal.symbol}:{signal.timeframe}"
            self._signals[topic].append(signal)

            # Notify subscribers
            for callback in self._subscribers.get(topic, []):
                try:
                    callback(signal)
                except Exception as e:
                    print(f"❌ Subscriber callback error: {e}")

        print(f"📤 Published: {signal.source} → {signal.symbol} {signal.action} ({signal.confidence}%)")

    def subscribe(self, symbol: str, timeframe: str, callback):
        """
        Subscribe to signals for a specific symbol/timeframe

        Args:
            symbol: Trading symbol (BTC, ETH, etc.)
            timeframe: Timeframe (15m, 1H, etc.)
            callback: Function to call when signal received
        """
        topic = f"{symbol}:{timeframe}"
        with self._lock:
            self._subscribers[topic].append(callback)

        print(f"📥 Subscribed to {topic}")

    def get_signals(
        self,
        symbol: str,
        timeframe: str = None,
        source: str = None,
        max_age_sec: int = 1800,
        include_expired: bool = False
    ) -> List[Signal]:
        """
        Get signals from bus

        Args:
            symbol: Trading symbol
            timeframe: Optional timeframe filter
            source: Optional source filter
            max_age_sec: Maximum signal age (default 30 min)
            include_expired: Include expired signals

        Returns:
            List of matching signals
        """
        with self._lock:
            results = []

            # Search topics
            if timeframe:
                topics = [f"{symbol}:{timeframe}"]
            else:
                topics = [t for t in self._signals.keys() if t.startswith(f"{symbol}:")]

            for topic in topics:
                for signal in self._signals.get(topic, []):
                    # Filter by source
                    if source and signal.source != source:
                        continue

                    # Filter by age
                    if signal.age_seconds() > max_age_sec:
                        continue

                    # Filter expired
                    if not include_expired and signal.is_expired():
                        continue

                    results.append(signal)

            return results

    def get_latest_signal(
        self,
        symbol: str,
        timeframe: str,
        source: str = None
    ) -> Optional[Signal]:
        """
        Get most recent signal

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            source: Optional source filter

        Returns:
            Latest signal or None
        """
        signals = self.get_signals(symbol, timeframe, source, max_age_sec=1800)
        if not signals:
            return None

        # Sort by timestamp (newest first)
        signals.sort(key=lambda s: s.timestamp, reverse=True)
        return signals[0]

    def clear_expired(self):
        """Remove expired signals from bus"""
        with self._lock:
            for topic, signals in list(self._signals.items()):
                # Keep only non-expired
                self._signals[topic] = [s for s in signals if not s.is_expired()]

                # Remove empty topics
                if not self._signals[topic]:
                    del self._signals[topic]

    def _cleanup_loop(self):
        """Background thread to clean expired signals"""
        while True:
            time.sleep(60)  # Run every minute
            try:
                self.clear_expired()
            except Exception as e:
                print(f"❌ Cleanup error: {e}")

    def get_stats(self) -> Dict:
        """Get bus statistics"""
        with self._lock:
            total_signals = sum(len(signals) for signals in self._signals.values())

            by_source = defaultdict(int)
            by_symbol = defaultdict(int)

            for signals in self._signals.values():
                for signal in signals:
                    by_source[signal.source] += 1
                    by_symbol[signal.symbol] += 1

            return {
                'total_signals': total_signals,
                'active_topics': len(self._signals),
                'by_source': dict(by_source),
                'by_symbol': dict(by_symbol),
                'subscribers': sum(len(subs) for subs in self._subscribers.values())
            }

    def save_to_file(self, filepath: str):
        """Save current signals to JSON file"""
        with self._lock:
            data = {}
            for topic, signals in self._signals.items():
                data[topic] = [s.to_dict() for s in signals]

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

        print(f"💾 Saved signals to {filepath}")

    def load_from_file(self, filepath: str):
        """Load signals from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            with self._lock:
                for topic, signals_data in data.items():
                    self._signals[topic] = [Signal.from_dict(s) for s in signals_data]

            print(f"📂 Loaded signals from {filepath}")
        except FileNotFoundError:
            print(f"⚠️ File not found: {filepath}")
        except Exception as e:
            print(f"❌ Load error: {e}")


# Global singleton instance
_signal_bus = None


def get_signal_bus() -> SignalBus:
    """Get global signal bus instance"""
    global _signal_bus
    if _signal_bus is None:
        _signal_bus = SignalBus()
    return _signal_bus


# ==========================================
# TESTING
# ==========================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SIGNAL BUS TESTING")
    print("="*80 + "\n")

    # Get bus
    bus = get_signal_bus()

    # Test 1: Publish signals
    print("TEST 1: Publishing signals...")

    signal1 = Signal(
        source="RBI_STRATEGY",
        symbol="BTC",
        timeframe="15m",
        action="BUY",
        confidence=78.5,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={
            'strategy_name': 'MeanReversion_v18',
            'rsi': 28.5,
            'regime': 'BULL'
        }
    )

    signal2 = Signal(
        source="VOLUME_ENGINE",
        symbol="BTC",
        timeframe="15m",
        action="BUY",
        confidence=85.0,
        ttl_sec=1800,
        timestamp=datetime.utcnow().isoformat() + 'Z',
        metadata={
            'rvol': 2.3,
            'z_score': 3.2
        }
    )

    bus.publish(signal1)
    bus.publish(signal2)

    # Test 2: Subscribe
    print("\nTEST 2: Subscribing to signals...")

    def on_signal(signal: Signal):
        print(f"  🔔 Callback received: {signal.source} {signal.action}")

    bus.subscribe("BTC", "15m", on_signal)

    # Test 3: Get signals
    print("\nTEST 3: Retrieving signals...")

    signals = bus.get_signals("BTC", "15m")
    print(f"  Found {len(signals)} signals for BTC-15m")

    for sig in signals:
        print(f"    - {sig.source}: {sig.action} ({sig.confidence}%) age={sig.age_seconds():.1f}s")

    # Test 4: Get latest
    print("\nTEST 4: Get latest signal...")
    latest = bus.get_latest_signal("BTC", "15m", source="VOLUME_ENGINE")
    if latest:
        print(f"  Latest VOLUME_ENGINE: {latest.action} ({latest.confidence}%)")

    # Test 5: Stats
    print("\nTEST 5: Bus statistics...")
    stats = bus.get_stats()
    print(f"  Total signals: {stats['total_signals']}")
    print(f"  Active topics: {stats['active_topics']}")
    print(f"  By source: {stats['by_source']}")
    print(f"  By symbol: {stats['by_symbol']}")

    # Test 6: Save/Load
    print("\nTEST 6: Save/Load...")
    bus.save_to_file("test_signals.json")

    # Create new bus and load
    bus2 = SignalBus()
    bus2.load_from_file("test_signals.json")

    signals_loaded = bus2.get_signals("BTC", "15m")
    print(f"  Loaded {len(signals_loaded)} signals")

    print("\n✅ All tests passed!\n")
