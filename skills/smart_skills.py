import json
import os
import platform
import subprocess
from typing import List, Dict, Any, Callable
from core.skill import Skill

class SmartSystemSkill(Skill):
    """Enhanced system control with cross-platform support and automation."""
    
    priority = 90  # High priority
    
    def __init__(self):
        self.os_type = platform.system()
        self.automation_history = []
    
    @property
    def name(self) -> str:
        return "smart_system_skill"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "set_volume",
                    "description": "Set system volume (0-100) with cross-platform support",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "level": {"type": "integer", "minimum": 0, "maximum": 100}
                        },
                        "required": ["level"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Open any application with smart detection",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {"type": "string", "description": "Application name (e.g., 'chrome', 'notepad', 'spotify')"}
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "system_command",
                    "description": "Execute safe system commands",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to execute"},
                            "safe_mode": {"type": "boolean", "description": "Enable safety checks", "default": True}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_info",
                    "description": "Get detailed system information",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_automation",
                    "description": "Create a multi-step automation sequence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "steps": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["name", "steps"]
                    }
                }
            }
        ]
    
    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_volume": self.set_volume,
            "open_application": self.open_application,
            "system_command": self.system_command,
            "get_system_info": self.get_system_info,
            "create_automation": self.create_automation
        }
    
    def set_volume(self, level: int) -> str:
        """Cross-platform volume control."""
        try:
            level = max(0, min(100, level))
            
            if self.os_type == "Darwin":  # macOS
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
            elif self.os_type == "Windows":
                # Use nircmd or powershell
                script = f"(New-Object -ComObject WScript.Shell).SendKeys([char]174)"  # Mute toggle
                subprocess.run(["powershell", "-Command", script], check=True)
            elif self.os_type == "Linux":
                subprocess.run(["amixer", "set", "Master", f"{level}%"], check=True)
            
            return json.dumps({"status": "success", "level": level, "platform": self.os_type})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def open_application(self, app_name: str) -> str:
        """Smart application launcher with common app detection."""
        
        app_map = {
            "chrome": {"Darwin": "Google Chrome", "Windows": "chrome.exe", "Linux": "google-chrome"},
            "firefox": {"Darwin": "Firefox", "Windows": "firefox.exe", "Linux": "firefox"},
            "vscode": {"Darwin": "Visual Studio Code", "Windows": "code.exe", "Linux": "code"},
            "spotify": {"Darwin": "Spotify", "Windows": "spotify.exe", "Linux": "spotify"},
            "notepad": {"Darwin": "TextEdit", "Windows": "notepad.exe", "Linux": "gedit"},
            "terminal": {"Darwin": "Terminal", "Windows": "cmd.exe", "Linux": "gnome-terminal"}
        }
        
        try:
            app_lower = app_name.lower()
            actual_app = app_map.get(app_lower, {}).get(self.os_type, app_name)
            
            if self.os_type == "Darwin":
                subprocess.run(["open", "-a", actual_app], check=True)
            elif self.os_type == "Windows":
                subprocess.run(["start", actual_app], shell=True, check=True)
            elif self.os_type == "Linux":
                subprocess.run([actual_app], check=True)
            
            return json.dumps({"status": "success", "app": actual_app, "platform": self.os_type})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e), "app": app_name})
    
    def system_command(self, command: str, safe_mode: bool = True) -> str:
        """Execute system commands with safety checks."""
        
        dangerous_commands = ["rm -rf", "del /f", "format", "mkfs", "dd if="]
        
        if safe_mode:
            if any(danger in command.lower() for danger in dangerous_commands):
                return json.dumps({"status": "blocked", "reason": "Dangerous command detected"})
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            return json.dumps({
                "status": "success",
                "output": result.stdout[:500],
                "error": result.stderr[:200] if result.stderr else None
            })
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "error", "message": "Command timeout"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def get_system_info(self) -> str:
        """Get comprehensive system information."""
        
        import psutil
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            info = {
                "platform": self.os_type,
                "platform_version": platform.version(),
                "processor": platform.processor(),
                "cpu_usage": f"{cpu_percent}%",
                "memory": {
                    "total": f"{memory.total / (1024**3):.2f} GB",
                    "used": f"{memory.used / (1024**3):.2f} GB",
                    "percent": f"{memory.percent}%"
                },
                "disk": {
                    "total": f"{disk.total / (1024**3):.2f} GB",
                    "used": f"{disk.used / (1024**3):.2f} GB",
                    "free": f"{disk.free / (1024**3):.2f} GB",
                    "percent": f"{disk.percent}%"
                }
            }
            
            return json.dumps({"status": "success", "info": info})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def create_automation(self, name: str, steps: List[str]) -> str:
        """Create and save automation sequences."""
        
        automation = {
            "name": name,
            "steps": steps,
            "created": __import__('time').time()
        }
        
        self.automation_history.append(automation)
        
        return json.dumps({
            "status": "success",
            "message": f"Automation '{name}' created with {len(steps)} steps",
            "automation": automation
        })


