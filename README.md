# MonitoCam

Sistema de videovigilancia para camaras IP con grabacion continua y previews en GIF.

## Caracteristicas

- Grabacion continua de camaras IP via RTSP
- Fragmentos de video de 1 hora en formato MP4
- Previews animados en GIF para cada grabacion
- Interfaz web para visualizacion y gestion
- Autenticacion con usuarios del sistema
- Almacenamiento configurable (SD o NAS)

## Requisitos

- Python 3.10+
- FFmpeg
- Node.js 18+ (para desarrollo frontend)

## Instalacion

### Backend

```bash
cd monitocam/backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Frontend

```bash
cd monitocam/frontend
npm install
```

## Configuracion

Editar `backend/config.yaml`:

```yaml
app:
  host: "0.0.0.0"
  port: 8585

storage:
  base_path: "/var/lib/monitocam/recordings"
  nas_path: "/mnt/nas"
  use_nas: false

recording:
  fragment_duration: 3600
  gif_duration: 5
  gif_fps: 5

jwt:
  secret_key: "change-this-in-production"
  algorithm: "HS256"
  expire_minutes: 1440
```

## Uso

### Desarrollo

Backend:
```bash
cd backend
uvicorn monitocam.src.main:app --reload --port 8585
```

Frontend:
```bash
cd frontend
npm run dev
```

### Produccion

```bash
# Crear directorio de almacenamiento
sudo mkdir -p /var/lib/monitocam/recordings
sudo chown $USER:$USER /var/lib/monitocam/recordings

# Ejecutar
uvicorn monitocam.src.main:app --host 0.0.0.0 --port 8585
```

## API

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/auth/login` | POST | Login (form data: username, password) |
| `/auth/me` | GET | Usuario actual |
| `/cameras` | GET | Listar camaras |
| `/cameras` | POST | Crear camara |
| `/cameras/{id}` | DELETE | Eliminar camara |
| `/cameras/{id}/start` | POST | Iniciar grabacion |
| `/cameras/{id}/stop` | POST | Detener grabacion |
| `/recordings` | GET | Listar grabaciones |
| `/recordings/{id}/download` | GET | Descargar MP4 |
| `/recordings/{id}/gif` | GET | Preview GIF |

## Tests

```bash
cd backend
pytest tests/ -v
```

## Estructura del proyecto

```
monitocam/
├── backend/
│   ├── src/
│   │   ├── main.py           # App FastAPI
│   │   ├── config.py         # Configuracion
│   │   ├── api/              # Rutas API
│   │   ├── core/             # Auth y seguridad
│   │   ├── models/           # Modelos Pydantic
│   │   ├── services/        # Recorder y Giffer
│   │   └── db/               # Base de datos
│   └── tests/                # Tests
└── frontend/
    ├── src/
    │   ├── views/            # Vistas Vue
    │   ├── stores/           # Pinia stores
    │   └── api/              # Cliente API
    └── package.json
```
