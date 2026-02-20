"""
ai_detector.py - AI Inference engine for vehicle detection
Uses YOLOv8 (Ultralytics) optimized for Raspberry Pi 5.
"""

import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class AiDetector:
    """
    Handles AI inference on image frames.
    """
    def __init__(self, model_path='yolov8n.pt', confidence=0.5):
        self.model = YOLO(model_path)
        self.confidence = confidence
        # Classes to detect: 3: 'motorcycle', maybe custom ATV class if model is trained
        # In standard COCO, motorcycle is index 3. 
        # ATVs are often misclassified as motorcycles or trucks.
        self.target_classes = [3] # Motorcycle
        logger.info(f"Modelul YOLOv8 ({model_path}) a fost încărcat.")

    def detect(self, frame):
        """
        Detects target vehicles in a frame.
        Returns True if a target vehicle is found.
        """
        if frame is None:
            return False
            
        results = self.model(frame, conf=self.confidence, verbose=False)
        
        found = False
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id in self.target_classes:
                    found = True
                    logger.warning(f"DETECȚIE: {self.model.names[cls_id]} identificat!")
                    break
            if found: break
            
        return found

    def get_names(self):
        return self.model.names
