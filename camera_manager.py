"""
camera_manager.py - Multi-threaded RTSP frame capturing
Now supports dynamic updates to the camera list.
"""

import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

class CameraStream:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.frame = None
        self.stopped = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.stopped = False
            self.thread = threading.Thread(target=self._update, args=(), daemon=True)
            self.thread.start()
        return self

    def _update(self):
        while not self.stopped:
            cap = cv2.VideoCapture(self.url)
            # Short timeout check
            if not cap.isOpened():
                logger.error(f"Nu s-a putut deschide fluxul: {self.name} ({self.url}). Reîncercare...")
                cap.release()
                time.sleep(5)
                continue

            logger.info(f"Conectat la fluxul: {self.name}")
            while not self.stopped:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"S-a pierdut conexiunea cu {self.name}. Re-conectare...")
                    break
                
                with self.lock:
                    self.frame = frame
                
                # Prevent CPU bottleneck
                time.sleep(0.01)
            
            cap.release()
            time.sleep(2)

    def read(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.stopped = True
        if self.thread:
            self.thread.join(timeout=2)

class CameraManager:
    def __init__(self, cameras_config):
        self.streams = {}
        self.update_config(cameras_config)

    def update_config(self, cameras_config):
        """Update active streams based on new config."""
        new_names = [c['name'] for c in cameras_config if c.get('enabled', True) and c.get('url')]
        
        # Stop streams that are no longer present or enabled
        to_remove = [name for name in self.streams if name not in new_names]
        for name in to_remove:
            logger.info(f"Oprire flux camera: {name}")
            self.streams[name].stop()
            del self.streams[name]

        # Start or update streams
        for cam in cameras_config:
            if not cam.get('enabled', True) or not cam.get('url'):
                continue
                
            name = cam['name']
            url = cam['url']
            
            if name in self.streams:
                if self.streams[name].url != url:
                    logger.info(f"Actualizare URL pentru {name}")
                    self.streams[name].stop()
                    self.streams[name] = CameraStream(name, url).start()
            else:
                logger.info(f"Inițializare flux camera: {name}")
                self.streams[name] = CameraStream(name, url).start()

    def get_latest_frames(self):
        return {name: stream.read() for name, stream in self.streams.items()}

    def stop_all(self):
        for stream in self.streams.values():
            stream.stop()
        self.streams = {}
