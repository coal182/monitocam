import os
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ.setdefault("AUTH_USERNAME", "testuser")
os.environ.setdefault("AUTH_PASSWORD", "testpass")


@pytest.mark.django_db
class TestRecordings:
    def test_list_recordings_empty(self, auth_client):
        response = auth_client.get("/recordings/")
        assert response.status_code == 200

    def test_list_recordings(self, auth_client, recordings):
        response = auth_client.get("/recordings/")
        assert response.status_code == 200
        assert len(response.json()) == len(recordings)

    def test_list_recordings_filter_camera(self, auth_client, recordings):
        camera_id = recordings[0].camera_id
        response = auth_client.get(f"/recordings/?camera_id={camera_id}")
        assert response.status_code == 200
        assert all(r["camera"] == camera_id for r in response.json())

    def test_unauthorized_access(self, client):
        response = client.get("/recordings/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestRecordingDownload:
    def test_download_recording(self, auth_client, recording):
        response = auth_client.get(f"/recordings/{recording.id}/download/")
        assert response.status_code == 200
        assert response["Content-Type"] == "video/mp4"
        assert response["Content-Disposition"].startswith("attachment")

    def test_download_not_found(self, auth_client, recording_no_file):
        response = auth_client.get(f"/recordings/{recording_no_file.id}/download/")
        assert response.status_code == 404

    def test_stream_recording(self, auth_client, recording):
        response = auth_client.get(f"/recordings/{recording.id}/stream/")
        assert response.status_code == 200
        assert response["Content-Type"] == "video/mp4"

    def test_stream_not_found(self, auth_client, recording_no_file):
        response = auth_client.get(f"/recordings/{recording_no_file.id}/stream/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestRecordingDestroy:
    def test_destroy_deletes_files(self, auth_client, recording):
        from pathlib import Path

        file_path = Path(recording.path)
        assert file_path.exists()

        response = auth_client.delete(f"/recordings/{recording.id}/")
        assert response.status_code == 204

        from recordings.models import Recording

        assert not Recording.objects.filter(id=recording.id).exists()

    def test_destroy_not_found(self, auth_client):
        response = auth_client.delete("/recordings/9999/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestRecordingCleanup:
    def test_cleanup_all(self, auth_client, recordings):
        from recordings.models import Recording

        total = Recording.objects.count()
        assert total == len(recordings)

        response = auth_client.delete("/recordings/cleanup/0/")
        assert response.status_code == 200
        assert response.json()["deleted"] == total

        assert Recording.objects.count() == 0

    def test_cleanup_filter_days(self, auth_client, recordings):
        from recordings.models import Recording

        response = auth_client.delete("/recordings/cleanup/1/")
        assert response.status_code == 200
        deleted = response.json()["deleted"]
        assert deleted >= 0


@pytest.mark.django_db
class TestGifEndpoints:
    def test_gif_file_endpoint(self, auth_client, recording_with_gif):
        response = auth_client.get(f"/recordings/gifs/{recording_with_gif.id}/file/")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/gif"

    def test_gif_file_not_found(self, auth_client):
        response = auth_client.get("/recordings/gifs/9999/file/")
        assert response.status_code == 404

    def test_gifs_list(self, auth_client, recordings):
        response = auth_client.get("/recordings/gifs/list/")
        assert response.status_code == 200
        data = response.json()
        assert all(r["has_gif"] for r in data)

    def test_gifs_list_filter_camera(self, auth_client, recordings):
        camera_id = recordings[0].camera_id
        response = auth_client.get(f"/recordings/gifs/list/?camera_id={camera_id}")
        assert response.status_code == 200
        assert all(r["camera"] == camera_id for r in response.json())

    def test_get_gif_generating(self, auth_client, recording_no_gif):
        response = auth_client.get(f"/recordings/{recording_no_gif.id}/get_gif/")
        assert response.status_code == 200
        assert response.json()["status"] == "generating"
