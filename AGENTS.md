# AGENTS.md — MonitoCam

## Quick Start

Read `CONTEXT.md` for full project context, glossary, architecture, and file structure.

## Tech Stack

- **Backend:** Django 5 + DRF + Celery + PostgreSQL + Redis
- **Frontend:** Angular 21 (TypeScript)
- **Infra:** Docker Compose (6 services) + Nginx

## Running

```bash
docker compose up -d          # Start all services
docker compose logs api       # Check API logs
docker compose logs celery-worker  # Check worker logs
```

- Frontend: `http://localhost:80`
- API direct: `http://localhost:8585`
- Health: `http://localhost/health/`

## Testing

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npx ng test
```

## Key Files

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Full glossary, architecture, data flows, API docs |
| `backend/config/settings/base.py` | Core Django settings (RECORDINGS_PATH, FRAGMENT_DURATION, GIF_*) |
| `backend/cameras/services/recorder.py` | ffmpeg process management (RecorderService) |
| `backend/cameras/services/recording_status.py` | Redis-based recording status (shared between containers) |
| `backend/config/celery.py` | Celery config, task routes, beat schedule |
| `backend/accounts/` | Auth app (NOT "auth" — Django conflict) |
| `docker-compose.yml` | Production services |
| `docker-compose.override.yml` | Dev overrides (live reload, debug) |

## Conventions

- **Author:** Cristian Martín <coal182@gmail.com>
- **Commits per task**, no auto-push
- **Main branch** only
- **Trailing slashes required** on all API URLs (Django `APPEND_SLASH=True`)
- **App name is `accounts`**, not `auth` (Django conflict with `django.contrib.auth`)
- **Recording status is in Redis**, not in-memory — API and Celery worker are separate containers
- **UID 1001** in Dockerfile matches host user for volume permissions

## Common Tasks

### Add a new Django app
1. Create `backend/{app_name}/` with models, views, serializers, urls, apps.py
2. Add to `INSTALLED_APPS` in `config/settings/base.py`
3. Add URL pattern in `config/urls.py`
4. Run `python manage.py makemigrations && python manage.py migrate`

### Add a new Celery task
1. Create task in `{app}/tasks.py` with `@shared_task(queue="...")`
2. Add route in `config/celery.py` → `app.conf.task_routes`
3. Available queues: `recordings`, `media`, `maintenance`

### Debug recording issues
```bash
docker compose logs celery-worker | grep -i "record\|ffmpeg\|error"
docker compose exec api python manage.py shell -c "from cameras.models import Camera; print(Camera.objects.all())"
```

### Reset Redis recording statuses
Happens automatically on celery-worker restart (worker_ready signal). Manual:
```bash
docker compose exec redis redis-cli FLUSHDB
```
