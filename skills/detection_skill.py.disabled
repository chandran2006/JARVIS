from core.skill import Skill
import torch
from ultralytics import YOLO
import cv2
import os
import time

class DetectionSkill(Skill):
    """
    Skill for detecting objects using YOLOv8, optimized for Apple Silicon (MPS).
    """
    
    def __init__(self):
        self.model = None
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"DetectionSkill: Using device '{self.device}'")

    @property
    def name(self):
        return "detection_skill"

    def _load_model(self):
        if self.model is None:
            print("Loading YOLOv8 model...")
            try:
                # Load the nano model for speed
                self.model = YOLO("yolov8n.pt") 
                self.model.to(self.device)
                print("YOLOv8 model loaded.")
            except Exception as e:
                print(f"Error loading YOLO model: {e}")
    
    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "detect_objects",
                    "description": "Detect objects in the current view using the camera.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
        ]

    def get_functions(self):
        return {
            "detect_objects": self.detect_objects
        }

    def detect_objects(self, **kwargs):

        """
        Captures a frame and runs object detection on it.
        """
        try:
            self._load_model()
            if not self.model:
                 return "Error: YOLO model failed to load."
            
            # Capture image
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Error: Could not open camera for detection."
            
            # Warmup
            time.sleep(1) 
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return "Error: Failed to capture image for detection."
            
            # Run inference
            results = self.model(frame)
            
            # Process results
            detections = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = self.model.names[cls_id]
                    detections.append(f"{label} ({conf:.2f})")
            
            if not detections:
                return "No objects detected."
            
            # Save the annotated image
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            os.makedirs(assets_dir, exist_ok=True)
            timestamp = int(time.time())
            filepath = os.path.join(assets_dir, f"detection_{timestamp}.jpg")
            
            # Plot results on the frame
            annotated_frame = results[0].plot()
            cv2.imwrite(filepath, annotated_frame)
            
            return f"Detected objects: {', '.join(detections)}. Image saved to {filepath}"
            
        except Exception as e:
            return f"Error during object detection: {str(e)}"
