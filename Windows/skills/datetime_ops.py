import json
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill

class DateTimeSkill(Skill):
    """Skill for providing current date and time information."""
    
    @property
    def name(self) -> str:
        return "datetime_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_current_datetime",
                    "description": "Get the current date and time in a human-readable format",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get only the current time",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_date",
                    "description": "Get only the current date",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_current_datetime": self.get_current_datetime,
            "get_current_time": self.get_current_time,
            "get_current_date": self.get_current_date
        }

    def get_current_datetime(self) -> str:
        """Get current date and time in IST."""
        try:
            now = datetime.now()
            formatted = now.strftime("%A, %B %d, %Y at %I:%M %p")
            
            return json.dumps({
                "status": "success",
                "datetime": formatted,
                "timezone": "IST"
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def get_current_time(self) -> str:
        """Get current time only."""
        try:
            now = datetime.now()
            formatted = now.strftime("%I:%M %p")
            
            return json.dumps({
                "status": "success",
                "time": formatted
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def get_current_date(self) -> str:
        """Get current date only."""
        try:
            now = datetime.now()
            formatted = now.strftime("%A, %B %d, %Y")
            
            return json.dumps({
                "status": "success",
                "date": formatted
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })