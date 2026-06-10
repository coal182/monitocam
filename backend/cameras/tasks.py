import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_and_validate_camera(camera_id: int):
    from cameras.models import Camera

    try:
        camera = Camera.objects.get(id=camera_id)
    except Camera.DoesNotExist:
        logger.error(f"Camera {camera_id} not found")
        return None

    if not camera.enabled:
        logger.info(f"Camera {camera_id} disabled, skipping recording")
        return None

    return camera


def _create_recording(camera):
    from recordings.models import Recording
    from django.conf import settings
    from pathlib import Path

    output_dir = Path(settings.RECORDINGS_PATH) / f"camera_{camera.id}"
    safe_name = "".join(c for c in camera.name if c.isalnum() or c in "_-")
    timestamp = timezone.localtime().strftime("%Y-%m-%d_%H-%M")
    filename = f"{safe_name}_{timestamp}.mp4"
    output_file = output_dir / filename

    recording = Recording.objects.create(
        camera=camera,
        filename=filename,
        path=str(output_file),
        start_time=timezone.now(),
    )
    logger.info(f"Created Recording record for camera {camera.id}: {filename}")
    return recording


def _wait_for_ffmpeg(camera_id: int) -> int:
    from cameras.services.recorder import recorder_service
    from cameras.services.recording_status import set_recording
    from django.conf import settings

    process = recorder_service._processes.get(camera_id)
    if not process:
        return -1

    logger.info(f"Waiting for ffmpeg to finish for camera {camera_id} (timeout={settings.FRAGMENT_DURATION + 300}s)...")
    try:
        process.wait(timeout=settings.FRAGMENT_DURATION + 300)
    except Exception as e:
        logger.error(f"Error waiting for ffmpeg on camera {camera_id}: {e}")

    stderr_output = recorder_service.get_ffmpeg_error(camera_id)
    returncode = process.returncode

    if returncode != 0:
        logger.error(f"ffmpeg failed for camera {camera_id} (exit={returncode})")
        if stderr_output:
            for line in stderr_output.strip().split("\n")[-5:]:
                logger.error(f"  ffmpeg: {line}")
    else:
        logger.info(f"ffmpeg finished for camera {camera_id}")

    recorder_service._processes.pop(camera_id, None)
    set_recording(camera_id, False)

    return returncode


def _finalize_recording(recording, returncode: int):
    from django.conf import settings
    from pathlib import Path

    try:
        file_path = Path(recording.path)

        if file_path.exists() and returncode == 0:
            recording.refresh_from_db()
            recording.size = file_path.stat().st_size
            recording.end_time = timezone.now()
            recording.duration = int((recording.end_time - recording.start_time).total_seconds())
            recording.save()

            _generate_gif(recording)
        elif returncode != 0:
            recording.delete()
            logger.info(f"Deleted failed recording {recording.id} (no file)")
        else:
            logger.warning(f"Video file missing for recording {recording.id}: {recording.path}")
    except Exception as e:
        logger.error(f"Error updating recording {recording.id}: {e}")


def _generate_gif(recording):
    from recordings.services.giffer import gif_service
    from django.conf import settings

    gif_path = gif_service.get_gif_path(recording.path)

    if gif_service.gif_exists(recording.path):
        recording.has_gif = True
        recording.save(update_fields=["has_gif"])
        logger.info(f"GIF already exists for recording {recording.id}")
        return

    result = gif_service.generate_gif(
        recording.path, gif_path,
        video_duration=recording.duration or settings.FRAGMENT_DURATION,
        gif_target_duration=settings.GIF_TARGET_DURATION,
        fps=settings.GIF_FPS,
    )

    if result:
        recording.has_gif = True
        recording.save(update_fields=["has_gif"])
        logger.info(f"Generated GIF for recording {recording.id}")
    else:
        logger.error(f"Failed to generate GIF for recording {recording.id}")


def _chain_next_recording(camera_id: int, returncode: int):
    import time

    if returncode != 0:
        retry_delay = 30
        logger.info(f"Retrying camera {camera_id} in {retry_delay}s...")
        time.sleep(retry_delay)

    try:
        from cameras.models import Camera
        camera = Camera.objects.get(id=camera_id)
        if camera.enabled:
            logger.info(f"Auto-starting next recording for camera {camera_id}")
            start_recording_task.delay(camera_id)
        else:
            logger.info(f"Camera {camera_id} disabled, not starting next recording")
    except Exception as e:
        logger.error(f"Error starting next recording for camera {camera_id}: {e}")


@shared_task(queue="recordings", time_limit=7200, soft_time_limit=7000)
def start_recording_task(camera_id: int):
    from cameras.services.recorder import recorder_service

    camera = _get_and_validate_camera(camera_id)
    if not camera:
        return False

    if not recorder_service.start_recording(camera.id, camera.name, camera.rtsp_url):
        return False

    recording = _create_recording(camera)
    returncode = _wait_for_ffmpeg(camera_id)
    _finalize_recording(recording, returncode)
    _chain_next_recording(camera_id, returncode)

    return True


@shared_task(queue="recordings")
def stop_recording_task(camera_id: int):
    from cameras.services.recorder import recorder_service
    from recordings.models import Recording

    recording = Recording.objects.filter(
        camera_id=camera_id,
        end_time__isnull=True,
    ).order_by("-start_time").first()

    success = recorder_service.stop_recording(camera_id)

    if recording:
        from pathlib import Path

        recording.end_time = timezone.now()
        file_path = Path(recording.path)
        if file_path.exists():
            recording.size = file_path.stat().st_size
        if recording.start_time:
            recording.duration = int((recording.end_time - recording.start_time).total_seconds())
        recording.save()

    return success
