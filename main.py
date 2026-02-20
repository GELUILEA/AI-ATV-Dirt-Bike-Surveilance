"""
main.py - Main integration script for AI Wash Guard
"""

import time
import logging
import signal
import sys
import argparse
from camera_manager import CameraManager
from ai_detector import AiDetector
from relay_controller import RelayController
from notifier import EmailNotifier
from database import DatabaseManager
from config_manager import ConfigManager

# ── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AWG")

class AIWashGuard:
    def __init__(self):
        self.running = True
        logger.info("Inițializare sistem AI Wash Guard...")
        
        # 1. Config
        self.config_mgr = ConfigManager()
        self.cfg = self.config_mgr.config
        
        cam_cfg = self.config_mgr.get_cameras()
        email_cfg = self.config_mgr.get_email_settings()
        db_cfg = self.config_mgr.get_mysql_settings()
        hw_cfg = self.config_mgr.get_hardware_settings()
        ai_cfg = self.cfg["ai"]
        
        # 2. Hardware
        self.relay_pins = hw_cfg["relay_pins"]
        self.relays = RelayController(pins=self.relay_pins, active_low=hw_cfg["active_low"])
        
        # 3. AI
        self.detector = AiDetector(model_path=ai_cfg["model"], confidence=ai_cfg["confidence"])
        
        # 4. Cameras (Only active ones)
        self.active_cameras = [c for c in cam_cfg if c.get("enabled", True)]
        self.cameras = CameraManager(self.active_cameras)
        
        # 5. Notifier
        self.notifier = EmailNotifier(email_cfg["sender"], email_cfg["app_password"], email_cfg["recipient"])
        self.email_enabled = email_cfg["enabled"]
        
        # 6. Database
        self.db = DatabaseManager(db_cfg["host"], db_cfg["user"], db_cfg["password"], db_cfg["database"])
        self.db_enabled = db_cfg["enabled"]
        
        # Track detection state
        self.detection_counters = {cam['name']: 0 for cam in self.active_cameras}
        self.session_ids = {cam['name']: None for cam in self.active_cameras}
        self.DETECTION_THRESHOLD = 2

    def run(self):
        if not self.active_cameras:
            logger.error("Nicio cameră activată în setări! Ieșire.")
            return

        logger.info(f"Monitorizare activă pentru {len(self.active_cameras)} boxe.")
        try:
            while self.running:
                frames = self.cameras.get_latest_frames()
                
                # cameras list to iterate through indices consistently
                for i, cam in enumerate(self.active_cameras):
                    cam_name = cam['name']
                    frame = frames.get(cam_name)
                    if frame is None: continue
                    
                    detected = self.detector.detect(frame)
                    
                    if detected:
                        self.detection_counters[cam_name] += 1
                        if self.detection_counters[cam_name] >= self.DETECTION_THRESHOLD:
                            logger.error(f"!!! ALARMĂ {cam_name} !!! Întrerupere curent.")
                            # Hardware index is based on global pins list if needed, 
                            # but here we use the camera ID for relay mapping
                            relay_idx = cam.get("id", i)
                            self.relays.set_relay(relay_idx, True)
                            
                            if self.detection_counters[cam_name] == self.DETECTION_THRESHOLD:
                                if self.email_enabled:
                                    self.notifier.send_alert(cam_name, "Vehicul Interzis (ATV/Cross)")
                                if self.db_enabled:
                                    self.session_ids[cam_name] = self.db.start_session(cam_name)
                                    self.db.log_incident(cam_name, "Vehicul Interzis (ATV/Cross)")
                    else:
                        if self.detection_counters[cam_name] > 0:
                            logger.info(f"Reluare curent {cam_name}. Zonă liberă.")
                            relay_idx = cam.get("id", i)
                            self.relays.set_relay(relay_idx, False)
                            
                            if self.db_enabled and self.session_ids[cam_name] is not None:
                                self.db.end_session(self.session_ids[cam_name])
                                self.session_ids[cam_name] = None
                                
                        self.detection_counters[cam_name] = 0
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            self.stop()

    def stop(self, *args):
        logger.info("Oprire sistem...")
        self.running = False
        if hasattr(self, 'cameras'): self.cameras.stop_all()
        if hasattr(self, 'relays'): self.relays.cleanup()
        if hasattr(self, 'db'): self.db.close()
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Wash Guard System")
    parser.add_argument("--settings", action="store_true", help="Deschide interfața de setări")
    args = parser.parse_args()

    if args.settings:
        from gui.settings_app import SettingsApp
        app = SettingsApp()
        app.mainloop()
    else:
        app = AIWashGuard()
        signal.signal(signal.SIGINT, app.stop)
        signal.signal(signal.SIGTERM, app.stop)
        app.run()
