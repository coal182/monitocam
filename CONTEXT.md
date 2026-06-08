# MonitoCam — Context

IP camera video surveillance system with continuous recording and animated GIF previews.

## Stack

- **Backend:** Django 5 + Django REST Framework + Celery + PostgreSQL + Redis
- **Frontend:** Angular 21 (TypeScript)
- **Infra:** Docker Compose (6 services) + Nginx reverse proxy
- **Auth:** JWT via HttpOnly cookies, hardcoded credentials from env vars (no database users)
- **Storage:** ffmpeg subprocesses for recording, Redis cache for recording status

## Domain Glossary

| Term | Definition |
|------|------------|
| **Camera** | An IP camera identified by name and RTSP URL. Has `enabled` flag. Stored in PostgreSQL. |
| **Recording** | A video fragment captured from a Camera. One Recording belongs to exactly one Camera. Stored as `.mp4` files on disk, tracked in PostgreSQL. |
| **Fragment** | A single `.mp4` file produced by one ffmpeg session. Duration is configurable (`FRAGMENT_DURATION`, default 600s = 10 minutes). |
| **GIF** | A 5-second animated thumbnail generated from a Recording's MP4. Stored alongside the MP4 with same name but `.gif` extension. |
| **RecorderService** | Singleton that manages ffmpeg subprocesses in the Celery worker process. Tracks active processes in an in-memory dict. |
| **Recording Status** | Redis cache key `recording:{camera_id}` indicating whether a camera is currently recording. Shared between API and Celery worker containers via Redis. |
| **SimpleUser** | A lightweight Python object (not a Django model) representing the authenticated user. Always `id=1`, username from env vars. |
| **Fragment Duration** | Length of each video fragment in seconds. Default: 600 (10 minutes). Configured in `base.py`. |
| **NAS** | Network Attached Storage. Production recordings are stored at `/mnt/nas-pictures/monitocam` on the host, mounted into containers at `/var/lib/monitocam/recordings`. |

## Architecture

```
┌─────────────┐     ┌─────────────┐
│   nginx     │────▶│    api      │
│  :80        │     │  (Django)   │
└─────────────┘     └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌────▼────┐ ┌────▼────┐
        │  postgres  │ │  redis  │ │ celery  │
        │   (DB)     │ │(cache+  │ │ (worker)│
        └───────────┘ │ broker) │ └─────────┘
                      └─────────┘
```

### Services (docker-compose.yml)

| Service | Role | Key Details |
|---------|------|-------------|
| `postgres` | Database | PostgreSQL 16, db=monitocam, user=monitocam |
| `redis` | Cache + Celery broker | Redis 7, appendonly persistence |
| `api` | Django app | Uvicorn ASGI, port 8585, runs migrations on start |
| `celery-worker` | Background tasks | 1 CPU, 1GB RAM, `--concurrency=1 --pool=prefork`, queues: recordings, media, maintenance |
| `celery-beat` | Periodic tasks | DatabaseScheduler, daily cleanup at 86400s |
| `nginx` | Reverse proxy + SPA | Strips `/api/` prefix, serves Angular build |

### Data Flow: Recording Lifecycle

1. User creates Camera via UI → `POST /api/cameras/`
2. If `enabled=True`, `start_recording_task` dispatched to Celery
3. Celery worker: `RecorderService.start_recording()` spawns ffmpeg subprocess
4. ffmpeg writes `.mp4` fragments to `RECORDINGS_PATH/camera_{id}/`
5. `Recording` DB record created with `start_time`, `path`, `filename`
6. Redis key `recording:{id}` set to `"1"` (shared status)
7. API reads Redis to show `"recording"` status in camera list
8. On stop: ffmpeg killed (SIGTERM → SIGKILL), `Recording` updated with `end_time`, `duration`, `size`
9. Redis key deleted

### Data Flow: GIF Generation

1. User views recording → `GET /api/recordings/{id}/get_gif/`
2. If `.gif` doesn't exist, `generate_gif_task` dispatched
3. Celery worker: `GifService.generate_gif()` runs ffmpeg with palette generation
4. GIF saved alongside MP4 (same name, `.gif` extension)
5. `Recording.has_gif = True`

## Key Configuration

