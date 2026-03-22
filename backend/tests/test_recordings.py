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


@pytest_asyncio.fixture
async def authenticated_client(client):
    with (
        patch("api.auth.verify_system_user") as mock_verify,
        patch("core.security.get_user_info") as mock_get_user,
    ):
        mock_verify.return_value = True
        mock_get_user.return_value = {"username": "admin"}
        response = await client.post(
            "/auth/login", data={"username": "admin", "password": "admin"}
        )
        token = response.json()["access_token"]

    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest_asyncio.fixture
async def setup_camera(authenticated_client):
    response = await authenticated_client.post(
        "/cameras", json={"name": "Test Cam", "rtsp_url": "rtsp://test.local/stream"}
    )
    return response.json()


class TestRecordings:
    @pytest.mark.asyncio
    async def test_list_recordings_empty(self, authenticated_client):
        response = await authenticated_client.get("/recordings")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_recordings_filter_by_camera(
        self, authenticated_client, setup_camera
    ):
        camera = setup_camera
        response = await authenticated_client.get(
            f"/recordings?camera_id={camera['id']}"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_recordings_filter_by_date(self, authenticated_client):
        response = await authenticated_client.get("/recordings?date=2026-03-22")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_recording_not_found(self, authenticated_client):
        response = await authenticated_client.get("/recordings/9999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        response = await client.get("/recordings")
        assert response.status_code == 401
