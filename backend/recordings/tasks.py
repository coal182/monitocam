import logging
from datetime import timedelta
from pathlib import Path

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(queue="media")
def generate_gif_task(recording_id: int):
    from recordings.models import Recording
    from recordings.services.giffer import gif_service
    from django.conf import settings

    try:
        recording = Recording.objects.get(id=recording_id)
    except Recording.DoesNotExist:
        logger.error(f"Recording {recording_id} not found")
        return False

    video_path = recording.path
    gif_path = gif_service.get_gif_path(video_path)

    if gif_service.gif_exists(video_path):
        logger.info(f"GIF already exists for recording {recording_id}")
        return True

    result = gif_service.generate_gif(
        video_path,
        gif_path,
        video_duration=recording.duration or settings.FRAGMENT_DURATION,
        gif_target_duration=settings.GIF_TARGET_DURATION,
        fps=settings.GIF_FPS,
    )

    if result:
        recording.has_gif = True
        recording.save(update_fields=["has_gif"])
        return True

    return False


@shared_task(queue="maintenance")
def cleanup_old_recordings_task(days: int = 30):
    from recordings.models import Recording

    cutoff_date = timezone.now() - timedelta(days=days)
    recordings = Recording.objects.filter(created_at__lt=cutoff_date)

    deleted_count = 0
    for recording in recordings:
        file_path = Path(recording.path)
        if file_path.exists():
            import os

            os.remove(file_path)

        gif_path = file_path.with_suffix(".gif")
        if gif_path.exists():
            import os

            os.remove(gif_path)

        recording.delete()
        deleted_count += 1

    logger.info(f"Cleaned up {deleted_count} recordings older than {days} days")
    return deleted_count
