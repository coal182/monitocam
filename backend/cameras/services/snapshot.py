import subprocess
import os
import signal
import time
import logging
import threading
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


class SnapshotService:
    def __init__(self):
        self._processes: dict[int, subprocess.Popen] = {}
        self._lock = threading.Lock()
        self._running: dict[int, bool] = {}

    def start_snapshot(self, camera_id: int, rtsp_url: str) -> bool:
        with self._lock:
            if camera_id in self._processes:
                logger.warning(f"Snapshot already running for camera {camera_id}")
                return False
            self._running[camera_id] = True

        output_dir = Path(settings.RECORDINGS_PATH) / f"camera_{camera_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "snapshot.jpg"

        cmd = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-timeout", "3000000",
            "-i", rtsp_url,
            "-vf", "fps=1/2",
            "-q:v", "5",
            "-update", "1",
            "-atomic_writing", "1",
            "-y",
            str(output_file),
        ]

        def _run_loop():
            backoff = 1
            while self._running.get(camera_id, False):
                try:
                    proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setsid,
                    )
                    with self._lock:
                        self._processes[camera_id] = proc
                    proc.wait()
                    logger.info(
                        f"Snapshot ffmpeg for camera {camera_id} "
                        f"exited with code {proc.returncode}"
                    )
                except Exception as e:
                    logger.error(
                        f"Snapshot ffmpeg error for camera {camera_id}: {e}"
                    )

                with self._lock:
                    self._processes.pop(camera_id, None)

                if not self._running.get(camera_id, False):
                    break

                logger.info(
                    f"Restarting snapshot for camera {camera_id} "
                    f"in {backoff}s..."
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)

        thread = threading.Thread(target=_run_loop, daemon=True)
        thread.start()
        logger.info(f"Started snapshot daemon for camera {camera_id}")
        return True

    def stop_snapshot(self, camera_id: int) -> bool:
        with self._lock:
            self._running[camera_id] = False
            proc = self._processes.pop(camera_id, None)
            if not proc:
                logger.info(
                    f"No snapshot process to stop for camera {camera_id}"
                )
                return False

        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
        except Exception as e:
            logger.error(
                f"Error stopping snapshot for camera {camera_id}: {e}"
            )
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass

        logger.info(f"Stopped snapshot daemon for camera {camera_id}")
        return True

    def stop_all(self):
        for camera_id in list(self._processes.keys()):
            self.stop_snapshot(camera_id)

    def get_snapshot_path(self, camera_id: int) -> str:
        return str(
            Path(settings.RECORDINGS_PATH)
            / f"camera_{camera_id}"
            / "snapshot.jpg"
        )


snapshot_service = SnapshotService()
