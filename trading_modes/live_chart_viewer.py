#!/usr/bin/env python3
"""
LIVE CHART VIEWER for RBI Trading System (WebSocket-based)

Shows real-time price charts with strategy indicators (ATR, SMA, RSI)
Uses Binance WebSocket for smooth, flicker-free updates

Usage:
    python trading_modes/live_chart_viewer.py --symbol SOLUSDT --timeframe 1h
"""

import sys
import os
from pathlib import Path

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

import time
import threading
import json
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for Windows
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.gridspec import GridSpec
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import talib
from risk_management.binance_truth_paper_trading import BinanceTruthAPI
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
import websocket

# Wrapper for cprint that auto-flushes (Windows real-time display fix)
def cprint(*args, **kwargs):
    _cprint(*args, **kwargs)
    sys.stdout.flush()


class LiveChartViewer:
    """Real-time WebSocket-based price chart with indicators"""

    def __init__(self, symbol: str, timeframe: str = '1h'):
        self.symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"
        self.timeframe = timeframe
        self.fig = None
        self.current_price = None
        self.ws = None
        self.ws_thread = None
        self.running = True

        # Historical data
        self.ohlcv_df = None
        self.last_ohlcv_fetch = None

        # Strategy parameters (from VolatilityBracket)
        self.atr_period = 14
        self.sma_period = 50
        self.rsi_period = 14
        self.multiplier = 1.5  # Bracket multiplier

        # Matplotlib animation
        self.animation = None

        cprint(f"\n{'='*80}", "cyan")
        cprint(f"LIVE CHART VIEWER (WebSocket)", "cyan", attrs=['bold'])
        cprint(f"{'='*80}", "cyan")
        cprint(f"Symbol: {self.symbol}", "white")
        cprint(f"Timeframe: {timeframe}", "white")
        cprint(f"Update Mode: Real-time WebSocket", "white")
        cprint(f"{'='*80}\n", "cyan")

    def fetch_historical_data(self):
        """Fetch initial historical OHLCV data"""
        try:
            cprint(f"📊 Fetching historical {self.symbol} data ({self.timeframe})...", "cyan")
            ohlcv = BinanceTruthAPI.get_ohlcv_data(
                self.symbol,
                timeframe=self.timeframe,
                days_back=3
            )
            if ohlcv is not None and len(ohlcv) >= 50:
                self.ohlcv_df = ohlcv
                self.last_ohlcv_fetch = datetime.now()
                cprint(f"✅ Loaded {len(ohlcv)} historical candles", "green")
                return True
            else:
                cprint(f"⚠️ Insufficient historical data", "yellow")
                return False
        except Exception as e:
            cprint(f"❌ Error fetching historical data: {e}", "red")
            import traceback
            cprint(f"{traceback.format_exc()}", "red")
            return False

    def refresh_historical_data(self):
        """Refresh historical data every 5 minutes"""
        if self.last_ohlcv_fetch is None or (datetime.now() - self.last_ohlcv_fetch).seconds > 300:
            cprint(f"🔄 Refreshing historical data...", "cyan")
            self.fetch_historical_data()

    def on_ws_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            if 'p' in data:  # Price update
                self.current_price = float(data['p'])
        except Exception as e:
            pass  # Ignore parsing errors

    def on_ws_error(self, ws, error):
        """Handle WebSocket errors"""
        cprint(f"⚠️ WebSocket error: {error}", "yellow")

    def on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        if self.running:
            cprint(f"⚠️ WebSocket closed, reconnecting...", "yellow")
            time.sleep(2)
            self.start_websocket()

    def on_ws_open(self, ws):
        """Handle WebSocket open"""
        cprint(f"✅ WebSocket connected to {self.symbol}", "green")

    def start_websocket(self):
        """Start WebSocket connection for real-time price updates"""
        if not self.running:
            return

        ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@ticker"

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open
        )

        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def calculate_indicators(self, df):
        """Calculate ATR, SMA, RSI, and brackets"""
        if df is None or len(df) < 50:
            return None

        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        # Indicators
        atr = talib.ATR(high, low, close, timeperiod=self.atr_period)
        sma = talib.SMA(close, timeperiod=self.sma_period)
        rsi = talib.RSI(close, timeperiod=self.rsi_period)

        # Volatility brackets
        upper_bracket = close + (self.multiplier * atr)
        lower_bracket = close - (self.multiplier * atr)

        return {
            'atr': atr,
            'sma': sma,
            'rsi': rsi,
            'upper_bracket': upper_bracket,
            'lower_bracket': lower_bracket
        }

    def setup_chart(self):
        """Setup chart layout"""
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.patch.set_facecolor('#0a0a0a')

        gs = GridSpec(3, 1, height_ratios=[3, 1, 1], hspace=0.35, figure=self.fig)

        # Price + Brackets chart
        self.ax_price = self.fig.add_subplot(gs[0])
        self.ax_price.set_facecolor('#1a1a1a')
        self.ax_price.set_title(f'{self.symbol} - {self.timeframe} (Live WebSocket)',
                                fontsize=14, fontweight='bold', color='white')
        self.ax_price.set_ylabel('Price (USDT)', fontsize=10, color='white')
        self.ax_price.grid(True, alpha=0.2, color='gray')
        self.ax_price.tick_params(colors='white')

        # ATR chart
        self.ax_atr = self.fig.add_subplot(gs[1], sharex=self.ax_price)
        self.ax_atr.set_facecolor('#1a1a1a')
        self.ax_atr.set_title('ATR (Volatility)', fontsize=10, color='white')
        self.ax_atr.set_ylabel('ATR', fontsize=9, color='white')
        self.ax_atr.grid(True, alpha=0.2, color='gray')
        self.ax_atr.tick_params(colors='white')

        # RSI chart
        self.ax_rsi = self.fig.add_subplot(gs[2], sharex=self.ax_price)
        self.ax_rsi.set_facecolor('#1a1a1a')
        self.ax_rsi.set_title('RSI (Momentum)', fontsize=10, color='white')
        self.ax_rsi.set_ylabel('RSI', fontsize=9, color='white')
        self.ax_rsi.set_xlabel('Time', fontsize=10, color='white')
        self.ax_rsi.grid(True, alpha=0.2, color='gray')
        self.ax_rsi.tick_params(colors='white')
        self.ax_rsi.axhline(50, color='gray', linestyle='--', alpha=0.5)
        self.ax_rsi.axhline(70, color='red', linestyle='--', alpha=0.3)
        self.ax_rsi.axhline(30, color='green', linestyle='--', alpha=0.3)

        plt.tight_layout()

    def update_chart(self, frame):
        """Update chart (called by FuncAnimation)"""
        try:
            # Refresh historical data periodically
            self.refresh_historical_data()

            if self.ohlcv_df is None or len(self.ohlcv_df) < 50:
                return

            # Calculate indicators
            indicators = self.calculate_indicators(self.ohlcv_df)
            if indicators is None:
                return

            # Get last 100 candles for display
            plot_df = self.ohlcv_df.tail(100).copy()
            plot_df.reset_index(drop=True, inplace=True)

            atr_plot = indicators['atr'][-100:]
            sma_plot = indicators['sma'][-100:]
            rsi_plot = indicators['rsi'][-100:]
            upper_bracket_plot = indicators['upper_bracket'][-100:]
            lower_bracket_plot = indicators['lower_bracket'][-100:]

            # Clear axes without flickering
            self.ax_price.clear()
            self.ax_atr.clear()
            self.ax_rsi.clear()

            # Reapply styling
            self.ax_price.set_facecolor('#1a1a1a')
            self.ax_atr.set_facecolor('#1a1a1a')
            self.ax_rsi.set_facecolor('#1a1a1a')

            # Use WebSocket price if available, otherwise last candle close
            display_price = self.current_price if self.current_price else plot_df['close'].iloc[-1]

            # Price chart
            self.ax_price.plot(plot_df.index, plot_df['close'], label='Price',
                              color='#00d4ff', linewidth=1.5, alpha=0.9)
            self.ax_price.plot(plot_df.index, sma_plot, label=f'SMA({self.sma_period})',
                              color='orange', linewidth=1, alpha=0.7)
            self.ax_price.plot(plot_df.index, upper_bracket_plot, label='Upper Bracket',
                              color='red', linestyle='--', linewidth=1)
            self.ax_price.plot(plot_df.index, lower_bracket_plot, label='Lower Bracket',
                              color='lime', linestyle='--', linewidth=1)
            self.ax_price.fill_between(plot_df.index, upper_bracket_plot, lower_bracket_plot,
                                       alpha=0.1, color='gray')

            # Show current WebSocket price as horizontal line if different from last candle
            if self.current_price and abs(self.current_price - plot_df['close'].iloc[-1]) > 0.01:
                self.ax_price.axhline(self.current_price, color='cyan', linestyle=':',
                                     linewidth=2, alpha=0.7, label=f'Live: ${self.current_price:.2f}')

            self.ax_price.set_title(f'{self.symbol} - {self.timeframe} - Live: ${display_price:.2f}',
                                   fontsize=14, fontweight='bold', color='white')
            self.ax_price.set_ylabel('Price (USDT)', fontsize=10, color='white')
            self.ax_price.legend(loc='upper left', fontsize=9, facecolor='#1a1a1a',
                                edgecolor='gray', labelcolor='white')
            self.ax_price.grid(True, alpha=0.2, color='gray')
            self.ax_price.tick_params(colors='white')

            # ATR chart
            self.ax_atr.plot(plot_df.index, atr_plot, label=f'ATR({self.atr_period})',
                            color='purple', linewidth=1.5)
            self.ax_atr.set_title(f'ATR (Volatility) - Current: {atr_plot[-1]:.4f}',
                                 fontsize=10, color='white')
            self.ax_atr.set_ylabel('ATR', fontsize=9, color='white')
            self.ax_atr.legend(loc='upper left', fontsize=8, facecolor='#1a1a1a',
                              edgecolor='gray', labelcolor='white')
            self.ax_atr.grid(True, alpha=0.2, color='gray')
            self.ax_atr.tick_params(colors='white')

            # RSI chart
            self.ax_rsi.plot(plot_df.index, rsi_plot, label=f'RSI({self.rsi_period})',
                            color='teal', linewidth=1.5)
            self.ax_rsi.axhline(50, color='gray', linestyle='--', alpha=0.5)
            self.ax_rsi.axhline(70, color='red', linestyle='--', alpha=0.3, label='Overbought')
            self.ax_rsi.axhline(30, color='green', linestyle='--', alpha=0.3, label='Oversold')
            self.ax_rsi.set_title(f'RSI (Momentum) - Current: {rsi_plot[-1]:.1f}',
                                 fontsize=10, color='white')
            self.ax_rsi.set_ylabel('RSI', fontsize=9, color='white')
            self.ax_rsi.set_xlabel('Time', fontsize=10, color='white')
            self.ax_rsi.set_ylim(0, 100)
            self.ax_rsi.legend(loc='upper left', fontsize=8, facecolor='#1a1a1a',
                              edgecolor='gray', labelcolor='white')
            self.ax_rsi.grid(True, alpha=0.2, color='gray')
            self.ax_rsi.tick_params(colors='white')

            # Calculate current values
            current_price = display_price
            current_upper = upper_bracket_plot[-1]
            current_lower = lower_bracket_plot[-1]
            current_atr = atr_plot[-1]
            current_rsi = rsi_plot[-1]
            current_sma = sma_plot[-1]

            # Signal detection
            signal = "NEUTRAL"
            signal_color = "yellow"

            # Check for LONG setup
            if current_price > current_upper and current_sma > sma_plot[-2] and current_rsi > 50:
                signal = "🚀 LONG SIGNAL"
                signal_color = "lime"
            # Check for SHORT setup
            elif current_price < current_lower and current_sma < sma_plot[-2] and current_rsi < 50:
                signal = "🔻 SHORT SIGNAL"
                signal_color = "red"

            # Add text box with current status
            status_text = (
                f"Live Price: ${current_price:.2f}\n"
                f"Upper Bracket: ${current_upper:.2f}\n"
                f"Lower Bracket: ${current_lower:.2f}\n"
                f"SMA({self.sma_period}): ${current_sma:.2f}\n"
                f"ATR: {current_atr:.4f}\n"
                f"RSI: {current_rsi:.1f}\n"
                f"\n{signal}"
            )

            self.ax_price.text(
                0.02, 0.98, status_text,
                transform=self.ax_price.transAxes,
                fontsize=9,
                verticalalignment='top',
                color='white',
                bbox=dict(boxstyle='round', facecolor='#2a2a2a', alpha=0.9, edgecolor='gray')
            )

            # Console update (less frequent to avoid spam)
            if frame % 10 == 0:  # Print every 10 frames
                timestamp = datetime.now().strftime('%H:%M:%S')
                cprint(f"✅ [{timestamp}] Price: ${current_price:.2f} | {signal}", "cyan")

        except Exception as e:
            cprint(f"⚠️ Chart update error: {e}", "yellow")

    def run(self):
        """Run live chart viewer"""
        # Fetch initial historical data
        if not self.fetch_historical_data():
            cprint("❌ Failed to fetch historical data. Cannot start chart viewer.", "red")
            return

        # Start WebSocket for real-time price updates
        cprint("🔌 Connecting to Binance WebSocket...", "cyan")
        self.start_websocket()
        time.sleep(2)  # Give WebSocket time to connect

        # Setup chart
        cprint("📈 Initializing chart...", "cyan")
        self.setup_chart()

        cprint("✅ Chart viewer started! Close window to exit.", "green")

        # Start animation (updates every 1000ms = 1 second)
        self.animation = FuncAnimation(
            self.fig,
            self.update_chart,
            interval=1000,  # Update every 1 second
            cache_frame_data=False
        )

        try:
            plt.show()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if self.ws:
                self.ws.close()
            cprint("\n❌ Chart viewer stopped", "red")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Live WebSocket Chart Viewer for RBI Trading")
    parser.add_argument('--symbol', type=str, default='SOLUSDT',
                       help='Trading symbol (e.g., SOLUSDT, ETHUSDT, BTC)')
    parser.add_argument('--timeframe', type=str, default='1h',
                       help='Timeframe (e.g., 1h, 4h, 15m)')

    args = parser.parse_args()

    viewer = LiveChartViewer(symbol=args.symbol, timeframe=args.timeframe)
    viewer.run()
