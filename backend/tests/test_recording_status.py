import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")


class TestRecordingStatus:
    def test_set_recording(self):
        from cameras.services.recording_status import set_recording, is_recording

        with patch("cameras.services.recording_status.cache") as mock_cache:
            with patch("cameras.services.recording_status._publish_status"):
                set_recording(1, True)
                mock_cache.set.assert_called_once_with("recording:1", "1", timeout=None)

    def test_clear_recording(self):
        from cameras.services.recording_status import set_recording

        with patch("cameras.services.recording_status.cache") as mock_cache:
            with patch("cameras.services.recording_status._publish_status"):
                set_recording(1, False)
                mock_cache.delete.assert_called_once_with("recording:1")

    def test_is_recording(self):
        from cameras.services.recording_status import is_recording

        with patch("cameras.services.recording_status.cache") as mock_cache:
            mock_cache.get.return_value = "1"
            assert is_recording(1) is True

            mock_cache.get.return_value = None
            assert is_recording(1) is False

    def test_publish_status(self):
        from cameras.services.recording_status import _publish_status
        import json

        with patch("cameras.services.recording_status._get_redis_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client

            _publish_status(1, True)

            mock_client.publish.assert_called_once()
            args = mock_client.publish.call_args
            assert args[0][0] == "cameras:status"
            data = json.loads(args[0][1])
            assert data["camera_id"] == 1
            assert data["is_recording"] is True

    def test_get_all_statuses(self):
        from cameras.services.recording_status import get_all_statuses

        with patch("cameras.services.recording_status.cache") as mock_cache:
            mock_cache.get.side_effect = lambda key: "1" if key == "recording:1" else None

            statuses = get_all_statuses()
            assert 1 in statuses
            assert statuses[1] is True
            assert 2 not in statuses
