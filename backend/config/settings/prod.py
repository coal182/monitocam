from urllib.parse import urlparse

from .base import *  # noqa: F401, F403

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-change-me-in-production")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# Parse DATABASE_URL: postgresql://user:pass@host:port/dbname
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    url = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": url.path[1:],  # strip leading /
            "USER": url.username or "monitocam",
            "PASSWORD": url.password or "",
            "HOST": url.hostname or "postgres",
            "PORT": str(url.port or 5432),
            "CONN_MAX_AGE": 30,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "monitocam"),
            "USER": os.environ.get("POSTGRES_USER", "monitocam"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "postgres"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": 30,
        }
    }

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
