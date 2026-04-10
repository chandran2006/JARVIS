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
            {"type":"function","function":{"name":"get_current_time",
             "description":"Get the current time",
             "parameters":{"type":"object","properties":{},"required":[]}}},
            {"type":"function","function":{"name":"get_current_date",
             "description":"Get today's date",
             "parameters":{"type":"object","properties":{},"required":[]}}},
            {"type":"function","function":{"name":"get_current_datetime",
             "description":"Get the current date and time together",
             "parameters":{"type":"object","properties":{},"required":[]}}},
            {"type":"function","function":{"name":"get_day_of_week",
             "description":"Get what day of the week it is today",
             "parameters":{"type":"object","properties":{},"required":[]}}},
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
        t   = now.strftime("%I:%M %p")
        h   = now.hour
        greeting = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"
        return json.dumps({"status":"success","message":f"{greeting}, sir. The time is {t}."})

    def get_current_date(self) -> str:
        d = datetime.now().strftime("%A, %B %d, %Y")
        return json.dumps({"status":"success","message":f"Today is {d}."})

    def get_current_datetime(self) -> str:
        dt = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        return json.dumps({"status":"success","message":f"It is {dt}."})

    def get_day_of_week(self) -> str:
        day = datetime.now().strftime("%A")
        return json.dumps({"status":"success","message":f"Today is {day}."})
