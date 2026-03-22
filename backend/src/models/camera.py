from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class CameraCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rtsp_url: str
    enabled: bool = True

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp_url(cls, v: str) -> str:
        if not v.startswith("rtsp://"):
            raise ValueError("URL must start with rtsp://")
        return v


class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rtsp_url: Optional[str] = None
    enabled: Optional[bool] = None

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith("rtsp://"):
            raise ValueError("URL must start with rtsp://")
        return v


class CameraResponse(BaseModel):
    id: int
    name: str
    rtsp_url: str
    enabled: bool
    status: str = "stopped"
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class CameraStatus(BaseModel):
    id: int
    name: str
    status: str
    is_recording: bool
    last_recording: Optional[str] = None
