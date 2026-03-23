import os
import json
from typing import List, Dict, Any, Callable
from core.skill import Skill

class MemorySkill(Skill):
    """Skill for persistent memory storage and retrieval."""
    
    def __init__(self):
        # Store memory in user's home directory
        self.memory_file = os.path.expanduser("~/.jarvic_memory.json")
        self._ensure_memory_file()
    
    @property
    def name(self) -> str:
        return "memory_skill"

    def _ensure_memory_file(self):
        """Create memory file if it doesn't exist."""
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f:
                json.dump({}, f)

    def _load_memory(self) -> dict:
        """Load memory from file."""
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_memory(self, memory: dict):
        """Save memory to file."""
        with open(self.memory_file, 'w') as f:
            json.dump(memory, f, indent=2)

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "remember_fact",
                    "description": "Store a piece of information in persistent memory for later recall",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "A short identifier for this memory (e.g., 'favorite_color', 'birthday')"
                            },
                            "value": {
                                "type": "string",
                                "description": "The information to remember"
                            }
                        },
                        "required": ["key", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "retrieve_memory",
                    "description": "Retrieve a previously stored piece of information from memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {
                                "type": "string",
                                "description": "The name of the item to retrieve (e.g., 'user_name')"
                            }
                        },
                        "required": ["item_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_all_memories",
                    "description": "List all stored memories and their keys",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "forget_fact",
                    "description": "Delete a specific memory from storage",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The identifier for the memory to delete"
                            }
                        },
                        "required": ["key"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "remember_fact": self.remember_fact,
            "retrieve_memory": self.retrieve_memory,
            "list_all_memories": self.list_all_memories,
            "forget_fact": self.forget_fact
        }

    def remember_fact(self, key: str, value: str) -> str:
        """
        Store a fact in memory.
        
        Args:
            key: Memory identifier
            value: Value to store
            
        Returns:
            JSON string with status
        """
        try:
            memory = self._load_memory()
            memory[key] = value
            self._save_memory(memory)
            
            return json.dumps({
                "status": "success",
                "message": f"I will remember that {key} is {value}",
                "key": key,
                "value": value
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to store memory: {str(e)}"
            })

    def retrieve_memory(self, item_name: str) -> str:
        """
        Retrieve a fact from memory.
        
        Args:
            item_name: Memory identifier
            
        Returns:
            JSON string with the stored value
        """
        try:
            memory = self._load_memory()
            
            if item_name in memory:
                return json.dumps({
                    "status": "success",
                    "item_name": item_name,
                    "value": memory[item_name]
                })
            else:
                return json.dumps({
                    "status": "not_found",
                    "message": f"I don't remember anything about '{item_name}'"
                })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to recall memory: {str(e)}"
            })

    def list_all_memories(self) -> str:
        """
        List all stored memories.
        
        Returns:
            JSON string with all memories
        """
        try:
            memory = self._load_memory()
            
            if not memory:
                return json.dumps({
                    "status": "success",
                    "message": "I don't have any memories stored yet",
                    "memories": {}
                })
            
            return json.dumps({
                "status": "success",
                "count": len(memory),
                "memories": memory
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to list memories: {str(e)}"
            })

    def forget_fact(self, key: str) -> str:
        """
        Delete a memory.
        
        Args:
            key: Memory identifier to delete
            
        Returns:
            JSON string with status
        """
        try:
            memory = self._load_memory()
            
            if key in memory:
                del memory[key]
                self._save_memory(memory)
                
                return json.dumps({
                    "status": "success",
                    "message": f"I have forgotten about '{key}'"
                })
            else:
                return json.dumps({
                    "status": "not_found",
                    "message": f"I don't have any memory about '{key}' to forget"
                })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to forget memory: {str(e)}"
            })
