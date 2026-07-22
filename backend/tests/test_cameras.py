import os
from unittest.mock import patch

import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ.setdefault("AUTH_USERNAME", "testuser")
os.environ.setdefault("AUTH_PASSWORD", "testpass")


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

    def test_get_camera(self, auth_client, camera):
        response = auth_client.get(f"/cameras/{camera.id}/")
        assert response.status_code == 200
        assert response.json()["id"] == camera.id

    def test_get_camera_not_found(self, auth_client):
        response = auth_client.get("/cameras/9999/")
        assert response.status_code == 404

    def test_delete_camera(self, auth_client, camera):
        response = auth_client.delete(f"/cameras/{camera.id}/")
        assert response.status_code == 204

        get_response = auth_client.get(f"/cameras/{camera.id}/")
        assert get_response.status_code == 404

    def test_unauthorized_access(self, client):
        response = client.get("/cameras/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestCameraRecording:
    def test_start_recording(self, auth_client, camera):
        response = auth_client.post(
            f"/cameras/{camera.id}/start/",
            {},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recording"
        assert data["camera_id"] == camera.id

    def test_stop_recording(self, auth_client, camera):
        response = auth_client.post(
            f"/cameras/{camera.id}/stop/",
            {},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
        assert data["camera_id"] == camera.id

    def test_camera_status(self, auth_client, camera):
        response = auth_client.get(f"/cameras/{camera.id}/status/")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == camera.id
        assert data["name"] == camera.name
        assert data["is_recording"] is False
        assert data["status"] == "stopped"

    def test_camera_statuses(self, auth_client, cameras):
        response = auth_client.get("/cameras/statuses/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(cameras)
        assert all("id" in c and "name" in c and "is_recording" in c for c in data)

    def test_start_disabled_camera(self, auth_client, disabled_camera):
        response = auth_client.post(
            f"/cameras/{disabled_camera.id}/start/",
            {},
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_sse_endpoint(self, auth_client):
        response = auth_client.get("/cameras/events/")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"
        assert response["Cache-Control"] == "no-cache"
        assert response["X-Accel-Buffering"] == "no"


@patch("cameras.services.snapshot.snapshot_service")
@pytest.mark.django_db
class TestCameraSnapshot:
    def test_snapshot_no_file(self, mock_snapshot, auth_client, camera):
        mock_snapshot.get_snapshot_path.return_value = "/nonexistent/snapshot.jpg"
        response = auth_client.get(f"/cameras/{camera.id}/snapshot/")
        assert response.status_code == 404
        assert response.json()["detail"] == "No snapshot available"

    def test_snapshot_unauthorized(self, mock_snapshot, client, camera):
        response = client.get(f"/cameras/{camera.id}/snapshot/")
        assert response.status_code == 401

    def test_snapshot_success(self, mock_snapshot, auth_client, camera, tmp_path):
        snapshot_dir = tmp_path / f"camera_{camera.id}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = snapshot_dir / "snapshot.jpg"
        snapshot_file.write_bytes(b"\xff\xd8\xff\xe0")

        mock_snapshot.get_snapshot_path.return_value = str(snapshot_file)
        response = auth_client.get(f"/cameras/{camera.id}/snapshot/")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/jpeg"
        assert b"".join(response.streaming_content) == b"\xff\xd8\xff\xe0"
