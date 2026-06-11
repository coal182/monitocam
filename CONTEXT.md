# MonitoCam — Context

IP camera video surveillance system with continuous recording and animated GIF previews.

## Stack

- **Backend:** Django 5 + Django REST Framework + Celery + PostgreSQL + Redis
- **Frontend:** Angular 21 (TypeScript)
- **Infra:** Docker Compose (6 services) + Nginx reverse proxy
- **Auth:** JWT via HttpOnly cookies, hardcoded credentials from env vars (no database users)
- **Storage:** ffmpeg subprocesses for recording, Redis cache for recording status, SSE for real-time updates

## Domain Glossary

| Term | Definition |
|------|------------|
| **Camera** | An IP camera identified by name and RTSP URL. Has `enabled` flag. Stored in PostgreSQL. |
| **Recording** | A video fragment captured from a Camera. One Recording belongs to exactly one Camera. Stored as `.mp4` files on disk, tracked in PostgreSQL. |
| **Fragment** | A single `.mp4` file produced by one ffmpeg session. Duration is configurable (`FRAGMENT_DURATION`, default 1800s = 30 minutes). |
| **GIF** | An animated timelapse thumbnail generated from a Recording's MP4. Duration is configurable (`GIF_TARGET_DURATION`, default 30s). Speed is auto-calculated as `video_duration / gif_target_duration`. Stored alongside the MP4 with same name but `.gif` extension. |
| **RecorderService** | Singleton that manages ffmpeg subprocesses in the Celery worker process. Tracks active processes in an in-memory dict. |
| **Recording Status** | Redis cache key `recording:{camera_id}` indicating whether a camera is currently recording. Shared between API and Celery worker containers via Redis. Published via Redis pub/sub for SSE. |
| **SimpleUser** | A lightweight Python object (not a Django model) representing the authenticated user. Always `id=1`, username from env vars. |
| **Fragment Duration** | Length of each video fragment in seconds. Default: 1800 (30 minutes). Configured in `base.py`. |
| **NAS** | Network Attached Storage. Production recordings are stored at `/mnt/nas-pictures/monitocam` on the host, mounted into containers at `/var/lib/monitocam/recordings`. |
| **SSE** | Server-Sent Events. Unidirectional real-time status updates from server to frontend via `EventSource`. Uses Redis pub/sub to broadcast recording status changes. |
| **Continuous Recording** | After a fragment finishes, the next one starts automatically via Celery task chaining. No gap between fragments. |

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
                      │ + pub/sub│
                      └─────────┘
