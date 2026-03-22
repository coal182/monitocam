import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app
from db.database import Base, engine


@pytest_asyncio.fixture
async def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAuth:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        with patch("api.auth.verify_system_user") as mock_verify:
            mock_verify.return_value = True
            response = await client.post(
                "/auth/login", data={"username": "testuser", "password": "testpass"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "username" in data

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        with patch("api.auth.verify_system_user") as mock_verify:
            mock_verify.return_value = False
            response = await client.post(
                "/auth/login", data={"username": "invalid", "password": "wrong"}
            )
            assert response.status_code == 401
            assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client):
        response = await client.post("/auth/login", data={"username": "test"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user(self, client):
        with (
            patch("api.auth.verify_system_user") as mock_verify,
            patch("core.security.get_user_info") as mock_get_user,
        ):
            mock_verify.return_value = True
            mock_get_user.return_value = {"username": "testuser"}
            login_response = await client.post(
                "/auth/login", data={"username": "testuser", "password": "testpass"}
            )
            token = login_response.json()["access_token"]

            response = await client.get(
                "/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            assert response.json()["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client):
        response = await client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
