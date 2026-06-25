import pytest
import sys
sys.path.append('.')
from services.auth.auth_service import hash_password, verify_password, create_access_token
from datetime import timedelta
from jose import jwt

SECRET_KEY = "trustrail-secret-key-change-in-production"
ALGORITHM = "HS256"


def test_hash_password_returns_string():
    hashed = hash_password("mypassword")
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_hash_password_is_deterministic():
    assert hash_password("mypassword") == hash_password("mypassword")


def test_hash_password_different_inputs():
    assert hash_password("password1") != hash_password("password2")


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_returns_string():
    token = create_access_token({"sub": "alice", "role": "user"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_contains_correct_claims():
    token = create_access_token(
        {"sub": "alice", "role": "user"},
        expires_delta=timedelta(minutes=30)
    )
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "alice"
    assert payload["role"] == "user"
    assert "exp" in payload


def test_create_access_token_expires():
    token = create_access_token(
        {"sub": "alice"},
        expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(Exception):
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
