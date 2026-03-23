from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable

class Skill(ABC):
    """Base class for all Skills."""
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return the list of tool schemas provided by this skill."""
        pass

    @abstractmethod
    def get_functions(self) -> Dict[str, Callable]:
        """Return a dictionary mapping function names to the actual callables."""
        pass

    def initialize(self, context: Dict[str, Any]):
        """
        Initialize the skill with context from the main application.
        Override this if the skill needs access to global state (e.g., pause_event).
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the skill."""
        pass
