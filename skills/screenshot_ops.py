import os
import json
import platform
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill

_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

class ScreenshotSkill(Skill):
    @property
    def name(self) -> str:
        return "screenshot_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "capture_screenshot",
                "description": "Take a screenshot of the entire screen and save to Desktop",
                "parameters": {"type": "object",
                               "properties": {
                                   "filename": {"type": "string",
                                               "description": "Optional custom filename without extension"}},
                               "required": []}}}
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {"capture_screenshot": self.capture_screenshot}

    def capture_screenshot(self, filename: str = None) -> str:
        try:
            from PIL import ImageGrab
            if not filename:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if not filename.endswith(".png"):
                filename += ".png"
            path = os.path.join(_DESKTOP, filename)
            ImageGrab.grab().save(path)
            return json.dumps({"status": "success",
                               "message": f"Screenshot saved to your Desktop as {filename}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

