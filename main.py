import time
import logging
import signal
import sys
import threading
from camera_manager import CameraManager
from ai_detector import AiDetector
from relay_controller import RelayController
from notifier import EmailNotifier
from database import DatabaseManager
from config_manager import ConfigManager
from gui.dashboard import DashboardApp

# ── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AWG")

class AIWashGuard:
    def __init__(self):
        self.running = True
        logger.info("🚗 Inițializare sistem AI Wash Guard...")
        
        # 1. Config
        self.config_mgr = ConfigManager()
        self.cfg = self.config_mgr.config
        
        # 2. Hardcoded / Defaults for detection logic
        self.DETECTION_THRESHOLD = 2
        
        # Initial setup of components
        self._setup_components()
        
        # Track detection state per camera
        self._reset_detection_states()

    def _setup_components(self):
        """Initialize or re-initialize all core components based on current config."""
        cam_cfg = self.config_mgr.get_cameras()
        email_cfg = self.config_mgr.get_email_settings()
        db_cfg = self.config_mgr.get_mysql_settings()
        hw_cfg = self.config_mgr.get_hardware_settings()
        ai_cfg = self.cfg.get("ai", {"model": "yolov8n.pt", "confidence": 0.5})
        
        # Hardware
        relay_pins = hw_cfg["relay_pins"]
        if not hasattr(self, 'relays'):
            self.relays = RelayController(pins=relay_pins, active_low=hw_cfg["active_low"])
        else:
            # Check if pins changed (simplified: just recreate if logic is complex)
            if self.relays.pins != relay_pins:
                logger.info("Pinii de releu s-au schimbat. Reinițializare hardware.")
                self.relays.cleanup()
                self.relays = RelayController(pins=relay_pins, active_low=hw_cfg["active_low"])

        # AI
        if not hasattr(self, 'detector'):
            self.detector = AiDetector(model_path=ai_cfg["model"], confidence=ai_cfg["confidence"])
        
        # Cameras (Robust: will be empty if none configured)
        self.active_cameras = [c for c in cam_cfg if c.get("enabled", True)]
        if not hasattr(self, 'cameras'):
            self.cameras = CameraManager(cam_cfg)
        else:
            self.cameras.update_config(cam_cfg)
        
        # Notifier
        if not hasattr(self, 'notifier'):
            self.notifier = EmailNotifier(email_cfg["sender"], email_cfg["app_password"], email_cfg["recipient"])
        else:
            self.notifier.update_credentials(email_cfg["sender"], email_cfg["app_password"], email_cfg["recipient"])
        self.email_enabled = email_cfg["enabled"]
        
        # Database
        if not hasattr(self, 'db'):
            self.db = DatabaseManager(db_cfg["host"], db_cfg["user"], db_cfg["password"], db_cfg["database"])
        else:
            self.db.update_config(db_cfg["host"], db_cfg["user"], db_cfg["password"], db_cfg["database"])
        self.db_enabled = db_cfg["enabled"]

    def _reset_detection_states(self):
        cam_cfg = self.config_mgr.get_cameras()
        self.detection_counters = {cam['name']: 0 for cam in cam_cfg}
        self.session_ids = {cam['name']: None for cam in cam_cfg}

    def reload_config(self):
        """Method called by GUI after saving settings."""
        logger.info("🔄 Reîncărcare configurație sistem...")
        self.config_mgr.load_config()
        self.cfg = self.config_mgr.config
        self._setup_components()
        # Note: we don't necessarily want to reset stats unless cams change significantly
        # but for simplicity, we refresh the keys
        self._reset_detection_states()

    def monitoring_loop(self):
        """Background thread for AI monitoring."""
        logger.info("🛰️ Buclă de monitorizare pornită (fundal).")
        try:
            while self.running:
                # If no cameras enabled, just wait
                if not self.active_cameras:
                    time.sleep(1)
                    continue

                frames = self.cameras.get_latest_frames()
                
                for i, cam in enumerate(self.active_cameras):
                    cam_name = cam['name']
                    frame = frames.get(cam_name)
                    if frame is None: continue
                    
                    detected = self.detector.detect(frame)
                    
                    if detected:
                        self.detection_counters[cam_name] += 1
                        if self.detection_counters[cam_name] >= self.DETECTION_THRESHOLD:
                            relay_idx = cam.get("id", i)
                            self.relays.set_relay(relay_idx, True)
                            
                            if self.detection_counters[cam_name] == self.DETECTION_THRESHOLD:
                                logger.error(f"!!! ALARMĂ {cam_name} !!! - Vehicul Interzis.")
                                if self.email_enabled:
                                    self.notifier.send_alert(cam_name, "Vehicul Interzis (ATV/Cross)")
                                if self.db_enabled:
                                    self.session_ids[cam_name] = self.db.start_session(cam_name)
                                    self.db.log_incident(cam_name, "Vehicul Interzis (ATV/Cross)")
                    else:
                        if self.detection_counters.get(cam_name, 0) > 0:
                            logger.info(f"Reluare curent {cam_name}. Zonă liberă.")
                            relay_idx = cam.get("id", i)
                            self.relays.set_relay(relay_idx, False)
                            
                            if self.db_enabled and self.session_ids.get(cam_name) is not None:
                                self.db.end_session(self.session_ids[cam_name])
                                self.session_ids[cam_name] = None
                                
                        self.detection_counters[cam_name] = 0
                
                time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Eroare în bucla de monitorizare: {e}")

    def stop(self, *args):
        logger.info("🛑 Proces de oprire... Vă rugăm așteptați.")
        self.running = False
        if hasattr(self, 'cameras'): self.cameras.stop_all()
        if hasattr(self, 'relays'): self.relays.cleanup()
        if hasattr(self, 'db'): self.db.close()
        sys.exit(0)

if __name__ == "__main__":
    try:
        engine = AIWashGuard()
        
        # Start AI monitoring thread
        monitor_thread = threading.Thread(target=engine.monitoring_loop, daemon=True)
        monitor_thread.start()
        
        # Start Dashboard
        app = DashboardApp(engine)
        
        # Signals
        signal.signal(signal.SIGINT, engine.stop)
        signal.signal(signal.SIGTERM, engine.stop)
        
        app.mainloop()
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        logger.error(f"Eroare fatală la pornire: {e}")
        messagebox.showerror("Eroare AI Wash Guard", f"Aplicația nu a putut porni:\n\n{e}")
        root.destroy()
        sys.exit(1)
    finally:
        if 'engine' in locals():
            engine.stop()
