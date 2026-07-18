# Technical Map — MonitoCam Backend

## Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | **Django 5** + Django REST Framework |
| ASGI Server | **Uvicorn** (2 workers) |
| Task Queue | **Celery 5** (prefork, concurrency=2) |
| Broker / Cache | **Redis 7** (appendonly) |
| Database | **PostgreSQL 16** (db: `monitocam`) |
| Auth | **JWT** (SimpleJWT) + HttpOnly cookies |
| Video Processing | **ffmpeg** (subprocess) |

---

## Directory Structure

```
backend/
├── config/               # Global configuration
│   ├── settings/         # base.py / dev.py / prod.py
│   ├── celery.py         # Celery app, routes, beat schedule
│   ├── urls.py           # Root URLconf
│   ├── asgi.py / wsgi.py
│   └── __init__.py       # Exports celery_app
├── accounts/             # Authentication (NOT "auth")
│   ├── backends.py       # EnvAuthBackend + SimpleUser
│   ├── authentication.py # JWTCookieAuthentication
│   ├── views.py          # Login / Logout / Me
│   └── serializers.py
├── cameras/              # Camera management
│   ├── models.py         # Camera (name, rtsp_url, enabled)
│   ├── views.py          # CRUD + status/statuses/start/stop/events
│   ├── tasks.py          # Continuous recording chain
│   ├── signals.py        # post_save → auto-start, pre_delete → auto-stop
│   └── services/
│       ├── recorder.py   # RecorderService (ffmpeg subprocess)
│       └── recording_status.py  # Redis cache + pub/sub + SSE
├── recordings/           # Recording management
│   ├── models.py         # Recording (camera FK, path, duration...)
│   ├── views.py          # CRUD + stream/download/gif/cleanup
│   ├── tasks.py          # generate_gif_task, cleanup_old_recordings
│   └── services/
│       └── giffer.py     # GifService (ffmpeg palettegen)
├── core/
│   └── views.py          # health_check
└── tests/                # 48 tests (pytest)
    ├── conftest.py       # Fixtures + auto mocks
    ├── test_auth.py      # 5 tests
    ├── test_cameras.py   # 13 tests
    ├── test_recordings.py # 17 tests
    ├── test_tasks.py     # 8 tests
    └── test_recording_status.py # 5 tests
```

---

## Container Architecture

```
┌─────────────┐     ┌─────────────────┐
│   nginx     │────▶│    api (uvicorn)│
│  :80        │     │  Django + DRF   │
└─────────────┘     └────────┬────────┘
                             │
                ┌────────────┼─────────────┐
                │            │             │
          ┌─────▼─────┐ ┌───▼─────┐ ┌─────▼──────────┐
          │ postgres   │ │  redis  │ │ celery-worker  │
          │ (DB)       │ │(cache   │ │ (2 CPUs, 1GB)  │
          └───────────┘ │ +broker) │ └────────────────┘
                        │ +pub/sub │
                        └─────────┘
                             ▲
                        ┌────┴────┐
                        │ celery- │
                        │  beat   │
                        └─────────┘
                            (daily cleanup)
```

### Celery Queues

| Queue | Purpose |
|-------|---------|
| `recordings` | Recording tasks (start/stop) |
| `media` | On-demand GIF generation |
| `maintenance` | Periodic cleanup of old recordings |

---

## Data Models

### Camera

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | PK |
| `name` | CharField(100) | Descriptive name |
| `rtsp_url` | CharField(500) | Camera RTSP URL |
| `enabled` | BooleanField | Whether active (default `True`) |
| `created_at` | DateTimeField | Creation date (auto) |

### Recording

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | PK |
| `camera` | ForeignKey → Camera | N:1 relationship |
| `filename` | CharField(255) | MP4 filename |
| `path` | CharField(500) | Full disk path |
| `start_time` | DateTimeField | Recording start |
| `end_time` | DateTimeField | Recording end |
| `duration` | IntegerField | Duration in seconds |
| `size` | IntegerField | Size in bytes |
| `has_gif` | BooleanField | Whether GIF was generated |
| `created_at` | DateTimeField | Creation date (auto) |

