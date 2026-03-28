# MonitoCam

Sistema de videovigilancia para cámaras IP con grabación continua y previews en GIF.

## Características

- Grabación continua de cámaras IP via RTSP
- Fragmentos de video de 30 minutos en formato MP4
- Previews animados en GIF para cada grabación
- Interfaz web Angular 21
- Autenticación con usuarios del sistema (PAM)
- Docker Compose para despliegue
- Almacenamiento configurable

## Requisitos

- Docker y Docker Compose
- Node.js 22+ (para desarrollo frontend)
- Python 3.11+ (para desarrollo backend)

## Instalación

### Producción con Docker

```bash
# Crear directorio de grabaciones
mkdir -p ~/monitocam_recordings

# Iniciar contenedores
docker compose up -d
```

### Desarrollo

Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8585
```

Frontend:
```bash
cd frontend
npm install
npm run start
```

## Configuración

Editar `backend/config.yaml`:

```yaml
app:
  host: "0.0.0.0"
  port: 8585

storage:
  base_path: "/recordings"  # Ruta dentro del contenedor

recording:
  fragment_duration: 1800  # 30 minutos
  gif_duration: 900        # 15 segundos
  gif_fps: 12
  gif_speed: 30            # Velocidad de reproducción

jwt:
  secret_key: "change-this-in-production"
  algorithm: "HS256"
  expire_minutes: 1440
```

## Docker

El volumen de grabaciones mapea el directorio del host:
- Host: `~/monitocam_recordings`
- Contenedor: `/recordings`

### Servicio systemd

Para ejecutar como servicio del sistema:

```bash
# Copiar servicio
sudo cp monitocam.service /etc/systemd/system/

# Recargar
sudo systemctl daemon-reload

# Habilitar e iniciar
sudo systemctl enable monitocam
sudo systemctl start monitocam
```

## Uso

Acceder a `http://localhost`

- Usuario: `admin`
- Contraseña: `admin`

### Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/auth/login` | POST | Login (form data: username, password) |
| `/auth/me` | GET | Usuario actual |
| `/cameras` | GET | Listar cámaras |
| `/cameras` | POST | Crear cámara |
| `/cameras/{id}` | DELETE | Eliminar cámara |
| `/cameras/{id}/start` | POST | Iniciar grabación |
| `/cameras/{id}/stop` | POST | Detener grabación |
| `/recordings` | GET | Listar grabaciones |
| `/recordings/cleanup/{days}` | DELETE | Eliminar grabaciones mayores a N días |
| `/recordings/{id}/download` | GET | Descargar MP4 |
| `/recordings/{id}/gif` | GET | Preview GIF |
| `/recordings/gifs/list` | GET | Listar GIFs |

## Tests

Backend:
```bash
cd backend
pytest tests/ -v
```

Frontend:
```bash
cd frontend
npm test
```

## Estructura del proyecto

```
monitocam/
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── monitocam.service
├── backend/
│   ├── src/
│   │   ├── main.py           # App FastAPI
│   │   ├── config.py         # Configuración
│   │   ├── api/              # Rutas API
│   │   ├── core/             # Auth y seguridad
│   │   ├── models/           # Modelos Pydantic
│   │   ├── services/         # Recorder y Giffer
│   │   └── db/               # Base de datos
│   ├── tests/                # Tests
│   └── config.yaml
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── core/         # Auth, guards, interceptors
    │   │   ├── features/     # Componentes (auth, cameras, recordings)
    │   │   ├── models/       # Interfaces TypeScript
    │   │   └── services/     # API service
    │   └── styles.css
    ├── angular.json
    └── package.json
```
