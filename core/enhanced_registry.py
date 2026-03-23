import os
import importlib.util
import inspect
import asyncio
from typing import Dict, List, Any, Callable, Optional
from pathlib import Path
from core.skill import Skill

class SkillMetadata:
    """Metadata for skill management."""
    
    def __init__(self, skill: Skill, priority: int = 50, enabled: bool = True):
        self.skill = skill
        self.priority = priority
        self.enabled = enabled
        self.load_time = 0
        self.call_count = 0
        self.error_count = 0
        self.dependencies: List[str] = []

class EnhancedSkillRegistry:
    """Advanced skill registry with hot-reload, priorities, and async support."""
    
    def __init__(self):
        self.skills: Dict[str, SkillMetadata] = {}
        self.tools_schema: List[Dict[str, Any]] = []
        self.functions: Dict[str, Callable] = {}
        self.skill_files: Dict[str, float] = {}  # Track file modification times
        self.context: Dict[str, Any] = {}
    
    def load_skills(self, skills_dir: str, context: Dict[str, Any] = None):
        """Load all skills from directory with error isolation."""
        
        if context:
            self.context = context
        
        if not os.path.exists(skills_dir):
            print(f"⚠️  Skills directory not found: {skills_dir}")
            return
        
        loaded_count = 0
        failed_count = 0
        
        for filename in sorted(os.listdir(skills_dir)):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = filename[:-3]
                file_path = os.path.join(skills_dir, filename)
                
                try:
                    self._load_skill_from_file(module_name, file_path)
                    loaded_count += 1
                except Exception as e:
                    print(f"❌ Failed to load {module_name}: {e}")
                    failed_count += 1
        
        self._rebuild_schema()
        print(f"✅ Loaded {loaded_count} skills ({failed_count} failed)")
    
    def _load_skill_from_file(self, module_name: str, file_path: str):
        """Load a single skill with metadata tracking."""
        
        import time
        start_time = time.time()
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            raise ImportError(f"Cannot load spec for {module_name}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Track file modification time for hot-reload
        self.skill_files[file_path] = os.path.getmtime(file_path)
        
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Skill) and obj is not Skill:
                skill_instance = obj()
                
                if self.context:
                    skill_instance.initialize(self.context)
                
                # Get priority from skill if available
                priority = getattr(skill_instance, 'priority', 50)
                
                metadata = SkillMetadata(skill_instance, priority=priority)
                metadata.load_time = time.time() - start_time
                
                self.skills[skill_instance.name] = metadata
                print(f"  📦 {skill_instance.name} (priority: {priority})")
    
    def _rebuild_schema(self):
        """Rebuild tools schema and function mappings."""
        
        self.tools_schema.clear()
        self.functions.clear()
        
        # Sort skills by priority (higher priority first)
        sorted_skills = sorted(
            self.skills.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        for skill_name, metadata in sorted_skills:
            if not metadata.enabled:
                continue
            
            try:
                self.tools_schema.extend(metadata.skill.get_tools())
                self.functions.update(metadata.skill.get_functions())
            except Exception as e:
                print(f"⚠️  Error loading tools from {skill_name}: {e}")
                metadata.error_count += 1
    
    def reload_skill(self, skill_name: str) -> bool:
        """Hot-reload a specific skill."""
        
        if skill_name not in self.skills:
            return False
        
        # Find the file path
        for file_path in self.skill_files.keys():
            if skill_name in file_path:
                try:
                    module_name = Path(file_path).stem
                    self._load_skill_from_file(module_name, file_path)
                    self._rebuild_schema()
                    print(f"🔄 Reloaded {skill_name}")
                    return True
                except Exception as e:
                    print(f"❌ Failed to reload {skill_name}: {e}")
                    return False
        
        return False
    
    def check_for_updates(self) -> List[str]:
        """Check if any skill files have been modified."""
        
        updated_skills = []
        
        for file_path, last_mtime in self.skill_files.items():
            try:
                current_mtime = os.path.getmtime(file_path)
                if current_mtime > last_mtime:
                    updated_skills.append(Path(file_path).stem)
            except:
                pass
        
        return updated_skills
    
    def enable_skill(self, skill_name: str):
        """Enable a disabled skill."""
        if skill_name in self.skills:
            self.skills[skill_name].enabled = True
            self._rebuild_schema()
    
    def disable_skill(self, skill_name: str):
        """Disable a skill without unloading it."""
        if skill_name in self.skills:
            self.skills[skill_name].enabled = False
            self._rebuild_schema()
    
    def get_function(self, name: str) -> Optional[Callable]:
        """Get function and track usage."""
        
        func = self.functions.get(name)
        
        if func:
            # Track which skill this function belongs to
            for skill_name, metadata in self.skills.items():
                if name in metadata.skill.get_functions():
                    metadata.call_count += 1
                    break
        
        return func
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get all enabled tools schema."""
        return self.tools_schema
    
    def get_skill_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded skills."""
        
        stats = {
            "total_skills": len(self.skills),
            "enabled_skills": sum(1 for m in self.skills.values() if m.enabled),
            "total_tools": len(self.tools_schema),
            "skills": {}
        }
        
        for name, metadata in self.skills.items():
            stats["skills"][name] = {
                "enabled": metadata.enabled,
                "priority": metadata.priority,
                "load_time": f"{metadata.load_time:.3f}s",
                "calls": metadata.call_count,
                "errors": metadata.error_count
            }
        
        return stats
    
    async def execute_async(self, function_name: str, **kwargs) -> Any:
        """Execute a function asynchronously if supported."""
        
        func = self.get_function(function_name)
        if not func:
            raise ValueError(f"Function {function_name} not found")
        
        # Check if function is async
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(**kwargs))