```

### Services (docker-compose.yml)

| Service | Role | Key Details |
|---------|------|-------------|
| `postgres` | Database | PostgreSQL 16, db=monitocam, user=monitocam |
| `redis` | Cache + Celery broker + pub/sub | Redis 7, appendonly persistence |
| `api` | Django app | Uvicorn ASGI, port 8585, runs migrations on start |
| `celery-worker` | Background tasks | 1 CPU, 1GB RAM, `--concurrency=2 --pool=prefork`, queues: recordings, media, maintenance |
| `celery-beat` | Periodic tasks | DatabaseScheduler, daily cleanup at 86400s |
| `nginx` | Reverse proxy + SPA | Strips `/api/` prefix, serves Angular build, `proxy_buffering off` for SSE |

### Data Flow: Recording Lifecycle (Continuous Chain)

1. User creates Camera via UI → `POST /api/cameras/`
2. If `enabled=True`, `start_recording_task` dispatched to Celery (via `post_save` signal)
3. Celery worker: `_get_and_validate_camera()` → `_create_recording()` → `RecorderService.start_recording()` spawns ffmpeg subprocess
4. `_wait_for_ffmpeg()` blocks until ffmpeg finishes (timeout: `FRAGMENT_DURATION + 300s`)
5. On success: `_finalize_recording()` updates Recording record (`end_time`, `duration`, `size`), then `_generate_gif()` creates GIF synchronously
6. `_chain_next_recording()` auto-starts next fragment if camera is still enabled
7. On failure (returncode != 0): Recording deleted from DB, 30s retry delay, then next attempt
8. Redis key `recording:{id}` set/deleted via `set_recording()` (published via Redis pub/sub)

### Data Flow: GIF Generation

1. On-demand: User views recording → `GET /api/recordings/{id}/get_gif/`
2. If `.gif` doesn't exist, `generate_gif_task` dispatched to Celery (media queue)
3. In recording chain: GIF generated synchronously after ffmpeg finishes (not via Celery task, to avoid deadlock with concurrency=1)
4. Celery worker / inline: `GifService.generate_gif()` runs ffmpeg with palette generation
5. Speed auto-calculated: `speed = video_duration / gif_target_duration`
6. GIF saved alongside MP4 (same name, `.gif` extension)
7. `Recording.has_gif = True`

### Data Flow: SSE Real-Time Status

1. Frontend connects to `GET /cameras/events/` via `EventSource`
2. Nginx proxies to Django with `proxy_buffering off`
3. Django view streams from Redis pub/sub channel `cameras:status`
4. On recording start/stop: `set_recording()` publishes status change to Redis pub/sub
5. `SseService` in frontend receives events, updates `statuses` signal
6. `CamerasComponent` reads `statuses()` for real-time recording indicators

## Key Configuration

| Setting | Value | Location |
|---------|-------|----------|
| `FRAGMENT_DURATION` | `1800` (30 min) | `config/settings/base.py` |
| `GIF_TARGET_DURATION` | `30` (seconds) | `config/settings/base.py` |
| `GIF_FPS` | `24` | `config/settings/base.py` |
| `RECORDINGS_PATH` | `/var/lib/monitocam/recordings` | `config/settings/base.py` |
| `TIME_ZONE` | `Europe/Madrid` (configurable via env var) | `config/settings/base.py` |
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
| `/cameras/{id}/status/` | GET | Yes | Get recording status for one camera |
| `/cameras/statuses/` | GET | Yes | Get recording status for all cameras |
| `/cameras/events/` | GET | No | SSE stream for real-time status updates |
| `/recordings/` | GET | Yes | List recordings (`?camera_id=` filter) |
| `/recordings/{id}/` | DELETE | Yes | Delete recording + files from disk |
| `/recordings/{id}/stream/` | GET | Yes | Stream MP4 |
| `/recordings/{id}/download/` | GET | Yes | Download MP4 as attachment |
| `/recordings/{id}/get_gif/` | GET | Yes | Get/generate GIF |
| `/recordings/gifs/{id}/file/` | GET | Yes | Serve GIF file |
| `/recordings/gifs/list/` | GET | Yes | List recordings with GIFs (`?camera_id=` filter) |
| `/recordings/cleanup/{days}/` | DELETE | Yes | Delete recordings older than N days (0 = all) |
| `/health/` | GET | No | Health check |

## Frontend Routes

| Path | Component | Guard |
|------|-----------|-------|
| `/login` | LoginComponent | `publicGuard` (redirects to `/` if logged in) |
| `/` | CamerasComponent | `authGuard` (redirects to `/login` if not) |
| `/recordings` | RecordingsComponent | `authGuard` |

## Frontend Services

| Service | Purpose |
|---------|---------|
| `ApiService` | All HTTP calls, base URL `/api`, trailing slashes on all URLs |
| `AuthService` | Signals-based auth state, login/logout/checkAuth |
| `SseService` | EventSource SSE with auto-reconnect, `statuses` signal for real-time camera status |

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
| `TIME_ZONE` | No | `Europe/Madrid` | Django timezone (affects filename timestamps) |
| `STATIC_ROOT` | No | `/var/lib/monitocam/staticfiles` | Django static files |
| `DJANGO_SETTINGS_MODULE` | No | `config.settings.dev` | Settings module |

## File Structure

```
monitocam/
├── docker-compose.yml          # 6 services: postgres, redis, api, celery-worker, celery-beat, nginx
├── docker-compose.override.yml # Dev: live reload, debug logs, local volume mounts
├── Dockerfile.backend          # Python 3.12-slim + ffmpeg, UID 1001
├── Dockerfile.frontend         # Node 22 build → Nginx serve (multi-stage)
├── nginx.conf                  # Reverse proxy: /api/ → api:8585, / → Angular SPA, SSE support
├── .env.example                # Required env vars template
├── backend/
│   ├── manage.py
│   ├── entrypoint.sh           # Wait DB → migrate → collectstatic → exec CMD
│   ├── requirements.txt        # Django, DRF, Celery, Redis, psycopg2, pytest, pytest-django
│   ├── pytest.ini              # DJANGO_SETTINGS_MODULE=config.settings.dev
│   ├── config/
│   │   ├── __init__.py         # Exports celery_app
│   │   ├── celery.py           # Celery app, beat schedule, task routes, worker_ready signal
│   │   ├── urls.py             # Root URLconf: admin, health, auth, cameras, recordings
│   │   ├── asgi.py / wsgi.py
│   │   └── settings/
│   │       ├── base.py         # Core config, DRF, JWT, CACHES (Redis), TIME_ZONE, GIF_TARGET_DURATION
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
│   │   ├── views.py            # CameraViewSet: CRUD + status/statuses/start/stop/events actions
│   │   ├── serializers.py      # CameraSerializer (with computed status), Create/Update
│   │   ├── tasks.py            # Refactored: _get_and_validate_camera, _create_recording, _wait_for_ffmpeg, _finalize_recording, _generate_gif, _chain_next_recording, start_recording_task, stop_recording_task
│   │   ├── signals.py          # post_save → auto-start, pre_delete → auto-stop
│   │   └── services/
│   │       ├── recorder.py     # RecorderService: ffmpeg subprocess management, stderr capture
│   │       └── recording_status.py  # Redis cache + pub/sub: set/is_recording/clear_all/publish/subscribe
│   ├── recordings/
│   │   ├── models.py           # Recording(camera FK, filename, path, start/end_time, duration, size, has_gif, created_at)
│   │   ├── views.py            # RecordingViewSet: list + stream + download + destroy + get_gif + gif_file + gifs_list + cleanup
│   │   ├── serializers.py      # RecordingSerializer (with camera_name, timestamp)
│   │   ├── tasks.py            # generate_gif_task, cleanup_old_recordings_task
│   │   └── services/
│   │       └── giffer.py       # GifService: ffmpeg GIF generation with dynamic speed, timeout scaling
│   ├── core/
│   │   └── views.py            # health_check: DB connectivity test
│   └── tests/
│       ├── conftest.py         # Fixtures + autouse mocks for Celery tasks and Redis cache
│       ├── test_auth.py        # 5 tests: login, invalid creds, me auth/unauth, logout
│       ├── test_cameras.py     # 13 tests: CRUD, invalid URL, 404, unauthorized, start/stop/status/statuses/SSE
│       ├── test_recordings.py  # 17 tests: list, download, stream, destroy, cleanup, GIF endpoints
│       ├── test_tasks.py       # 8 tests: _get_and_validate_camera, _create_recording, _finalize_recording, _generate_gif
│       └── test_recording_status.py  # 5 tests: set/clear/is_recording, publish, get_all
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
    │       │   ├── api.service.ts      # All HTTP calls, base URL /api, trailing slashes
    │       │   ├── api.service.spec.ts # 16 tests: cameras, recordings, auth, URL helpers
    │       │   ├── sse.service.ts      # EventSource SSE with auto-reconnect, statuses signal
    │       │   └── sse.service.spec.ts # 7 tests: connect, disconnect, message handling, listeners
    │       ├── core/
    │       │   ├── auth.service.ts     # Signals-based auth state
    │       │   ├── auth.guard.ts       # authGuard, publicGuard
    │       │   └── auth.interceptor.ts # withCredentials: true
    │       └── features/
    │           ├── auth/login.component.ts
    │           ├── cameras/
    │           │   ├── cameras.component.ts
    │           │   └── cameras.component.spec.ts  # 5 tests: create, load, SSE, toggle
    │           └── recordings/
    │               ├── recordings.component.ts
    │               └── recordings.component.spec.ts  # 7 tests: header, refresh, format helpers
