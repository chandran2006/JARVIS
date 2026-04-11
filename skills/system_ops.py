import os
import json
import re
import platform
import subprocess
import shutil
from typing import List, Dict, Any, Callable
from core.skill import Skill

_OS = platform.system()

# ── Windows app registry with multiple fallback paths ────────────────────────
_WIN_APPS = {
    "chrome":               ["chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "google chrome":        ["chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "firefox":              ["firefox.exe", r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "edge":                 ["msedge.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    "microsoft edge":       ["msedge.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    "notepad":              ["notepad.exe"],
    "notepad++":            ["notepad++.exe", r"C:\Program Files\Notepad++\notepad++.exe",
                             r"C:\Program Files (x86)\Notepad++\notepad++.exe"],
    "calculator":           ["calc.exe"],
    "calc":                 ["calc.exe"],
    "paint":                ["mspaint.exe"],
    "explorer":             ["explorer.exe"],
    "file explorer":        ["explorer.exe"],
    "cmd":                  ["cmd.exe"],
    "command prompt":       ["cmd.exe"],
    "terminal":             ["wt.exe", "cmd.exe"],
    "windows terminal":     ["wt.exe"],
    "powershell":           ["powershell.exe"],
    "vscode":               ["code.exe", r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe"],
    "visual studio code":   ["code.exe", r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe"],
    "spotify":              ["spotify.exe", r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe"],
    "vlc":                  ["vlc.exe", r"C:\Program Files\VideoLAN\VLC\vlc.exe"],
    "word":                 ["winword.exe", r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"],
    "excel":                ["excel.exe", r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"],
    "powerpoint":           ["powerpnt.exe", r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"],
    "task manager":         ["taskmgr.exe"],
    "settings":             ["ms-settings:"],
    "system settings":      ["ms-settings:"],
    "windows settings":     ["ms-settings:"],
    "the system":           ["ms-settings:"],
    "system":               ["ms-settings:"],
    "control":              ["control.exe"],
    "camera":               ["microsoft.windows.camera:"],
    "teams":                ["teams.exe", r"C:\Users\{user}\AppData\Local\Microsoft\Teams\current\Teams.exe"],
    "zoom":                 ["zoom.exe", r"C:\Users\{user}\AppData\Roaming\Zoom\bin\Zoom.exe"],
    "discord":              ["discord.exe", r"C:\Users\{user}\AppData\Local\Discord\app-*\Discord.exe"],
    "steam":                ["steam.exe", r"C:\Program Files (x86)\Steam\steam.exe"],
    "whatsapp":             ["whatsapp.exe", r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe"],
    "telegram":             ["telegram.exe", r"C:\Users\{user}\AppData\Roaming\Telegram Desktop\Telegram.exe"],
    "obs":                  ["obs64.exe", r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"],
    "brave":                ["brave.exe", r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"],
    "opera":                ["opera.exe", r"C:\Users\{user}\AppData\Local\Programs\Opera\opera.exe"],
    "winrar":               ["winrar.exe", r"C:\Program Files\WinRAR\WinRAR.exe"],
    "7zip":                 ["7zFM.exe", r"C:\Program Files\7-Zip\7zFM.exe"],
    "snipping tool":        ["SnippingTool.exe", "SnipSketch.exe"],
    "wordpad":              ["wordpad.exe"],
    "control panel":        ["control.exe"],
    "device manager":       ["devmgmt.msc"],
    "task scheduler":       ["taskschd.msc"],
    "registry editor":      ["regedit.exe"],
    "event viewer":         ["eventvwr.msc"],
    "paint 3d":             ["PaintStudio3D.exe"],
    "photos":               ["ms-photos:"],
    "maps":                 ["bingmaps:"],
    "clock":                ["ms-clock:"],
    "store":                ["ms-windows-store:"],
    "mail":                 ["outlookforwindows:"],
    "skype":                ["skype.exe", r"C:\Program Files (x86)\Microsoft\Skype for Desktop\Skype.exe"],
}

def _resolve_path(template: str) -> str:
    """Replace {user} placeholder with actual username."""
    return template.replace("{user}", os.environ.get("USERNAME", ""))

def _launch_windows(app_name: str) -> bool:
    """Try every known path for an app. Returns True if launched."""
    key = app_name.lower().strip()
    candidates = _WIN_APPS.get(key, [app_name])

    for candidate in candidates:
        candidate = _resolve_path(candidate)
        # ms- protocol URIs
        if candidate.endswith(":") or candidate.startswith("ms-"):
            try:
                subprocess.Popen(f'start {candidate}', shell=True)
                return True
            except Exception:
                continue
        # .msc files
        if candidate.endswith(".msc"):
            try:
                subprocess.Popen(["mmc", candidate], shell=False)
                return True
            except Exception:
                continue
        # Absolute path that exists
        if os.path.isabs(candidate) and os.path.exists(candidate):
            try:
                subprocess.Popen([candidate], shell=False)
                return True
            except Exception:
                continue
        # Glob paths (e.g. Discord app-*)
        if "*" in candidate:
            import glob
            matches = glob.glob(candidate)
            if matches:
                try:
                    subprocess.Popen([matches[0]], shell=False)
                    return True
                except Exception:
                    continue
        # On PATH
        if shutil.which(candidate):
            try:
                subprocess.Popen([candidate], shell=False)
                return True
            except Exception:
                continue
        # shell=True fallback (handles .exe names without full path)
        try:
            result = subprocess.Popen(candidate, shell=True)
            return True
        except Exception:
            continue
    return False


class SystemSkill(Skill):
    @property
    def name(self) -> str:
        return "system_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "set_volume",
                "description": "Set system speaker volume 0-100",
                "parameters": {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]}}},
            {"type": "function", "function": {
                "name": "open_app",
                "description": "Open any application by name — chrome, firefox, notepad, vscode, spotify, etc.",
                "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}}},
            {"type": "function", "function": {
                "name": "close_app",
                "description": "Close/kill a running application by name",
                "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}}},
            {"type": "function", "function": {
                "name": "get_battery",
                "description": "Get battery percentage and charging status",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "get_system_info",
                "description": "Get CPU, RAM, and disk usage",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "take_screenshot",
                "description": "Take a screenshot and save to Desktop",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "lock_screen",
                "description": "Lock the computer screen",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "set_brightness",
                "description": "Set screen brightness 0-100",
                "parameters": {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]}}},
            {"type": "function", "function": {
                "name": "shutdown_pc",
                "description": "Shutdown or restart the computer",
                "parameters": {"type": "object", "properties": {"restart": {"type": "boolean", "default": False}}, "required": []}}},
            {"type": "function", "function": {
                "name": "get_running_processes",
                "description": "List top running processes by CPU usage",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "get_clipboard",
                "description": "Read the current clipboard text content",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "set_clipboard",
                "description": "Copy text to the clipboard",
                "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
            {"type": "function", "function": {
                "name": "mute_volume",
                "description": "Mute or unmute system volume",
                "parameters": {"type": "object", "properties": {"mute": {"type": "boolean", "default": True}}, "required": []}}},
            {"type": "function", "function": {
                "name": "empty_recycle_bin",
                "description": "Empty the Windows Recycle Bin",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "get_ip_address",
                "description": "Get the local and public IP address",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "run_command",
                "description": "Run a safe shell command and return output",
                "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_volume":           self.set_volume,
            "open_app":             self.open_app,
            "close_app":            self.close_app,
            "get_battery":          self.get_battery,
            "get_system_info":      self.get_system_info,
            "take_screenshot":      self.take_screenshot,
            "lock_screen":          self.lock_screen,
            "set_brightness":       self.set_brightness,
            "shutdown_pc":          self.shutdown_pc,
            "get_running_processes":self.get_running_processes,
            "get_clipboard":        self.get_clipboard,
            "set_clipboard":        self.set_clipboard,
            "mute_volume":          self.mute_volume,
            "empty_recycle_bin":    self.empty_recycle_bin,
            "get_ip_address":       self.get_ip_address,
            "run_command":          self.run_command,
        }

    # ── volume ────────────────────────────────────────────────────────────────
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
                    script = (
                        f"$wsh = New-Object -ComObject WScript.Shell;"
                        f"1..50 | ForEach-Object {{ $wsh.SendKeys([char]174) }};"
                        f"$s = [int]({level}/2);"
                        f"1..$s | ForEach-Object {{ $wsh.SendKeys([char]175) }}"
                    )
                    subprocess.run(["powershell", "-c", script], capture_output=True, timeout=8)
            elif _OS == "Darwin":
                os.system(f"osascript -e 'set volume output volume {level}'")
            else:
                subprocess.run(["amixer", "set", "Master", f"{level}%"], check=True)
            return json.dumps({"status": "success", "message": f"Volume set to {level} percent, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def mute_volume(self, mute: bool = True) -> str:
        try:
            if _OS == "Windows":
                try:
                    from ctypes import cast, POINTER
                    from comtypes import CLSCTX_ALL
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices   = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    vol = cast(interface, POINTER(IAudioEndpointVolume))
                    vol.SetMute(1 if mute else 0, None)
                except Exception:
                    # Fallback: send mute key via PowerShell
                    key = "173"  # VK_VOLUME_MUTE
                    script = f"$wsh=New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]{key})"
                    subprocess.run(["powershell", "-c", script], capture_output=True, timeout=5)
            action = "muted" if mute else "unmuted"
            return json.dumps({"status": "success", "message": f"Volume {action}, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── open app ──────────────────────────────────────────────────────────────
    def open_app(self, app_name: str) -> str:
        key = app_name.lower().strip()

        # Websites that should open in browser, not as .exe
        _WEBSITES = {
            "youtube":   "https://www.youtube.com",
            "google":    "https://www.google.com",
            "gmail":     "https://mail.google.com",
            "maps":      "https://maps.google.com",
            "github":    "https://github.com",
            "netflix":   "https://www.netflix.com",
            "whatsapp":  "https://web.whatsapp.com",
            "chatgpt":   "https://chat.openai.com",
            "instagram": "https://www.instagram.com",
            "twitter":   "https://www.twitter.com",
            "facebook":  "https://www.facebook.com",
            "linkedin":  "https://www.linkedin.com",
            "reddit":    "https://www.reddit.com",
            "amazon":    "https://www.amazon.in",
            "flipkart":  "https://www.flipkart.com",
            "drive":     "https://drive.google.com",
            "meet":      "https://meet.google.com",
            "zoom":      "https://zoom.us",
            "stackoverflow": "https://stackoverflow.com",
        }

        # Detect "open <site> in <browser>"
        in_match = re.search(r"^(.+?)\s+in\s+(.+)$", key)
        if in_match:
            site_part    = in_match.group(1).strip()
            browser_part = in_match.group(2).strip()
            url = _WEBSITES.get(site_part, f"https://www.{site_part}.com")
            if _OS == "Windows":
                browser_paths = _WIN_APPS.get(browser_part, [browser_part + ".exe"])
                for bp in browser_paths:
                    bp = _resolve_path(bp)
                    if os.path.exists(bp):
                        subprocess.Popen([bp, url])
                        return json.dumps({"status": "success",
                                           "message": f"Opening {site_part} in {browser_part}, sir."})
                subprocess.Popen(f'start {browser_part} "{url}"', shell=True)
                return json.dumps({"status": "success",
                                   "message": f"Opening {site_part} in {browser_part}, sir."})

        # Pure website name → open in default browser (reuses existing tab if possible)
        if key in _WEBSITES:
            import webbrowser
            webbrowser.open(_WEBSITES[key])
            return json.dumps({"status": "success",
                               "message": f"Opening {key}, sir."})

        try:
            if _OS == "Windows":
                launched = _launch_windows(key)
                if launched:
                    return json.dumps({"status": "success", "message": f"Opening {app_name} now, sir."})
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                return json.dumps({"status": "success", "message": f"Opening {app_name}, sir."})
            elif _OS == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([key])
            return json.dumps({"status": "success", "message": f"Opening {app_name} now, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Could not open {app_name}: {e}"})

    # ── close app ─────────────────────────────────────────────────────────────
    def close_app(self, app_name: str) -> str:
        try:
            if _OS == "Windows":
                key = app_name.lower().strip()
                candidates = _WIN_APPS.get(key, [app_name + ".exe"])
                killed = False
                for c in candidates:
                    exe = os.path.basename(c)
                    if not exe.endswith(".exe"):
                        exe = app_name + ".exe"
                    r = subprocess.run(["taskkill", "/f", "/im", exe], capture_output=True)
                    if r.returncode == 0:
                        killed = True
                        break
                if not killed:
                    subprocess.run(["taskkill", "/f", "/im", app_name + ".exe"], capture_output=True)
            elif _OS == "Darwin":
                subprocess.run(["pkill", "-x", app_name], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", app_name], capture_output=True)
            return json.dumps({"status": "success", "message": f"{app_name} has been closed, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── battery ───────────────────────────────────────────────────────────────
    def get_battery(self) -> str:
        try:
            import psutil
            b = psutil.sensors_battery()
            if b is None:
                return json.dumps({"status": "success", "message": "No battery detected. Running on AC power."})
            state = "charging" if b.power_plugged else "discharging"
            mins  = int(b.secsleft / 60) if b.secsleft > 0 and not b.power_plugged else None
            extra = f", about {mins} minutes remaining" if mins else ""
            return json.dumps({"status": "success",
                               "message": f"Battery is at {b.percent:.0f} percent and {state}{extra}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── system info ───────────────────────────────────────────────────────────
    def get_system_info(self) -> str:
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=0.5)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            freq = psutil.cpu_freq()
            freq_str = f" at {freq.current:.0f} MHz" if freq else ""
            msg = (f"CPU is at {cpu:.0f} percent{freq_str}, "
                   f"RAM is {ram.percent:.0f} percent used "
                   f"({ram.used//(1024**3):.1f} of {ram.total//(1024**3):.1f} gigabytes), "
                   f"and disk has {disk.free//(1024**3):.1f} gigabytes free out of {disk.total//(1024**3):.1f}.")
            return json.dumps({"status": "success", "message": msg})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── screenshot ────────────────────────────────────────────────────────────
    def take_screenshot(self) -> str:
        try:
            from PIL import ImageGrab
            from datetime import datetime
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            fname   = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            ImageGrab.grab().save(os.path.join(desktop, fname))
            return json.dumps({"status": "success", "message": f"Screenshot saved to your Desktop as {fname}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── lock ──────────────────────────────────────────────────────────────────
    def lock_screen(self) -> str:
        try:
            if _OS == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            elif _OS == "Darwin":
                os.system("pmset displaysleepnow")
            else:
                os.system("gnome-screensaver-command -l")
            return json.dumps({"status": "success", "message": "Screen locked, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── brightness ────────────────────────────────────────────────────────────
    def set_brightness(self, level: int) -> str:
        level = max(0, min(100, int(level)))
        try:
            if _OS == "Windows":
                try:
                    import screen_brightness_control as sbc
                    sbc.set_brightness(level)
                except ImportError:
                    script = (f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                              f".WmiSetBrightness(1,{level})")
                    subprocess.run(["powershell", "-c", script], capture_output=True, timeout=8)
                return json.dumps({"status": "success", "message": f"Brightness set to {level} percent, sir."})
            elif _OS == "Darwin":
                val = level / 100
                os.system(f"osascript -e 'tell application \"System Events\" to set brightness of display 1 to {val}'")
                return json.dumps({"status": "success", "message": f"Brightness set to {level} percent, sir."})
            else:
                return json.dumps({"status": "error", "message": "Brightness control not supported on this OS."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── shutdown ──────────────────────────────────────────────────────────────
    def shutdown_pc(self, restart: bool = False) -> str:
        try:
            if _OS == "Windows":
                cmd = "shutdown /r /t 5" if restart else "shutdown /s /t 5"
            elif _OS == "Darwin":
                cmd = "sudo shutdown -r now" if restart else "sudo shutdown -h now"
            else:
                cmd = "sudo reboot" if restart else "sudo shutdown -h now"
            action = "restarting" if restart else "shutting down"
            subprocess.Popen(cmd, shell=True)
            return json.dumps({"status": "success", "message": f"System is {action} in 5 seconds, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── processes ─────────────────────────────────────────────────────────────
    def get_running_processes(self) -> str:
        try:
            import psutil
            procs = sorted(psutil.process_iter(["name", "cpu_percent", "memory_percent"]),
                           key=lambda p: p.info["cpu_percent"] or 0, reverse=True)[:8]
            parts = [f"{p.info['name']} ({p.info['cpu_percent']:.1f}% CPU)" for p in procs if p.info["name"]]
            return json.dumps({"status": "success",
                               "message": "Top processes: " + ", ".join(parts) + "."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── clipboard ─────────────────────────────────────────────────────────────
    def get_clipboard(self) -> str:
        try:
            try:
                import pyperclip
                text = pyperclip.paste()
            except Exception:
                result = subprocess.run(["powershell", "-c", "Get-Clipboard"],
                                        capture_output=True, text=True, timeout=5)
                text = result.stdout.strip()
            if not text:
                return json.dumps({"status": "success", "message": "Clipboard is empty, sir."})
            short = text[:200] + ("..." if len(text) > 200 else "")
            return json.dumps({"status": "success", "message": f"Clipboard contains: {short}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def set_clipboard(self, text: str) -> str:
        try:
            try:
                import pyperclip
                pyperclip.copy(text)
            except Exception:
                subprocess.run(["powershell", "-c", f"Set-Clipboard -Value '{text}'"],
                               capture_output=True, timeout=5)
            return json.dumps({"status": "success", "message": "Text copied to clipboard, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── recycle bin ───────────────────────────────────────────────────────────
    def empty_recycle_bin(self) -> str:
        try:
            subprocess.run(["powershell", "-c", "Clear-RecycleBin -Force"], capture_output=True, timeout=10)
            return json.dumps({"status": "success", "message": "Recycle Bin emptied, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── IP address ────────────────────────────────────────────────────────────
    def get_ip_address(self) -> str:
        try:
            import socket, requests
            local_ip = socket.gethostbyname(socket.gethostname())
            try:
                public_ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
            except Exception:
                public_ip = "unavailable"
            return json.dumps({"status": "success",
                               "message": f"Your local IP is {local_ip} and public IP is {public_ip}."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # ── run command ───────────────────────────────────────────────────────────
    def run_command(self, command: str) -> str:
        # Safety: block destructive commands
        blocked = ["rm -rf", "del /f", "format", "mkfs", "dd if=", ":(){", "shutdown", "rmdir /s"]
        if any(b in command.lower() for b in blocked):
            return json.dumps({"status": "error", "message": "That command is blocked for safety, sir."})
        try:
            result = subprocess.run(command, shell=True, capture_output=True,
                                    text=True, timeout=15)
            out = (result.stdout or result.stderr or "Command executed.").strip()[:300]
            return json.dumps({"status": "success", "message": out})
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "error", "message": "Command timed out, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
