import os
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ.setdefault("AUTH_USERNAME", "testuser")
os.environ.setdefault("AUTH_PASSWORD", "testpass")


@pytest.fixture
def auth_client(client):
    login_response = client.post(
        "/auth/login/",
        {"username": "testuser", "password": "testpass"},
        content_type="application/json",
    )
    token = login_response.json()["access_token"]
    client.cookies.set("access_token", token)
    return client


@pytest.mark.django_db
class TestCameras:
    def test_list_cameras_empty(self, auth_client):
        response = auth_client.get("/cameras/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_camera(self, auth_client):
        camera_data = {
            "name": "Front Door",
            "rtsp_url": "rtsp://192.168.1.100:554/stream1",
            "enabled": True,
        }
        response = auth_client.post(
            "/cameras/", camera_data, content_type="application/json"
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Front Door"
        assert data["rtsp_url"] == "rtsp://192.168.1.100:554/stream1"

    def test_create_camera_invalid_url(self, auth_client):
        camera_data = {"name": "Test", "rtsp_url": "not-a-url"}
        response = auth_client.post(
            "/cameras/", camera_data, content_type="application/json"
        )
        assert response.status_code == 400

    def test_get_camera(self, auth_client):
        create_response = auth_client.post(
            "/cameras/",
            {"name": "Test", "rtsp_url": "rtsp://test.local/stream"},
            content_type="application/json",
        )
        camera_id = create_response.json()["id"]

        response = auth_client.get(f"/cameras/{camera_id}/")
        assert response.status_code == 200
        assert response.json()["id"] == camera_id

    def test_get_camera_not_found(self, auth_client):
        response = auth_client.get("/cameras/9999/")
        assert response.status_code == 404

    def test_delete_camera(self, auth_client):
        create_response = auth_client.post(
            "/cameras/",
            {"name": "ToDelete", "rtsp_url": "rtsp://test.local/stream"},
            content_type="application/json",
        )
        camera_id = create_response.json()["id"]

        response = auth_client.delete(f"/cameras/{camera_id}/")
        assert response.status_code == 204

        get_response = auth_client.get(f"/cameras/{camera_id}/")
        assert get_response.status_code == 404

    def test_unauthorized_access(self, client):
        response = client.get("/cameras/")
        assert response.status_code == 401