---

## Data Flow: Recording Lifecycle

```
POST /cameras/ (enabled=true)
        │
        ▼
  post_save signal
        │
        ▼
  start_recording_task.delay(id) ────▶ Celery (queue: recordings)
        │
        ▼
  _get_and_validate_camera(id)
        │
        ├── Camera.DoesNotExist → return
        ├── !camera.enabled → return
        │
        ▼
  RecorderService.start_recording()
        │  └── spawns ffmpeg:
        │        -rtsp_transport udp -i <rtsp_url>
        │        -c:v copy -an -t <FRAGMENT_DURATION>
        │        -movflags +frag_keyframe+empty_moov+default_base_moof
        │
        ▼
  _create_recording() → Recording in DB
        │
        ▼
  _wait_for_ffmpeg() → blocks until ffmpeg finishes
        │                timeout: FRAGMENT_DURATION + 300s
        │
        ├── returncode == 0 → _finalize_recording()
        │                       ├── Updates end_time, duration, size
        │                       └── _generate_gif() (sync, same worker)
        │
        └── returncode != 0 → recording.delete()
                                └── 30s retry delay
        │
        ▼
  _chain_next_recording()
        │
        ├── camera.enabled → start_recording_task.delay (infinite loop)
        └── !enabled → stop
```

---

## Data Flow: SSE (Real-Time)

```
Frontend (EventSource) ───GET /cameras/events/───▶ Nginx
                                                      │
                                              proxy_buffering off
                                                      │
                                                      ▼
                                              Django StreamingHttpResponse
                                                      │
                                              subscribe_status(callback)
                                                      │
                                              Redis pub/sub "cameras:status"
                                                      ▲
                                                      │
                                              set_recording(camera_id, bool)
                                              (called by RecorderService)
```

---

## API Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/health/` | GET | No | Health check (+ DB) |
| `/auth/login/` | POST | No | Login → JWT + cookie |
| `/auth/logout/` | POST | No | Clear cookie |
| `/auth/me/` | GET | Yes | `{username}` |
| `/cameras/` | GET | Yes | List cameras |
| `/cameras/` | POST | Yes | Create camera |
| `/cameras/{id}/` | GET | Yes | Camera detail |
| `/cameras/{id}/` | DELETE | Yes | Delete camera |
| `/cameras/{id}/start/` | POST | Yes | Start recording |
| `/cameras/{id}/stop/` | POST | Yes | Stop recording |
| `/cameras/{id}/status/` | GET | Yes | Individual status |
| `/cameras/statuses/` | GET | Yes | All statuses |
| `/cameras/events/` | GET | No | SSE streaming |
| `/recordings/` | GET | Yes | List (`?camera_id=` filter) |
| `/recordings/{id}/` | DELETE | Yes | Delete + disk files |
| `/recordings/{id}/stream/` | GET | Yes | Stream MP4 |
| `/recordings/{id}/download/` | GET | Yes | Download MP4 |
| `/recordings/{id}/get_gif/` | GET | Yes | Get/generate GIF |
| `/recordings/gifs/list/` | GET | Yes | List recordings with GIF |
| `/recordings/gifs/{id}/file/` | GET | Yes | Serve GIF file |
| `/recordings/cleanup/{days}/` | DELETE | Yes | Bulk cleanup |

---

## Security

- **Auth:** No database users. Fixed credentials via `AUTH_USERNAME` / `AUTH_PASSWORD` env vars.
- **JWT:** Signed with `JWT_SECRET_KEY`, 24h expiry, carried in HttpOnly cookie (`SameSite=Lax`, `Secure` in prod).
- **SimpleUser:** Lightweight Python object (`id=1`, `username` from env var) replacing Django's User model.
- **Auth backend:** `EnvAuthBackend` — authenticates against environment variables, no DB query.
- **Permissions:** `IsAuthenticated` default in DRF. Only login, logout, SSE, and health are public.
- **Nginx:** Reverse proxy hiding `api:8585`, only exposes port 80.

