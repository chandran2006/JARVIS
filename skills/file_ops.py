import os
import json
import shutil
from typing import List, Dict, Any, Callable
from core.skill import Skill

_DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

class FileSkill(Skill):
    @property
    def name(self) -> str:
        return "file_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "create_file",
                "description": "Create a text file on the Desktop with given content",
                "parameters": {"type": "object",
                               "properties": {
                                   "filename": {"type": "string"},
                                   "content":  {"type": "string", "default": ""}},
                               "required": ["filename"]}}},
            {"type": "function", "function": {
                "name": "read_file",
                "description": "Read a file from the Desktop",
                "parameters": {"type": "object",
                               "properties": {"filename": {"type": "string"}},
                               "required": ["filename"]}}},
            {"type": "function", "function": {
                "name": "append_to_file",
                "description": "Append text to an existing Desktop file",
                "parameters": {"type": "object",
                               "properties": {
                                   "filename": {"type": "string"},
                                   "content":  {"type": "string"}},
                               "required": ["filename", "content"]}}},
            {"type": "function", "function": {
                "name": "delete_file",
                "description": "Delete a file from the Desktop",
                "parameters": {"type": "object",
                               "properties": {"filename": {"type": "string"}},
                               "required": ["filename"]}}},
            {"type": "function", "function": {
                "name": "list_desktop_files",
                "description": "List all files and folders on the Desktop",
                "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {
                "name": "create_folder",
                "description": "Create a new folder on the Desktop",
                "parameters": {"type": "object",
                               "properties": {"folder_name": {"type": "string"}},
                               "required": ["folder_name"]}}},
            {"type": "function", "function": {
                "name": "delete_folder",
                "description": "Delete a folder from the Desktop",
                "parameters": {"type": "object",
                               "properties": {"folder_name": {"type": "string"}},
                               "required": ["folder_name"]}}},
            {"type": "function", "function": {
                "name": "rename_file",
                "description": "Rename a file or folder on the Desktop",
                "parameters": {"type": "object",
                               "properties": {
                                   "old_name": {"type": "string"},
                                   "new_name": {"type": "string"}},
                               "required": ["old_name", "new_name"]}}},
            {"type": "function", "function": {
                "name": "open_file",
                "description": "Open a file from the Desktop with its default application",
                "parameters": {"type": "object",
                               "properties": {"filename": {"type": "string"}},
                               "required": ["filename"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "create_file":        self.create_file,
            "read_file":          self.read_file,
            "append_to_file":     self.append_to_file,
            "delete_file":        self.delete_file,
            "list_desktop_files": self.list_desktop_files,
            "create_folder":      self.create_folder,
            "delete_folder":      self.delete_folder,
            "rename_file":        self.rename_file,
            "open_file":          self.open_file,
        }

    def _p(self, name: str) -> str:
        return os.path.join(_DESKTOP, os.path.basename(name))

    def create_file(self, filename: str, content: str = "") -> str:
        try:
            with open(self._p(filename), "w", encoding="utf-8") as f:
                f.write(content)
            return json.dumps({"status": "success",
                               "message": f"File {filename} created on your Desktop, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def read_file(self, filename: str) -> str:
        try:
            p = self._p(filename)
            if not os.path.exists(p):
                return json.dumps({"status": "error",
                                   "message": f"{filename} was not found on your Desktop."})
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            short = content[:300] + ("..." if len(content) > 300 else "")
            return json.dumps({"status": "success", "message": short})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def append_to_file(self, filename: str, content: str) -> str:
        try:
            with open(self._p(filename), "a", encoding="utf-8") as f:
                f.write("\n" + content)
            return json.dumps({"status": "success",
                               "message": f"Text added to {filename}, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_file(self, filename: str) -> str:
        try:
            p = self._p(filename)
            if not os.path.exists(p):
                return json.dumps({"status": "error",
                                   "message": f"{filename} was not found on your Desktop."})
            os.remove(p)
            return json.dumps({"status": "success",
                               "message": f"{filename} has been deleted, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def list_desktop_files(self) -> str:
        try:
            items = os.listdir(_DESKTOP)
            files   = [f for f in items if os.path.isfile(os.path.join(_DESKTOP, f))]
            folders = [f for f in items if os.path.isdir(os.path.join(_DESKTOP, f))]
            parts = []
            if folders:
                parts.append(f"{len(folders)} folders: {', '.join(folders[:10])}")
            if files:
                parts.append(f"{len(files)} files: {', '.join(files[:10])}")
            if not parts:
                return json.dumps({"status": "success", "message": "Your Desktop is empty, sir."})
            return json.dumps({"status": "success",
                               "message": "Your Desktop has " + " and ".join(parts) + "."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def create_folder(self, folder_name: str) -> str:
        try:
            path = self._p(folder_name)
            os.makedirs(path, exist_ok=True)
            return json.dumps({"status": "success",
                               "message": f"Folder '{folder_name}' created on your Desktop, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_folder(self, folder_name: str) -> str:
        try:
            path = self._p(folder_name)
            if not os.path.exists(path):
                return json.dumps({"status": "error",
                                   "message": f"Folder '{folder_name}' not found on your Desktop."})
            shutil.rmtree(path)
            return json.dumps({"status": "success",
                               "message": f"Folder '{folder_name}' deleted, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rename_file(self, old_name: str, new_name: str) -> str:
        try:
            src = self._p(old_name)
            dst = self._p(new_name)
            if not os.path.exists(src):
                return json.dumps({"status": "error",
                                   "message": f"'{old_name}' not found on your Desktop."})
            os.rename(src, dst)
            return json.dumps({"status": "success",
                               "message": f"Renamed '{old_name}' to '{new_name}', sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def open_file(self, filename: str) -> str:
        try:
            import subprocess
            p = self._p(filename)
            if not os.path.exists(p):
                return json.dumps({"status": "error",
                                   "message": f"'{filename}' not found on your Desktop."})
            subprocess.Popen(f'start "" "{p}"', shell=True)
            return json.dumps({"status": "success",
                               "message": f"Opening {filename}, sir."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
