import json
import logging
import threading

from django.core.cache import cache
from redis import Redis

logger = logging.getLogger(__name__)

RECORDING_KEY_PREFIX = "recording:"
SSE_CHANNEL = "cameras:status"

_redis_client = None
_subscribers = []
_lock = threading.Lock()


def _get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        from django.conf import settings
        redis_url = settings.CACHES["default"]["LOCATION"]
        _redis_client = Redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def set_recording(camera_id: int, is_recording: bool):
    key = f"{RECORDING_KEY_PREFIX}{camera_id}"
    if is_recording:
        cache.set(key, "1", timeout=None)
    else:
        cache.delete(key)

    _publish_status(camera_id, is_recording)
    logger.debug(f"Set recording status for camera {camera_id}: {is_recording}")


def _publish_status(camera_id: int, is_recording: bool):
    try:
        client = _get_redis_client()
        message = json.dumps({"camera_id": camera_id, "is_recording": is_recording})
        client.publish(SSE_CHANNEL, message)
    except Exception as e:
        logger.error(f"Failed to publish status change: {e}")


def subscribe_status(callback):
    def _listener():
        try:
            client = _get_redis_client()
            pubsub = client.pubsub()
            pubsub.subscribe(SSE_CHANNEL)
            for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    callback(data)
        except Exception as e:
            logger.error(f"SSE listener error: {e}")

    thread = threading.Thread(target=_listener, daemon=True)
    thread.start()
    return thread


def is_recording(camera_id: int) -> bool:
    key = f"{RECORDING_KEY_PREFIX}{camera_id}"
    return cache.get(key) is not None


def get_all_statuses() -> dict:
    statuses = {}
    for i in range(1, 100):
        key = f"{RECORDING_KEY_PREFIX}{i}"
        if cache.get(key) is not None:
            statuses[i] = True
    return statuses


def clear_all():
    keys_to_delete = []
    for i in range(1, 100):
        key = f"{RECORDING_KEY_PREFIX}{i}"
        if cache.get(key) is not None:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        cache.delete(key)

    if keys_to_delete:
        logger.info(f"Cleared {len(keys_to_delete)} stale recording statuses from Redis")