| Setting | Value | Location |
|---------|-------|----------|
| `FRAGMENT_DURATION` | `600` (10 min) | `config/settings/base.py` |
| `GIF_DURATION` | `5` (seconds) | `config/settings/base.py` |
| `GIF_FPS` | `5` | `config/settings/base.py` |
| `GIF_SPEED` | `4` (4x playback) | `config/settings/base.py` |
| `RECORDINGS_PATH` | `/var/lib/monitocam/recordings` | `config/settings/base.py` |
| `JWT expiry` | 24 hours | `config/settings/base.py` |
| `AUTH_USERNAME` | env var | `docker-compose.yml` |
| `AUTH_PASSWORD` | env var | `docker-compose.yml` |

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/login/` | POST | No | Login, returns JWT + sets httponly cookie |
| `/auth/logout/` | POST | No | Clears cookie |
| `/auth/me/` | GET | Yes | Returns `{username}` |
| `/cameras/` | GET | Yes | List cameras |
| `/cameras/` | POST | Yes | Create camera |
| `/cameras/{id}/` | GET | Yes | Get camera |
| `/cameras/{id}/` | DELETE | Yes | Delete camera |
| `/cameras/{id}/start/` | POST | Yes | Start recording (Celery task) |
| `/cameras/{id}/stop/` | POST | Yes | Stop recording (Celery task) |
| `/recordings/` | GET | Yes | List recordings (`?camera_id=` filter) |
| `/recordings/{id}/stream/` | GET | Yes | Stream MP4 |
| `/recordings/{id}/get_gif/` | GET | Yes | Get/generate GIF |
| `/recordings/gifs/list/` | GET | Yes | List recordings with GIFs |
| `/recordings/cleanup/{days}/` | DELETE | Yes | Delete recordings older than N days |
| `/health/` | GET | No | Health check |

## Frontend Routes

| Path | Component | Guard |
|------|-----------|-------|
| `/login` | LoginComponent | `publicGuard` (redirects to `/` if logged in) |
| `/` | CamerasComponent | `authGuard` (redirects to `/login` if not) |
| `/recordings` | RecordingsComponent | `authGuard` |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PASSWORD` | Yes | `postgres` | PostgreSQL password |
| `AUTH_USERNAME` | Yes | `admin` | Login username |
| `AUTH_PASSWORD` | Yes | `admin` | Login password |
| `JWT_SECRET_KEY` | Yes | `change-me-in-production` | JWT signing key |
| `REDIS_URL` | No | `redis://redis:6379/0` | Redis connection URL |
| `DATABASE_URL` | No | — | PostgreSQL connection URL |
| `RECORDINGS_PATH` | No | `/var/lib/monitocam/recordings` | Where MP4 files are stored |
| `STATIC_ROOT` | No | `/var/lib/monitocam/staticfiles` | Django static files |
| `DJANGO_SETTINGS_MODULE` | No | `config.settings.dev` | Settings module |

## File Structure

