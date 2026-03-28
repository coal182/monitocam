import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path as PathParam
from fastapi.responses import FileResponse

from models.recording import RecordingResponse, RecordingList
from db.database import get_db, Camera
from core.security import get_current_user
from config import get_settings
from services.giffer import gif_service


settings = get_settings()
router = APIRouter(prefix="/recordings", tags=["recordings"])


def _stem_id(file_path: str) -> str:
    p = Path(file_path)
    stem = p.stem.replace(".gif", "").replace(".mp4", "")
    return str(abs(hash(stem)))


def get_recordings_from_files(
    camera_id: Optional[int] = None, date: Optional[str] = None
):
    recordings = []
    base_path = Path(settings.storage.recordings_path)

    if not base_path.exists():
        return recordings

    for camera_dir in base_path.iterdir():
        if camera_dir.is_dir():
            try:
                cam_id = int(camera_dir.name.replace("camera_", ""))
            except ValueError:
                continue
            if camera_id and cam_id != camera_id:
                continue

            for video_file in camera_dir.glob("*.mp4"):
                file_date = video_file.stem.split("_")[-2]
                if date and file_date != date:
                    continue

                stat = video_file.stat()
                recordings.append(
                    {
                        "id": _stem_id(str(video_file)),
                        "camera_id": cam_id,
                        "filename": video_file.name,
                        "path": str(video_file),
                        "start_time": file_date,
                        "duration": settings.recording.fragment_duration,
                        "size": stat.st_size,
                        "has_gif": gif_service.gif_exists(str(video_file)),
                    }
                )

    return recordings


@router.get("", response_model=List[RecordingResponse])
async def list_recordings(
    camera_id: Optional[int] = Query(None),
    date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    all_recordings = get_recordings_from_files(camera_id, date)
    camera_names = {c.id: c.name for c in db.query(Camera).all()}

    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_recordings[start:end]

    result = []
    for rec in paginated:
        cam_name = camera_names.get(rec["camera_id"], "Unknown")
        result.append(
            RecordingResponse(
                id=rec["id"],
                camera_id=rec["camera_id"],
                camera_name=cam_name,
                filename=rec["filename"],
                path=rec["path"],
                start_time=rec["start_time"],
                duration=rec["duration"],
                size=rec["size"],
                has_gif=rec["has_gif"],
            )
        )

    return result


@router.get("/gifs/list")
async def list_gifs(
    camera_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    gifs = []
    base_path = Path(settings.storage.recordings_path)

    if not base_path.exists():
        return gifs

    for camera_dir in base_path.iterdir():
        if camera_dir.is_dir():
            try:
                cam_id = int(camera_dir.name.replace("camera_", ""))
            except ValueError:
                continue
            if camera_id and cam_id != camera_id:
                continue

            for gif_file in sorted(
                camera_dir.glob("*.gif"), key=lambda x: x.stat().st_mtime, reverse=True
            ):
                stat = gif_file.stat()
                parts = gif_file.stem.rsplit("_", 1)
                if len(parts) == 2:
                    date_str = parts[0].split("_")[-1]
                    time_str = parts[1].replace("-", ":")
                    timestamp_str = f"{date_str} {time_str}"
                else:
                    timestamp_str = gif_file.stem.replace("_", " ")

                gifs.append(
                    {
                        "id": _stem_id(str(gif_file)),
                        "camera_id": cam_id,
                        "filename": gif_file.name,
                        "path": str(gif_file),
                        "timestamp": timestamp_str,
                        "size": stat.st_size,
                    }
                )

    camera_names = {c.id: c.name for c in db.query(Camera).all()}

    for gif in gifs:
        gif["camera_name"] = camera_names.get(gif["camera_id"], "Unknown")

    return gifs


@router.get("/gifs/{gif_id}/file")
async def get_gif_file(
    gif_id: str,
    current_user: dict = Depends(get_current_user),
):
    base_path = Path(settings.storage.recordings_path)

    for camera_dir in base_path.iterdir():
        if camera_dir.is_dir():
            for gif_file in camera_dir.glob("*.gif"):
                if _stem_id(str(gif_file)) == gif_id:
                    return FileResponse(path=str(gif_file), media_type="image/gif")

    raise HTTPException(status_code=404, detail="GIF not found")


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(
    recording_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    recordings = get_recordings_from_files()
    recording = next((r for r in recordings if r["id"] == recording_id), None)

    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    camera = db.query(Camera).filter(Camera.id == recording["camera_id"]).first()

    return RecordingResponse(
        id=recording["id"],
        camera_id=recording["camera_id"],
        camera_name=camera.name if camera else "Unknown",
        filename=recording["filename"],
        path=recording["path"],
        start_time=recording["start_time"],
        duration=recording["duration"],
        size=recording["size"],
        has_gif=recording["has_gif"],
    )


@router.delete("/{recording_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recording(
    recording_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    recordings = get_recordings_from_files()
    recording = next((r for r in recordings if r["id"] == recording_id), None)

    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    video_path = Path(recording["path"])
    if video_path.exists():
        video_path.unlink()

    gif_path = gif_service.get_gif_path(str(video_path))
    gif_file = Path(gif_path)
    if gif_file.exists():
        gif_file.unlink()


@router.delete("/cleanup/{days}", status_code=status.HTTP_204_NO_CONTENT)
async def cleanup_old_recordings(
    days: int = PathParam(..., ge=1, description="Delete recordings older than N days"),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cutoff_date = datetime.now() - timedelta(days=days)
    base_path = Path(settings.storage.recordings_path)

    if not base_path.exists():
        return

    deleted_count = 0
    for camera_dir in base_path.iterdir():
        if not camera_dir.is_dir():
            continue

        for video_file in camera_dir.glob("*.mp4"):
            if video_file.name.endswith(".tmp"):
                continue

            file_mtime = datetime.fromtimestamp(video_file.stat().st_mtime)

            if file_mtime < cutoff_date:
                video_path = Path(video_file)
                if video_path.exists():
                    video_path.unlink()
                    deleted_count += 1

                gif_path = gif_service.get_gif_path(str(video_file))
                gif_file = Path(gif_path)
                if gif_file.exists():
                    gif_file.unlink()

    print(f"Deleted {deleted_count} recordings older than {days} days")


@router.get("/{recording_id}/gif")
async def get_recording_gif(
    recording_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    recordings = get_recordings_from_files()
    recording = next((r for r in recordings if r["id"] == recording_id), None)

    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    video_path = recording["path"]
    gif_path = gif_service.get_gif_path(video_path)

    if not gif_service.gif_exists(video_path):
        gif_service.generate_gif(
            video_path,
            gif_path,
            duration=settings.recording.gif_duration,
            fps=settings.recording.gif_fps,
            speed=settings.recording.gif_speed,
        )

    gif_file = Path(gif_path)
    if not gif_file.exists():
        raise HTTPException(status_code=500, detail="Failed to generate GIF")

    return FileResponse(path=str(gif_file), media_type="image/gif")


@router.get("/{recording_id}/stream")
async def stream_recording(
    recording_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    recordings = get_recordings_from_files()
    recording = next((r for r in recordings if r["id"] == recording_id), None)

    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    video_path = Path(recording["path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=str(video_path), media_type="video/mp4")
