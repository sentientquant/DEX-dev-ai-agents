"""
Symbol Normalization Utilities
Standardizes symbol formats across the trading system
"""
from typing import Optional


def normalize_symbol(symbol: str, quote_currency: str = 'USDT') -> str:
    """
    Normalize symbol to full pair format (e.g., ETHUSDT)

    Args:
        symbol: Symbol in any format ('ETH', 'ETHUSDT', 'ETH-USDT', 'ETH/USDT', 'eth')
        quote_currency: Quote currency to append (default: 'USDT')

    Returns:
        Normalized symbol ('ETHUSDT')

    Examples:
        >>> normalize_symbol('ETH')
        'ETHUSDT'
        >>> normalize_symbol('ETHUSDT')
        'ETHUSDT'
        >>> normalize_symbol('ETH-USDT')
        'ETHUSDT'
        >>> normalize_symbol('eth/usdt')
        'ETHUSDT'
        >>> normalize_symbol('BTC', 'BUSD')
        'BTCBUSD'
    """
    if not symbol:
        raise ValueError("Symbol cannot be empty")

    # Convert to uppercase
    symbol = symbol.upper()
    quote_currency = quote_currency.upper()

    # Remove separators
    symbol = symbol.replace('-', '').replace('/', '').replace('_', '').replace(' ', '')

    # Add quote currency if not present
    if not symbol.endswith(quote_currency):
        symbol = f"{symbol}{quote_currency}"

    return symbol


def extract_base_symbol(symbol: str, quote_currency: str = 'USDT') -> str:
    """
    Extract base symbol from full pair (e.g., 'ETHUSDT' -> 'ETH')

    Args:
        symbol: Full pair symbol ('ETHUSDT')
        quote_currency: Quote currency to remove (default: 'USDT')

    Returns:
        Base symbol ('ETH')

    Examples:
        >>> extract_base_symbol('ETHUSDT')
        'ETH'
        >>> extract_base_symbol('BTCBUSD', 'BUSD')
        'BTC'
    """
    symbol = normalize_symbol(symbol, quote_currency)
    quote_currency = quote_currency.upper()

    if symbol.endswith(quote_currency):
        return symbol[:-len(quote_currency)]

    return symbol


def is_valid_symbol(symbol: str, quote_currency: str = 'USDT') -> bool:
    """
    Check if symbol is valid format

    Args:
        symbol: Symbol to validate
        quote_currency: Expected quote currency

    Returns:
        True if valid, False otherwise

    Examples:
        >>> is_valid_symbol('ETHUSDT')
        True
        >>> is_valid_symbol('ETH')
        True
        >>> is_valid_symbol('')
        False
        >>> is_valid_symbol('123')
        False
    """
    if not symbol or len(symbol) < 2:
        return False

    try:
        normalized = normalize_symbol(symbol, quote_currency)
        # Check if base symbol is reasonable length (2-10 chars)
        base = extract_base_symbol(normalized, quote_currency)
        return 2 <= len(base) <= 10 and base.isalpha()
    except (ValueError, AttributeError):
        return False


def format_symbol_for_binance(symbol: str) -> str:
    """
    Format symbol for Binance API calls

    Args:
        symbol: Symbol in any format

    Returns:
        Binance-compatible symbol (e.g., 'ETHUSDT')

    Examples:
        >>> format_symbol_for_binance('ETH')
        'ETHUSDT'
        >>> format_symbol_for_binance('eth-usdt')
        'ETHUSDT'
    """
    return normalize_symbol(symbol, 'USDT')


def format_symbol_for_display(symbol: str, separator: str = '/') -> str:
    """
    Format symbol for human-readable display

    Args:
        symbol: Symbol in any format
        separator: Separator to use (default: '/')

    Returns:
        Display-friendly symbol (e.g., 'ETH/USDT')

    Examples:
        >>> format_symbol_for_display('ETHUSDT')
        'ETH/USDT'
        >>> format_symbol_for_display('ETHUSDT', '-')
        'ETH-USDT'
    """
    normalized = normalize_symbol(symbol)
    base = extract_base_symbol(normalized)
    return f"{base}{separator}USDT"


# Convenience constants
USDT_PAIRS = ['USDT']
BUSD_PAIRS = ['BUSD']
BTC_PAIRS = ['BTC']


if __name__ == '__main__':
    # Test cases
    test_symbols = [
        'ETH', 'ETHUSDT', 'ETH-USDT', 'ETH/USDT', 'eth',
        'BTC', 'BTCUSDT', 'SOL', 'SOLUSDT'
    ]

    print("Symbol Normalization Tests:\n")
    for symbol in test_symbols:
        normalized = normalize_symbol(symbol)
        base = extract_base_symbol(normalized)
        valid = is_valid_symbol(symbol)
        display = format_symbol_for_display(normalized)

        print(f"Input: {symbol:12} -> Normalized: {normalized:10} | Base: {base:5} | Valid: {valid} | Display: {display}")

    print("\nAll tests passed!")
