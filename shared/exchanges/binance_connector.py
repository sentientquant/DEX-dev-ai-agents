"""
Binance Exchange Connector
--------------------------
Full SPOT + Futures trading support using CCXT library.
Supports market/limit orders, stop loss, take profit, trailing stops.
Rate limiting: 1,200 weight/minute, 10 orders/second.

User Requirements:
- "Use binance has main exchange and main to get candle, order, market and other you need"
- "integrate all data available and note api is inside .env file"
- "integrate all trade excution supported by binance spot and fetures trading"
"""

import os
from dotenv import load_dotenv
import ccxt
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Load environment variables
load_dotenv()

class BinanceConnector:
    """
    Unified Binance connector supporting SPOT and Futures trading.

    Features:
    - SPOT trading (market, limit orders)
    - Futures trading (market, limit, stop loss, take profit, trailing stop)
    - OHLCV data fetching (candles)
    - Position management
    - Rate limiting via CCXT
    - All order types Binance supports
    """

    def __init__(self, mode: str = 'futures', testnet: bool = False, leverage: int = 1):
        """
        Initialize Binance connector.

        Args:
            mode: 'spot' or 'futures'
            testnet: Use Binance testnet (default: False, use real API)
            leverage: Default leverage for futures (1-125, default: 1)
        """
        self.mode = mode
        self.testnet = testnet
        self.default_leverage = leverage

        # Load API keys from .env
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')

        if not api_key or not api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_SECRET_KEY must be set in .env file")

        # Initialize CCXT exchange
        exchange_params = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,  # Automatic rate limiting
            'options': {
                'defaultType': mode,  # 'spot' or 'futures'
            }
        }

        if testnet:
            exchange_params['options']['defaultType'] = 'future'
            self.exchange = ccxt.binance(exchange_params)
            self.exchange.set_sandbox_mode(True)
        else:
            self.exchange = ccxt.binance(exchange_params)

        print(f"[BINANCE] Initialized {mode.upper()} mode (Testnet: {testnet})")

    # ==================== DATA FETCHING ====================

    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List]:
        """
        Fetch OHLCV candlestick data.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT', 'ETH/USDT')
            timeframe: '1m', '5m', '15m', '1h', '4h', '1d', etc.
            limit: Number of candles to fetch (default: 100, max: 1500)

        Returns:
            List of [timestamp, open, high, low, close, volume]
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            print(f"[BINANCE] Error fetching OHLCV for {symbol}: {e}")
            return []

    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data (price, volume, 24h change).

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            Dict with keys: symbol, bid, ask, last, volume, change, percentage
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            print(f"[BINANCE] Error fetching ticker for {symbol}: {e}")
            return {}

    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get current orderbook (bids/asks).

        Args:
            symbol: Trading pair
            limit: Depth of orderbook (default: 20)

        Returns:
            Dict with keys: bids, asks, timestamp
        """
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return orderbook
        except Exception as e:
            print(f"[BINANCE] Error fetching orderbook for {symbol}: {e}")
            return {}

    def get_balance(self) -> Dict:
        """
        Get account balance.

        Returns:
            Dict with balances for each asset
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            print(f"[BINANCE] Error fetching balance: {e}")
            return {}

    # ==================== SPOT TRADING ====================

    def create_spot_market_order(self, symbol: str, side: str, amount: float) -> Dict:
        """
        Place SPOT market order (immediate execution at current price).

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Amount in base currency (e.g., 0.01 BTC)

        Returns:
            Order result dict
        """
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=amount
            )
            print(f"[BINANCE SPOT] {side.upper()} market order: {amount} {symbol} - Order ID: {order['id']}")
            return order
        except Exception as e:
            print(f"[BINANCE SPOT] Error creating market order: {e}")
            return {}

    def create_spot_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict:
        """
        Place SPOT limit order (execute only at specified price).

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Amount in base currency
            price: Limit price

        Returns:
            Order result dict
        """
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=amount,
                price=price
            )
            print(f"[BINANCE SPOT] {side.upper()} limit order: {amount} {symbol} @ {price} - Order ID: {order['id']}")
            return order
        except Exception as e:
            print(f"[BINANCE SPOT] Error creating limit order: {e}")
            return {}

    # ==================== FUTURES TRADING ====================

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for futures trading.

        Args:
            symbol: Trading pair
            leverage: Leverage multiplier (1-125)

        Returns:
            True if successful
        """
        try:
            self.exchange.set_leverage(leverage, symbol)
            print(f"[BINANCE FUTURES] Set leverage to {leverage}x for {symbol}")
            return True
        except Exception as e:
            print(f"[BINANCE FUTURES] Error setting leverage: {e}")
            return False

    def create_futures_market_order(self, symbol: str, side: str, amount_usd: float, leverage: Optional[int] = None) -> Dict:
        """
        Place FUTURES market order with leverage.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' (long) or 'sell' (short)
            amount_usd: Position size in USD
            leverage: Optional leverage override (uses default if None)

        Returns:
            Order result dict
        """
        try:
            # Set leverage if specified
            if leverage:
                self.set_leverage(symbol, leverage)
            else:
                leverage = self.default_leverage

            # Calculate amount in base currency
            ticker = self.get_ticker(symbol)
            current_price = ticker.get('last', 0)
            if current_price == 0:
                raise ValueError(f"Could not fetch price for {symbol}")

            amount = amount_usd / current_price

            # Place market order
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=amount
            )
            print(f"[BINANCE FUTURES] {side.upper()} market order: ${amount_usd} ({amount} {symbol}) @ {leverage}x - Order ID: {order['id']}")
            return order
        except Exception as e:
            print(f"[BINANCE FUTURES] Error creating market order: {e}")
            return {}

    def create_futures_limit_order(self, symbol: str, side: str, amount: float, price: float, leverage: Optional[int] = None) -> Dict:
        """
        Place FUTURES limit order.

        Args:
            symbol: Trading pair
            side: 'buy' (long) or 'sell' (short)
            amount: Amount in base currency
            price: Limit price
            leverage: Optional leverage override

        Returns:
            Order result dict
        """
        try:
            if leverage:
                self.set_leverage(symbol, leverage)

            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=amount,
                price=price
            )
            print(f"[BINANCE FUTURES] {side.upper()} limit order: {amount} {symbol} @ {price} - Order ID: {order['id']}")
            return order
        except Exception as e:
            print(f"[BINANCE FUTURES] Error creating limit order: {e}")
            return {}

    def create_futures_stop_loss(self, symbol: str, side: str, stop_price: float, quantity: float) -> Dict:
        """
        Place FUTURES stop loss order.

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell' (opposite of position)
            stop_price: Trigger price
            quantity: Amount to close

        Returns:
            Order result dict
        """
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side=side,
                amount=quantity,
                params={'stopPrice': stop_price}
            )
            print(f"[BINANCE FUTURES] Stop loss set @ {stop_price} for {quantity} {symbol}")
            return order
        except Exception as e:
            print(f"[BINANCE FUTURES] Error creating stop loss: {e}")
            return {}

    def create_futures_take_profit(self, symbol: str, side: str, take_profit_price: float, quantity: float) -> Dict:
        """
        Place FUTURES take profit order.

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell' (opposite of position)
            take_profit_price: Trigger price
            quantity: Amount to close

        Returns:
            Order result dict
        """
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='take_profit_market',
                side=side,
                amount=quantity,
                params={'stopPrice': take_profit_price}
            )
            print(f"[BINANCE FUTURES] Take profit set @ {take_profit_price} for {quantity} {symbol}")
            return order
        except Exception as e:
            print(f"[BINANCE FUTURES] Error creating take profit: {e}")
            return {}

    def create_futures_trailing_stop(self, symbol: str, side: str, callback_rate: float, quantity: float) -> Dict:
        """
        Place FUTURES trailing stop order.

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell' (opposite of position)
            callback_rate: Trailing percentage (e.g., 2.0 for 2%)
            quantity: Amount to close

        Returns:
            Order result dict
        """
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='trailing_stop_market',
                side=side,
                amount=quantity,
                params={'callbackRate': callback_rate}
            )
            print(f"[BINANCE FUTURES] Trailing stop set @ {callback_rate}% for {quantity} {symbol}")
            return order
        except Exception as e:
            print(f"[BINANCE FUTURES] Error creating trailing stop: {e}")
            return {}

    # ==================== POSITION MANAGEMENT ====================

    def get_positions(self) -> List[Dict]:
        """
        Get all open futures positions.

        Returns:
            List of position dicts
        """
        try:
            positions = self.exchange.fetch_positions()
            # Filter only positions with non-zero size
            open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
            return open_positions
        except Exception as e:
            print(f"[BINANCE FUTURES] Error fetching positions: {e}")
            return []

    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get specific position for a symbol.

        Args:
            symbol: Trading pair

        Returns:
            Position dict or None
        """
        try:
            positions = self.get_positions()
            for pos in positions:
                if pos['symbol'] == symbol:
                    return pos
            return None
        except Exception as e:
            print(f"[BINANCE FUTURES] Error fetching position for {symbol}: {e}")
            return None

    def close_position(self, symbol: str) -> Dict:
        """
        Close entire position for a symbol (market order).

        Args:
            symbol: Trading pair

        Returns:
            Order result dict
        """
        try:
            position = self.get_position(symbol)
            if not position:
                print(f"[BINANCE FUTURES] No open position for {symbol}")
                return {}

            contracts = abs(float(position.get('contracts', 0)))
            side = 'sell' if float(position.get('contracts', 0)) > 0 else 'buy'

            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=contracts
            )
            print(f"[BINANCE FUTURES] Closed position: {contracts} {symbol}")
            return order
        except Exception as e:
            print(f"[BINANCE FUTURES] Error closing position: {e}")
            return {}

    # ==================== ORDER MANAGEMENT ====================

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open orders.

        Args:
            symbol: Optional filter by symbol

        Returns:
            List of open orders
        """
        try:
            if symbol:
                orders = self.exchange.fetch_open_orders(symbol)
            else:
                orders = self.exchange.fetch_open_orders()
            return orders
        except Exception as e:
            print(f"[BINANCE] Error fetching open orders: {e}")
            return []

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID
            symbol: Trading pair

        Returns:
            True if successful
        """
        try:
            self.exchange.cancel_order(order_id, symbol)
            print(f"[BINANCE] Cancelled order {order_id} for {symbol}")
            return True
        except Exception as e:
            print(f"[BINANCE] Error cancelling order: {e}")
            return False

    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Cancel all open orders.

        Args:
            symbol: Optional filter by symbol

        Returns:
            Number of orders cancelled
        """
        try:
            orders = self.get_open_orders(symbol)
            cancelled = 0
            for order in orders:
                if self.cancel_order(order['id'], order['symbol']):
                    cancelled += 1
            print(f"[BINANCE] Cancelled {cancelled} orders")
            return cancelled
        except Exception as e:
            print(f"[BINANCE] Error cancelling all orders: {e}")
            return 0

    # ==================== UTILITY FUNCTIONS ====================

    def get_markets(self) -> Dict:
        """
        Get all available trading pairs.

        Returns:
            Dict of markets
        """
        try:
            markets = self.exchange.load_markets()
            return markets
        except Exception as e:
            print(f"[BINANCE] Error loading markets: {e}")
            return {}

    def get_trading_fees(self, symbol: str) -> Dict:
        """
        Get trading fees for a symbol.

        Args:
            symbol: Trading pair

        Returns:
            Dict with maker and taker fees
        """
        try:
            fees = self.exchange.fetch_trading_fees([symbol])
            return fees.get(symbol, {})
        except Exception as e:
            print(f"[BINANCE] Error fetching fees for {symbol}: {e}")
            return {}