---

## Key Configuration

| Variable / Constant | Default | Where defined |
|---------------------|---------|---------------|
| `FRAGMENT_DURATION` | 1800s (30 min) | `config/settings/base.py` |
| `GIF_TARGET_DURATION` | 30s | `config/settings/base.py` |
| `GIF_FPS` | 5 | `config/settings/base.py` |
| `RECORDINGS_PATH` | `/var/lib/monitocam/recordings` | env var / `base.py` |
| `TIME_ZONE` | `Europe/Madrid` | env var / `base.py` |
| `REDIS_URL` | `redis://redis:6379/0` | env var / `dev.py` / `prod.py` |
| `DATABASE_URL` | — | env var / `dev.py` / `prod.py` |
| `JWT expiry` | 24h | `base.py` (`SIMPLE_JWT`) |
| `AUTH_USERNAME` | — | env var (required) |
| `AUTH_PASSWORD` | — | env var (required) |

---

## Design Decisions

1. **Redis as cross-container bridge** — API and Celery worker run in separate containers. Recording status is shared via Redis cache (`recording:{camera_id}`) + pub/sub for SSE.

2. **Continuous recording by chaining** — `_chain_next_recording()` automatically starts the next fragment. No gaps between fragments. On failure, retries after 30s.

3. **Synchronous GIF** — Generated in the same recording worker (not as a separate Celery task) to avoid deadlock with `concurrency=2`.

4. **SSE over WebSockets** — Unidirectional, simpler than WebSockets. No `django-channels` needed. Redis pub/sub for broadcast.

5. **Progressive MP4 fragments** — `-movflags +frag_keyframe+empty_moov+default_base_moof` allows streaming of MP4 before the file is fully written.

6. **Dynamic GIF speed** — `speed = video_duration / gif_target_duration`. Timelapse of the entire fragment duration. Timeout scales: `video_duration / speed + 120`.

7. **Nginx strips `/api/`** — `proxy_pass http://api:8585/` (trailing slash) makes `/api/cameras/` reach Django as `/cameras/`.

8. **Tests without infrastructure** — Auto mocks for Celery `.delay()` and Redis cache in `conftest.py`. No Redis or Celery needed to run tests locally.

9. **Stale status cleanup** — On worker startup, `worker_ready` signal clears all `recording:*` keys from Redis to prevent false states after restarts.

10. **UID 1001** — Container runs as UID 1001 to match the host user, avoiding permission issues on the shared recordings volume.

---

## Testing (48 tests)

| File | Tests | What it covers |
|------|-------|----------------|
| `test_auth.py` | 5 | Login, invalid credentials, auth, logout |
| `test_cameras.py` | 13 | CRUD, invalid URL, 404, unauth, start/stop/status/SSE |
| `test_recordings.py` | 17 | List, download, stream, delete, cleanup, GIF endpoints |
| `test_tasks.py` | 8 | Internal recording pipeline helpers |
| `test_recording_status.py` | 5 | Redis cache: set/clear/is_recording, publish, get_all |

```bash
cd backend && python -m pytest tests/ -v
```

---

## Key System Files

| File | Role |
|------|------|
| `backend/config/settings/base.py` | Central config (DRF, JWT, Redis, constants) |
| `backend/config/celery.py` | Celery app, task routes, beat schedule, worker_ready |
| `backend/cameras/tasks.py` | Complete recording pipeline (6 helpers + 2 tasks) |
| `backend/cameras/services/recorder.py` | `RecorderService`: ffmpeg process management |
| `backend/cameras/services/recording_status.py` | Redis cache + pub/sub for shared state |
| `backend/recordings/services/giffer.py` | `GifService`: GIF generation with ffmpeg |
| `backend/tests/conftest.py` | Global fixtures + auto mocks (Redis, Celery) |
| `docker-compose.yml` | 6 service definitions |
| `nginx.conf` | Reverse proxy, `/api/` stripping, SSE no buffering |
