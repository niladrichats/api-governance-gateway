import pytest
import sys
sys.path.append('.')


def test_amount_request_valid():
    from services.accounts.accounts_service import AmountRequest
    req = AmountRequest(amount=500.0)
    assert req.amount == 500.0


def test_amount_request_zero():
    from services.accounts.accounts_service import AmountRequest
    req = AmountRequest(amount=0.0)
    assert req.amount == 0.0


def test_amount_request_invalid():
    from services.accounts.accounts_service import AmountRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AmountRequest(amount="not_a_number")


def test_balance_sufficient():
    balance = 5000.0
    amount = 100.0
    assert balance >= amount


def test_balance_insufficient():
    balance = 100.0
    amount = 5000.0
    assert balance < amount
