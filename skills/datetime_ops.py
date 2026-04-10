import json
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill

class DateTimeSkill(Skill):
    @property
    def name(self) -> str:
        return "datetime_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current time",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_date",
                    "description": "Get today's date",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_datetime",
                    "description": "Get both the current date and time together",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_day_of_week",
                    "description": "Get what day of the week it is today",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_current_time":     self.get_current_time,
            "get_current_date":     self.get_current_date,
            "get_current_datetime": self.get_current_datetime,
            "get_day_of_week":      self.get_day_of_week,
        }

    def get_current_time(self) -> str:
        now = datetime.now()
        return json.dumps({"time": now.strftime("%I:%M %p")})

    def get_current_date(self) -> str:
        now = datetime.now()
        return json.dumps({"date": now.strftime("%A, %B %d, %Y")})

    def get_current_datetime(self) -> str:
        now = datetime.now()
        return json.dumps({
            "datetime": now.strftime("%A, %B %d, %Y at %I:%M %p"),
        })

    def get_day_of_week(self) -> str:
        return json.dumps({"day": datetime.now().strftime("%A")})
