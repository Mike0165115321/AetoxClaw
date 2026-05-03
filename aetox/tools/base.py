from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    Abstract base class for all AetoxOS tools.
    Standardizes how tools are defined and executed.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        The main logic of the tool.
        Must return a dictionary with 'status' and 'output'.
        """
        pass

    def get_metadata(self) -> Dict[str, str]:
        """Returns tool metadata for the AI to understand."""
        return {
            "name": self.name,
            "description": self.description
        }
