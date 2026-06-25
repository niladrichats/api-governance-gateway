import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
sys.path.append('.')


@pytest.fixture
def auth_client():
    with patch('shared.tracing.setup_tracing'):
        with patch('services.auth.auth_service.setup_tracing'):
            with patch('services.auth.database.DATABASE_URL', 'sqlite:///./test_auth.db'):
                from services.auth import database
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker

                engine = create_engine(
                    'sqlite:///./test_auth.db',
                    connect_args={"check_same_thread": False}
                )
                database.Base.metadata.create_all(bind=engine)
                TestSession = sessionmaker(bind=engine)

                from services.auth.auth_service import app, hash_password
                from services.auth.database import User

                db = TestSession()
                if db.query(User).count() == 0:
                    db.add(User(
                        username="testuser",
                        hashed_password=hash_password("testpass"),
                        role="user"
                    ))
                    db.commit()
                db.close()

                def override_get_db():
                    db = TestSession()
                    try:
                        yield db
                    finally:
                        db.close()

                from services.auth.auth_service import get_db
                app.dependency_overrides[get_db] = override_get_db

                client = TestClient(app)
                yield client

                app.dependency_overrides.clear()
                database.Base.metadata.drop_all(bind=engine)


def test_root_endpoint(auth_client):
    response = auth_client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Auth Service"
    assert response.json()["status"] == "running"


def test_login_valid_credentials(auth_client):
    response = auth_client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(auth_client):
    response = auth_client.post(
        "/token",
        data={"username": "testuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_nonexistent_user(auth_client):
    response = auth_client.post(
        "/token",
        data={"username": "nobody", "password": "anything"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
