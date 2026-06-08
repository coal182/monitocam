# MonitoCam

Sistema de videovigilancia para cámaras IP con grabación continua y previews en GIF.

## Características

- Grabación continua de cámaras IP via RTSP
- Fragmentos de video de 1 hora en formato MP4
- Previews animados en GIF para cada grabación
- Interfaz web Angular 21
- Autenticación JWT con cookies HttpOnly
- Django 5 + Django REST Framework
- Celery para tareas en segundo plano (grabación, GIFs, limpieza)
- PostgreSQL + Redis
- Docker Compose para despliegue
- Nginx como reverse proxy con SSL

## Requisitos

- Docker y Docker Compose

## Instalación

### Desarrollo

```bash
# Copiar variables de entorno
cp .env.example .env

# Iniciar contenedores (dev mode con live reload)
docker compose up -d

# Acceder a la API
http://localhost:8585

# Acceder al frontend
http://localhost:3000
```

### Producción

```bash
# Configurar variables de entorno
cp .env.example .env
# Editar .env con valores seguros

# Iniciar servicios
docker compose up -d

# Para SSL (certbot)
docker compose --profile prod run certbot
```

## Configuración

### Variables de entorno (.env)

```bash
# Database
DB_PASSWORD=postgres

# Auth (hardcoded credentials)
AUTH_USERNAME=admin
AUTH_PASSWORD=admin

# JWT
JWT_SECRET_KEY=change-me-in-production

# Domain (prod only)
# DOMAIN=monitocam.example.com
# CERTBOT_EMAIL=admin@example.com
```

### Configuración

Los valores de grabación están en `backend/config/settings/base.py`:

```python
RECORDINGS_PATH = "/var/lib/monitocam/recordings"
FRAGMENT_DURATION = 3600  # 1 hora
GIF_DURATION = 5          # 5 segundos
GIF_FPS = 5
GIF_SPEED = 4
```

## Arquitectura Docker

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
        │   (DB)     │ │ (broker)│ │ (worker)│
        └───────────┘ └─────────┘ └─────────┘
```

## Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/auth/login/` | POST | Login (JSON: username, password) |
| `/auth/logout/` | POST | Logout |
| `/auth/me/` | GET | Usuario actual |
| `/cameras/` | GET | Listar cámaras |
| `/cameras/` | POST | Crear cámara |
| `/cameras/{id}/` | GET | Obtener cámara |
| `/cameras/{id}/` | DELETE | Eliminar cámara |
| `/cameras/{id}/start/` | POST | Iniciar grabación |
| `/cameras/{id}/stop/` | POST | Detener grabación |
| `/cameras/{id}/status/` | GET | Estado de grabación |
| `/recordings/` | GET | Listar grabaciones |
| `/recordings/{id}/stream/` | GET | Stream MP4 |
| `/recordings/gifs/list/` | GET | Listar GIFs |
| `/recordings/cleanup/{days}/` | DELETE | Eliminar grabaciones mayores a N días |
| `/health/` | GET | Health check |

## Desarrollo

### Backend (Django)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8585
```

### Frontend (Angular)

```bash
cd frontend
npm install
npm run start
```

### Tests

```bash
cd backend
pytest tests/ -v
```

## Estructura del proyecto

```
monitocam/
├── docker-compose.yml          # Servicios Docker
├── docker-compose.override.yml # Dev overrides
├── Dockerfile.backend          # Django app
├── Dockerfile.frontend         # Angular app
├── nginx.conf                  # Reverse proxy
├── .env.example                # Variables de entorno
├── backend/
│   ├── config/                 # Django project
│   │   ├── settings/           # base.py, dev.py, prod.py
│   │   ├── celery.py           # Celery config
│   │   ├── urls.py             # Root URLs
│   │   └── asgi.py             # ASGI (uvicorn)
│   ├── cameras/                # App cámaras
│   │   ├── models.py           # Camera model
│   │   ├── views.py            # CameraViewSet
│   │   ├── serializers.py      # DRF serializers
│   │   ├── tasks.py            # Celery tasks
│   │   ├── signals.py          # Auto-start recording
│   │   └── services/           # RecorderService
│   ├── recordings/             # App grabaciones
│   │   ├── models.py           # Recording model
│   │   ├── views.py            # RecordingViewSet
│   │   ├── serializers.py      # DRF serializers
│   │   ├── tasks.py            # Celery tasks
│   │   └── services/           # GifService
│   ├── accounts/               # Autenticación
│   │   ├── backends.py         # EnvAuthBackend
│   │   ├── authentication.py   # JWTCookieAuthentication
│   │   ├── views.py            # Login, Logout, Me
│   │   └── serializers.py      # Login, User serializers
│   ├── core/                   # Compartido
│   │   └── views.py            # Health check
│   ├── tests/                  # Tests
│   ├── manage.py
│   └── requirements.txt
└── frontend/                   # Angular app
```

## Celery Workers

- **celery-worker**: Tareas de grabación y GIFs
- **celery-beat**: Tareas periódicas (limpieza diaria)

Colas:
- `recordings`: Iniciar/detener grabación
- `media`: Generación de GIFs
- `maintenance`: Limpieza de grabaciones antiguas

## Troubleshooting

### Los contenedores no inician

```bash
docker compose logs api
docker compose logs celery-worker
```

### La base de datos no conecta

```bash
docker compose exec api python manage.py dbshell
```

### Las grabaciones no se inician

```bash
docker compose logs celery-worker
docker compose exec api python manage.py shell -c "from cameras.models import Camera; print(Camera.objects.all())"
```
