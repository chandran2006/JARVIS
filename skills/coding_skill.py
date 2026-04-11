import os
import json
import time
import threading
import subprocess
import pyautogui
from typing import List, Dict, Any, Callable
from core.skill import Skill

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.02

# Languages JARVIS can detect from the question
_LANG_HINTS = {
    "python": "python", "py": "python",
    "javascript": "javascript", "js": "javascript", "node": "javascript",
    "java": "java",
    "c++": "cpp", "cpp": "cpp",
    "c#": "csharp", "csharp": "csharp",
    "html": "html", "css": "css",
    "sql": "sql",
    "typescript": "typescript", "ts": "typescript",
    "react": "javascript",
    "flutter": "dart", "dart": "dart",
    "kotlin": "kotlin",
    "swift": "swift",
    "rust": "rust",
    "go": "go",
    "php": "php",
    "ruby": "ruby",
    "bash": "bash", "shell": "bash",
}


def _detect_language(question: str) -> str:
    q = question.lower()
    for hint, lang in _LANG_HINTS.items():
        if hint in q:
            return lang
    return "python"  # default


def _generate_code(question: str, language: str) -> str:
    """Use Groq to generate clean code for the question."""
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()

        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        prompt = (
            f"Write {language} code for the following task. "
            f"Output ONLY the raw code — no markdown, no backticks, no explanation, no comments unless necessary.\n\n"
            f"Task: {question}"
        )
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        code = resp.choices[0].message.content.strip()
        # Strip markdown code fences if model added them anyway
        import re
        code = re.sub(r"^```[\w]*\n?", "", code)
        code = re.sub(r"\n?```$", "", code)
        return code.strip()
    except Exception as e:
        return f"# Error generating code: {e}"


def _type_code(code: str):
    """
    Type code into the currently focused window.
    Uses pyautogui with smart line-by-line typing to handle indentation correctly.
    """
    pyautogui.FAILSAFE = False
    time.sleep(1.0)  # Give user time to click into the editor

    lines = code.split("\n")
    for i, line in enumerate(lines):
        # Type the line character by character to preserve special chars
        if line:
            pyautogui.write(line, interval=0.008)
        if i < len(lines) - 1:
            pyautogui.press("enter")
        time.sleep(0.01)


class CodingSkill(Skill):
    @property
    def name(self) -> str:
        return "coding_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {"type": "function", "function": {
                "name": "write_code",
                "description": (
                    "Generate code for any programming task and type it directly "
                    "into the active editor, IDE, or coding platform (LeetCode, HackerRank, etc.). "
                    "Use when user says 'write code', 'do this coding', 'solve this', 'code for me', etc."
                ),
                "parameters": {"type": "object", "properties": {
                    "question": {"type": "string", "description": "The coding problem or task description"},
                    "language": {"type": "string", "description": "Programming language (python, javascript, java, cpp, etc.)", "default": "python"},
                    "type_it":  {"type": "boolean", "description": "Whether to type the code into the active window", "default": True},
                }, "required": ["question"]}}},
            {"type": "function", "function": {
                "name": "explain_code",
                "description": "Explain what a piece of code does in simple terms",
                "parameters": {"type": "object", "properties": {
                    "code": {"type": "string", "description": "The code to explain"},
                }, "required": ["code"]}}},
            {"type": "function", "function": {
                "name": "fix_code",
                "description": "Fix bugs in code and type the corrected version into the active editor",
                "parameters": {"type": "object", "properties": {
                    "code":     {"type": "string", "description": "The buggy code"},
                    "language": {"type": "string", "default": "python"},
                    "type_it":  {"type": "boolean", "default": True},
                }, "required": ["code"]}}},
            {"type": "function", "function": {
                "name": "optimize_code",
                "description": "Optimize code for better performance and type it into the active editor",
                "parameters": {"type": "object", "properties": {
                    "code":     {"type": "string", "description": "The code to optimize"},
                    "language": {"type": "string", "default": "python"},
                    "type_it":  {"type": "boolean", "default": True},
                }, "required": ["code"]}}},
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "write_code":    self.write_code,
            "explain_code":  self.explain_code,
            "fix_code":      self.fix_code,
            "optimize_code": self.optimize_code,
        }

    def write_code(self, question: str, language: str = "", type_it: bool = True) -> str:
        if not language:
            language = _detect_language(question)

        code = _generate_code(question, language)
        if not code or code.startswith("# Error"):
            return json.dumps({"status": "error", "message": "Could not generate code, sir."})

        if type_it:
            # Type in background so JARVIS can speak first
            threading.Thread(target=_type_code, args=(code,), daemon=True).start()
            lines = code.count("\n") + 1
            return json.dumps({"status": "success",
                               "message": f"Writing {lines}-line {language} code into your editor now, sir."})
        else:
            # Just return the code as text
            return json.dumps({"status": "success", "message": f"Here is the {language} code:\n{code}"})

    def explain_code(self, code: str) -> str:
        try:
            from groq import Groq
            from dotenv import load_dotenv
            load_dotenv()
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user",
                           "content": f"Explain this code in 2-3 simple sentences:\n\n{code}"}],
                max_tokens=150, temperature=0.3,
            )
            explanation = resp.choices[0].message.content.strip()
            return json.dumps({"status": "success", "message": explanation})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def fix_code(self, code: str, language: str = "python", type_it: bool = True) -> str:
        try:
            from groq import Groq
            from dotenv import load_dotenv
            load_dotenv()
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user",
                           "content": f"Fix all bugs in this {language} code. Output ONLY the fixed code, no explanation:\n\n{code}"}],
                max_tokens=1024, temperature=0.1,
            )
            import re
            fixed = resp.choices[0].message.content.strip()
            fixed = re.sub(r"^```[\w]*\n?", "", fixed)
            fixed = re.sub(r"\n?```$", "", fixed).strip()

            if type_it:
                threading.Thread(target=_type_code, args=(fixed,), daemon=True).start()
                return json.dumps({"status": "success",
                                   "message": "Fixed code is being typed into your editor, sir."})
            return json.dumps({"status": "success", "message": fixed})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def optimize_code(self, code: str, language: str = "python", type_it: bool = True) -> str:
        try:
            from groq import Groq
            from dotenv import load_dotenv
            load_dotenv()
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user",
                           "content": f"Optimize this {language} code for better performance and readability. Output ONLY the optimized code:\n\n{code}"}],
                max_tokens=1024, temperature=0.1,
            )
            import re
            optimized = resp.choices[0].message.content.strip()
            optimized = re.sub(r"^```[\w]*\n?", "", optimized)
            optimized = re.sub(r"\n?```$", "", optimized).strip()

            if type_it:
                threading.Thread(target=_type_code, args=(optimized,), daemon=True).start()
                return json.dumps({"status": "success",
                                   "message": "Optimized code is being typed into your editor, sir."})
            return json.dumps({"status": "success", "message": optimized})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
