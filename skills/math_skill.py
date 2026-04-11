import json
import math
import re
from typing import List, Dict, Any, Callable
from core.skill import Skill


class MathSkill(Skill):
    @property
    def name(self) -> str:
        return "math_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "calculate",
                "description": "Evaluate any math expression: arithmetic, percentages, square roots, powers, etc.",
                "parameters": {"type": "object",
                               "properties": {"expression": {"type": "string",
                                                             "description": "Math expression e.g. '25 * 4', 'sqrt(144)', '15% of 200'"}},
                               "required": ["expression"]}}},
            {"type": "function", "function": {
                "name": "unit_convert",
                "description": "Convert between units: km/miles, kg/lbs, celsius/fahrenheit, meters/feet, liters/gallons",
                "parameters": {"type": "object",
                               "properties": {
                                   "value":     {"type": "number"},
                                   "from_unit": {"type": "string"},
                                   "to_unit":   {"type": "string"}},
                               "required": ["value", "from_unit", "to_unit"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "calculate":    self.calculate,
            "unit_convert": self.unit_convert,
        }

    def calculate(self, expression: str) -> str:
        try:
            expr = expression.lower().strip()
            # Handle "X% of Y"
            pct = re.match(r"([\d.]+)\s*%\s*of\s*([\d.]+)", expr)
            if pct:
                result = float(pct.group(1)) / 100 * float(pct.group(2))
                return json.dumps({"status": "success",
                                   "message": f"{pct.group(1)}% of {pct.group(2)} is {result:g}."})
            # Safe eval with math functions
            allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            allowed.update({"abs": abs, "round": round, "pow": pow})
            expr_clean = re.sub(r"[^0-9+\-*/().%^ a-z]", "", expr)
            expr_clean = expr_clean.replace("^", "**").replace("x", "*")
            result = eval(expr_clean, {"__builtins__": {}}, allowed)  # noqa: S307
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return json.dumps({"status": "success",
                               "message": f"The answer is {result:,}."})
        except Exception as e:
            return json.dumps({"status": "error",
                               "message": f"I could not calculate that: {e}"})

    def unit_convert(self, value: float, from_unit: str, to_unit: str) -> str:
        f, t = from_unit.lower().strip(), to_unit.lower().strip()
        try:
            conversions = {
                ("km", "miles"):      lambda v: v * 0.621371,
                ("miles", "km"):      lambda v: v * 1.60934,
                ("kg", "lbs"):        lambda v: v * 2.20462,
                ("lbs", "kg"):        lambda v: v * 0.453592,
                ("celsius", "fahrenheit"): lambda v: v * 9/5 + 32,
                ("fahrenheit", "celsius"): lambda v: (v - 32) * 5/9,
                ("meters", "feet"):   lambda v: v * 3.28084,
                ("feet", "meters"):   lambda v: v * 0.3048,
                ("cm", "inches"):     lambda v: v * 0.393701,
                ("inches", "cm"):     lambda v: v * 2.54,
                ("liters", "gallons"):lambda v: v * 0.264172,
                ("gallons", "liters"):lambda v: v * 3.78541,
                ("m", "feet"):        lambda v: v * 3.28084,
                ("feet", "m"):        lambda v: v * 0.3048,
                ("c", "f"):           lambda v: v * 9/5 + 32,
                ("f", "c"):           lambda v: (v - 32) * 5/9,
            }
            fn = conversions.get((f, t))
            if fn:
                result = round(fn(value), 4)
                return json.dumps({"status": "success",
                                   "message": f"{value} {from_unit} is {result} {to_unit}."})
            return json.dumps({"status": "error",
                               "message": f"I don't know how to convert {from_unit} to {to_unit}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