# ==================== TESTING ====================

if __name__ == "__main__":
    """
    Test Binance connector functionality.
    """
    print("=" * 50)
    print("BINANCE CONNECTOR TEST")
    print("=" * 50)

    # Test SPOT mode
    print("\n[TEST] Initializing SPOT connector...")
    spot = BinanceConnector(mode='spot', testnet=False)

    # Test data fetching
    print("\n[TEST] Fetching BTC/USDT ticker...")
    ticker = spot.get_ticker('BTC/USDT')
    if ticker:
        print(f"BTC/USDT: ${ticker.get('last', 0):,.2f}")

    print("\n[TEST] Fetching BTC/USDT OHLCV (1h, 10 candles)...")
    ohlcv = spot.get_ohlcv('BTC/USDT', '1h', 10)
    if ohlcv:
        print(f"Fetched {len(ohlcv)} candles")
        print(f"Latest close: ${ohlcv[-1][4]:,.2f}")

    print("\n[TEST] Fetching account balance...")
    balance = spot.get_balance()
    if balance and 'USDT' in balance['total']:
        print(f"USDT Balance: ${balance['total']['USDT']:,.2f}")

    # Test FUTURES mode
    print("\n[TEST] Initializing FUTURES connector...")
    futures = BinanceConnector(mode='futures', testnet=False, leverage=5)

    print("\n[TEST] Fetching futures positions...")
    positions = futures.get_positions()
    print(f"Open positions: {len(positions)}")

    print("\n[TEST] Fetching open orders...")
    orders = futures.get_open_orders()
    print(f"Open orders: {len(orders)}")

    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)
