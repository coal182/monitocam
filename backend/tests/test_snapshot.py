import os
from unittest.mock import patch

import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")


@pytest.mark.django_db
class TestSnapshotServiceIdempotency:
    def test_start_snapshot_twice_spawns_single_daemon(self, settings, tmp_path):
        settings.RECORDINGS_PATH = str(tmp_path)
        from cameras.services.snapshot import SnapshotService

        svc = SnapshotService()
        with patch("cameras.services.snapshot.threading.Thread") as mock_thread:
            assert svc.start_snapshot(1, "rtsp://127.0.0.1/stream") is True
            assert svc.start_snapshot(1, "rtsp://127.0.0.1/stream") is False
            assert mock_thread.call_count == 1

    def test_start_snapshot_after_stop_spawns_again(self, settings, tmp_path):
        settings.RECORDINGS_PATH = str(tmp_path)
        from cameras.services.snapshot import SnapshotService

        svc = SnapshotService()
        with patch("cameras.services.snapshot.threading.Thread"):
            assert svc.start_snapshot(1, "rtsp://127.0.0.1/stream") is True
            svc.stop_snapshot(1)
            assert svc.start_snapshot(1, "rtsp://127.0.0.1/stream") is True

    def test_running_flag_cleared_on_stop(self, settings, tmp_path):
        settings.RECORDINGS_PATH = str(tmp_path)
        from cameras.services.snapshot import SnapshotService

        svc = SnapshotService()
        with patch("cameras.services.snapshot.threading.Thread"):
            svc.start_snapshot(1, "rtsp://127.0.0.1/stream")
            assert svc._running[1] is True
            svc.stop_snapshot(1)
            assert svc._running[1] is False
