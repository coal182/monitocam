import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, cameras, recordings
from config import get_settings
from services.recorder import recorder_service
from db.database import SessionLocal, Camera


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MonitoCam application")

    db = SessionLocal()
    try:
        cameras = db.query(Camera).filter(Camera.enabled == True).all()
        for cam in cameras:
            recorder_service.start_recording(cam.id, cam.name, cam.rtsp_url)
            logger.info(f"Auto-started recording for camera: {cam.name}")
    finally:
        db.close()

    yield
    logger.info("Shutting down MonitoCam application")
    recorder_service.stop_all()


app = FastAPI(
    title="MonitoCam",
    description="IP Camera Recording System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(recordings.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "monitocam"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
