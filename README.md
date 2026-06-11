# MonitoCam

IP camera video surveillance system with continuous recording and animated GIF previews.

## Features

- Continuous recording of IP cameras via RTSP
- 30-minute video fragments in MP4 format
- Animated GIF timelapse previews for each recording
- Real-time recording status via Server-Sent Events (SSE)
- Angular 21 web interface
- JWT authentication with HttpOnly cookies
- Django 5 + Django REST Framework
- Celery for background tasks (recording, GIFs, cleanup)
- PostgreSQL + Redis
- Docker Compose deployment
- Nginx reverse proxy
- Configurable timezone (default: Europe/Madrid)

## Requirements

- Docker and Docker Compose

## Installation

### Development

```bash
cp .env.example .env
docker compose up -d

# API direct: http://localhost:8585
# Frontend: http://localhost:80
# Health: http://localhost/health/
```

### Production

```bash
cp .env.example .env
# Edit .env with secure values
docker compose up -d
# For SSL: docker compose --profile prod run certbot
```

## Configuration

### Environment Variables (.env)

```bash
DB_PASSWORD=postgres
AUTH_USERNAME=admin
AUTH_PASSWORD=admin
JWT_SECRET_KEY=change-me-in-production
# TIME_ZONE=Europe/Madrid
```

### Recording Settings

`backend/config/settings/base.py`:

```python
RECORDINGS_PATH = "/var/lib/monitocam/recordings"
FRAGMENT_DURATION = 1800  # 30 minutes
GIF_TARGET_DURATION = 30  # speed auto-calculated
GIF_FPS = 24
TIME_ZONE = "Europe/Madrid"
```

## Docker Architecture

```
┌─────────────┐     ┌─────────────┐
│   nginx     │────▶│    api      │
│  (proxy)    │     │  (Django)   │
└─────────────┘     └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌────▼────┐ ┌────▼────┐
        │  postgres  │ │  redis  │ │ celery  │
        │   (DB)     │ │(broker+ │ │ (worker)│
        └───────────┘ │ pub/sub)│ └─────────┘
                      └─────────┘
```

| Service | Role | Details |
|---------|------|---------|
| `postgres` | Database | PostgreSQL 16 |
| `redis` | Cache + broker + pub/sub | Redis 7 |
| `api` | Django app | Uvicorn ASGI, port 8585 |
| `celery-worker` | Background tasks | `--concurrency=2 --pool=prefork` |
| `celery-beat` | Periodic tasks | Daily cleanup |
| `nginx` | Reverse proxy + SPA | Strips `/api/` prefix, SSE support |

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/login/` | POST | No | Login |
| `/auth/logout/` | POST | No | Logout |
| `/auth/me/` | GET | Yes | Current user |
| `/cameras/` | GET/POST | Yes | List/create cameras |
| `/cameras/{id}/` | GET/DELETE | Yes | Get/delete camera |
| `/cameras/{id}/start/` | POST | Yes | Start recording |
| `/cameras/{id}/stop/` | POST | Yes | Stop recording |
| `/cameras/{id}/status/` | GET | Yes | Recording status |
| `/cameras/statuses/` | GET | Yes | All cameras status |
| `/cameras/events/` | GET | No | SSE real-time status |
| `/recordings/` | GET | Yes | List recordings |
| `/recordings/{id}/` | DELETE | Yes | Delete recording + files |
| `/recordings/{id}/stream/` | GET | Yes | Stream MP4 |
| `/recordings/{id}/download/` | GET | Yes | Download MP4 |
| `/recordings/{id}/get_gif/` | GET | Yes | Get/generate GIF |
| `/recordings/gifs/{id}/file/` | GET | Yes | Serve GIF |
| `/recordings/gifs/list/` | GET | Yes | List GIFs |
| `/recordings/cleanup/{days}/` | DELETE | Yes | Cleanup (0 = all) |
| `/health/` | GET | No | Health check |

## Tests

```bash
# Backend (no Docker needed)
cd backend && python -m pytest tests/ -v

# Frontend (no Docker needed)
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless

# From Docker
docker compose exec api python -m pytest tests/ -v
```

94 tests: 48 backend + 46 frontend.

## Celery

- **celery-worker**: Recording + GIF tasks (`--concurrency=2`)
- **celery-beat**: Daily cleanup

Queues: `recordings`, `media`, `maintenance`

### Continuous Recording Chain

Fragment finishes → GIF generated → next fragment starts automatically.
On failure: 30s retry delay → next attempt.

## Troubleshooting

```bash
docker compose logs celery-worker | grep -i "record\|ffmpeg\|error"
docker compose exec redis redis-cli FLUSHDB  # Reset statuses
```
