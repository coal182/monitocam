import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

RECORDING_KEY_PREFIX = "recording:"


def set_recording(camera_id: int, is_recording: bool):
    key = f"{RECORDING_KEY_PREFIX}{camera_id}"
    if is_recording:
        cache.set(key, "1", timeout=None)
    else:
        cache.delete(key)
    logger.debug(f"Set recording status for camera {camera_id}: {is_recording}")


def is_recording(camera_id: int) -> bool:
    key = f"{RECORDING_KEY_PREFIX}{camera_id}"
    return cache.get(key) is not None


def clear_all():
    from django.core.cache import cache

    keys_to_delete = []
    for i in range(1, 100):
        key = f"{RECORDING_KEY_PREFIX}{i}"
        if cache.get(key) is not None:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        cache.delete(key)

    if keys_to_delete:
        logger.info(f"Cleared {len(keys_to_delete)} stale recording statuses from Redis")
