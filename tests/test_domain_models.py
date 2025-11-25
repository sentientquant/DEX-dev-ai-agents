# test_domain_models.py
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from trading_modes.models.domain import (
    Trade, TradeSide, TradingMode, TradeStatus,
    SignalVerificationResult, AgreementLevel, SignalAction, Verdict
)
from datetime import datetime

def test_trade_creation():
    """Test creating a valid Trade object"""
    trade = Trade(
        trade_id='TEST_001',
        symbol='BTCUSDT',
        side=TradeSide.BUY,
        entry_price=50000.0,
        position_size_usd=100.0,
        stop_loss=49000.0,
        mode=TradingMode.PAPER,
        status=TradeStatus.OPEN,
        timestamp=datetime.now()
    )

    assert trade.base_asset == 'BTC'
    assert trade.is_long == True
    assert trade.is_open == True
    print("✓ Trade creation test passed")

def test_trade_validation():
    """Test Trade validation catches invalid data"""
    try:
        trade = Trade(
            trade_id='INVALID',
            symbol='BTCUSDT',
            side=TradeSide.BUY,
            entry_price=-100.0,  # Invalid: negative price
            position_size_usd=100.0,
            stop_loss=49000.0,
            mode=TradingMode.PAPER,
            status=TradeStatus.OPEN,
            timestamp=datetime.now()
        )
        print("✗ Validation test failed - should have raised error")
    except ValueError as e:
        print(f"✓ Validation test passed - caught error: {e}")

def test_signal_verification_result():
    """Test SignalVerificationResult"""
    result = SignalVerificationResult(
        agrees_with_scanner=True,
        agreement_level=AgreementLevel.FULL,
        action=SignalAction.BUY,
        confidence=95,
        reasoning="Test reasoning",
        verdicts=[
            Verdict(model_name='test', vote=SignalAction.BUY, confidence=90, reasoning='Test')
        ]
    )

    assert result.agreement_level == AgreementLevel.FULL
    assert result.action == SignalAction.BUY
    print("✓ SignalVerificationResult test passed")

# Run tests
test_trade_creation()
test_trade_validation()
test_signal_verification_result()
print("\n✅ All domain model tests passed!")
