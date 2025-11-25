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
                from binance.client import Client as BinanceClient
                from binance.exceptions import BinanceAPIException

                self.binance_api = BinanceTruthAPI()

                # Initialize REAL Binance client for LIVE trading
                binance_api_key = os.getenv('BINANCE_API_KEY')
                binance_secret_key = os.getenv('BINANCE_SECRET_KEY')

                if binance_api_key and binance_secret_key:
                    # CRITICAL FIX: Proper Binance initialization with timestamp handling
                    # Error: "Timestamp for this request was 1000ms ahead of the server's time"
                    # Solution: Initialize client correctly and pass recvWindow to API calls, not constructor
                    import time

                    # Initialize client WITHOUT recv_window in constructor (it's not valid there!)
                    self.binance_client = BinanceClient(
                        binance_api_key,
                        binance_secret_key,
                        {'timeout': 30}  # ONLY timeout here - no recv_window!
                    )

                    # Calculate time offset with Binance server
                    connected = False
                    for attempt in range(3):
                        try:
                            # Calculate time offset
                            server_time = self.binance_client.get_server_time()
                            local_time = int(time.time() * 1000)
                            time_offset = server_time['serverTime'] - local_time

                            cprint(f"🕐 Time sync: Local={local_time}, Server={server_time['serverTime']}, Offset={time_offset}ms", "cyan")

                            # Test connection with proper recvWindow as API parameter
                            recv_window = 10000 * (attempt + 1)  # 10s, 20s, 30s
                            account_info = self.binance_client.get_account(recvWindow=recv_window)

                            # If we get here, connection successful
                            connected = True
                            self.recv_window = recv_window  # Store for future use
                            cprint(f"✅ Binance connection successful (recvWindow={recv_window}ms)", "green")
                            cprint(f"   Account Type: {account_info.get('accountType', 'SPOT')}", "cyan")
                            break

                        except Exception as e:
                            error_msg = str(e)
                            if "Timestamp" in error_msg or "-1021" in error_msg:
                                cprint(f"⚠️  Attempt {attempt+1} failed: Timestamp issue, retrying with larger recvWindow...", "yellow")
                                # Optionally sync system time on Windows
                                if attempt == 1 and os.name == 'nt':
                                    try:
                                        import subprocess
                                        subprocess.run(['w32tm', '/resync'], capture_output=True, check=False)
                                        cprint("   🔧 Attempted Windows time sync", "cyan")
                                    except:
                                        pass
                            else:
                                cprint(f"❌ Failed to initialize Binance: {e}", "red")
                                raise e

                    if not connected:
                        # Final attempt with maximum recvWindow
                        try:
                            account_info = self.binance_client.get_account(recvWindow=60000)
                            self.recv_window = 60000
                            connected = True
                            cprint(f"⚠️  Using maximum recvWindow (60s) as fallback", "yellow")
                        except Exception as final_err:
                            cprint(f"❌ Failed to initialize Binance after all attempts: {final_err}", "red")
                            raise final_err

                    # Initialize CCXT Binance client for OCO orders (better API support)
                    self.ccxt_binance = ccxt.binance({
                        'apiKey': binance_api_key,
                        'secret': binance_secret_key,
                        'enableRateLimit': True,
                        'options': {
                            'defaultType': 'spot',
                            'recvWindow': 60000,  # CCXT handles this correctly
                            'adjustForTimeDifference': True,  # Auto-adjust timestamps
                        }
                    })
                    cprint(f"✅ Initialized Binance LIVE trading", "green")
                    cprint(f"   API Status: Connected", "cyan")
                    cprint(f"   Account Type: {account_info.get('accountType', 'SPOT')}", "cyan")
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

    def get_balance(self):
        """
        Get available balance for trading

        Returns:
            Available balance in USD
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

                    # Find USDT balance (available for trading)
                    usdt_balance = 0.0
                    for balance in account['balances']:
                        if balance['asset'] == 'USDT':
                            usdt_balance = float(balance['free'])
                            break

                    return usdt_balance
                except Exception as e:
                    cprint(f"   ❌ Failed to get Binance balance: {str(e)}", "red")
                    return 0.0
            else:
                # Paper trading mode - return placeholder
                return 10000.0  # Default paper trading balance
        else:
            from src.config import USDC_ADDRESS
            return self.solana.get_token_balance_usd(USDC_ADDRESS)

    def place_oco_order(self, symbol, side, tp1_quantity, sl_quantity, stop_price, stop_limit_price, take_profit_price):
        """
        Place OCO (One-Cancels-Other) order on Binance with ASYMMETRIC QUANTITIES

        OCO = One limit order (TP) + One stop-limit order (SL), whichever fills first cancels the other

        ASYMMETRIC STRUCTURE:
        - TP1 = 40% (profit target)
        - SL = 100% (full protection - prevents orphaned TP2/TP3 when SL triggers)

        When TP1 hits -> SL cancelled, 60% remains for TP2/TP3
        When SL hits -> TP1 cancelled, 100% closed, TP2/TP3 auto-cancelled by Binance (no qty left)

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL' (entry side)
            tp1_quantity: TP1 quantity (40% of position)
            sl_quantity: SL quantity (100% of position)
            stop_price: Stop loss trigger price
            stop_limit_price: Stop loss limit price (slightly worse than trigger)
            take_profit_price: Take profit limit price

        Returns:
            Order response from Binance
        """
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