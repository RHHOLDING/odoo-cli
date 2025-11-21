"""
Shell session model for interactive mode
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ShellSession:
    """
    Represents an interactive shell session

    Attributes:
        namespace: Shell namespace with available objects
        history: Command history
        client: Reference to the OdooClient instance
    """
    namespace: Dict[str, Any] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    client: Optional[Any] = None

    def add_to_namespace(self, name: str, obj: Any) -> None:
        """Add an object to the shell namespace"""
        self.namespace[name] = obj

    def add_to_history(self, command: str) -> None:
        """Add a command to the history"""
        self.history.append(command)
