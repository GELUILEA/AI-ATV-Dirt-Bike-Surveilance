import sys
import os
import logging
import traceback

# Setup logging to console
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DEBUG")

def run_diagnostic():
    logger.info("=== AI WASH GUARD DIAGNOSTIC START ===")
    
    # 1. Environment Check
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current Working Directory: {os.getcwd()}")
    
    # 2. Files Check
    required_files = ["main.py", "config_manager.py", "camera_manager.py", "ai_detector.py", "relay_controller.py", "database.py", "notifier.py", "gui/dashboard.py", "gui/settings_app.py"]
    for f in required_files:
        if os.path.exists(f):
            logger.info(f"[OK] Fișier găsit: {f}")
        else:
            logger.error(f"[FAIL] Fișier LIPSĂ: {f}")

    # 3. Import Tests
    try:
        import customtkinter as ctk
        import cv2
        import PIL
        from ultralytics import YOLO
        logger.info("[OK] Toate bibliotecile externe (customtkinter, cv2, PIL, ultralytics) sunt instalate.")
    except ImportError as e:
        logger.error(f"[FAIL] Bibliotecă lipsă: {e}")
        return

    # 4. Config Test
    try:
        from config_manager import ConfigManager
        cm = ConfigManager()
        logger.info(f"[OK] ConfigManager funcțional. Camere detectate: {len(cm.get_cameras())}")
    except Exception as e:
        logger.error(f"[FAIL] ConfigManager eroare: {e}")

    # 5. AI Detector Test
    try:
        from ai_detector import AiDetector
        detector = AiDetector(model_path="yolov8n.pt")
        logger.info("[OK] Modelul YOLO a fost încărcat cu succes.")
    except Exception as e:
        logger.error(f"[FAIL] AiDetector eroare (posibil yolov8n.pt lipsește): {e}")

    # 6. Database Test (Lazy check)
    try:
        from database import DatabaseManager
        db = DatabaseManager("localhost", "root", "", "test_db")
        logger.info("[OK] DatabaseManager inițializat (Mod Lazy).")
    except Exception as e:
        logger.error(f"[FAIL] DatabaseManager eroare: {e}")

    # 7. GUI Test (Check if window can be created)
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        logger.info("[OK] Tkinter GUI are suport în sistem.")
        root.destroy()
    except Exception as e:
        logger.error(f"[FAIL] Eroare suport GUI: {e}")

    logger.info("=== DIAGNOSTIC FINALIZAT ===")

if __name__ == "__main__":
    try:
        run_diagnostic()
    except Exception:
        traceback.print_exc()
