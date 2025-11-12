"""
🌊 Moon Dev's Liquidation Monitor
Built with love by Moon Dev 🚀

Luna the Liquidation Agent tracks sudden increases in liquidation volume and announces when she sees potential market moves

Need an API key? for a limited time, bootcamp members get free api keys for claude, openai, helius, birdeye & quant elite gets access to the moon dev api. join here: https://algotradecamp.com
"""

import os
import sys
import pandas as pd
import time
from datetime import datetime, timedelta
from termcolor import colored, cprint
from dotenv import load_dotenv
import openai
import anthropic
from pathlib import Path
import requests  # For Coinalyze Free API
from collections import deque
import traceback
import numpy as np
import re

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Add project root to Python path for imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows Unicode encoding issues BEFORE any imports that print emojis
from src.utils.windows_unicode_fix import fix_windows_unicode
fix_windows_unicode()

# Now import project modules
from src import nice_funcs as n
from src import nice_funcs_hyperliquid as hl
from src.agents.api import MoonDevAPI
from src.agents.base_agent import BaseAgent

# Configuration
CHECK_INTERVAL_MINUTES = 10  # How often to check liquidations
LIQUIDATION_ROWS = 10000   # Number of rows to fetch each time
LIQUIDATION_THRESHOLD = .5  # Multiplier for average liquidation to detect significant events

# Model override settings - Adding DeepSeek support
MODEL_OVERRIDE = "deepseek-chat"  # Set to "deepseek-chat" or "deepseek-reasoner" to use DeepSeek, "0" to use default
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  # Base URL for DeepSeek API

# OHLCV Data Settings
TIMEFRAME = '15m'  # Candlestick timeframe
LOOKBACK_BARS = 100  # Number of candles to analyze

# Select which time window to use for comparisons (options: 15, 60, 240)
# 15 = 15 minutes (most reactive to sudden changes)
# 60 = 1 hour (medium-term changes)
# 240 = 4 hours (longer-term changes)
COMPARISON_WINDOW = 15  # Default to 15 minutes for quick reactions

# AI Settings - Override config.py if set
from src import config

# Only set these if you want to override config.py settings
AI_MODEL = False  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE
AI_MAX_TOKENS = 50  # Set > 0 to override config.AI_MAX_TOKENS

# Voice settings
VOICE_MODEL = "tts-1"
VOICE_NAME = "nova"  # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1

# AI Analysis Prompt
LIQUIDATION_ANALYSIS_PROMPT = """
You must respond in exactly 3 lines:
Line 1: Only write BUY, SELL, or NOTHING
Line 2: One short reason why
Line 3: Only write "Confidence: X%" where X is 0-100

Analyze market with total {pct_change}% increase in liquidations:

Current Long Liquidations: ${current_longs:,.2f} ({pct_change_longs:+.1f}% change)
Current Short Liquidations: ${current_shorts:,.2f} ({pct_change_shorts:+.1f}% change)
Time Period: Last {LIQUIDATION_ROWS} liquidation events

Market Data (Last {LOOKBACK_BARS} {TIMEFRAME} candles):
{market_data}

Large long liquidations often indicate potential bottoms (shorts taking profit)
Large short liquidations often indicate potential tops (longs taking profit)
Consider the ratio of long vs short liquidations and their relative changes
"""

