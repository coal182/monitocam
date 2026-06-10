import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GifService:
    def generate_gif(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        video_duration: int = 0,
        gif_target_duration: int = 30,
        fps: int = 5,
    ) -> Optional[str]:
        if not Path(video_path).exists():
            logger.error(f"Video file not found: {video_path}")
            return None

        if output_path is None:
            output_path = str(Path(video_path).with_suffix(".gif"))

        if video_duration <= 0:
            logger.error(f"Invalid video duration: {video_duration}")
            return None

        speed = max(1, int(video_duration / gif_target_duration))
        timeout = max(180, video_duration // 5) + 120

        logger.info(f"Generating GIF: speed={speed}x, timeout={timeout}s, input={video_duration}s")

        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-filter:v",
            f"setpts=PTS/{speed},fps={fps},scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop",
            "0",
            output_path,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode == 0:
                logger.info(f"Generated GIF: {output_path} ({speed}x speed)")
                return output_path
            else:
                logger.error(f"FFmpeg error: {result.stderr[-1000:]}")
                return None
        except subprocess.TimeoutExpired:
            logger.error(f"GIF generation timed out after {timeout}s")
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
