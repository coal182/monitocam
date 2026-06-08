import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("monitocam")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cleanup-old-recordings-daily": {
        "task": "recordings.tasks.cleanup_old_recordings_task",
        "schedule": 86400.0,
        "args": (30,),
    },
}

app.conf.task_routes = {
    "cameras.tasks.*": {"queue": "recordings"},
    "recordings.tasks.generate_gif_task": {"queue": "media"},
    "recordings.tasks.cleanup_old_recordings_task": {"queue": "maintenance"},
}
