import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
sys.path.append('.')


@pytest.fixture
def gateway_client():
    with patch('shared.tracing.setup_tracing'):
        with patch('gateway.gateway.setup_tracing'):
            from gateway.gateway import app
            client = TestClient(app)
            yield client


def test_gateway_root(gateway_client):
    response = gateway_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "API Gateway"
    assert data["status"] == "running"
    assert "routes" in data


def test_gateway_requires_auth(gateway_client):
    response = gateway_client.get("/v1/accounts/ACC1001/balance")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_gateway_invalid_token(gateway_client):
    response = gateway_client.get(
        "/v1/accounts/ACC1001/balance",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401


def test_gateway_missing_bearer_prefix(gateway_client):
    response = gateway_client.get(
        "/v1/accounts/ACC1001/balance",
        headers={"Authorization": "notabearer token"}
    )
    assert response.status_code == 401


def test_gateway_unknown_service(gateway_client):
    from services.auth.auth_service import create_access_token
    token = create_access_token({"sub": "alice", "role": "user"})
    with patch('gateway.gateway.httpx.AsyncClient'):
        response = gateway_client.get(
            "/v1/unknownservice/something",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
