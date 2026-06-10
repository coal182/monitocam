import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ.setdefault("AUTH_USERNAME", "testuser")
os.environ.setdefault("AUTH_PASSWORD", "testpass")


@pytest.mark.django_db
class TestGetAndValidateCamera:
    def test_valid_camera(self, camera):
        from cameras.tasks import _get_and_validate_camera

        result = _get_and_validate_camera(camera.id)
        assert result is not None
        assert result.id == camera.id

    def test_camera_not_found(self):
        from cameras.tasks import _get_and_validate_camera

        result = _get_and_validate_camera(9999)
        assert result is None

    def test_disabled_camera(self, disabled_camera):
        from cameras.tasks import _get_and_validate_camera

        result = _get_and_validate_camera(disabled_camera.id)
        assert result is None


@pytest.mark.django_db
class TestCreateRecording:
    def test_create_recording(self, camera, tmp_path):
        from cameras.tasks import _create_recording
        from recordings.models import Recording

        with patch("django.conf.settings") as mock_settings:
            mock_settings.RECORDINGS_PATH = str(tmp_path)
            recording = _create_recording(camera)

        assert recording is not None
        assert recording.camera.id == camera.id
        assert recording.filename.endswith(".mp4")
        assert Recording.objects.filter(id=recording.id).exists()


@pytest.mark.django_db
class TestFinalizeRecording:
    def test_finalize_success(self, recording, tmp_path):
        from cameras.tasks import _finalize_recording

        fake_file = tmp_path / "TestCamera_2026-06-10_12-00.mp4"
        fake_file.write_bytes(b"\x00" * 1024)
        recording.path = str(fake_file)
        recording.save(update_fields=["path"])

        with patch("cameras.tasks._generate_gif"):
            _finalize_recording(recording, 0)

        recording.refresh_from_db()
        assert recording.size == 1024
        assert recording.end_time is not None
        assert recording.duration is not None

    def test_finalize_failed(self, recording):
        from cameras.tasks import _finalize_recording
        from recordings.models import Recording

        recording_id = recording.id
        _finalize_recording(recording, 1)

        assert not Recording.objects.filter(id=recording_id).exists()


@pytest.mark.django_db
class TestGenerateGif:
    def test_generate_gif(self, recording):
        from cameras.tasks import _generate_gif

        recording.duration = 1800
        recording.save()

        mock_gif_service = MagicMock()
        mock_gif_service.get_gif_path.return_value = "/tmp/test.gif"
        mock_gif_service.gif_exists.return_value = False
        mock_gif_service.generate_gif.return_value = "/tmp/test.gif"

        with patch("recordings.services.giffer.gif_service", mock_gif_service):
            _generate_gif(recording)

            recording.refresh_from_db()
            assert recording.has_gif is True
            mock_gif_service.generate_gif.assert_called_once()

    def test_generate_gif_already_exists(self, recording_with_gif):
        from cameras.tasks import _generate_gif

        mock_gif_service = MagicMock()
        mock_gif_service.get_gif_path.return_value = "/tmp/test.gif"
        mock_gif_service.gif_exists.return_value = True

        with patch("recordings.services.giffer.gif_service", mock_gif_service):
            _generate_gif(recording_with_gif)

            recording_with_gif.refresh_from_db()
            assert recording_with_gif.has_gif is True
            mock_gif_service.generate_gif.assert_not_called()
