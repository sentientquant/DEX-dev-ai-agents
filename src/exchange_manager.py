"""
🌙 Moon Dev's Exchange Manager
Unified interface for trading on Solana and HyperLiquid
Built with love by Moon Dev 🚀
"""

import os
import sys
# Make termcolor optional
try:
    from termcolor import colored, cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text
from dotenv import load_dotenv
import pandas as pd
import time
import ccxt  # CCXT for unified exchange API

# Load environment variables
load_dotenv()

class ExchangeManager:
    """
    Unified exchange interface for seamless switching between Solana and HyperLiquid
    """

    def __init__(self, exchange=None):
        """Initialize the exchange manager with the specified exchange"""
        from src import config

        # Use provided exchange or default from config
        self.exchange = exchange or config.EXCHANGE
        self.account = None

        # Initialize based on exchange type
        if self.exchange.lower() == 'hyperliquid':
            try:
                import eth_account
                from src import nice_funcs_hyperliquid as hl

                # Get HyperLiquid key from environment
                hl_key = os.getenv('HYPER_LIQUID_KEY')
                if not hl_key:
                    raise ValueError("HYPER_LIQUID_KEY not found in environment")

                # Initialize account
                self.account = eth_account.Account.from_key(hl_key)
                self.hl = hl

                cprint(f"✅ Initialized HyperLiquid exchange manager", "green")
                cprint(f"   Account: {self.account.address[:6]}...{self.account.address[-4:]}", "cyan")

            except Exception as e:
                cprint(f"❌ Failed to initialize HyperLiquid: {str(e)}", "red")
                raise

        elif self.exchange.lower() == 'solana':
            try:
                from src import nice_funcs as solana
                self.solana = solana
                cprint(f"✅ Initialized Solana exchange manager", "green")

            except Exception as e:
                cprint(f"❌ Failed to initialize Solana: {str(e)}", "red")
                raise

        elif self.exchange.lower() == 'binance':
            try:
                # Import Binance Truth API for real market data
                from risk_management.binance_truth_paper_trading import BinanceTruthAPI

                self.binance_api = BinanceTruthAPI()

                # PERMANENT FIX: Only import binance library if we have API keys
                # This prevents hanging on import when running in PAPER mode
                binance_api_key = os.getenv('BINANCE_API_KEY')
                binance_secret_key = os.getenv('BINANCE_SECRET_KEY')

                BinanceClient = None
                BinanceAPIException = None

                # Skip import if no API keys (PAPER mode doesn't need it)
                if not binance_api_key or not binance_secret_key:
                    cprint(f"ℹ️  No Binance API keys found - PAPER mode only", "cyan")
                    self.binance_client = None
                    self.ccxt_binance = None
                else:
                    # CRITICAL FIX: Import with subprocess timeout to prevent hanging
                    # The binance library can hang indefinitely on import
                    import subprocess
                    import sys

                    cprint(f"[INFO] Testing Binance library availability (5s timeout)...", "cyan")

                    # Test import in subprocess with timeout
                    test_import_code = "from binance.client import Client; print('OK')"
                    try:
                        result = subprocess.run(
                            [sys.executable, "-c", test_import_code],
                            capture_output=True,
                            timeout=5.0,  # 5 second timeout
                            text=True
                        )

                        if result.returncode == 0 and "OK" in result.stdout:
                            # Import succeeded in subprocess, safe to import in main process
                            cprint(f"[INFO] Loading Binance library for LIVE trading...", "cyan")
                            from binance.client import Client as BinanceClient
                            from binance.exceptions import BinanceAPIException
                            cprint(f"✅ Binance library loaded successfully", "green")
                        else:
                            cprint(f"⚠️  Binance library test failed", "yellow")
                            cprint(f"   Continuing in PAPER mode without LIVE trading", "yellow")
                            BinanceClient = None
                            BinanceAPIException = None
                    except subprocess.TimeoutExpired:
                        cprint(f"⚠️  Binance library import timed out (network issue)", "yellow")
                        cprint(f"   Continuing in PAPER mode without LIVE trading", "yellow")
                        BinanceClient = None
                        BinanceAPIException = None
                    except Exception as import_err:
                        cprint(f"⚠️  Failed to test binance library: {import_err}", "yellow")
                        cprint(f"   Continuing in PAPER mode without LIVE trading", "yellow")
                        BinanceClient = None
                        BinanceAPIException = None

                # Only proceed with LIVE trading setup if we have BinanceClient
                if BinanceClient is not None and binance_api_key and binance_secret_key:
                    # PERMANENT FIX: Sync Windows time BEFORE initializing Binance
                    # This prevents timestamp errors from the start
                    if os.name == 'nt':
                        try:
                            import subprocess
                            cprint(f"🔧 Syncing Windows system time with internet time servers...", "cyan")
                            result = subprocess.run(['w32tm', '/resync'], capture_output=True, text=True, timeout=10, check=False)
                            if result.returncode == 0:
                                cprint(f"   ✅ Time synchronized successfully", "green")
                                # Wait for time sync to propagate
                                time.sleep(1)
                            else:
                                cprint(f"   ⚠️  Time sync returned: {result.stdout.strip()}", "yellow")
                                cprint(f"   Note: Time sync may require administrator privileges", "yellow")
                        except subprocess.TimeoutExpired:
                            cprint(f"   ⚠️  Time sync timed out", "yellow")
                        except Exception as sync_err:
                            cprint(f"   ⚠️  Time sync skipped: {sync_err}", "yellow")

                    # CRITICAL FIX: Initialize CCXT first (better timestamp handling)
                    # CCXT has built-in 'adjustForTimeDifference' which python-binance lacks
                    cprint(f"🔧 Initializing Binance via CCXT (timestamp auto-adjustment)...", "cyan")

                    self.ccxt_binance = ccxt.binance({
                        'apiKey': binance_api_key,
                        'secret': binance_secret_key,
                        'enableRateLimit': True,
                        'timeout': 30000,  # 30 second timeout
                        'options': {
                            'defaultType': 'spot',
                            'recvWindow': 60000,  # 60 second receive window
                            'adjustForTimeDifference': True,  # CRITICAL: Auto-adjust for clock drift
                        }
                    })

                    # Test CCXT connection and load markets
                    connected = False
                    for attempt in range(3):
                        try:
                            # Synchronize time offset with exchange
                            cprint(f"🕐 Fetching server time (attempt {attempt+1}/3)...", "cyan")
                            self.ccxt_binance.load_time_difference()  # Calculates and stores offset

                            # Test account access
                            account_info = self.ccxt_binance.fetch_balance()

                            # Load market data
                            self.ccxt_binance.load_markets()

                            connected = True
                            offset_ms = self.ccxt_binance.options.get('timeDifference', 0)
                            cprint(f"✅ CCXT Binance connected (time offset: {offset_ms}ms)", "green")
                            cprint(f"   Account Type: SPOT", "cyan")
                            cprint(f"   Total Balance: ${account_info['total'].get('USDT', 0):.2f} USDT", "cyan")
                            break

                        except Exception as e:
                            error_msg = str(e)
                            cprint(f"⚠️  CCXT attempt {attempt+1} failed: {error_msg}", "yellow")
                            if attempt < 2:
                                time.sleep(2)  # Wait before retry
                            else:
                                cprint(f"❌ Failed to initialize CCXT Binance: {e}", "red")
                                raise e

                    if not connected:
                        raise Exception("Failed to connect to Binance via CCXT after 3 attempts")

                    # PERMANENT FIX: Initialize python-binance client LAST (optional fallback)
                    # Use CCXT as primary client since it handles timestamps correctly
                    try:
                        cprint(f"🔧 Initializing python-binance client (fallback)...", "cyan")

                        # Get timestamp offset from CCXT
                        time_offset = self.ccxt_binance.options.get('timeDifference', 0)

                        self.binance_client = BinanceClient(
                            binance_api_key,
                            binance_secret_key,
                            {'timeout': 30},
                            ping=False  # Disable auto-ping
                        )

                        # PERMANENT FIX: Apply timestamp offset to python-binance client
                        if time_offset != 0:
                            cprint(f"   🔧 Applying {time_offset}ms offset to python-binance client", "cyan")
                            self.binance_client.timestamp_offset = time_offset

                        self.recv_window = 60000  # Use max receive window
                        cprint(f"   ✅ python-binance client ready (backup for specific APIs)", "green")

                    except Exception as fallback_err:
                        cprint(f"   ⚠️  python-binance client init failed: {fallback_err}", "yellow")
                        cprint(f"   Using CCXT only (recommended)", "cyan")
                        self.binance_client = None
                        self.recv_window = 60000

                    # CCXT already initialized above with better timestamp handling
                    cprint(f"✅ Initialized Binance LIVE trading", "green")
                    cprint(f"   Primary: CCXT (timestamp auto-adjustment)", "cyan")
                    cprint(f"   Fallback: python-binance (legacy API support)", "cyan" if self.binance_client else "yellow")
                else:
                    self.binance_client = None
                    self.ccxt_binance = None
                    cprint(f"✅ Initialized Binance exchange manager (PAPER MODE ONLY)", "green")
                    cprint(f"   Using REAL Binance market data for analysis", "cyan")
                    cprint(f"   Paper trades logged to TradingDatabase", "cyan")
                    cprint(f"   ⚠️  BINANCE_API_KEY and BINANCE_SECRET_KEY not found - LIVE trading disabled", "yellow")

            except Exception as e:
                cprint(f"❌ Failed to initialize Binance: {str(e)}", "red")
                raise

        else:
            raise ValueError(f"Unknown exchange: {self.exchange}")

    def market_buy(self, symbol_or_token, usd_amount):
        """
        Execute a market buy order

        Args:
            symbol_or_token: Symbol (for HyperLiquid/Binance) or token address (for Solana)
            usd_amount: USD amount to buy

        Returns:
            Order result from the respective exchange
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.market_buy(symbol_or_token, usd_amount, self.account)
        elif self.exchange.lower() == 'binance':
            # REAL Binance trading if client is initialized (LIVE mode)
            if self.binance_client:
                try:
                    # Ensure symbol has USDT suffix
                    symbol = symbol_or_token if symbol_or_token.endswith('USDT') else f"{symbol_or_token}USDT"

                    # Get current price
                    current_price = float(self.binance_client.get_symbol_ticker(symbol=symbol)['price'])

                    # Calculate quantity (how many coins to buy)
                    quantity = usd_amount / current_price

                    # Get symbol info for precision
                    info = self.binance_client.get_symbol_info(symbol)
                    step_size = None
                    for filter in info['filters']:
                        if filter['filterType'] == 'LOT_SIZE':
                            step_size = float(filter['stepSize'])
                            break

                    # Round quantity to proper precision
                    if step_size:
                        precision = len(str(step_size).rstrip('0').split('.')[-1])
                        quantity = round(quantity, precision)

                    # Execute REAL market buy order
                    cprint(f"   [BINANCE] Executing LIVE market BUY: {quantity} {symbol} @ ${current_price:.6f}", "cyan")
                    order = self.binance_client.order_market_buy(symbol=symbol, quantity=quantity)

                    return {
                        'success': True,
                        'symbol': symbol,
                        'side': 'BUY',
                        'price': float(order.get('fills', [{}])[0].get('price', current_price)),
                        'quantity': float(order.get('executedQty', quantity)),
                        'size_usd': usd_amount,
                        'order_id': order.get('orderId'),
                        'note': 'LIVE order executed on Binance',
                        'raw_order': order
                    }

                except Exception as e:
                    cprint(f"   ❌ Binance LIVE order failed: {str(e)}", "red")
                    return {
                        'success': False,
                        'error': str(e),
                        'symbol': symbol_or_token,
                        'side': 'BUY',
                        'size_usd': usd_amount
                    }
            else:
                # Paper trading mode (no API keys)
                current_price = self.binance_api.get_live_price(symbol_or_token)
                return {
                    'success': True,
                    'symbol': symbol_or_token,
                    'side': 'BUY',
                    'price': current_price,
                    'size_usd': usd_amount,
                    'note': 'Paper trade - logged to database by flow'
                }
        else:
            return self.solana.market_buy(symbol_or_token, usd_amount)

    def market_sell(self, symbol_or_token, usd_amount_or_percent):
        """
        Execute a market sell order

        Args:
            symbol_or_token: Symbol (for HyperLiquid/Binance) or token address (for Solana)
            usd_amount_or_percent: USD amount for HyperLiquid/Binance, percentage for Solana

        Returns:
            Order result from the respective exchange
        """
        if self.exchange.lower() == 'hyperliquid':
            # HyperLiquid expects USD amount
            return self.hl.market_sell(symbol_or_token, usd_amount_or_percent, self.account)
        elif self.exchange.lower() == 'binance':
            # REAL Binance trading if client is initialized (LIVE mode)
            if self.binance_client:
                try:
                    # Ensure symbol has USDT suffix
                    symbol = symbol_or_token if symbol_or_token.endswith('USDT') else f"{symbol_or_token}USDT"

                    # Get current price
                    current_price = float(self.binance_client.get_symbol_ticker(symbol=symbol)['price'])

                    # Calculate quantity (how many coins to sell)
                    quantity = usd_amount_or_percent / current_price

                    # Get symbol info for precision
                    info = self.binance_client.get_symbol_info(symbol)
                    step_size = None
                    for filter in info['filters']:
                        if filter['filterType'] == 'LOT_SIZE':
                            step_size = float(filter['stepSize'])
                            break

                    # Round quantity to proper precision
                    if step_size:
                        precision = len(str(step_size).rstrip('0').split('.')[-1])
                        quantity = round(quantity, precision)

                    # Execute REAL market sell order
                    cprint(f"   [BINANCE] Executing LIVE market SELL: {quantity} {symbol} @ ${current_price:.6f}", "cyan")
                    order = self.binance_client.order_market_sell(symbol=symbol, quantity=quantity)

                    return {
                        'success': True,
                        'symbol': symbol,
                        'side': 'SELL',
                        'price': float(order.get('fills', [{}])[0].get('price', current_price)),
                        'quantity': float(order.get('executedQty', quantity)),
                        'size_usd': usd_amount_or_percent,
                        'order_id': order.get('orderId'),
                        'note': 'LIVE order executed on Binance',
                        'raw_order': order
                    }

                except Exception as e:
                    cprint(f"   ❌ Binance LIVE order failed: {str(e)}", "red")
                    return {
                        'success': False,
                        'error': str(e),
                        'symbol': symbol_or_token,
                        'side': 'SELL',
                        'size_usd': usd_amount_or_percent
                    }
            else:
                # Paper trading mode (no API keys)
                current_price = self.binance_api.get_live_price(symbol_or_token)
                return {
                    'success': True,
                    'symbol': symbol_or_token,
                    'side': 'SELL',
                    'price': current_price,
                    'size_usd': usd_amount_or_percent,
                    'note': 'Paper trade - logged to database by flow'
                }
        else:
            # Solana expects percentage (0-100)
            return self.solana.market_sell(symbol_or_token, usd_amount_or_percent)

    def get_position(self, symbol_or_token):
        """
        Get current position for a symbol/token

        Returns:
            Position data in normalized format
        """
        if self.exchange.lower() == 'hyperliquid':
            positions, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, is_long = \
                self.hl.get_position(symbol_or_token, self.account)

            # Normalize to common format
            if im_in_pos:
                return {
                    'has_position': True,
                    'size': float(pos_size),
                    'symbol': pos_sym,
                    'entry_price': entry_px,
                    'pnl_percent': pnl_perc,
                    'is_long': is_long,
                    'raw_data': positions
                }
            else:
                return {
                    'has_position': False,
                    'size': 0,
                    'symbol': symbol_or_token,
                    'entry_price': 0,
                    'pnl_percent': 0,
                    'is_long': True,
                    'raw_data': positions
                }

        elif self.exchange.lower() == 'binance':
            # For Binance, positions tracked in TradingDatabase (not paper trader)
            # This is a placeholder - actual position tracking in IntelligentPositionManager
            return {
                'has_position': False,
                'size': 0,
                'symbol': symbol_or_token,
                'entry_price': 0,
                'pnl_percent': 0,
                'is_long': True,
                'raw_data': None,
                'note': 'Position tracking via TradingDatabase'
            }

        else:
            # Get Solana position
            try:
                position_data = self.solana.get_position(symbol_or_token)

                # Normalize Solana position data
                if position_data and position_data.get('amount', 0) > 0:
                    return {
                        'has_position': True,
                        'size': position_data.get('amount', 0),
                        'symbol': symbol_or_token,
                        'entry_price': position_data.get('entry_price', 0),
                        'pnl_percent': position_data.get('pnl_percent', 0),
                        'is_long': True,  # Solana is spot only
                        'raw_data': position_data
                    }
                else:
                    return {
                        'has_position': False,
                        'size': 0,
                        'symbol': symbol_or_token,
                        'entry_price': 0,
                        'pnl_percent': 0,
                        'is_long': True,
                        'raw_data': None
                    }
            except:
                return {
                    'has_position': False,
                    'size': 0,
                    'symbol': symbol_or_token,
                    'entry_price': 0,
                    'pnl_percent': 0,
                    'is_long': True,
                    'raw_data': None
                }

    def get_token_balance_usd(self, symbol_or_token):
        """
        Get USD value of token balance

        Returns:
            USD value of position
        """
        if self.exchange.lower() == 'hyperliquid':
            position = self.get_position(symbol_or_token)
            if position['has_position']:
                # Get current price
                price = self.hl.get_current_price(symbol_or_token)
                return abs(position['size']) * price
            return 0
        else:
            return self.solana.get_token_balance_usd(symbol_or_token)

    def close_position(self, symbol_or_token):
        """
        Close an open position

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)

        Returns:
            Close order result
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.kill_switch(symbol_or_token, self.account)
        else:
            # Use chunk_kill for Solana
            from src.config import max_usd_order_size, slippage
            return self.solana.chunk_kill(symbol_or_token, max_usd_order_size, slippage)

    def ai_entry(self, symbol_or_token, usd_amount):
        """
        AI-assisted entry (wrapper for market_buy with additional logic)

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)
            usd_amount: USD amount to enter
        """
        if self.exchange.lower() == 'hyperliquid':
            # For HyperLiquid, use market_buy directly
            return self.market_buy(symbol_or_token, usd_amount)
        else:
            # For Solana, use the ai_entry function
            return self.solana.ai_entry(symbol_or_token, usd_amount)

    def chunk_kill(self, symbol_or_token, max_order_size=None, slippage=None):
        """
        Close position in chunks (primarily for Solana, but works for both)

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)
            max_order_size: Maximum order size per chunk
            slippage: Slippage tolerance
        """
        if self.exchange.lower() == 'hyperliquid':
            # HyperLiquid doesn't need chunking, just close the position
            return self.hl.kill_switch(symbol_or_token, self.account)
        else:
            from src.config import max_usd_order_size, slippage as default_slippage
            max_order_size = max_order_size or max_usd_order_size
            slippage = slippage or default_slippage
            return self.solana.chunk_kill(symbol_or_token, max_order_size, slippage)

    def get_current_price(self, symbol_or_token):
        """
        Get current price of symbol/token

        Returns:
            Current price in USD
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.get_current_price(symbol_or_token)
        else:
            return self.solana.token_price(symbol_or_token)

    def get_account_value(self):
        """
        Get total account value

        Returns:
            Total account value in USD
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.get_account_value(self.account)
        else:
            # For Solana, sum up all token values
            from src.config import address
            positions = self.solana.fetch_wallet_holdings_og(address)
            total_value = 0
            if positions is not None and not positions.empty:
                for _, row in positions.iterrows():
                    total_value += row.get('value_usd', 0)
            return total_value

    def get_balance(self, asset: str = 'USDT'):
        """
        Get available balance for trading

        Args:
            asset: Asset to query (default 'USDT'). For Binance, can be 'USDT', 'BTC', 'ETH', etc.

        Returns:
            Available balance (USDT in USD, other assets in native units)
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.get_balance(self.account)
        elif self.exchange.lower() == 'binance':
            # REAL Binance balance if client is initialized (LIVE mode)
            if self.binance_client:
                try:
                    # Get account info with proper recvWindow
                    recv_window = getattr(self, 'recv_window', 60000)  # Use stored or default to 60s
                    account = self.binance_client.get_account(recvWindow=recv_window)

                    # Find balance for requested asset
                    for balance in account['balances']:
                        if balance['asset'] == asset:
                            return float(balance['free'])

                    # Asset not found
                    return 0.0

                except Exception as e:
                    cprint(f"   ❌ Failed to get Binance balance for {asset}: {str(e)}", "red")
                    return 0.0
            else:
                # Paper trading mode - return placeholder
                if asset == 'USDT':
                    return 10000.0  # Default paper trading balance
                else:
                    return 0.0  # No other assets in paper mode
        else:
            from src.config import USDC_ADDRESS
            return self.solana.get_token_balance_usd(USDC_ADDRESS)

    def place_oco_order(self, symbol, side, tp1_quantity, sl_quantity, stop_price, stop_limit_price, take_profit_price):
        """
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        DEPRECATED - DO NOT USE
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        This method is DEPRECATED as of 2024-11.
        Use place_bracket_orders_spot() instead.

        Reason: Binance OCO cannot have asymmetric quantities. Both legs must have
        the same quantity, which breaks our 40/30/30 TP ladder strategy.

        The bracket order system places separate SL + TP orders with proper
        lifecycle management (TP fills -> replace SL, SL fills -> cancel TPs).

        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        """
        raise DeprecationWarning(
            "place_oco_order() is DEPRECATED. Use place_bracket_orders_spot() instead. "
            "OCO cannot have asymmetric quantities - use separate SL + TP orders."
        )
        if self.exchange.lower() == 'binance' and self.binance_client:
            try:
                # Ensure symbol has USDT suffix
                if not symbol.endswith('USDT'):
                    symbol = f"{symbol}USDT"

                # For BUY positions: OCO sells at TP (limit) or SL (stop-limit)
                # For SELL positions: OCO buys back at TP (limit) or SL (stop-limit)
                oco_side = 'SELL' if side == 'BUY' else 'BUY'

                # Get symbol info for proper precision
                symbol_info = self.binance_client.get_symbol_info(symbol)
                price_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')
                lot_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')

                price_precision = price_filter['tickSize'].find('1') - 1
                qty_precision = lot_filter['stepSize'].find('1') - 1

                # Round prices and quantities to proper precision
                tp1_quantity = round(tp1_quantity, qty_precision)
                sl_quantity = round(sl_quantity, qty_precision)
                stop_price = round(stop_price, price_precision)
                stop_limit_price = round(stop_limit_price, price_precision)
                take_profit_price = round(take_profit_price, price_precision)

                cprint(f"   [BINANCE] Placing OCO order: {oco_side} {symbol}", "cyan")
                cprint(f"   OCO Quantity: {sl_quantity} (100% position for both legs)", "cyan")
                cprint(f"   Stop Loss: ${stop_price} | Take Profit: ${take_profit_price}", "cyan")

                # Place OCO order using NEW python-binance API format
                # The NEW API requires aboveType/belowType parameters
                # We use FULL quantity for both legs for simplicity
                recv_window = getattr(self, 'recv_window', 60000)

                # Use FULL position quantity for both legs
                oco_quantity = sl_quantity  # 100% position

                # NEW API FORMAT: Use above/below parameters
                # For SELL OCO (exit after BUY):
                #   - aboveType: LIMIT_MAKER (TP above current price)
                #   - belowType: STOP_LOSS_LIMIT (SL below current price)
                if oco_side == 'SELL':
                    order = self.binance_client.create_oco_order(
                        symbol=symbol,
                        side=oco_side,  # CRITICAL FIX: Add mandatory 'side' parameter
                        quantity=str(oco_quantity),

                        # Take Profit (above current price)
                        aboveType='LIMIT_MAKER',
                        abovePrice=str(take_profit_price),

                        # Stop Loss (below current price)
                        belowType='STOP_LOSS_LIMIT',
                        belowStopPrice=str(stop_price),
                        belowPrice=str(stop_limit_price),
                        belowTimeInForce='GTC',

                        # Add recvWindow for timestamp tolerance
                        recvWindow=recv_window
                    )
                else:
                    # For BUY OCO (exit after SELL short):
                    #   - aboveType: STOP_LOSS_LIMIT (SL above current price)
                    #   - belowType: LIMIT_MAKER (TP below current price)
                    order = self.binance_client.create_oco_order(
                        symbol=symbol,
                        side=oco_side,  # CRITICAL FIX: Add mandatory 'side' parameter
                        quantity=str(oco_quantity),

                        # Stop Loss (above current price for short cover)
                        aboveType='STOP_LOSS_LIMIT',
                        aboveStopPrice=str(stop_price),
                        abovePrice=str(stop_limit_price),
                        aboveTimeInForce='GTC',

                        # Take Profit (below current price for short cover)
                        belowType='LIMIT_MAKER',
                        belowPrice=str(take_profit_price),

                        # Add recvWindow for timestamp tolerance
                        recvWindow=recv_window
                    )

                cprint(f"   [OK] OCO order placed - Order List ID: {order.get('orderListId')}", "green")
                return {'success': True, 'order': order, 'orderListId': order.get('orderListId')}

            except Exception as e:
                cprint(f"   [ERROR] Failed to place OCO order: {str(e)}", "red")
                return {'success': False, 'error': str(e)}
        else:
            cprint(f"   [WARN] OCO orders not supported for {self.exchange}", "yellow")
            return {'success': False, 'error': 'OCO not supported'}

    def place_limit_order(self, symbol, side, quantity, price):
        """
        Place limit order on Binance

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Amount to trade
            price: Limit price

        Returns:
            Order response from Binance
        """
        if self.exchange.lower() == 'binance' and self.binance_client:
            try:
                # Ensure symbol has USDT suffix
                symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"

                # Get symbol info for precision
                info = self.binance_client.get_symbol_info(symbol)
                price_precision = None
                qty_precision = None
                for filter in info['filters']:
                    if filter['filterType'] == 'PRICE_FILTER':
                        tick_size = float(filter['tickSize'])
                        price_precision = len(str(tick_size).rstrip('0').split('.')[-1])
                    if filter['filterType'] == 'LOT_SIZE':
                        step_size = float(filter['stepSize'])
                        qty_precision = len(str(step_size).rstrip('0').split('.')[-1])

                # Round to proper precision
                price = round(price, price_precision) if price_precision else price
                quantity = round(quantity, qty_precision) if qty_precision else quantity

                cprint(f"   [BINANCE] Placing LIMIT order: {side} {quantity} {symbol} @ ${price:.6f}", "cyan")

                # Create order with proper recvWindow
                recv_window = getattr(self, 'recv_window', 60000)
                order = self.binance_client.create_order(
                    symbol=symbol,
                    side=side,
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=quantity,
                    price=str(price),
                    recvWindow=recv_window
                )

                cprint(f"   [OK] Limit order placed - Order ID: {order.get('orderId')}", "green")
                return order

            except Exception as e:
                cprint(f"   [ERROR] Failed to place limit order: {str(e)}", "red")
                return {'success': False, 'error': str(e)}
        else:
            cprint(f"   [WARN] Limit orders not supported for {self.exchange}", "yellow")
            return {'success': False, 'error': 'Limit orders not supported'}

    def place_stop_loss_order(self, symbol, side, quantity, stop_price, limit_price):
        """
        Place STOP_LOSS_LIMIT order on Binance with COMPREHENSIVE validation

        CRITICAL FIXES:
        1. Verify base asset balance (can't SELL what you don't have)
        2. Check USDT margin requirement (Binance platform requirement)
        3. Use ACTUAL account balance, not calculated quantity
        4. Proper quantity precision and validation

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT' or 'BTC')
            side: 'BUY' or 'SELL' (exit side, opposite of position)
            quantity: Requested quantity to exit
            stop_price: Stop trigger price
            limit_price: Stop limit price (slightly worse than trigger for guaranteed fill)

        Returns:
            {"success": True/False, "orderId": ..., "order": {...}, "error": "..."}
        """
        if self.exchange.lower() != 'binance' or not self.binance_client:
            cprint(f"   [SL] ⚠️  Binance client not available", "yellow")
            return {"success": False, "error": "Binance client not available"}

        try:
            import math  # PERMANENT FIX: Import math BEFORE using it

            # Normalize symbol
            symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"
            base_asset = symbol.replace('USDT', '')  # BTC, ETH, SOL, etc.

            # CRITICAL FIX #1: Verify we actually HAVE the base asset
            # Can't place SELL order without the asset in account
            try:
                actual_balance = self.get_balance(base_asset)

                if actual_balance <= 0:
                    error_msg = f"No {base_asset} balance found in account (can't place SELL SL)"
                    cprint(f"   [SL] ❌ {error_msg}", "red")
                    cprint(f"   [SL] 💡 Market buy may have failed or not settled yet", "yellow")
                    return {"success": False, "error": error_msg}

                # Use ACTUAL balance if less than requested (safety)
                if actual_balance < quantity:
                    cprint(f"   [SL] ⚠️  Requested qty {quantity:.8f} > available {actual_balance:.8f}", "yellow")
                    cprint(f"   [SL] 🔧 Using actual balance instead", "cyan")
                    quantity = actual_balance

                cprint(f"   [SL] ✅ {base_asset} balance verified: {actual_balance:.8f} (using {quantity:.8f})", "green")

            except Exception as base_check_err:
                error_msg = f"Failed to verify {base_asset} balance: {base_check_err}"
                cprint(f"   [SL] ❌ {error_msg}", "red")
                return {"success": False, "error": error_msg}

            # CRITICAL FIX #2: Check USDT margin requirement
            # Binance requires minimum USDT balance for STOP_LOSS_LIMIT orders
            # even for SELL orders (platform margin/collateral requirement)
            try:
                usdt_balance = self.get_balance('USDT')
                MIN_USDT_MARGIN_PER_SL = 50.0  # Reduced from $300 to $50 (more realistic)

                if usdt_balance < MIN_USDT_MARGIN_PER_SL:
                    error_msg = f"Insufficient USDT margin (${usdt_balance:.2f} < ${MIN_USDT_MARGIN_PER_SL:.2f} required)"
                    cprint(f"   [SL] ⚠️  {error_msg}", "yellow")
                    cprint(f"   [SL] 💡 Binance requires USDT margin for STOP_LOSS_LIMIT orders", "cyan")
                    return {"success": False, "error": error_msg}
                else:
                    cprint(f"   [SL] ✅ USDT margin check passed: ${usdt_balance:.2f}", "green")
            except Exception as margin_check_err:
                cprint(f"   [SL] ⚠️  Could not verify USDT margin: {margin_check_err}", "yellow")
                # Continue anyway - margin check is safety measure

            # Get symbol filters for precision (symbol already normalized above)
            try:
                exchange_info = self.binance_client.get_symbol_info(symbol)
                filters = {f['filterType']: f for f in exchange_info.get('filters', [])}

                lot_filter = filters.get('LOT_SIZE', {})
                price_filter = filters.get('PRICE_FILTER', {})

                step_size = float(lot_filter.get('stepSize', '0.00000001'))
                min_qty = float(lot_filter.get('minQty', '0.00000001'))
                tick_size = float(price_filter.get('tickSize', '0.01'))

                # Calculate precision
                qty_precision = max(0, -int(round(math.log10(step_size)))) if step_size > 0 else 8
                price_precision = max(0, -int(round(math.log10(tick_size)))) if tick_size > 0 else 2

                # Round values
                quantity_rounded = math.floor(quantity / step_size) * step_size
                quantity_rounded = max(quantity_rounded, min_qty)
                stop_price_rounded = round(stop_price / tick_size) * tick_size
                limit_price_rounded = round(limit_price / tick_size) * tick_size

                # Format for API (no scientific notation)
                qty_str = f"{quantity_rounded:.{qty_precision}f}"
                stop_str = f"{stop_price_rounded:.{price_precision}f}"
                limit_str = f"{limit_price_rounded:.{price_precision}f}"

            except Exception as filter_err:
                cprint(f"   [SL] ⚠️  Could not get filters: {filter_err}, using raw values", "yellow")
                qty_str = str(quantity)
                stop_str = str(stop_price)
                limit_str = str(limit_price)

            recv_window = getattr(self, 'recv_window', 60000)

            cprint(f"   [SL] Placing STOP_LOSS_LIMIT: {side} {qty_str} {symbol} @ stop={stop_str}, limit={limit_str}", "cyan")

            order = self.binance_client.create_order(
                symbol=symbol,
                side=side,
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=qty_str,
                stopPrice=stop_str,
                price=limit_str,
                recvWindow=recv_window
            )

            cprint(f"   [SL] ✅ Order placed - ID: {order.get('orderId')}", "green")

            return {
                "success": True,
                "order": order,
                "orderId": order.get('orderId'),
                "type": 'STOP_LOSS_LIMIT',
                "origQty": float(order.get('origQty', quantity)),
                "stopPrice": float(order.get('stopPrice', stop_price)),
                "price": float(order.get('price', limit_price))
            }

        except Exception as e:
            cprint(f"   [SL] ❌ Failed: {e}", "red")
            return {"success": False, "error": str(e)}

    def get_all_positions(self):
        """
        Get all open positions

        Returns:
            List of position dictionaries
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.get_all_positions(self.account)
        else:
            from src.config import address, EXCLUDED_TOKENS
            positions = self.solana.fetch_wallet_holdings_og(address)

            all_positions = []
            if positions is not None and not positions.empty:
                for _, row in positions.iterrows():
                    token = row.get('token_address', '')
                    if token not in EXCLUDED_TOKENS and row.get('value_usd', 0) > 0:
                        all_positions.append({
                            'symbol': token,
                            'size': row.get('amount', 0),
                            'entry_price': row.get('price', 0),
                            'pnl_percent': 0,  # Solana doesn't track this directly
                            'is_long': True,  # Solana is spot only
                            'value_usd': row.get('value_usd', 0)
                        })
            return all_positions

    def set_leverage(self, symbol, leverage):
        """
        Set leverage for a symbol (HyperLiquid only)

        Args:
            symbol: Trading symbol
            leverage: Leverage amount (1-50)
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.set_leverage(symbol, leverage, self.account)
        else:
            cprint(f"⚠️ Leverage not applicable for Solana spot trading", "yellow")
            return None

    def get_data(self, symbol_or_token, days_back, timeframe):
        """
        Get OHLCV data for analysis

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)
            days_back: Number of days of historical data
            timeframe: Timeframe (1m, 5m, 15m, 1H, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        if self.exchange.lower() == 'hyperliquid':
            # HyperLiquid doesn't have get_data in our implementation yet
            # For now, return empty dataframe
            cprint(f"⚠️ OHLCV data not yet implemented for HyperLiquid", "yellow")
            return pd.DataFrame()
        else:
            return self.solana.get_data(symbol_or_token, days_back, timeframe)

    def fetch_wallet_holdings(self, wallet_address=None):
        """
        Fetch all wallet holdings

        Args:
            wallet_address: Optional wallet address (for Solana)

        Returns:
            DataFrame with holdings
        """
        if self.exchange.lower() == 'hyperliquid':
            # Convert HyperLiquid positions to DataFrame format
            positions = self.get_all_positions()
            if positions:
                df = pd.DataFrame(positions)
                return df
            return pd.DataFrame()
        else:
            from src.config import address
            wallet_address = wallet_address or address
            return self.solana.fetch_wallet_holdings_og(wallet_address)

    def get_symbol_filters(self, symbol: str) -> dict:
        """
        Get all filters for a symbol from Binance exchange info

        Returns dict with: LOT_SIZE, MIN_NOTIONAL, PRICE_FILTER, etc.
        """
        if self.exchange.lower() != 'binance':
            return {}

        try:
            info = self.binance_client.get_symbol_info(symbol)
            filters = {}

            for f in info['filters']:
                filter_type = f['filterType']
                filters[filter_type] = f

            return filters
        except Exception as e:
            cprint(f"   ⚠️  Failed to get filters for {symbol}: {e}", "yellow")
            return {}

    def round_quantity_to_lot_size(self, quantity: float, symbol: str) -> float:
        """
        Round quantity to Binance LOT_SIZE requirement

        Args:
            quantity: Raw quantity (e.g., 0.549084)
            symbol: Trading pair (e.g., 'SOLUSDT')

        Returns:
            Rounded quantity that meets LOT_SIZE filter (e.g., 0.54)
            Returns 0.0 if quantity is below minimum
        """
        import math

        if self.exchange.lower() != 'binance':
            return quantity

        filters = self.get_symbol_filters(symbol)

        if 'LOT_SIZE' not in filters:
            cprint(f"   ⚠️  No LOT_SIZE filter for {symbol}, using raw quantity", "yellow")
            return quantity

        lot_filter = filters['LOT_SIZE']
        step_size = float(lot_filter['stepSize'])
        min_qty = float(lot_filter['minQty'])
        max_qty = float(lot_filter['maxQty'])

        # Round down to nearest step_size
        rounded = math.floor(quantity / step_size) * step_size

        # Ensure within min/max bounds
        if rounded < min_qty:
            cprint(f"   ⚠️  Quantity {rounded:.8f} below min {min_qty} for {symbol}", "yellow")
            return 0.0  # Signal that quantity is too small

        if rounded > max_qty:
            cprint(f"   ⚠️  Quantity {rounded:.8f} above max {max_qty} for {symbol}", "yellow")
            rounded = max_qty

        return rounded

    def format_quantity_for_binance(self, quantity: float, symbol: str) -> str:
        """
        Format quantity for Binance API:
        1. Round to LOT_SIZE
        2. Format as decimal string (no scientific notation)
        3. Remove trailing zeros

        Args:
            quantity: Raw quantity
            symbol: Trading pair

        Returns:
            Formatted string ready for Binance API (e.g., "0.54" or "0.0000465")
            Returns "0" if quantity is too small
        """
        if self.exchange.lower() != 'binance':
            return str(quantity)

        # Step 1: Round to LOT_SIZE
        rounded = self.round_quantity_to_lot_size(quantity, symbol)

        if rounded == 0.0:
            return "0"

        # Step 2: Format to string with 8 decimals (no scientific notation)
        formatted = f"{rounded:.8f}"

        # Step 3: Remove trailing zeros and decimal point if needed
        formatted = formatted.rstrip('0').rstrip('.')

        return formatted

    def place_bracket_orders_spot(
        self,
        symbol: str,
        entry_side: str,
        total_qty: float,
        stop_price: float,
        stop_limit_price: float,
        take_profits: list  # List of (price, qty) tuples
    ) -> dict:
        """
        Place bracket orders for SPOT trading: SL (100%) + TP ladder (partials)

        REPLACES OCO with separate orders for better profit profile:
        - Stop Loss: 100% of position (full protection)
        - Take Profits: Partial allocations (e.g., 40/30/30)

        Lifecycle:
        - If SL hits: cancel all TP orders
        - If any TP fills: replace SL with reduced quantity
        - If all TPs fill: cancel SL

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT' or 'BTC')
            entry_side: 'BUY' or 'SELL' (the entry side)
            total_qty: Total position quantity
            stop_price: Stop loss trigger price
            stop_limit_price: Stop loss limit price (slightly worse than trigger)
            take_profits: List of (price, qty) tuples for TP ladder

        Returns:
            {
                "success": True/False,
                "sl_order": {"orderId": ..., "type": ..., "origQty": ..., "stopPrice": ..., "price": ...},
                "tp_orders": [{"orderId": ..., "price": ..., "origQty": ...}, ...],
                "errors": []
            }
        """
        result = {
            "success": False,
            "sl_order": None,
            "tp_orders": [],
            "errors": []
        }

        if self.exchange.lower() != 'binance':
            result["errors"].append(f"Bracket orders only supported for Binance, not {self.exchange}")
            return result

        if not self.binance_client:
            result["errors"].append("Binance client not initialized (PAPER mode)")
            return result

        try:
            # Normalize symbol to XXXUSDT format
            symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"

            # Determine exit side (opposite of entry)
            exit_side = 'SELL' if entry_side.upper() == 'BUY' else 'BUY'

            # Get symbol filters for precision
            filters = self.get_symbol_filters(symbol)
            if not filters:
                result["errors"].append(f"Could not get filters for {symbol}")
                return result

            # Extract precision from filters
            lot_filter = filters.get('LOT_SIZE', {})
            price_filter = filters.get('PRICE_FILTER', {})
            notional_filter = filters.get('NOTIONAL', filters.get('MIN_NOTIONAL', {}))

            step_size = float(lot_filter.get('stepSize', '0.00000001'))
            min_qty = float(lot_filter.get('minQty', '0.00000001'))
            tick_size = float(price_filter.get('tickSize', '0.01'))
            min_notional = float(notional_filter.get('minNotional', '5.0'))

            # Calculate precision from step/tick size
            qty_precision = self._get_precision_from_step(step_size)
            price_precision = self._get_precision_from_step(tick_size)

            cprint(f"   [BRACKET] Symbol: {symbol}, Exit Side: {exit_side}", "cyan")
            cprint(f"   [BRACKET] Total Qty: {total_qty}, Step Size: {step_size}, Tick Size: {tick_size}", "cyan")

            # Round total quantity
            total_qty_rounded = self._round_to_step(total_qty, step_size, min_qty)
            if total_qty_rounded == 0:
                result["errors"].append(f"Total quantity {total_qty} rounds to 0 (min: {min_qty})")
                return result

            # Round prices
            stop_price_rounded = self._round_price(stop_price, tick_size)
            stop_limit_price_rounded = self._round_price(stop_limit_price, tick_size)

            recv_window = getattr(self, 'recv_window', 60000)

            # ============================================================
            # STEP 1: Place STOP_LOSS_LIMIT for 100% of position
            # ============================================================
            cprint(f"   [BRACKET] Placing SL: {exit_side} {total_qty_rounded} @ stop={stop_price_rounded}, limit={stop_limit_price_rounded}", "yellow")

            try:
                sl_order = self.binance_client.create_order(
                    symbol=symbol,
                    side=exit_side,
                    type='STOP_LOSS_LIMIT',
                    timeInForce='GTC',
                    quantity=self._format_qty(total_qty_rounded, qty_precision),
                    stopPrice=self._format_price(stop_price_rounded, price_precision),
                    price=self._format_price(stop_limit_price_rounded, price_precision),
                    recvWindow=recv_window
                )

                result["sl_order"] = {
                    "orderId": sl_order.get('orderId'),
                    "type": 'STOP_LOSS_LIMIT',
                    "origQty": float(sl_order.get('origQty', total_qty_rounded)),
                    "stopPrice": float(sl_order.get('stopPrice', stop_price_rounded)),
                    "price": float(sl_order.get('price', stop_limit_price_rounded)),
                    "status": sl_order.get('status', 'NEW')
                }
                cprint(f"   [BRACKET] ✅ SL placed - OrderId: {result['sl_order']['orderId']}", "green")

            except Exception as sl_error:
                result["errors"].append(f"Failed to place SL order: {str(sl_error)}")
                cprint(f"   [BRACKET] ❌ SL failed: {sl_error}", "red")
                return result

            # ============================================================
            # STEP 2: Place TP limit orders for each allocation
            # ============================================================
            for i, (tp_price, tp_qty) in enumerate(take_profits, 1):
                # Round TP price and quantity
                tp_price_rounded = self._round_price(tp_price, tick_size)
                tp_qty_rounded = self._round_to_step(tp_qty, step_size, min_qty)

                # Check if quantity is valid
                if tp_qty_rounded == 0:
                    result["errors"].append(f"TP{i} quantity {tp_qty} rounds to 0 (min: {min_qty})")
                    cprint(f"   [BRACKET] ⚠️ TP{i} skipped - qty too small", "yellow")
                    continue

                # Check minimum notional
                notional = tp_qty_rounded * tp_price_rounded
                if notional < min_notional:
                    result["errors"].append(f"TP{i} notional ${notional:.2f} < min ${min_notional}")
                    cprint(f"   [BRACKET] ⚠️ TP{i} skipped - notional too small", "yellow")
                    continue

                cprint(f"   [BRACKET] Placing TP{i}: {exit_side} {tp_qty_rounded} @ {tp_price_rounded}", "cyan")

                try:
                    tp_order = self.binance_client.create_order(
                        symbol=symbol,
                        side=exit_side,
                        type='LIMIT',
                        timeInForce='GTC',
                        quantity=self._format_qty(tp_qty_rounded, qty_precision),
                        price=self._format_price(tp_price_rounded, price_precision),
                        recvWindow=recv_window
                    )

                    result["tp_orders"].append({
                        "orderId": tp_order.get('orderId'),
                        "level": i,
                        "price": float(tp_order.get('price', tp_price_rounded)),
                        "origQty": float(tp_order.get('origQty', tp_qty_rounded)),
                        "status": tp_order.get('status', 'NEW')
                    })
                    cprint(f"   [BRACKET] ✅ TP{i} placed - OrderId: {tp_order.get('orderId')}", "green")

                except Exception as tp_error:
                    result["errors"].append(f"Failed to place TP{i}: {str(tp_error)}")
                    cprint(f"   [BRACKET] ⚠️ TP{i} failed: {tp_error}", "yellow")

            # Success if we have SL and at least one TP
            if result["sl_order"] and len(result["tp_orders"]) > 0:
                result["success"] = True
                cprint(f"   [BRACKET] ✅ Bracket complete: 1 SL + {len(result['tp_orders'])} TPs", "green")
            elif result["sl_order"]:
                result["success"] = True  # SL alone is acceptable (TPs optional)
                cprint(f"   [BRACKET] ⚠️ Bracket partial: SL placed, 0 TPs (below notional)", "yellow")

            return result

        except Exception as e:
            result["errors"].append(f"Bracket order exception: {str(e)}")
            cprint(f"   [BRACKET] ❌ Exception: {e}", "red")
            return result

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """
        Cancel a specific order by orderId

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            order_id: Binance order ID

        Returns:
            {"success": True/False, "order": {...}, "error": "..."}
        """
        if self.exchange.lower() != 'binance' or not self.binance_client:
            return {"success": False, "error": "Binance client not available"}

        try:
            symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"
            recv_window = getattr(self, 'recv_window', 60000)

            result = self.binance_client.cancel_order(
                symbol=symbol,
                orderId=order_id,
                recvWindow=recv_window
            )

            cprint(f"   [CANCEL] ✅ Order {order_id} cancelled", "green")
            return {"success": True, "order": result}

        except Exception as e:
            error_msg = str(e)
            # "Unknown order sent" means order already filled/cancelled
            if "Unknown order" in error_msg or "-2011" in error_msg:
                cprint(f"   [CANCEL] Order {order_id} already filled/cancelled", "yellow")
                return {"success": True, "order": None, "note": "Already filled/cancelled"}

            cprint(f"   [CANCEL] ❌ Failed to cancel {order_id}: {e}", "red")
            return {"success": False, "error": error_msg}

    def get_order_status(self, symbol: str, order_id: int) -> dict:
        """
        Get status of a specific order

        Args:
            symbol: Trading pair
            order_id: Binance order ID

        Returns:
            Order info dict or error
        """
        if self.exchange.lower() != 'binance' or not self.binance_client:
            return {"success": False, "error": "Binance client not available"}

        try:
            symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"
            recv_window = getattr(self, 'recv_window', 60000)

            order = self.binance_client.get_order(
                symbol=symbol,
                orderId=order_id,
                recvWindow=recv_window
            )

            return {
                "success": True,
                "orderId": order.get('orderId'),
                "status": order.get('status'),  # NEW, FILLED, CANCELED, PARTIALLY_FILLED
                "executedQty": float(order.get('executedQty', 0)),
                "origQty": float(order.get('origQty', 0)),
                "price": float(order.get('price', 0)),
                "type": order.get('type'),
                "side": order.get('side'),
                "raw": order
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def replace_stop_loss(
        self,
        symbol: str,
        old_order_id: int,
        new_qty: float,
        stop_price: float,
        stop_limit_price: float,
        exit_side: str
    ) -> dict:
        """
        Replace stop loss order with new quantity (after TP fill)

        Atomic operation: cancel old SL, place new SL
        If new SL fails, we have no protection (critical error)

        Args:
            symbol: Trading pair
            old_order_id: Current SL order ID to cancel
            new_qty: New remaining quantity
            stop_price: Stop trigger price
            stop_limit_price: Stop limit price
            exit_side: 'BUY' or 'SELL'

        Returns:
            {"success": True/False, "new_order": {...}, "error": "..."}
        """
        result = {"success": False, "new_order": None, "error": None}

        if self.exchange.lower() != 'binance' or not self.binance_client:
            result["error"] = "Binance client not available"
            return result

        try:
            symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"

            # Get filters
            filters = self.get_symbol_filters(symbol)
            lot_filter = filters.get('LOT_SIZE', {})
            price_filter = filters.get('PRICE_FILTER', {})

            step_size = float(lot_filter.get('stepSize', '0.00000001'))
            min_qty = float(lot_filter.get('minQty', '0.00000001'))
            tick_size = float(price_filter.get('tickSize', '0.01'))

            qty_precision = self._get_precision_from_step(step_size)
            price_precision = self._get_precision_from_step(tick_size)

            # Round values
            new_qty_rounded = self._round_to_step(new_qty, step_size, min_qty)
            stop_price_rounded = self._round_price(stop_price, tick_size)
            stop_limit_price_rounded = self._round_price(stop_limit_price, tick_size)

            # Check if remaining quantity is valid
            if new_qty_rounded == 0:
                cprint(f"   [REPLACE_SL] No remaining qty to protect ({new_qty} rounds to 0)", "yellow")
                # Cancel old SL anyway
                self.cancel_order(symbol, old_order_id)
                result["success"] = True
                result["note"] = "No SL needed - position fully exited"
                return result

            recv_window = getattr(self, 'recv_window', 60000)

            # Step 1: Cancel old SL
            cprint(f"   [REPLACE_SL] Cancelling old SL {old_order_id}...", "cyan")
            cancel_result = self.cancel_order(symbol, old_order_id)

            if not cancel_result.get("success"):
                # If cancel failed but order was already gone, continue
                if "Already filled/cancelled" not in cancel_result.get("note", ""):
                    result["error"] = f"Failed to cancel old SL: {cancel_result.get('error')}"
                    return result

            # Step 2: Place new SL with reduced quantity
            cprint(f"   [REPLACE_SL] Placing new SL: {exit_side} {new_qty_rounded} @ {stop_price_rounded}", "cyan")

            new_sl = self.binance_client.create_order(
                symbol=symbol,
                side=exit_side,
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=self._format_qty(new_qty_rounded, qty_precision),
                stopPrice=self._format_price(stop_price_rounded, price_precision),
                price=self._format_price(stop_limit_price_rounded, price_precision),
                recvWindow=recv_window
            )

            result["success"] = True
            result["new_order"] = {
                "orderId": new_sl.get('orderId'),
                "origQty": float(new_sl.get('origQty', new_qty_rounded)),
                "stopPrice": float(new_sl.get('stopPrice', stop_price_rounded)),
                "status": new_sl.get('status', 'NEW')
            }

            cprint(f"   [REPLACE_SL] ✅ New SL placed - OrderId: {result['new_order']['orderId']}", "green")
            return result

        except Exception as e:
            result["error"] = f"Replace SL exception: {str(e)}"
            cprint(f"   [REPLACE_SL] ❌ CRITICAL: {e}", "red")
            return result

    def cancel_all_bracket_orders(self, symbol: str, sl_order_id: int, tp_order_ids: list) -> dict:
        """
        Cancel all bracket orders (SL + all TPs)

        Used when SL fills (cancel remaining TPs) or position manually closed

        Args:
            symbol: Trading pair
            sl_order_id: Stop loss order ID (can be None if already cancelled)
            tp_order_ids: List of TP order IDs

        Returns:
            {"success": True/False, "cancelled": [...], "errors": [...]}
        """
        result = {"success": True, "cancelled": [], "errors": []}

        # Cancel SL if provided
        if sl_order_id:
            sl_result = self.cancel_order(symbol, sl_order_id)
            if sl_result.get("success"):
                result["cancelled"].append({"type": "SL", "orderId": sl_order_id})
            else:
                result["errors"].append(f"SL {sl_order_id}: {sl_result.get('error')}")

        # Cancel all TPs
        for tp_id in tp_order_ids:
            tp_result = self.cancel_order(symbol, tp_id)
            if tp_result.get("success"):
                result["cancelled"].append({"type": "TP", "orderId": tp_id})
            else:
                result["errors"].append(f"TP {tp_id}: {tp_result.get('error')}")

        # Success if we cancelled at least one (or all were already cancelled)
        result["success"] = len(result["cancelled"]) > 0 or len(result["errors"]) == 0

        cprint(f"   [CANCEL_ALL] Cancelled {len(result['cancelled'])} orders, {len(result['errors'])} errors", "cyan")
        return result

    # ============================================================
    # HELPER METHODS FOR PRECISION HANDLING
    # ============================================================

    def _get_precision_from_step(self, step: float) -> int:
        """Get decimal precision from step size (e.g., 0.001 -> 3)"""
        if step >= 1:
            return 0
        step_str = f"{step:.10f}".rstrip('0')
        if '.' in step_str:
            return len(step_str.split('.')[1])
        return 0

    def _round_to_step(self, value: float, step: float, min_val: float) -> float:
        """Round value down to nearest step, respecting minimum"""
        import math
        if step == 0:
            return value
        rounded = math.floor(value / step) * step
        if rounded < min_val:
            return 0.0
        return rounded

    def _round_price(self, price: float, tick_size: float) -> float:
        """Round price to tick size"""
        import math
        if tick_size == 0:
            return price
        return round(price / tick_size) * tick_size

    def _format_qty(self, qty: float, precision: int) -> str:
        """Format quantity with proper precision"""
        formatted = f"{qty:.{precision}f}"
        return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted

    def _format_price(self, price: float, precision: int) -> str:
        """Format price with proper precision"""
        formatted = f"{price:.{precision}f}"
        return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted

    def __str__(self):
        """String representation of the exchange manager"""
        return f"ExchangeManager(exchange={self.exchange})"

    def __repr__(self):
        """Representation of the exchange manager"""
        return self.__str__()


# Convenience function for quick initialization
def create_exchange_manager(exchange=None):
    """
    Create and return an ExchangeManager instance

    Args:
        exchange: Optional exchange override ('solana' or 'hyperliquid')

    Returns:
        ExchangeManager instance
    """
    return ExchangeManager(exchange)