```

## Key Design Decisions

1. **No database users** — Auth is env-var based (`AUTH_USERNAME`/`AUTH_PASSWORD`). `SimpleUser(id=1)` is a lightweight stand-in for Django's User model. JWT tokens carry `user_id=1` and `username`.

2. **Redis for cross-container state** — Recording status is stored in Redis (not in-memory) because the API and Celery worker run in separate containers. `RecorderService._processes` is per-worker-instance, but `recording_status` is shared via Redis.

3. **Stale status cleanup** — On Celery worker startup, a `worker_ready` signal clears all `recording:*` keys from Redis to prevent false "recording" status after restarts.

4. **Continuous recording chain** — After a fragment finishes, `_chain_next_recording()` auto-starts the next one. On failure, 30s retry delay before next attempt. GIF generated synchronously (not via Celery) to avoid deadlock with `concurrency=2`.

5. **Fragment-based recording** — ffmpeg writes 30-minute fragments (`-t 1800`). Each fragment creates a separate `Recording` record. The `-movflags +frag_keyframe+empty_moov+default_base_moof` flags enable progressive MP4 (streamable before download completes).

6. **Dynamic GIF speed** — `speed = video_duration / gif_target_duration` instead of fixed 4x. Entire recording captured as timelapse. Timeout scales with video length (`video_duration / speed + 60`).

7. **SSE over WebSockets** — Unidirectional status updates don't need bidirectional communication. SSE is simpler, no `django-channels` needed. Uses Redis pub/sub for broadcasting.

8. **UID 1001** — Docker container runs as UID 1001 to match the host user `cristian_martin`. This avoids permission issues on the shared recordings volume.

9. **Nginx strips `/api/` prefix** — `proxy_pass http://api:8585/` (trailing slash) strips the `/api/` prefix. Frontend calls `/api/cameras/` → Django sees `/cameras/`.

10. **Trailing slashes required** — Django `APPEND_SLASH=True` (default). Frontend uses trailing slashes on all API calls. POST requests without trailing slash would 500.

11. **Configurable timezone** — `TIME_ZONE` env var with `Europe/Madrid` default. `USE_TZ=True` keeps DB in UTC, `timezone.localtime()` for display. Filenames use local time.

12. **Testing without infrastructure** — Tests mock Celery `.delay()` calls and Redis cache via autouse fixtures. `pytest-django` provides Django test fixtures (`client`, `db`, `auth_client`). No Redis or Celery needed to run tests locally.

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
# Backend (from host — no Docker needed)
cd backend && python -m pytest tests/ -v

# Frontend (from host — no Docker needed)
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless

# Backend (from Docker)
docker compose exec api python -m pytest tests/ -v
```

94 tests total: 48 backend + 46 frontend.

## Git Conventions

- **Author:** Cristian Martín <coal182@gmail.com>
- **Commits per task**, no auto-push
- **Main branch** only (no feature branches currently)
