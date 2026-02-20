"""
config_manager.py - Persistent configuration for AI Wash Guard
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "cameras": [
        {"id": 0, "name": "Boxa 1", "url": "rtsp://admin:parola1@192.168.1.101:554/Streaming/Channels/101", "enabled": True},
        {"id": 1, "name": "Boxa 2", "url": "rtsp://admin:parola1@192.168.1.102:554/Streaming/Channels/101", "enabled": False},
        {"id": 2, "name": "Boxa 3", "url": "rtsp://admin:parola1@192.168.1.103:554/Streaming/Channels/101", "enabled": False},
        {"id": 3, "name": "Boxa 4", "url": "rtsp://admin:parola1@192.168.1.104:554/Streaming/Channels/101", "enabled": False},
    ],
    "email": {
        "enabled": False,
        "sender": "adresa.ta@gmail.com",
        "app_password": "",
        "recipient": "destinatar@email.com"
    },
    "mysql": {
        "enabled": False,
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "wash_guard_db"
    },
    "hardware": {
        "relay_pins": [23, 24, 17, 27],
        "active_low": True
    },
    "ai": {
        "confidence": 0.45,
        "model": "yolov8n.pt"
    }
}

class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._deep_update(self.config, loaded)
                logger.info("Configurație încărcată din fișier.")
            except Exception as e:
                logger.error(f"Eroare la încărcarea configurației: {e}")
        else:
            self.save() # Create default file

    def save(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configurație salvată.")
        except Exception as e:
            logger.error(f"Eroare la salvarea configurației: {e}")

    def _deep_update(self, base, update):
        for k, v in update.items():
            if isinstance(v, dict) and k in base:
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def get_cameras(self):
        return self.config["cameras"]

    def get_email_settings(self):
        return self.config["email"]

    def get_mysql_settings(self):
        return self.config["mysql"]

    def get_hardware_settings(self):
        return self.config["hardware"]

    def update_settings(self, section, data):
        if section in self.config:
            self.config[section] = data
            self.save()
