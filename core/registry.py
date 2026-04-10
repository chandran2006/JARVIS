import os
import importlib.util
import inspect
from typing import Dict, List, Any, Callable, Optional
from .skill import Skill

class SkillRegistry:
    def __init__(self):
        self._skills:   Dict[str, Skill]    = {}
        self._tools:    List[Dict[str, Any]] = []
        self._functions: Dict[str, Callable] = {}

    # ── load all .py files in a directory ────────────────────────────────────
    def load_skills(self, skills_dir: str, context: Dict[str, Any] = None):
        if not os.path.exists(skills_dir):
            print(f"[Registry] Skills directory not found: {skills_dir}")
            return

        ok = fail = 0
        for fname in sorted(os.listdir(skills_dir)):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            path = os.path.join(skills_dir, fname)
            try:
                self._load_file(fname[:-3], path, context)
                ok += 1
            except Exception as e:
                print(f"  [SKIP] Skipped {fname}: {e}")
                fail += 1

        print(f"[Registry] {ok} skills loaded, {fail} skipped — {len(self._tools)} tools available.")

    def _load_file(self, module_name: str, path: str, context):
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec or not spec.loader:
            raise ImportError("Cannot create module spec")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, Skill) and obj is not Skill:
                instance = obj()
                if context:
                    instance.initialize(context)
                self._register(instance)
                print(f"  [OK] {instance.name}")

    def _register(self, skill: Skill):
        self._skills[skill.name] = skill
        # Deduplicate — skip any tool whose function name is already registered
        existing = {t["function"]["name"] for t in self._tools}
        for tool in skill.get_tools():
            if tool["function"]["name"] not in existing:
                self._tools.append(tool)
                existing.add(tool["function"]["name"])
        self._functions.update(skill.get_functions())

    # ── accessors ─────────────────────────────────────────────────────────────
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return self._tools

    def get_function(self, name: str) -> Optional[Callable]:
        return self._functions.get(name)
