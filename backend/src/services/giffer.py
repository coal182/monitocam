import subprocess
import logging
from pathlib import Path
from typing import Optional

from config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)


class GifService:
    def generate_gif(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        duration: int = 5,
        fps: int = 5,
        speed: int = 4,
    ) -> Optional[str]:
        if not Path(video_path).exists():
            logger.error(f"Video file not found: {video_path}")
            return None

        if output_path is None:
            output_path = str(Path(video_path).with_suffix(".gif"))

        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-filter:v",
            f"setpts=PTS/{speed},fps={fps},scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-t",
            str(duration),
            "-loop",
            "0",
            output_path,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=duration + 30
            )
            if result.returncode == 0:
                logger.info(f"Generated GIF: {output_path} ({speed}x speed)")
                return output_path
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("GIF generation timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to generate GIF: {e}")
            return None

    def gif_exists(self, video_path: str) -> bool:
        gif_path = str(Path(video_path).with_suffix(".gif"))
        return Path(gif_path).exists()

    def get_gif_path(self, video_path: str) -> str:
        return str(Path(video_path).with_suffix(".gif"))


gif_service = GifService()
