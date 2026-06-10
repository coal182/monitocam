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
# Backend (from host — no Docker needed)
cd backend && python -m pytest tests/ -v

# Frontend (from host — no Docker needed)
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

94 tests total: 48 backend + 46 frontend.

## Key Files

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Full glossary, architecture, data flows, API docs |
| `backend/config/settings/base.py` | Core Django settings (RECORDINGS_PATH, FRAGMENT_DURATION, GIF_TARGET_DURATION, TIME_ZONE) |
| `backend/cameras/services/recorder.py` | ffmpeg process management (RecorderService) |
| `backend/cameras/services/recording_status.py` | Redis cache + pub/sub for recording status (shared between containers) |
| `backend/cameras/tasks.py` | Refactored task helpers: _get_and_validate_camera, _create_recording, _wait_for_ffmpeg, _finalize_recording, _generate_gif, _chain_next_recording |
| `backend/config/celery.py` | Celery config, task routes, beat schedule |
| `backend/accounts/` | Auth app (NOT "auth" — Django conflict) |
| `frontend/src/app/services/sse.service.ts` | EventSource SSE with auto-reconnect, statuses signal |
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
- **Python imports inside functions** — Django convention for avoiding circular imports
- **Underscore prefix** for private helper functions (`_get_and_validate_camera`, etc.)

## Testing Conventions

- **Autouse fixtures** in `conftest.py` mock Celery `.delay()` calls and Redis cache — no local Redis/Celery needed
- **`pytest-django`** provides Django test fixtures (`client`, `db`, `auth_client`)
- **`AUTH_USERNAME`/`AUTH_PASSWORD`** forced to `"testuser"`/`"testpass"` in conftest.py if not set
- **Frontend tests** use `HttpClientTestingModule` with `HttpTestingController` — always flush requests after `detectChanges()`
- **`await fixture.whenStable()`** needed after flushing async HTTP in component tests

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
4. Mock `.delay()` in `conftest.py` autouse fixture if task is dispatched from signals/views

### Add a new endpoint
1. Create view in `{app}/views.py`
2. Add URL pattern in `{app}/urls.py` (trailing slash required)
3. Add route in `config/urls.py` if new app
4. Frontend: add method in `api.service.ts` with trailing slash
5. Add test in `tests/test_{app}.py`

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

### Run tests locally (no Docker)
```bash
cd backend && python -m pytest tests/ -v
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless
```
