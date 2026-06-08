import logging

from celery import shared_task

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

    return recorder_service.start_recording(camera.id, camera.name, camera.rtsp_url)


@shared_task(queue="recordings")
def stop_recording_task(camera_id: int):
    from cameras.services.recorder import recorder_service

    return recorder_service.stop_recording(camera_id)
