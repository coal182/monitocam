import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from cameras.models import Camera
from cameras.tasks import start_recording_task, stop_recording_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Camera)
def camera_post_save(sender, instance, created, **kwargs):
    if instance.enabled:
        logger.info(f"Camera {instance.id} enabled, starting recording")
        start_recording_task.delay(instance.id)
    else:
        logger.info(f"Camera {instance.id} disabled, stopping recording")
        stop_recording_task.delay(instance.id)


@receiver(pre_delete, sender=Camera)
def camera_pre_delete(sender, instance, **kwargs):
    logger.info(f"Camera {instance.id} being deleted, stopping recording")
    stop_recording_task.delay(instance.id)
