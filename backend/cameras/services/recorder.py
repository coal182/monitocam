import subprocess
import os
import signal
import logging
import tempfile
from pathlib import Path
from datetime import datetime

from django.conf import settings

from cameras.services.recording_status import set_recording as redis_set_recording

logger = logging.getLogger(__name__)


class RecorderService:
    def __init__(self):
        self._processes: dict[int, subprocess.Popen] = {}
        self._stderr_files: dict[int, tempfile.NamedTemporaryFile] = {}

    def start_recording(self, camera_id: int, camera_name: str, rtsp_url: str) -> bool:
        if camera_id in self._processes:
            logger.warning(f"Camera {camera_id} already recording")
            return False

        output_dir = Path(settings.RECORDINGS_PATH) / f"camera_{camera_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c for c in camera_name if c.isalnum() or c in "_-")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        output_file = output_dir / f"{safe_name}_{timestamp}.mp4"

        stderr_file = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
        self._stderr_files[camera_id] = stderr_file

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
                stderr=stderr_file,
                preexec_fn=os.setsid,
            )
            self._processes[camera_id] = process
            redis_set_recording(camera_id, True)
            logger.info(f"Started recording camera {camera_id}: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording camera {camera_id}: {e}")
            return False

    def get_ffmpeg_error(self, camera_id: int) -> str:
        stderr_file = self._stderr_files.pop(camera_id, None)
        if stderr_file:
            try:
                stderr_file.seek(0)
                error = stderr_file.read()[-2000:]
                os.unlink(stderr_file.name)
                return error
            except Exception:
                pass
        return ""

    def stop_recording(self, camera_id: int) -> bool:
        if camera_id not in self._processes:
            redis_set_recording(camera_id, False)
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
            self.get_ffmpeg_error(camera_id)
            redis_set_recording(camera_id, False)
            logger.info(f"Stopped recording camera {camera_id}")
        return True

    def is_recording(self, camera_id: int) -> bool:
        from cameras.services.recording_status import is_recording as redis_is_recording
        return redis_is_recording(camera_id)

    def stop_all(self):
        for camera_id in list(self._processes.keys()):
            self.stop_recording(camera_id)


recorder_service = RecorderService()
