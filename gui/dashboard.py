"""
dashboard.py - Main Dashboard for AI Wash Guard with Quad-View
"""

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading
import time
import logging
from gui.settings_app import SettingsApp
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class CameraWidget(ctk.CTkFrame):
    """Component to display a single camera feed."""
    def __init__(self, parent, camera_name, placeholder_v=0):
        super().__init__(parent)
        self.camera_name = camera_name
        
        self.label_name = ctk.CTkLabel(self, text=camera_name, font=("Arial", 14, "bold"))
        self.label_name.pack(pady=2)
        
        self.video_label = ctk.CTkLabel(self, text="Conectare flux...", bg_color="black")
        self.video_label.pack(expand=True, fill="both", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(self, text="Status: IDLE", text_color="gray")
        self.status_label.pack(pady=2)

    def update_frame(self, frame, is_alert=False):
        """Update the label with a new OpenCV frame."""
        if frame is not None:
            # Resize frame to fit widget (approx)
            h, w = frame.shape[:2]
            aspect = w / h
            target_w = 400
            target_h = int(target_w / aspect)
            
            frame_resized = cv2.resize(frame, (target_w, target_h))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(target_w, target_h))
            
            self.video_label.configure(image=img_tk, text="")
            
        if is_alert:
            self.status_label.configure(text="STATUS: !!! ALARMĂ !!!", text_color="red")
            self.configure(border_width=2, border_color="red")
        else:
            self.status_label.configure(text="STATUS: OK", text_color="green")
            self.configure(border_width=0)

class DashboardApp(ctk.CTk):
    def __init__(self, monitoring_engine):
        super().__init__()
        self.engine = monitoring_engine
        self.config_mgr = ConfigManager()
        
        self.title("🛡️ AI Wash Guard - Dashboard")
        self.geometry("1100x850")
        
        # UI Setup
        self._build_top_menu()
        self._build_grid()
        
        # Start update loop
        self.update_interval = 30 # ms
        self.after(self.update_interval, self._update_loop)

    def _build_top_menu(self):
        self.top_frame = ctk.CTkFrame(self, height=50)
        self.top_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        self.title_label = ctk.CTkLabel(self.top_frame, text="🚐 AI WASH GUARD MONITORING", font=("Arial", 18, "bold"))
        self.title_label.pack(side="left", padx=20)
        
        self.settings_btn = ctk.CTkButton(self.top_frame, text="⚙️ Setări", width=100, command=self._open_settings)
        self.settings_btn.pack(side="right", padx=20)

    def _build_grid(self):
        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Grid layout 2x2
        self.grid_frame.grid_columnconfigure((0, 1), weight=1)
        self.grid_frame.grid_rowconfigure((0, 1), weight=1)
        
        self.cam_widgets = {}
        cam_configs = self.config_mgr.get_cameras()
        
        for i in range(4):
            cfg = cam_configs[i] if i < len(cam_configs) else {"name": f"Boxa {i+1}"}
            name = cfg["name"]
            
            row = i // 2
            col = i % 2
            
            widget = CameraWidget(self.grid_frame, name)
            widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.cam_widgets[name] = widget

    def _update_loop(self):
        """Periodically update camera feeds from the monitoring engine."""
        frames = self.engine.cameras.get_latest_frames()
        
        for name, widget in self.cam_widgets.items():
            frame = frames.get(name)
            # Check if this camera is currently triggering an alert in the engine
            is_alert = self.engine.detection_counters.get(name, 0) >= self.engine.DETECTION_THRESHOLD
            widget.update_frame(frame, is_alert)
            
        self.after(self.update_interval, self._update_loop)

    def _open_settings(self):
        SettingsApp(self)

if __name__ == "__main__":
    # For standalone testing (won't have engine)
    app = DashboardApp(None)
    app.mainloop()
