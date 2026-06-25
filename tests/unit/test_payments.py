import pytest
import sys
sys.path.append('.')


def test_payment_request_valid_amount():
    from services.payments.payments_service import PaymentRequest
    payment = PaymentRequest(
        from_account="ACC1001",
        to_account="ACC2002",
        amount=100.0,
        currency="USD"
    )
    assert payment.amount == 100.0
    assert payment.currency == "USD"


def test_payment_request_default_currency():
    from services.payments.payments_service import PaymentRequest
    payment = PaymentRequest(
        from_account="ACC1001",
        to_account="ACC2002",
        amount=100.0
    )
    assert payment.currency == "USD"


def test_payment_request_invalid_missing_fields():
    from services.payments.payments_service import PaymentRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PaymentRequest(from_account="ACC1001")


def test_saga_state_tracking():
    from services.payments.payments_service import saga_state, process_saga_result
    payment_id = "test-payment-123"
    saga_state[payment_id] = {
        "balance_checked": True,
        "fraud_assessed": True,
        "fraud_details": {
            "risk_level": "LOW",
            "confidence": 0.9,
            "reasoning": "Normal transaction"
        }
    }
    assert saga_state[payment_id]["balance_checked"] is True
    assert saga_state[payment_id]["fraud_assessed"] is True


def test_high_risk_fraud_blocks_payment():
    from services.payments.payments_service import saga_state
    payment_id = "test-fraud-456"
    saga_state[payment_id] = {
        "fraud_assessed": False,
        "fraud_details": {
            "risk_level": "HIGH",
            "confidence": 0.95,
            "reasoning": "Structuring detected"
        }
    }
    assert saga_state[payment_id]["fraud_assessed"] is False
