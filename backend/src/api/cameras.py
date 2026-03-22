from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from models.camera import CameraCreate, CameraUpdate, CameraResponse, CameraStatus
from db.database import get_db, Camera
from core.security import get_current_user
from services.recorder import recorder_service


router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    current_user: dict = Depends(get_current_user), db=Depends(get_db)
):
    cameras = db.query(Camera).all()
    result = []
    for cam in cameras:
        is_recording = recorder_service.is_recording(cam.id)
        status_str = (
            "recording" if is_recording else ("stopped" if cam.enabled else "disabled")
        )
        result.append(
            CameraResponse(
                id=cam.id,
                name=cam.name,
                rtsp_url=cam.rtsp_url,
                enabled=cam.enabled,
                status=status_str,
                created_at=cam.created_at.isoformat() if cam.created_at else None,
            )
        )
    return result


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    camera = Camera(
        name=camera_data.name,
        rtsp_url=camera_data.rtsp_url,
        enabled=camera_data.enabled,
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)

    if camera.enabled:
        recorder_service.start_recording(camera.id, camera.name, camera.rtsp_url)

    return CameraResponse(
        id=camera.id,
        name=camera.name,
        rtsp_url=camera.rtsp_url,
        enabled=camera.enabled,
        status="recording" if camera.enabled else "stopped",
        created_at=camera.created_at.isoformat() if camera.created_at else None,
    )


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    is_recording = recorder_service.is_recording(camera.id)
    status_str = (
        "recording" if is_recording else ("stopped" if camera.enabled else "disabled")
    )

    return CameraResponse(
        id=camera.id,
        name=camera.name,
        rtsp_url=camera.rtsp_url,
        enabled=camera.enabled,
        status=status_str,
        created_at=camera.created_at.isoformat() if camera.created_at else None,
    )


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    recorder_service.stop_recording(camera_id)
    db.delete(camera)
    db.commit()


@router.get("/{camera_id}/status", response_model=CameraStatus)
async def get_camera_status(
    camera_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    is_recording = recorder_service.is_recording(camera.id)

    return CameraStatus(
        id=camera.id,
        name=camera.name,
        status="recording" if is_recording else "stopped",
        is_recording=is_recording,
        last_recording=None,
    )


@router.post("/{camera_id}/start")
async def start_recording(
    camera_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    success = recorder_service.start_recording(camera.id, camera.name, camera.rtsp_url)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start recording")

    return {"status": "recording", "camera_id": camera_id}


@router.post("/{camera_id}/stop")
async def stop_recording(
    camera_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)
):
    success = recorder_service.stop_recording(camera_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop recording")

    return {"status": "stopped", "camera_id": camera_id}
