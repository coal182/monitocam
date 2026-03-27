import subprocess
import os
import signal
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import get_settings
from services.giffer import gif_service


settings = get_settings()
logger = logging.getLogger(__name__)


class RecorderService:
    def __init__(self):
        self._processes: dict[int, subprocess.Popen] = {}
        self._gif_service = gif_service

    def start_recording(self, camera_id: int, camera_name: str, rtsp_url: str) -> bool:
        if camera_id in self._processes:
            logger.warning(f"Camera {camera_id} already recording")
            return False

        output_dir = Path(settings.storage.recordings_path) / f"camera_{camera_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        thread = threading.Thread(
            target=self._recording_loop,
            args=(camera_id, camera_name, rtsp_url, str(output_dir)),
            daemon=True,
        )
        thread.start()
        logger.info(f"Started recording thread for camera {camera_id}")
        return True

    def _recording_loop(
        self, camera_id: int, camera_name: str, rtsp_url: str, output_dir: str
    ):
        safe_name = "".join(c for c in camera_name if c.isalnum() or c in "_-")
        segment_duration = settings.recording.fragment_duration

        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            output_file = Path(output_dir) / f"{safe_name}_{timestamp}.mp4"
            gif_file = Path(output_dir) / f"{safe_name}_{timestamp}.gif"

            logger.info(f"Starting segment: {output_file}")

            cmd = [
                "ffmpeg",
                "-re",
                "-rtsp_transport",
                "udp",
                "-i",
                rtsp_url,
                "-c:v",
                "copy",
                "-an",
                "-f",
                "mpegts",
                "-flush_packets",
                "1",
                "-t",
                str(segment_duration),
                str(output_file),
            ]

            cmd = [
                "ffmpeg",
                "-rtsp_transport", 
                "udp",
                "-i", 
                rtsp_url,
                "-c:v", 
                "copy",
                "-an",
                "-f", 
                "mp4",
                "-movflags", 
                "+frag_keyframe+empty_moov+default_base_moof",
                "-t", 
                str(segment_duration),
                str(output_file),
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            self._processes[camera_id] = process

            try:
                process.wait()

                if process.returncode in (0, 255):
                    if output_file.exists() and output_file.stat().st_size > 100:
                        logger.info(
                            f"Segment complete ({output_file.stat().st_size} bytes), re-muxing to MP4"
                        )
                        try:
            #                self._remux_to_mp4(str(output_file))
            #                logger.info(f"Re-mux complete, generating GIF")
                            self._gif_service.generate_gif(
                                str(output_file),
                                str(gif_file),
                                duration=settings.recording.gif_duration,
                                fps=settings.recording.gif_fps,
                                speed=settings.recording.gif_speed,
                            )
                        except Exception as e:
                            logger.error(f"Re-mux failed: {e}")
                            try:
                                self._gif_service.generate_gif(
                                    str(output_file),
                                    str(gif_file),
                                    duration=settings.recording.gif_duration,
                                    fps=settings.recording.gif_fps,
                                    speed=settings.recording.gif_speed,
                                )
                            except Exception as ge:
                                logger.error(f"GIF generation failed: {ge}")
                else:
                    logger.warning(f"Segment ended with code {process.returncode}")

            except Exception as e:
                logger.error(f"Recording error: {e}")
            finally:
                if camera_id in self._processes:
                    del self._processes[camera_id]

    def _remux_to_mp4(self, ts_path: str):
        ts_file = Path(ts_path)
        mp4_temp = ts_file.with_suffix(".mp4.tmp")
        cmd = [
            "ffmpeg",
            "-i",
            str(ts_file),
            "-c",
            "copy",
            "-f",
            "mp4",
            "-movflags",
            "+faststart",
            str(mp4_temp),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and mp4_temp.exists():
            ts_file.unlink()
            mp4_temp.rename(ts_file)
            logger.info(f"Re-muxed {ts_file.name} to MP4")
        else:
            logger.error(f"Re-mux failed: {result.stderr}")
            if mp4_temp.exists():
                mp4_temp.unlink()
            raise RuntimeError("Re-mux failed")

    def stop_recording(self, camera_id: int) -> bool:
        if camera_id not in self._processes:
            return False

        process = self._processes[camera_id]
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass
        finally:
            del self._processes[camera_id]
            logger.info(f"Stopped recording camera {camera_id}")
        return True

    def is_recording(self, camera_id: int) -> bool:
        return camera_id in self._processes

    def get_status(self, camera_id: int) -> dict:
        return {
            "id": camera_id,
            "is_recording": self.is_recording(camera_id),
            "process_exists": camera_id in self._processes,
        }

    def stop_all(self):
        for camera_id in list(self._processes.keys()):
            self.stop_recording(camera_id)


recorder_service = RecorderService()