class SmartWebSkill(Skill):
    """Enhanced web operations with history and smart search."""
    
    priority = 80
    
    def __init__(self):
        self.search_history = []
    
    @property
    def name(self) -> str:
        return "smart_web_skill"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "smart_search",
                    "description": "Intelligent web search with multiple engines",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "engine": {"type": "string", "enum": ["google", "youtube", "github", "stackoverflow"], "default": "google"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_url",
                    "description": "Open any URL in default browser",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_search_history",
                    "description": "Get recent search history",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            }
        ]
    
    def get_functions(self) -> Dict[str, Callable]:
        return {
            "smart_search": self.smart_search,
            "open_url": self.open_url,
            "get_search_history": self.get_search_history
        }
    
    def smart_search(self, query: str, engine: str = "google") -> str:
        """Multi-engine search support."""
        
        import webbrowser
        
        engines = {
            "google": f"https://www.google.com/search?q={query}",
            "youtube": f"https://www.youtube.com/results?search_query={query}",
            "github": f"https://github.com/search?q={query}",
            "stackoverflow": f"https://stackoverflow.com/search?q={query}"
        }
        
        try:
            url = engines.get(engine, engines["google"])
            webbrowser.open(url)
            
            self.search_history.append({
                "query": query,
                "engine": engine,
                "timestamp": __import__('time').time()
            })
            
            return json.dumps({"status": "success", "query": query, "engine": engine})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def open_url(self, url: str) -> str:
        """Open any URL."""
        
        import webbrowser
        
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            webbrowser.open(url)
            return json.dumps({"status": "success", "url": url})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def get_search_history(self) -> str:
        """Return recent searches."""
        
        recent = self.search_history[-10:]
        return json.dumps({"status": "success", "history": recent, "count": len(recent)})


class SmartFileSkill(Skill):
    """Enhanced file operations with safety and smart features."""
    
    priority = 75
    
    @property
    def name(self) -> str:
        return "smart_file_skill"
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Create a file with content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                            "overwrite": {"type": "boolean", "default": False}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read file contents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List files in a directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "default": "."}
                        },
                        "required": []
                    }
                }
            }
        ]
    
    def get_functions(self) -> Dict[str, Callable]:
        return {
            "create_file": self.create_file,
            "read_file": self.read_file,
            "list_directory": self.list_directory
        }
    
    def create_file(self, path: str, content: str, overwrite: bool = False) -> str:
        """Create file with safety checks."""
        
        try:
            if os.path.exists(path) and not overwrite:
                return json.dumps({"status": "error", "message": "File exists. Set overwrite=true to replace."})
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return json.dumps({"status": "success", "path": path, "size": len(content)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def read_file(self, path: str) -> str:
        """Read file with size limits."""
        
        try:
            if not os.path.exists(path):
                return json.dumps({"status": "error", "message": "File not found"})
            
            size = os.path.getsize(path)
            if size > 1024 * 1024:  # 1MB limit
                return json.dumps({"status": "error", "message": "File too large (>1MB)"})
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return json.dumps({"status": "success", "content": content, "size": size})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    def list_directory(self, path: str = ".") -> str:
        """List directory contents."""
        
        try:
            if not os.path.exists(path):
                return json.dumps({"status": "error", "message": "Directory not found"})
            
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                items.append({
                    "name": item,
                    "type": "dir" if os.path.isdir(full_path) else "file",
                    "size": os.path.getsize(full_path) if os.path.isfile(full_path) else None
                })
            
            return json.dumps({"status": "success", "path": path, "items": items, "count": len(items)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