```
monitocam/
├── docker-compose.yml          # 6 services: postgres, redis, api, celery-worker, celery-beat, nginx
├── docker-compose.override.yml # Dev: live reload, debug logs, local volume mounts
├── Dockerfile.backend          # Python 3.12-slim + ffmpeg, UID 1001
├── Dockerfile.frontend         # Node 22 build → Nginx serve (multi-stage)
├── nginx.conf                  # Reverse proxy: /api/ → api:8585, / → Angular SPA
├── .env.example                # Required env vars template
├── backend/
│   ├── manage.py
│   ├── entrypoint.sh           # Wait DB → migrate → collectstatic → exec CMD
│   ├── requirements.txt        # Django, DRF, Celery, Redis, psycopg2, pytest
│   ├── pytest.ini              # DJANGO_SETTINGS_MODULE=config.settings.dev
│   ├── config/
│   │   ├── __init__.py         # Exports celery_app
│   │   ├── celery.py           # Celery app, beat schedule, task routes, worker_ready signal
│   │   ├── urls.py             # Root URLconf: admin, health, auth, cameras, recordings
│   │   ├── asgi.py / wsgi.py
│   │   └── settings/
│   │       ├── base.py         # Core config, DRF, JWT, CACHES (Redis), logging
│   │       ├── dev.py          # DEBUG=True, PostgreSQL via DATABASE_URL or SQLite fallback
│   │       └── prod.py         # DEBUG=False, PostgreSQL, security headers
│   ├── accounts/               # Auth app (NOT named "auth" — Django conflict)
│   │   ├── backends.py         # EnvAuthBackend: authenticate against env vars
│   │   ├── authentication.py   # JWTCookieAuthentication: cookie + Bearer header
│   │   ├── views.py            # LoginView, LogoutView, MeView
│   │   ├── serializers.py      # LoginSerializer, UserSerializer
│   │   └── urls.py             # login/, logout/, me/
│   ├── cameras/
│   │   ├── models.py           # Camera(name, rtsp_url, enabled, created_at)
│   │   ├── views.py            # CameraViewSet: CRUD + status/start/stop actions
│   │   ├── serializers.py      # CameraSerializer (with computed status), Create/Update
│   │   ├── tasks.py            # start_recording_task, stop_recording_task
│   │   ├── signals.py          # post_save → auto-start, pre_delete → auto-stop
│   │   └── services/
│   │       ├── recorder.py     # RecorderService: ffmpeg subprocess management
│   │       └── recording_status.py  # Redis cache: set/is_recording/clear_all
│   ├── recordings/
│   │   ├── models.py           # Recording(camera FK, filename, path, start/end_time, duration, size, has_gif)
│   │   ├── views.py            # RecordingViewSet: list + stream/get_gif/gifs_list/cleanup
│   │   ├── serializers.py      # RecordingSerializer (with camera_name)
│   │   ├── tasks.py            # generate_gif_task, cleanup_old_recordings_task
│   │   └── services/
│   │       └── giffer.py       # GifService: ffmpeg GIF generation with palette
│   ├── core/
│   │   └── views.py            # health_check: DB connectivity test
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py        # 5 tests: login, invalid creds, me auth/unauth, logout
│       ├── test_cameras.py     # 7 tests: CRUD, invalid URL, 404, unauthorized
│       └── test_recordings.py  # 2 tests: list, unauthorized
└── frontend/
    ├── src/
    │   ├── main.ts             # Bootstrap with router, httpClient, AuthService
    │   └── app/
    │       ├── app.routes.ts   # /login, /, /recordings
    │       ├── app.component.ts
    │       ├── models/
    │       │   ├── camera.model.ts
    │       │   └── recording.model.ts
    │       ├── services/
    │       │   └── api.service.ts      # All HTTP calls, base URL /api
    │       ├── core/
    │       │   ├── auth.service.ts     # Signals-based auth state
    │       │   ├── auth.guard.ts       # authGuard, publicGuard
    │       │   └── auth.interceptor.ts # withCredentials: true
    │       └── features/
    │           ├── auth/login.component.ts
    │           ├── cameras/cameras.component.ts
    │           └── recordings/recordings.component.ts
```

## Key Design Decisions

1. **No database users** — Auth is env-var based (`AUTH_USERNAME`/`AUTH_PASSWORD`). `SimpleUser(id=1)` is a lightweight stand-in for Django's User model. JWT tokens carry `user_id=1` and `username`.

2. **Redis for cross-container state** — Recording status is stored in Redis (not in-memory) because the API and Celery worker run in separate containers. `RecorderService._processes` is per-worker-instance, but `recording_status` is shared via Redis.

3. **Stale status cleanup** — On Celery worker startup, a `worker_ready` signal clears all `recording:*` keys from Redis to prevent false "recording" status after restarts.

4. **Single ffmpeg per camera** — `--concurrency=1 --pool=prefork` ensures only one recording task runs at a time. `RecorderService._processes` prevents duplicate recordings for the same camera.

5. **Fragment-based recording** — ffmpeg writes 10-minute fragments (`-t 600`). Each fragment creates a separate `Recording` record. The `-movflags +frag_keyframe+empty_moov+default_base_moof` flags enable progressive MP4 (streamable before download completes).

6. **UID 1001** — Docker container runs as UID 1001 to match the host user `cristian_martin`. This avoids permission issues on the shared recordings volume.

7. **Nginx strips `/api/` prefix** — `proxy_pass http://api:8585/` (trailing slash) strips the `/api/` prefix. Frontend calls `/api/cameras/` → Django sees `/cameras/`.

8. **Trailing slashes required** — Django `APPEND_SLASH=True` (default). Frontend uses trailing slashes on all API calls. POST requests without trailing slash would 500.

## Running

```bash
# Development
cp .env.example .env
docker compose up -d
# Frontend: http://localhost:80
# API direct: http://localhost:8585

# Production
cp .env.example .env
# Edit .env with real secrets
docker compose up -d
# For SSL: docker compose --profile prod run certbot
```

## Tests

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npx ng test
```

## Git Conventions

- **Author:** Cristian Martín <coal182@gmail.com>
- **Commits per task**, no auto-push
- **Main branch** only (no feature branches currently)
