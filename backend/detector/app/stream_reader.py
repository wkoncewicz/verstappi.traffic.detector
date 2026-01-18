# stream_reader.py
"""
Snapshot-based VLC reader (works with VLC 4.x, headless).
- uses video_take_snapshot to capture frames
- forces --vout=dummy, --avcodec-hw=none etc to avoid X11/VDPAU errors
- keeps deque of last N non-black frames and returns last valid frame
"""

import vlc
import cv2
import os
import tempfile
import threading
import time
from collections import deque

class VLCStreamReader:
    def __init__(
        self,
        url,
        width=1280,
        height=720,
        cache_ms=2500,    
        interval=0.03,
        deque_size=5,
        black_threshold=10,   # mean brightness below this = considered black
    ):
        self.url = url
        self.width = int(width)
        self.height = int(height)
        self.cache_ms = int(cache_ms)
        self.interval = float(interval)
        self.deque_size = int(deque_size)
        self.black_threshold = float(black_threshold)

        self._tmpfile = os.path.join(tempfile.gettempdir(), f"vlc_snapshot_{os.getpid()}.png")
        self._frame = None
        self._frames_deque = deque(maxlen=self.deque_size)  # hold last non-black frames (BGR)
        self._running = True
        self._lock = threading.RLock()

        args = [
            "--no-xlib",
            "--vout=dummy",
            "--aout=dummy",
            "--no-video-title-show",
            "--no-spu",
            "--no-osd",
            f"--network-caching={self.cache_ms}",
            f"--live-caching={self.cache_ms}",
        ]
        try:
            self.instance = vlc.Instance(args)
        except TypeError:
            self.instance = vlc.Instance(*args)

        # if self.instance is None:
        #     print("VLC instance creation failed with full args, trying minimal args...")
        #     try:
        #         self.instance = vlc.Instance("--no-xlib")
        #     except:
        #         self.instance = vlc.Instance()
        
        # if self.instance is None:
        #     raise RuntimeError("Failed to create VLC instance. Check VLC installation and arguments.")

        self.player = self.instance.media_player_new()
        media = self.instance.media_new(self.url)
        self.player.set_media(media)
        self.player.play()

        # wait a bit for the stream to start
        time.sleep(1.0)

        # snapshot thread
        self._thread = threading.Thread(target=self._snapshot_loop, daemon=True)
        self._thread.start()

    def _is_black(self, img):
        if img is None:
            return True
        # mean of grayscale; fast measure
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return float(gray.mean()) < self.black_threshold

    def _snapshot_loop(self):
        while self._running:
            try:
                # 0 = video track id
                self.player.video_take_snapshot(0, self._tmpfile, self.width, self.height)
                if os.path.exists(self._tmpfile):
                    img = cv2.imread(self._tmpfile)
                    if img is not None:
                        with self._lock:
                            self._frame = img
                            if not self._is_black(img):
                                # push non-black frames into deque
                                self._frames_deque.append(img.copy())
            except Exception as e:
                print("VLCStreamReader snapshot error:", e)
            time.sleep(self.interval)

    def get_frame(self):
        """
        Returns a copy of the last good frame:
        - prefer last non-black from deque
        - else return last snapshot (may be black)
        - else None
        """
        with self._lock:
            if len(self._frames_deque) > 0:
                return self._frames_deque[-1].copy()
            elif self._frame is not None:
                return self._frame.copy()
            else:
                return None

    def stop(self):
        self._running = False
        try:
            self.player.stop()
        except Exception:
            pass
        try:
            self.instance.release()
        except Exception:
            pass
        # remove tmp if exists
        try:
            if os.path.exists(self._tmpfile):
                os.remove(self._tmpfile)
        except Exception:
            pass
