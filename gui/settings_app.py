"""
settings_app.py - GUI for configuring AI Wash Guard
"""

import customtkinter as ctk
from tkinter import messagebox
from config_manager import ConfigManager

# Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SettingsApp(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        
        self.title("🛡️ AI Wash Guard - Setări")
        self.geometry("700x650")
        self.attributes("-topmost", True)  # Keep on top
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._build_ui()
        
        # Make it modal-ish
        if parent:
            self.grab_set()

    def _build_ui(self):
        # Tabview
        self.tabview = ctk.CTkTabview(self, width=650)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_cam = self.tabview.add("🎥 Camere")
        self.tab_email = self.tabview.add("📧 Email")
        self.tab_db = self.tabview.add("🗄️ Bază de Date")
        self.tab_hw = self.tabview.add("⚙️ Sistem")
        
        self._build_camera_tab()
        self._build_email_tab()
        self._build_db_tab()
        self._build_hw_tab()
        
        # Save Button at bottom
        self.save_btn = ctk.CTkButton(self, text="💾 Salvează Toate Setările", 
                                     command=self._save_all, height=40, font=("Arial", 14, "bold"))
        self.save_btn.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

    def _build_camera_tab(self):
        self.cam_entries = []
        cameras = self.config_manager.get_cameras()
        
        for i, cam in enumerate(cameras):
            frame = ctk.CTkFrame(self.tab_cam)
            frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(frame, text=f"Boxa {i+1}:", width=60).grid(row=0, column=0, padx=5, pady=5)
            
            name_var = ctk.StringVar(value=cam["name"])
            name_entry = ctk.CTkEntry(frame, textvariable=name_var, width=120)
            name_entry.grid(row=0, column=1, padx=5, pady=5)
            
            url_var = ctk.StringVar(value=cam["url"])
            url_entry = ctk.CTkEntry(frame, textvariable=url_var, width=320)
            url_entry.grid(row=0, column=2, padx=5, pady=5)
            
            en_var = ctk.BooleanVar(value=cam.get("enabled", True))
            en_cb = ctk.CTkCheckBox(frame, text="Activ", variable=en_var)
            en_cb.grid(row=0, column=3, padx=5, pady=5)
            
            self.cam_entries.append({"name": name_var, "url": url_var, "enabled": en_var})

    def _build_email_tab(self):
        email = self.config_manager.get_email_settings()
        
        self.email_en_var = ctk.BooleanVar(value=email["enabled"])
        ctk.CTkCheckBox(self.tab_email, text="Activează Notificări Email", variable=self.email_en_var).pack(pady=10)
        
        f = ctk.CTkFrame(self.tab_email)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(f, text="Gmail User:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.email_user = ctk.CTkEntry(f, width=300)
        self.email_user.insert(0, email["sender"])
        self.email_user.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(f, text="App Password:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.email_pass = ctk.CTkEntry(f, width=300, show="*")
        self.email_pass.insert(0, email["app_password"])
        self.email_pass.grid(row=1, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(f, text="Destinatar:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.email_to = ctk.CTkEntry(f, width=300)
        self.email_to.insert(0, email["recipient"])
        self.email_to.grid(row=2, column=1, padx=10, pady=10)

    def _build_db_tab(self):
        db = self.config_manager.get_mysql_settings()
        
        self.db_en_var = ctk.BooleanVar(value=db["enabled"])
        ctk.CTkCheckBox(self.tab_db, text="Activează Logare MySQL", variable=self.db_en_var).pack(pady=10)
        
        f = ctk.CTkFrame(self.tab_db)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        
        fields = [("Host:", "host"), ("User:", "user"), ("Parolă:", "password"), ("Baza Date:", "database")]
        self.db_entries = {}
        
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(f, text=label).grid(row=i, column=0, padx=10, pady=10, sticky="e")
            entry = ctk.CTkEntry(f, width=300)
            if key == "password": entry.configure(show="*")
            entry.insert(0, db[key])
            entry.grid(row=i, column=1, padx=10, pady=10)
            self.db_entries[key] = entry

    def _build_hw_tab(self):
        hw = self.config_manager.get_hardware_settings()
        ai = self.config_manager.config["ai"]
        
        f = ctk.CTkFrame(self.tab_hw)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(f, text="AI Confidence (0.1 - 0.9):").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.ai_conf = ctk.CTkEntry(f, width=100)
        self.ai_conf.insert(0, str(ai["confidence"]))
        self.ai_conf.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(f, text="Pini Relee (BCM):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.hw_pins = ctk.CTkEntry(f, width=200)
        self.hw_pins.insert(0, ", ".join(map(str, hw["relay_pins"])))
        self.hw_pins.grid(row=1, column=1, padx=10, pady=10, sticky="w")

    def _save_all(self):
        # 1. Cameras
        new_cameras = []
        for i, ent in enumerate(self.cam_entries):
            new_cameras.append({
                "id": i,
                "name": ent["name"].get(),
                "url": ent["url"].get(),
                "enabled": ent["enabled"].get()
            })
        self.config_manager.config["cameras"] = new_cameras
        
        # 2. Email
        self.config_manager.config["email"] = {
            "enabled": self.email_en_var.get(),
            "sender": self.email_user.get(),
            "app_password": self.email_pass.get(),
            "recipient": self.email_to.get()
        }
        
        # 3. DB
        self.config_manager.config["mysql"] = {
            "enabled": self.db_en_var.get(),
            "host": self.db_entries["host"].get(),
            "user": self.db_entries["user"].get(),
            "password": self.db_entries["password"].get(),
            "database": self.db_entries["database"].get()
        }
        
        # 4. HW & AI
        try:
            pins = [int(p.strip()) for p in self.hw_pins.get().split(",")]
            self.config_manager.config["hardware"]["relay_pins"] = pins
            self.config_manager.config["ai"]["confidence"] = float(self.ai_conf.get())
        except Exception as e:
            messagebox.showerror("Eroare", f"Format invalid pentru pini sau AI confidence: {e}")
           # Save to file
        self.config_manager.save()
        
        # Trigger engine reload and UI refresh
        if self.master and hasattr(self.master, 'engine'):
            self.master.engine.reload_config()
            
        if hasattr(self.master, 'refresh_widgets'):
            self.master.refresh_widgets()
            
        messagebox.showinfo("Succes", "Setările au fost salvate și aplicate!")
        self.destroy()

if __name__ == "__main__":
    app = SettingsApp()
    app.mainloop()
