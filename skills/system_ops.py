import os
import json
import platform
import subprocess
from typing import List, Dict, Any, Callable
from core.skill import Skill

_OS = platform.system()

_WIN_APPS = {
    "chrome":"chrome.exe","google chrome":"chrome.exe",
    "firefox":"firefox.exe","edge":"msedge.exe",
    "notepad":"notepad.exe","notepad++":"notepad++.exe",
    "calculator":"calc.exe","calc":"calc.exe",
    "paint":"mspaint.exe","paint 3d":"mspaint3d.exe",
    "explorer":"explorer.exe","file explorer":"explorer.exe",
    "cmd":"cmd.exe","command prompt":"cmd.exe",
    "terminal":"wt.exe","windows terminal":"wt.exe",
    "powershell":"powershell.exe",
    "vscode":"code.exe","visual studio code":"code.exe",
    "spotify":"spotify.exe","vlc":"vlc.exe",
    "word":"winword.exe","excel":"excel.exe","powerpoint":"powerpnt.exe",
    "task manager":"taskmgr.exe","settings":"ms-settings:",
    "camera":"microsoft.windows.camera:","mail":"outlookforwindows:",
    "teams":"teams.exe","zoom":"zoom.exe","discord":"discord.exe",
    "steam":"steam.exe","whatsapp":"whatsapp.exe",
}

class SystemSkill(Skill):
    @property
    def name(self) -> str:
        return "system_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type":"function","function":{"name":"set_volume",
             "description":"Set system speaker volume 0-100",
             "parameters":{"type":"object","properties":{"level":{"type":"integer"}},"required":["level"]}}},
            {"type":"function","function":{"name":"open_app",
             "description":"Open any application by name",
             "parameters":{"type":"object","properties":{"app_name":{"type":"string"}},"required":["app_name"]}}},
            {"type":"function","function":{"name":"get_battery",
             "description":"Get battery percentage and charging status",
             "parameters":{"type":"object","properties":{},"required":[]}}},
            {"type":"function","function":{"name":"get_system_info",
             "description":"Get CPU, RAM, and disk usage",
             "parameters":{"type":"object","properties":{},"required":[]}}},
            {"type":"function","function":{"name":"take_screenshot",
             "description":"Take a screenshot and save to Desktop",
             "parameters":{"type":"object","properties":{},"required":[]}}},
            {"type":"function","function":{"name":"lock_screen",
             "description":"Lock the computer screen",
             "parameters":{"type":"object","properties":{},"required":[]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_volume":      self.set_volume,
            "open_app":        self.open_app,
            "get_battery":     self.get_battery,
            "get_system_info": self.get_system_info,
            "take_screenshot": self.take_screenshot,
            "lock_screen":     self.lock_screen,
        }

    def set_volume(self, level: int) -> str:
        level = max(0, min(100, int(level)))
        try:
            if _OS == "Windows":
                try:
                    from ctypes import cast, POINTER
                    from comtypes import CLSCTX_ALL
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices   = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    vol = cast(interface, POINTER(IAudioEndpointVolume))
                    vol.SetMasterVolumeLevelScalar(level / 100, None)
                except Exception:
                    # PowerShell fallback
                    script = (
                        f"$wsh = New-Object -ComObject WScript.Shell;"
                        f"1..50 | ForEach-Object {{ $wsh.SendKeys([char]174) }};"
                        f"$s = [int]({level}/2);"
                        f"1..$s | ForEach-Object {{ $wsh.SendKeys([char]175) }}"
                    )
                    subprocess.run(["powershell","-c",script], capture_output=True, timeout=8)
            elif _OS == "Darwin":
                os.system(f"osascript -e 'set volume output volume {level}'")
            else:
                subprocess.run(["amixer","set","Master",f"{level}%"], check=True)
            return json.dumps({"status":"success","message":f"Volume set to {level} percent, sir."})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})

    def open_app(self, app_name: str) -> str:
        key = app_name.lower().strip()
        try:
            if _OS == "Windows":
                exe = _WIN_APPS.get(key, app_name)
                subprocess.Popen(exe, shell=True)
            elif _OS == "Darwin":
                subprocess.Popen(["open","-a",app_name])
            else:
                subprocess.Popen([key])
            return json.dumps({"status":"success","message":f"Opening {app_name} now, sir."})
        except Exception as e:
            return json.dumps({"status":"error","message":f"Could not open {app_name}: {e}"})

    def get_battery(self) -> str:
        try:
            import psutil
            b = psutil.sensors_battery()
            if b is None:
                return json.dumps({"status":"success","message":"No battery detected. Running on AC power."})
            state = "charging" if b.power_plugged else "discharging"
            mins  = int(b.secsleft / 60) if b.secsleft > 0 and not b.power_plugged else None
            extra = f", about {mins} minutes remaining" if mins else ""
            return json.dumps({"status":"success",
                               "message":f"Battery is at {b.percent:.0f} percent and {state}{extra}."})
        except ImportError:
            return json.dumps({"status":"error","message":"psutil is not installed."})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})

    def get_system_info(self) -> str:
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=0.5)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            msg  = (f"CPU is at {cpu:.0f} percent, "
                    f"RAM is {ram.percent:.0f} percent used "
                    f"({ram.used//(1024**3):.1f} of {ram.total//(1024**3):.1f} gigabytes), "
                    f"and disk has {disk.free//(1024**3):.1f} gigabytes free.")
            return json.dumps({"status":"success","message":msg})
        except ImportError:
            return json.dumps({"status":"error","message":"psutil is not installed."})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})

    def take_screenshot(self) -> str:
        try:
            from PIL import ImageGrab
            from datetime import datetime
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            fname   = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            ImageGrab.grab().save(os.path.join(desktop, fname))
            return json.dumps({"status":"success","message":f"Screenshot saved to your Desktop as {fname}."})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})

    def lock_screen(self) -> str:
        try:
            if _OS == "Windows":
                subprocess.run(["rundll32.exe","user32.dll,LockWorkStation"])
            elif _OS == "Darwin":
                os.system("pmset displaysleepnow")
            else:
                os.system("gnome-screensaver-command -l")
            return json.dumps({"status":"success","message":"Screen locked, sir."})
        except Exception as e:
            return json.dumps({"status":"error","message":str(e)})
