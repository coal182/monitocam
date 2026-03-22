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
    with patch("main.core.security.oauth2_scheme") as mock_scheme:
        mock_scheme.return_value.__aenter__ = lambda s: "mock_token"
        mock_scheme.return_value.__aexit__ = lambda s, *a: None

        with patch("main.core.security.decode_token") as mock_decode:
            mock_decode.return_value = type(
                "obj", (object,), {"username": "testuser"}
            )()

            with patch("main.core.security.get_user_info") as mock_get_user:
                mock_get_user.return_value = {"username": "testuser"}

                from main import app as app_instance

                async with AsyncClient(
                    transport=ASGITransport(app=app_instance), base_url="http://test"
                ) as ac:
                    ac.headers.update({"Authorization": "Bearer mock_token"})
                    yield ac


class TestCameras:
    @pytest.mark.asyncio
    async def test_list_cameras_empty(self, authenticated_client):
        response = await authenticated_client.get("/cameras")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_camera(self, authenticated_client):
        camera_data = {
            "name": "Front Door",
            "rtsp_url": "rtsp://192.168.1.100:554/stream1",
            "enabled": True,
        }
        response = await authenticated_client.post("/cameras", json=camera_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Front Door"
        assert data["rtsp_url"] == "rtsp://192.168.1.100:554/stream1"
        assert "id" in data
        assert data["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_create_camera_invalid_url(self, authenticated_client):
        camera_data = {"name": "Test", "rtsp_url": "not-a-url"}
        response = await authenticated_client.post("/cameras", json=camera_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_camera(self, authenticated_client):
        create_response = await authenticated_client.post(
            "/cameras", json={"name": "Test", "rtsp_url": "rtsp://test.local/stream"}
        )
        camera_id = create_response.json()["id"]

        response = await authenticated_client.get(f"/cameras/{camera_id}")
        assert response.status_code == 200
        assert response.json()["id"] == camera_id

    @pytest.mark.asyncio
    async def test_get_camera_not_found(self, authenticated_client):
        response = await authenticated_client.get("/cameras/9999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_camera(self, authenticated_client):
        create_response = await authenticated_client.post(
            "/cameras",
            json={"name": "ToDelete", "rtsp_url": "rtsp://test.local/stream"},
        )
        camera_id = create_response.json()["id"]

        response = await authenticated_client.delete(f"/cameras/{camera_id}")
        assert response.status_code == 204

        get_response = await authenticated_client.get(f"/cameras/{camera_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        response = await client.get("/cameras")
        assert response.status_code == 401
