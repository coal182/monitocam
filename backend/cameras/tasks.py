import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(queue="recordings", time_limit=7200, soft_time_limit=7000)
def start_recording_task(camera_id: int):
    import os
    import signal

    from cameras.models import Camera
    from cameras.services.recorder import recorder_service
    from cameras.services.recording_status import set_recording

    try:
        camera = Camera.objects.get(id=camera_id)
    except Camera.DoesNotExist:
        logger.error(f"Camera {camera_id} not found")
        return False

    if not camera.enabled:
        logger.info(f"Camera {camera_id} disabled, skipping recording")
        return False

    success = recorder_service.start_recording(camera.id, camera.name, camera.rtsp_url)

    if not success:
        return False

    from recordings.models import Recording
    from django.conf import settings
    from pathlib import Path

    output_dir = Path(settings.RECORDINGS_PATH) / f"camera_{camera_id}"
    safe_name = "".join(c for c in camera.name if c.isalnum() or c in "_-")
    timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{safe_name}_{timestamp}.mp4"
    output_file = output_dir / filename

    recording = Recording.objects.create(
        camera=camera,
        filename=filename,
        path=str(output_file),
        start_time=timezone.now(),
    )
    logger.info(f"Created Recording record for camera {camera_id}: {filename}")

    process = recorder_service._processes.get(camera_id)
    if process:
        logger.info(f"Waiting for ffmpeg to finish for camera {camera_id} (timeout={settings.FRAGMENT_DURATION + 300}s)...")
        try:
            process.wait(timeout=settings.FRAGMENT_DURATION + 300)
        except Exception as e:
            logger.error(f"Error waiting for ffmpeg on camera {camera_id}: {e}")

        stderr_output = recorder_service.get_ffmpeg_error(camera_id)
        returncode = process.returncode
        duration = (timezone.now() - recording.start_time).total_seconds()

        if returncode != 0:
            logger.error(f"ffmpeg failed for camera {camera_id} (exit={returncode}, duration={duration:.1f}s)")
            if stderr_output:
                for line in stderr_output.strip().split("\n")[-5:]:
                    logger.error(f"  ffmpeg: {line}")
        else:
            logger.info(f"ffmpeg finished for camera {camera_id}")

        recorder_service._processes.pop(camera_id, None)
        set_recording(camera_id, False)

        try:
            file_path = Path(recording.path)
            if file_path.exists() and returncode == 0:
                recording.refresh_from_db()
                recording.size = file_path.stat().st_size
                recording.end_time = timezone.now()
                recording.duration = int((recording.end_time - recording.start_time).total_seconds())
                recording.save()

                from recordings.services.giffer import gif_service
                gif_path = gif_service.get_gif_path(recording.path)
                if not gif_service.gif_exists(recording.path):
                    result = gif_service.generate_gif(
                        recording.path, gif_path,
                        duration=settings.GIF_DURATION,
                        fps=settings.GIF_FPS,
                        speed=settings.GIF_SPEED,
                    )
                    if result:
                        recording.has_gif = True
                        recording.save(update_fields=["has_gif"])
                        logger.info(f"Generated GIF for recording {recording.id}")
                    else:
                        logger.error(f"Failed to generate GIF for recording {recording.id}")
                else:
                    recording.has_gif = True
                    recording.save(update_fields=["has_gif"])
                    logger.info(f"GIF already exists for recording {recording.id}")
            elif returncode != 0:
                recording.delete()
                logger.info(f"Deleted failed recording {recording.id} (no file)")
            else:
                logger.warning(f"Video file missing for recording {recording.id}: {recording.path}")
        except Exception as e:
            logger.error(f"Error updating recording {recording.id}: {e}")

        import time

        if returncode != 0:
            retry_delay = 30
            logger.info(f"Retrying camera {camera_id} in {retry_delay}s...")
            time.sleep(retry_delay)

        try:
            camera.refresh_from_db()
            if camera.enabled:
                logger.info(f"Auto-starting next recording for camera {camera_id}")
                start_recording_task.delay(camera_id)
            else:
                logger.info(f"Camera {camera_id} disabled, not starting next recording")
        except Exception as e:
            logger.error(f"Error starting next recording for camera {camera_id}: {e}")

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
