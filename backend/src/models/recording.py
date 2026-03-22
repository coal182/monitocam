from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RecordingResponse(BaseModel):
    id: str
    camera_id: int
    camera_name: Optional[str] = None
    filename: str
    path: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    size: Optional[int] = None
    has_gif: bool = False

    class Config:
        from_attributes = True


class RecordingList(BaseModel):
    recordings: list[RecordingResponse]
    total: int
    page: int
    page_size: int


class RecordingFilters(BaseModel):
    camera_id: Optional[int] = None
    date: Optional[str] = None
    page: int = 1
    page_size: int = 50
