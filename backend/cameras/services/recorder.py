import subprocess
import os
import signal
import logging
from pathlib import Path
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)


class RecorderService:
    def __init__(self):
        self._processes: dict[int, subprocess.Popen] = {}

    def start_recording(self, camera_id: int, camera_name: str, rtsp_url: str) -> bool:
        if camera_id in self._processes:
            logger.warning(f"Camera {camera_id} already recording")
            return False

        output_dir = Path(settings.RECORDINGS_PATH) / f"camera_{camera_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c for c in camera_name if c.isalnum() or c in "_-")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        output_file = output_dir / f"{safe_name}_{timestamp}.mp4"

        cmd = [
            "ffmpeg",
            "-rtsp_transport", "udp",
            "-i", rtsp_url,
            "-c:v", "copy",
            "-an",
            "-f", "mp4",
            "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
            "-t", str(settings.FRAGMENT_DURATION),
            str(output_file),
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            self._processes[camera_id] = process
            logger.info(f"Started recording camera {camera_id}: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording camera {camera_id}: {e}")
            return False

    def stop_recording(self, camera_id: int) -> bool:
        if camera_id not in self._processes:
            return False

        process = self._processes[camera_id]
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except Exception as e:
            logger.error(f"Error stopping recording camera {camera_id}: {e}")
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except Exception:
                pass
        finally:
            del self._processes[camera_id]
            logger.info(f"Stopped recording camera {camera_id}")
        return True

    def is_recording(self, camera_id: int) -> bool:
        return camera_id in self._processes

    def stop_all(self):
        for camera_id in list(self._processes.keys()):
            self.stop_recording(camera_id)


recorder_service = RecorderService()
