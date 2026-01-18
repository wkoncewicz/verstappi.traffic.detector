# ffmpeg_reader.py
"""
FFmpeg pipe reader: ffmpeg -i <url> -f rawvideo -pix_fmt bgr24 -s WxH -an -sn -
Reads raw frames from stdout in a background thread and exposes get_frame().
Requires ffmpeg binary in PATH.
"""

import subprocess
import threading
import numpy as np
import time
from collections import deque

class FFmpegStreamReader:
    def __init__(self, url, width=1280, height=720, fps=25, queue_size=3):
        print("Initializing FFmpegStreamReader...")
        self.url = url
        self.width = int(width)
        self.height = int(height)
        self.fps = int(fps)
        self.queue_size = int(queue_size)

        # ffmpeg command
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-fflags", "nobuffer",
            "-rw_timeout", "3000000",     # in microseconds
            "-i", self.url,
            "-an", "-sn",
            "-vf", f"scale={self.width}:{self.height}",
            "-pix_fmt", "bgr24",
            "-f", "rawvideo",
            "-"
        ]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**7)
        self._running = True
        self._lock = threading.RLock()
        self._frame = None
        self._dq = deque(maxlen=self.queue_size)
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        print("Starting FFmpeg read thread...")
        self._thread.start()

    def _read_loop(self):
        frame_size = self.width * self.height * 3
        while self._running:
            try:
                raw = self.proc.stdout.read(frame_size)
                if not raw or len(raw) < frame_size:
                    # stream ended or temporary error
                    time.sleep(0.1)
                    continue
                frame = np.frombuffer(raw, np.uint8).reshape((self.height, self.width, 3))
                with self._lock:
                    self._frame = frame
                    self._dq.append(frame.copy())
            except Exception as e:
                print("FFmpegStreamReader read error:", e)
                time.sleep(0.1)

    def get_frame(self):
        with self._lock:
            if len(self._dq) > 0:
                return self._dq[-1].copy()
            elif self._frame is not None:
                return self._frame.copy()
            else:
                return None

    def stop(self):
        self._running = False
        try:
            self.proc.terminate()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=1)
        except Exception:
            pass