class LiquidationAgent(BaseAgent):
    """Luna the Liquidation Monitor 🌊"""
    
    def __init__(self):
        """Initialize Luna the Liquidation Agent"""
        super().__init__('liquidation')
        
        # Set AI parameters - use config values unless overridden
        self.ai_model = AI_MODEL if AI_MODEL else config.AI_MODEL
        self.ai_temperature = AI_TEMPERATURE if AI_TEMPERATURE > 0 else config.AI_TEMPERATURE
        self.ai_max_tokens = AI_MAX_TOKENS if AI_MAX_TOKENS > 0 else config.AI_MAX_TOKENS
        
        print(f"🤖 Using AI Model: {self.ai_model}")
        if AI_MODEL or AI_TEMPERATURE > 0 or AI_MAX_TOKENS > 0:
            print("⚠️ Note: Using some override settings instead of config.py defaults")
            if AI_MODEL:
                print(f"  - Model: {AI_MODEL}")
            if AI_TEMPERATURE > 0:
                print(f"  - Temperature: {AI_TEMPERATURE}")
            if AI_MAX_TOKENS > 0:
                print(f"  - Max Tokens: {AI_MAX_TOKENS}")
                
        load_dotenv()
        
        # Get API keys
        openai_key = os.getenv("OPENAI_KEY")
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        deepseek_key = os.getenv("DEEPSEEK_KEY")
        
        if not openai_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        if not anthropic_key:
            raise ValueError("🚨 ANTHROPIC_KEY not found in environment variables!")
            
        # Initialize OpenAI client for DeepSeek
        if deepseek_key and MODEL_OVERRIDE.lower() == "deepseek-chat":
            self.deepseek_client = openai.OpenAI(
                api_key=deepseek_key,
                base_url=DEEPSEEK_BASE_URL
            )
            print("🚀 DeepSeek model initialized!")
        else:
            self.deepseek_client = None
            
        # Initialize other clients
        openai.api_key = openai_key
        self.client = anthropic.Anthropic(api_key=anthropic_key)

        # Initialize Coinalyze Free API instead of MoonDevAPI
        # NOTE: Coinalyze historical liquidation data may require account verification
        # Fallback: Use Binance OI data to detect liquidations (OI drops = liquidations)
        coinalyze_key = os.getenv("COINALYZE_API_KEY")
        self.use_oi_fallback = True  # Use OI-based liquidation detection as primary method

        self.coinalyze_api_key = coinalyze_key if coinalyze_key else None
        self.coinalyze_base_url = "https://api.coinalyze.net/v1"
        self.binance_oi_url = "https://fapi.binance.com/fapi/v1/openInterest"
        self.binance_price_url = "https://fapi.binance.com/fapi/v1/ticker/price"

        cprint("Using Binance OI-based liquidation detection (FREE)", "green")
        cprint("OI drops indicate liquidation events - this is how pros track liquidations", "cyan")
        
        # Create data directories if they don't exist
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.data_dir = PROJECT_ROOT / "src" / "data"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load historical data
        self.history_file = self.data_dir / "liquidation_history.csv"
        self.load_history()
        
        print("🌊 Luna the Liquidation Agent initialized!")
        print(f"🎯 Alerting on liquidation increases above +{LIQUIDATION_THRESHOLD*100:.0f}% from previous")
        print(f"📊 Analyzing last {LIQUIDATION_ROWS} liquidation events")
        print(f"📈 Using {LOOKBACK_BARS} {TIMEFRAME} candles for market context")
        
    def load_history(self):
        """Load or initialize historical liquidation data"""
        try:
            if self.history_file.exists():
                self.liquidation_history = pd.read_csv(self.history_file)
                
                # Handle transition from old format to new format
                if 'long_size' not in self.liquidation_history.columns:
                    print("📝 Converting history to new format with long/short tracking...")
                    # Assume 50/50 split for old records (we'll get accurate data on next update)
                    self.liquidation_history['long_size'] = self.liquidation_history['total_size'] / 2
                    self.liquidation_history['short_size'] = self.liquidation_history['total_size'] / 2
                
                print(f"📈 Loaded {len(self.liquidation_history)} historical liquidation records")
            else:
                self.liquidation_history = pd.DataFrame(columns=['timestamp', 'long_size', 'short_size', 'total_size'])
                print("📝 Created new liquidation history file")
                
            # Clean up old data (keep only last 24 hours)
            if not self.liquidation_history.empty:
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.liquidation_history = self.liquidation_history[
                    pd.to_datetime(self.liquidation_history['timestamp']) > cutoff_time
                ]
                self.liquidation_history.to_csv(self.history_file, index=False)
                
        except Exception as e:
            print(f"❌ Error loading history: {str(e)}")
            self.liquidation_history = pd.DataFrame(columns=['timestamp', 'long_size', 'short_size', 'total_size'])
            
    def _get_current_liquidations(self):
        """
        Detect liquidations using Binance Open Interest changes (FREE method)

        When Open Interest drops sharply, it indicates liquidation events.
        This is actually how professional traders track liquidations in real-time.

        Returns: (estimated_long_liquidations, estimated_short_liquidations) in USD
        """
        try:
            print("\n🔍 Detecting liquidations via Open Interest changes (Binance Free API)...")

            # Get current OI for BTC and ETH
            btc_oi_response = requests.get(
                self.binance_oi_url,
                params={"symbol": "BTCUSDT"},
                timeout=10
            )
            btc_price_response = requests.get(
                self.binance_price_url,
                params={"symbol": "BTCUSDT"},
                timeout=10
            )
            eth_oi_response = requests.get(
                self.binance_oi_url,
                params={"symbol": "ETHUSDT"},
                timeout=10
            )
            eth_price_response = requests.get(
                self.binance_price_url,
                params={"symbol": "ETHUSDT"},
                timeout=10
            )

            if (btc_oi_response.status_code != 200 or btc_price_response.status_code != 200 or
                eth_oi_response.status_code != 200 or eth_price_response.status_code != 200):
                print(f"❌ Binance API error fetching OI data")
                return None, None

            # Parse responses
            btc_oi_data = btc_oi_response.json()
            btc_price_data = btc_price_response.json()
            eth_oi_data = eth_oi_response.json()
            eth_price_data = eth_price_response.json()

            # Calculate current OI in USD
            btc_oi_usd = float(btc_oi_data['openInterest']) * float(btc_price_data['price'])
            eth_oi_usd = float(eth_oi_data['openInterest']) * float(eth_price_data['price'])
            total_oi_usd = btc_oi_usd + eth_oi_usd

            # Get previous OI from history
            if not self.liquidation_history.empty:
                previous_record = self.liquidation_history.iloc[-1]
                previous_total_oi = previous_record.get('total_size', total_oi_usd)

                # Calculate OI change (negative = liquidations)
                oi_change_usd = total_oi_usd - previous_total_oi
                oi_change_pct = (oi_change_usd / previous_total_oi * 100) if previous_total_oi > 0 else 0

                # If OI dropped, estimate liquidations
                # We can't know long vs short split without funding data, so estimate 50/50
                # Or use price movement to infer direction
                if oi_change_usd < 0:
                    estimated_liquidations = abs(oi_change_usd)

                    # Try to determine if longs or shorts got liquidated based on price
                    try:
                        # Get price change from last check
                        btc_current_price = float(btc_price_data['price'])
                        # Store price in history for next comparison
                        if 'btc_price' in previous_record:
                            btc_previous_price = previous_record.get('btc_price', btc_current_price)
                            price_change_pct = ((btc_current_price - btc_previous_price) / btc_previous_price * 100)

                            # If price dropped AND OI dropped = Long liquidations
                            # If price rose AND OI dropped = Short liquidations (less common)
                            if price_change_pct < -0.5:  # Price dropped
                                estimated_long_liq = estimated_liquidations * 0.8  # 80% longs
                                estimated_short_liq = estimated_liquidations * 0.2  # 20% shorts
                            elif price_change_pct > 0.5:  # Price rose
                                estimated_long_liq = estimated_liquidations * 0.2
                                estimated_short_liq = estimated_liquidations * 0.8
                            else:  # Sideways
                                estimated_long_liq = estimated_liquidations * 0.5
                                estimated_short_liq = estimated_liquidations * 0.5
                        else:
                            # First run, assume 50/50
                            estimated_long_liq = estimated_liquidations * 0.5
                            estimated_short_liq = estimated_liquidations * 0.5

                    except:
                        # Fallback to 50/50 split
                        estimated_long_liq = estimated_liquidations * 0.5
                        estimated_short_liq = estimated_liquidations * 0.5

                else:
                    # OI increased or stayed flat = no liquidations
                    estimated_long_liq = 0
                    estimated_short_liq = 0

                # Calculate percentage changes for display
                pct_change_longs = ((estimated_long_liq - previous_record.get('long_size', 0)) /
                                   previous_record.get('long_size', 1)) * 100 if previous_record.get('long_size', 0) > 0 else 0
                pct_change_shorts = ((estimated_short_liq - previous_record.get('short_size', 0)) /
                                    previous_record.get('short_size', 1)) * 100 if previous_record.get('short_size', 0) > 0 else 0

            else:
                # First run - no liquidations detected yet
                estimated_long_liq = 0
                estimated_short_liq = 0
                oi_change_usd = 0
                oi_change_pct = 0
                pct_change_longs = 0
                pct_change_shorts = 0

            # Print liquidation detection box
            print("\n" + "╔" + "═" * 70 + "╗")
            print("║           🌙 Moon Dev's Liquidation Detector (OI-Based) 💦        ║")
            print("╠" + "═" * 70 + "╣")
            print(f"║  Current Total OI: ${total_oi_usd:,.2f}".ljust(71) + "║")
            print(f"║  OI Change: ${oi_change_usd:,.2f} ({oi_change_pct:+.2f}%)".ljust(71) + "║")
            print(f"║  ".ljust(71) + "║")
            print(f"║  Estimated LONG Liquidations:  ${estimated_long_liq:,.2f} [{pct_change_longs:+.1f}%]".ljust(71) + "║")
            print(f"║  Estimated SHORT Liquidations: ${estimated_short_liq:,.2f} [{pct_change_shorts:+.1f}%]".ljust(71) + "║")
            print(f"║  ".ljust(71) + "║")
            print(f"║  Method: OI drops = Liquidation events (Pro trader technique)".ljust(71) + "║")
            print("╚" + "═" * 70 + "╝")

            # Store current BTC price and total OI for next comparison
            self.current_btc_price = float(btc_price_data['price'])
            self.current_total_oi = total_oi_usd

            return estimated_long_liq, estimated_short_liq

        except Exception as e:
            print(f"❌ Error detecting liquidations via OI: {str(e)}")
            traceback.print_exc()
            return None, None
            
    def _analyze_opportunity(self, current_longs, current_shorts, previous_longs, previous_shorts):
        """Get AI analysis of the liquidation event"""
        try:
            # Calculate percentage changes
            pct_change_longs = ((current_longs - previous_longs) / previous_longs) * 100 if previous_longs > 0 else 0
            pct_change_shorts = ((current_shorts - previous_shorts) / previous_shorts) * 100 if previous_shorts > 0 else 0
            total_pct_change = ((current_longs + current_shorts - previous_longs - previous_shorts) / 
                              (previous_longs + previous_shorts)) * 100 if (previous_longs + previous_shorts) > 0 else 0
            
            # Get market data from Binance (primary) or Hyperliquid (backup)
            market_data = None

            try:
                # Try Binance first (FREE, faster)
                print("📊 Fetching market data from Binance...")
                url = "https://fapi.binance.com/fapi/v1/klines"
                params = {
                    "symbol": "BTCUSDT",
                    "interval": "15m",
                    "limit": LOOKBACK_BARS
                }
                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    klines = response.json()
                    # Convert to DataFrame
                    market_data = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    market_data = market_data[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    market_data[['open', 'high', 'low', 'close', 'volume']] = market_data[['open', 'high', 'low', 'close', 'volume']].astype(float)
                    print("✅ Binance market data fetched successfully")
            except Exception as e:
                print(f"⚠️ Binance failed: {e}, trying Hyperliquid backup...")

            # Fallback to Hyperliquid if Binance fails
            if market_data is None or market_data.empty:
                try:
                    print("📊 Fetching market data from Hyperliquid (backup)...")
                    market_data = hl.get_data(
                        symbol="BTC",
                        timeframe=TIMEFRAME,
                        bars=LOOKBACK_BARS,
                        add_indicators=True
                    )
                except Exception as e:
                    print(f"⚠️ Hyperliquid also failed: {e}")

            if market_data is None or market_data.empty:
                print("⚠️ Could not fetch market data from any source, proceeding with liquidation analysis only")
                market_data_str = "No market data available"
            else:
                # Format market data nicely - show last 5 candles
                market_data_str = market_data.tail(5).to_string()
            
            # Prepare the context
            context = LIQUIDATION_ANALYSIS_PROMPT.format(
                pct_change=f"{total_pct_change:.2f}",
                current_size=current_longs + current_shorts,
                previous_size=previous_longs + previous_shorts,
                LIQUIDATION_ROWS=LIQUIDATION_ROWS,
                current_longs=current_longs,
                current_shorts=current_shorts,
                pct_change_longs=pct_change_longs,
                pct_change_shorts=pct_change_shorts,
                LOOKBACK_BARS=LOOKBACK_BARS,
                TIMEFRAME=TIMEFRAME,
                market_data=market_data_str
            )
            
            print(f"\n🤖 Analyzing liquidation spike with AI...")
            
            # Use DeepSeek if configured
            if self.deepseek_client and MODEL_OVERRIDE.lower() == "deepseek-chat":
                print("🚀 Using DeepSeek for analysis...")
                response = self.deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a liquidation analyst. You must respond in exactly 3 lines: BUY/SELL/NOTHING, reason, and confidence."},
                        {"role": "user", "content": context}
                    ],
                    max_tokens=self.ai_max_tokens,
                    temperature=self.ai_temperature,
                    stream=False
                )
                response_text = response.choices[0].message.content.strip()
            else:
                # Use Claude as before
                print("🤖 Using Claude for analysis...")
                message = self.client.messages.create(
                    model=self.ai_model,
                    max_tokens=self.ai_max_tokens,
                    temperature=self.ai_temperature,
                    messages=[{
                        "role": "user",
                        "content": context
                    }]
                )
                response_text = str(message.content)
            
            # Handle response
            if not response_text:
                print("❌ No response from AI")
                return None
                
            # Handle TextBlock response if using Claude
            if 'TextBlock' in response_text:
                match = re.search(r"text='([^']*)'", response_text)
                if match:
                    response_text = match.group(1)
                    
            # Parse response - handle both newline and period-based splits
            lines = [line.strip() for line in response_text.split('\n') if line.strip()]
            if not lines:
                print("❌ Empty response from AI")
                return None
                
            # First line should be the action
            action = lines[0].strip().upper()
            if action not in ['BUY', 'SELL', 'NOTHING']:
                print(f"⚠️ Invalid action: {action}")
                return None
                
            # Rest is analysis
            analysis = lines[1] if len(lines) > 1 else ""
            
            # Extract confidence from third line
            confidence = 50  # Default confidence
            if len(lines) > 2:
                try:
                    matches = re.findall(r'(\d+)%', lines[2])
                    if matches:
                        confidence = int(matches[0])
                except:
                    print("⚠️ Could not parse confidence, using default")
            
            return {
                'action': action,
                'analysis': analysis,
                'confidence': confidence,
                'pct_change': total_pct_change,
                'pct_change_longs': pct_change_longs,
                'pct_change_shorts': pct_change_shorts,
                'model_used': 'deepseek-chat' if self.deepseek_client else self.ai_model
            }
            
        except Exception as e:
            print(f"❌ Error in AI analysis: {str(e)}")
            traceback.print_exc()
            return None
            
    def _format_announcement(self, analysis):
        """Format liquidation analysis into a speech-friendly message"""
        try:
            if analysis:
                # Determine which liquidation type was more significant
                if abs(analysis['pct_change_longs']) > abs(analysis['pct_change_shorts']):
                    liq_type = "LONG"
                    pct_change = analysis['pct_change_longs']
                else:
                    liq_type = "SHORT"
                    pct_change = analysis['pct_change_shorts']
                
                # Format the percentage change message
                if pct_change > 0:
                    change_msg = f"up {abs(pct_change):.1f}%"
                else:
                    change_msg = f"down {abs(pct_change):.1f}%"
                
                message = (
                    f"ayo moon dev seven seven seven! "
                    f"Massive {liq_type} liquidations detected! "
                    f"{change_msg} in the last period! "
                    f"AI suggests {analysis['action']} with {analysis['confidence']}% confidence 🌙"
                )
                return message
            return None
            
        except Exception as e:
            print(f"❌ Error formatting announcement: {str(e)}")
            return None
            
    def _announce(self, message):
        """Announce message using OpenAI TTS"""
        if not message:
            return
            
        try:
            print(f"\n📢 Announcing: {message}")
            
            # Generate speech
            response = openai.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                input=message,
                speed=VOICE_SPEED
            )
            
            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = self.audio_dir / f"liquidation_alert_{timestamp}.mp3"
            
            response.stream_to_file(audio_file)
            
            # Play audio using system command
            os.system(f"afplay {audio_file}")
            
        except Exception as e:
            print(f"❌ Error in announcement: {str(e)}")
            
    def _save_to_history(self, long_size, short_size):
        """Save current liquidation data to history"""
        try:
            if long_size is not None and short_size is not None:
                # Create new row (include BTC price and total OI for next comparison)
                new_row = pd.DataFrame([{
                    'timestamp': datetime.now(),
                    'long_size': long_size,
                    'short_size': short_size,
                    'total_size': getattr(self, 'current_total_oi', 0),  # Store actual OI, not liquidations
                    'btc_price': getattr(self, 'current_btc_price', 0)
                }])

                # Add to history
                if self.liquidation_history.empty:
                    self.liquidation_history = new_row
                else:
                    self.liquidation_history = pd.concat([self.liquidation_history, new_row], ignore_index=True)

                # Keep only last 24 hours
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.liquidation_history = self.liquidation_history[
                    pd.to_datetime(self.liquidation_history['timestamp']) > cutoff_time
                ]

                # Save to file
                self.liquidation_history.to_csv(self.history_file, index=False)

        except Exception as e:
            print(f"❌ Error saving to history: {str(e)}")
            traceback.print_exc()
            
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            # Get current liquidation data
            current_longs, current_shorts = self._get_current_liquidations()
            
            if current_longs is not None and current_shorts is not None:
                # Get previous size
                if not self.liquidation_history.empty:
                    previous_record = self.liquidation_history.iloc[-1]
                    
                    # Handle missing columns gracefully
                    previous_longs = previous_record.get('long_size', 0)
                    previous_shorts = previous_record.get('short_size', 0)
                    
                    # Only trigger if we have valid previous data
                    if previous_longs > 0 and previous_shorts > 0:
                        # Check if we have a significant increase in either longs or shorts
                        # Adding 1 to threshold so 0.5 means 150% of previous value
                        threshold = 1 + LIQUIDATION_THRESHOLD
                        if (current_longs > (previous_longs * threshold) or 
                            current_shorts > (previous_shorts * threshold)):
                            # Get AI analysis
                            analysis = self._analyze_opportunity(current_longs, current_shorts, 
                                                              previous_longs, previous_shorts)
                            
                            if analysis:
                                # Format and announce
                                message = self._format_announcement(analysis)
                                if message:
                                    self._announce(message)
                                    
                                    # Print detailed analysis
                                    print("\n" + "╔" + "═" * 50 + "╗")
                                    print("║        🌙 Moon Dev's Liquidation Analysis 💦       ║")
                                    print("╠" + "═" * 50 + "╣")
                                    print(f"║  Action: {analysis['action']:<41} ║")
                                    print(f"║  Confidence: {analysis['confidence']}%{' '*36} ║")
                                    analysis_lines = analysis['analysis'].split('\n')
                                    for line in analysis_lines:
                                        print(f"║  {line:<47} ║")
                                    print("╚" + "═" * 50 + "╝")
                
                # Save to history
                self._save_to_history(current_longs, current_shorts)
                
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")
            traceback.print_exc()

    def run(self):
        """Run the liquidation monitor continuously"""
        print("\n🌊 Starting liquidation monitoring...")
        
        while True:
            try:
                self.run_monitoring_cycle()
                print(f"\n💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Luna the Liquidation Agent shutting down gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying

if __name__ == "__main__":
    agent = LiquidationAgent()
    agent.run()
