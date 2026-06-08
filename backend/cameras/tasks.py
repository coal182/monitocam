import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(queue="recordings")
def start_recording_task(camera_id: int):
    from cameras.models import Camera
    from cameras.services.recorder import recorder_service

    try:
        camera = Camera.objects.get(id=camera_id)
    except Camera.DoesNotExist:
        logger.error(f"Camera {camera_id} not found")
        return False

    success = recorder_service.start_recording(camera.id, camera.name, camera.rtsp_url)

    if success:
        from recordings.models import Recording
        from django.conf import settings
        from pathlib import Path

        output_dir = Path(settings.RECORDINGS_PATH) / f"camera_{camera_id}"
        safe_name = "".join(c for c in camera.name if c.isalnum() or c in "_-")
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"{safe_name}_{timestamp}.mp4"
        output_file = output_dir / filename

        Recording.objects.create(
            camera=camera,
            filename=filename,
            path=str(output_file),
            start_time=timezone.now(),
        )
        logger.info(f"Created Recording record for camera {camera_id}: {filename}")

    return success


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
