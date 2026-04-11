import os
import json
import time
from typing import List, Dict, Any, Callable
from core.skill import Skill

_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

class CameraSkill(Skill):
    @property
    def name(self) -> str:
        return "camera_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "take_photo",
                "description": "Take a photo using the webcam and save it to the Desktop",
                "parameters": {"type": "object", "properties": {}, "required": []}}}
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {"take_photo": self.take_photo}

    def take_photo(self) -> str:
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return json.dumps({"status": "error",
                                   "message": "Could not open the camera, sir."})
            # Warm up camera (first few frames are dark)
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return json.dumps({"status": "error",
                                   "message": "Failed to capture image from camera, sir."})
            fname    = f"photo_{int(time.time())}.jpg"
            filepath = os.path.join(_DESKTOP, fname)
            cv2.imwrite(filepath, frame)
            return json.dumps({"status": "success",
                               "message": f"Photo taken and saved to your Desktop as {fname}, sir."})
        except ImportError:
            return json.dumps({"status": "error",
                               "message": "OpenCV is not installed. Run pip install opencv-python."})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Camera error: {e}"})
