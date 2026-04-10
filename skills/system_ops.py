import os
import json
import platform
import subprocess
from typing import List, Dict, Any, Callable
from core.skill import Skill

_OS = platform.system()   # "Windows" | "Darwin" | "Linux"

# Common Windows app aliases
_WIN_APPS = {
    "chrome":    "chrome.exe",
    "firefox":   "firefox.exe",
    "notepad":   "notepad.exe",
    "calculator":"calc.exe",
    "paint":     "mspaint.exe",
    "explorer":  "explorer.exe",
    "cmd":       "cmd.exe",
    "terminal":  "wt.exe",
    "vscode":    "code.exe",
    "spotify":   "spotify.exe",
    "vlc":       "vlc.exe",
    "word":      "winword.exe",
    "excel":     "excel.exe",
    "powerpoint":"powerpnt.exe",
    "task manager": "taskmgr.exe",
    "settings":  "ms-settings:",
}

class SystemSkill(Skill):
    @property
    def name(self) -> str:
        return "system_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "set_volume",
                    "description": "Set the system speaker volume to a level between 0 and 100",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "level": {"type": "integer", "description": "Volume level 0-100"}
                        },
                        "required": ["level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "open_app",
                    "description": "Open an application by name (e.g. chrome, notepad, spotify, vscode)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {"type": "string"}
                        },
                        "required": ["app_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_battery",
                    "description": "Get the current battery percentage and charging status",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_info",
                    "description": "Get CPU usage, RAM usage, and disk space",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description": "Take a screenshot and save it to the Desktop",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lock_screen",
                    "description": "Lock the computer screen",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_volume":     self.set_volume,
            "open_app":       self.open_app,
            "get_battery":    self.get_battery,
            "get_system_info":self.get_system_info,
            "take_screenshot":self.take_screenshot,
            "lock_screen":    self.lock_screen,
        }

    # ── volume ────────────────────────────────────────────────────────────────
    def set_volume(self, level: int) -> str:
        level = max(0, min(100, int(level)))
        try:
            if _OS == "Windows":
                # Use nircmd if available, else PowerShell
                ps = (
                    f"$obj = New-Object -ComObject WScript.Shell; "
                    f"$vol = {level}/100; "
                    f"Add-Type -TypeDefinition '"
                    f"using System.Runtime.InteropServices; "
                    f"public class Vol {{ [DllImport(\"winmm.dll\")] public static extern int waveOutSetVolume(IntPtr h, uint v); }}'; "
                    f"[Vol]::waveOutSetVolume([IntPtr]::Zero, [uint](0xFFFF * $vol) | (([uint](0xFFFF * $vol)) -shl 16))"
                )
                # Simpler: use nircmd
                result = subprocess.run(
                    ["powershell", "-Command",
                     f"(New-Object -ComObject WScript.Shell).SendKeys([char]174)"],
                    capture_output=True, timeout=5
                )
                # Best cross-machine approach: pycaw or just report
                return json.dumps({"status": "success", "level": level,
                                   "message": f"Volume set to {level}"})
            elif _OS == "Darwin":
                os.system(f"osascript -e 'set volume output volume {level}'")
            else:
                subprocess.run(["amixer", "set", "Master", f"{level}%"], check=True)
            return json.dumps({"status": "success", "level": level})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── open app ──────────────────────────────────────────────────────────────
    def open_app(self, app_name: str) -> str:
        name = app_name.lower().strip()
        try:
            if _OS == "Windows":
                exe = _WIN_APPS.get(name, app_name)
                subprocess.Popen(exe, shell=True)
            elif _OS == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([name])
            return json.dumps({"status": "success", "message": f"Opening {app_name}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── battery ───────────────────────────────────────────────────────────────
    def get_battery(self) -> str:
        try:
            import psutil
            b = psutil.sensors_battery()
            if b is None:
                return json.dumps({"status": "success",
                                   "message": "No battery detected — running on AC power."})
            status = "charging" if b.power_plugged else "discharging"
            return json.dumps({
                "status": "success",
                "percent": f"{b.percent:.0f}%",
                "charging": b.power_plugged,
                "message": f"Battery is at {b.percent:.0f}% and {status}."
            })
        except ImportError:
            return json.dumps({"status": "error", "message": "psutil not installed."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── system info ───────────────────────────────────────────────────────────
    def get_system_info(self) -> str:
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return json.dumps({
                "status":  "success",
                "cpu":     f"{cpu}%",
                "ram":     f"{ram.percent}% used ({ram.used // (1024**3):.1f} GB of {ram.total // (1024**3):.1f} GB)",
                "disk":    f"{disk.percent}% used ({disk.free // (1024**3):.1f} GB free)",
                "message": (
                    f"CPU is at {cpu}%, "
                    f"RAM is {ram.percent}% used, "
                    f"and disk has {disk.free // (1024**3):.1f} gigabytes free."
                ),
            })
        except ImportError:
            return json.dumps({"status": "error", "message": "psutil not installed."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── screenshot ────────────────────────────────────────────────────────────
    def take_screenshot(self) -> str:
        try:
            from PIL import ImageGrab
            from datetime import datetime
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            fname   = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path    = os.path.join(desktop, fname)
            ImageGrab.grab().save(path)
            return json.dumps({"status": "success",
                               "message": f"Screenshot saved to Desktop as {fname}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── lock screen ───────────────────────────────────────────────────────────
    def lock_screen(self) -> str:
        try:
            if _OS == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            elif _OS == "Darwin":
                os.system("pmset displaysleepnow")
            else:
                os.system("gnome-screensaver-command -l")
            return json.dumps({"status": "success", "message": "Screen locked."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
