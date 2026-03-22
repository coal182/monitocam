import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8585
    debug: bool = False


class StorageConfig(BaseModel):
    base_path: str = "/var/lib/monitocam/recordings"
    nas_path: str = "/mnt/nas"
    use_nas: bool = False

    @property
    def recordings_path(self) -> str:
        if self.use_nas and os.path.exists(self.nas_path):
            return self.nas_path
        return self.base_path


class RecordingConfig(BaseModel):
    fragment_duration: int = 3600
    gif_duration: int = 5
    gif_fps: int = 5
    gif_speed: int = 4


class JWTConfig(BaseModel):
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    expire_minutes: int = 1440


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    storage: StorageConfig = StorageConfig()
    recording: RecordingConfig = RecordingConfig()
    jwt: JWTConfig = JWTConfig()

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "Settings":
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                config_data = yaml.safe_load(f)
            return cls(**config_data)
        return cls()


def get_settings() -> Settings:
    return Settings.from_yaml()
