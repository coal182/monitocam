import os
from unittest.mock import patch, MagicMock

import pytest
from django.test import RequestFactory
from django.utils import timezone


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ["AUTH_USERNAME"] = os.environ.get("AUTH_USERNAME") or "testuser"
os.environ["AUTH_PASSWORD"] = os.environ.get("AUTH_PASSWORD") or "testpass"


@pytest.fixture(autouse=True)
def mock_celery_tasks():
    """Mock Celery task .delay() calls so tests don't need Redis."""
    with patch("cameras.tasks.start_recording_task.delay") as mock_start, \
         patch("cameras.tasks.stop_recording_task.delay") as mock_stop, \
         patch("cameras.signals.start_recording_task.delay") as mock_sig_start, \
         patch("cameras.signals.stop_recording_task.delay") as mock_sig_stop, \
         patch("recordings.tasks.generate_gif_task.delay") as mock_gif:
        mock_start.return_value = MagicMock()
        mock_stop.return_value = MagicMock()
        mock_sig_start.return_value = MagicMock()
        mock_sig_stop.return_value = MagicMock()
        mock_gif.return_value = MagicMock()
        yield


@pytest.fixture(autouse=True)
def mock_redis_cache():
    """Mock Django Redis cache so tests don't need a running Redis."""
    with patch("cameras.services.recording_status.cache") as mock_cache:
        mock_cache.get.return_value = None
        yield mock_cache


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def camera(db):
    from cameras.models import Camera

    return Camera.objects.create(
        name="Test Camera",
        rtsp_url="rtsp://192.168.1.100:554/stream1",
        enabled=True,
    )


@pytest.fixture
def disabled_camera(db):
    from cameras.models import Camera

    return Camera.objects.create(
        name="Disabled Camera",
        rtsp_url="rtsp://192.168.1.101:554/stream1",
        enabled=False,
    )


@pytest.fixture
def cameras(db):
    from cameras.models import Camera

    return [
        Camera.objects.create(
            name=f"Camera {i}",
            rtsp_url=f"rtsp://192.168.1.{100 + i}:554/stream1",
            enabled=i % 2 == 0,
        )
        for i in range(3)
    ]


@pytest.fixture
def recording(camera, tmp_path):
    from recordings.models import Recording

    file = tmp_path / "camera_1" / "TestCamera_2026-06-10_12-00.mp4"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(b"\x00" * 1024)

    return Recording.objects.create(
        camera=camera,
        filename="TestCamera_2026-06-10_12-00.mp4",
        path=str(file),
        start_time=timezone.now(),
    )


@pytest.fixture
def recording_no_file(camera):
    from recordings.models import Recording

    return Recording.objects.create(
        camera=camera,
        filename="TestCamera_2026-06-10_12-00.mp4",
        path="/tmp/nonexistent/test.mp4",
        start_time=timezone.now(),
    )


@pytest.fixture
def recording_with_gif(camera, tmp_path):
    from recordings.models import Recording

    mp4 = tmp_path / "camera_1" / "TestCamera_2026-06-10_12-00.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    mp4.write_bytes(b"\x00" * 1024)

    gif = tmp_path / "camera_1" / "TestCamera_2026-06-10_12-00.gif"
    gif.write_bytes(b"GIF89a")

    return Recording.objects.create(
        camera=camera,
        filename="TestCamera_2026-06-10_12-00.mp4",
        path=str(mp4),
        has_gif=True,
        start_time=timezone.now(),
    )


@pytest.fixture
def recording_no_gif(camera, tmp_path):
    from recordings.models import Recording

    mp4 = tmp_path / "camera_1" / "TestCamera_2026-06-10_12-00.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    mp4.write_bytes(b"\x00" * 1024)

    return Recording.objects.create(
        camera=camera,
        filename="TestCamera_2026-06-10_12-00.mp4",
        path=str(mp4),
        has_gif=False,
        start_time=timezone.now(),
    )


@pytest.fixture
def recordings(camera):
    from recordings.models import Recording

    return [
        Recording.objects.create(
            camera=camera,
            filename=f"TestCamera_2026-06-{10 - i:02d}_12-00.mp4",
            path=f"/tmp/test{i}.mp4",
            has_gif=i < 2,
            start_time=timezone.now() - timezone.timedelta(days=i),
        )
        for i in range(5)
    ]


@pytest.fixture
def auth_client(client):
    login_response = client.post(
        "/auth/login/",
        {"username": "testuser", "password": "testpass"},
        content_type="application/json",
    )
    token = login_response.json()["access_token"]
    client.cookies["access_token"] = token
    return client
