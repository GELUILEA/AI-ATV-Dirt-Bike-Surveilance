"""
camera_manager.py - Multi-stream RTSP manager for Hikvision cameras
Uses threads to ensure low latency for AI processing.
"""

import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

class CameraStream:
    """Handles a single RTSP stream in a background thread."""
    def __init__(self, name, rtsp_url):
        self.name = name
        self.rtsp_url = rtsp_url
        self.cap = cv2.VideoCapture(rtsp_url)
        self.frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        if not self.cap.isOpened():
            logger.error(f"Nu s-a putut deschide stream-ul pentru {name}")
        else:
            self.running = True
            self.thread = threading.Thread(target=self._update, name=f"Thread-{name}", daemon=True)
            self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"Conexiune pierdută cu {self.name}. Reîncercare...")
                self.cap.release()
                time.sleep(5)
                self.cap = cv2.VideoCapture(self.rtsp_url)
                continue
            
            with self.lock:
                self.frame = frame

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()

class CameraManager:
    """Manages multiple CameraStream instances."""
    def __init__(self, camera_configs: list):
        """
        camera_configs: List of dicts with {'name': 'Boxa 1', 'url': 'rtsp://...'}
        """
        self.streams = {}
        for cfg in camera_configs:
            name = cfg['name']
            url = cfg['url']
            logger.info(f"Inițializare flux camera: {name}")
            self.streams[name] = CameraStream(name, url)

    def get_latest_frames(self) -> dict:
        """Returns the latest frame for each camera."""
        return {name: stream.get_frame() for name, stream in self.streams.items()}

    def stop_all(self):
        for stream in self.streams.values():
            stream.stop()
        logger.info("Toate fluxurile video au fost oprite.")
