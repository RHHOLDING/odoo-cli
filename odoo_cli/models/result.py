"""
Command result model for standardized output
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List, Union
import json


@dataclass
class CommandResult:
    """Standardized output for all CLI commands"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None  # connection, auth, data
    count: Optional[int] = None
    truncated: bool = False
    suggestion: Optional[str] = None
    details: Optional[str] = None

    def to_json(self) -> str:
        """Convert to JSON string for output"""
        result = {'success': self.success}

        if self.success:
            result['data'] = self.data
            if self.count is not None:
                result['count'] = self.count
            if self.truncated:
                result['truncated'] = self.truncated
        else:
            result['error'] = self.error or 'Unknown error'
            result['error_type'] = self.error_type or 'unknown'
            if self.details:
                result['details'] = self.details
            if self.suggestion:
                result['suggestion'] = self.suggestion

        return json.dumps(result, indent=2, default=str)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {'success': self.success}

        if self.success:
            result['data'] = self.data
            if self.count is not None:
                result['count'] = self.count
            if self.truncated:
                result['truncated'] = self.truncated
        else:
            result['error'] = self.error or 'Unknown error'
            result['error_type'] = self.error_type or 'unknown'
            if self.details:
                result['details'] = self.details
            if self.suggestion:
                result['suggestion'] = self.suggestion

        return result

    @classmethod
    def success_result(cls, data: Any, count: Optional[int] = None, truncated: bool = False) -> 'CommandResult':
        """Create a success result"""
        return cls(
            success=True,
            data=data,
            count=count,
            truncated=truncated
        )

    @classmethod
    def error_result(cls, error: str, error_type: str, details: Optional[str] = None, suggestion: Optional[str] = None) -> 'CommandResult':
        """Create an error result"""
        return cls(
            success=False,
            error=error,
            error_type=error_type,
            details=details,
            suggestion=suggestion
        )

    def get_exit_code(self) -> int:
        """Get appropriate exit code based on error type"""
        if self.success:
            return 0
        elif self.error_type == 'connection':
            return 1
        elif self.error_type == 'auth':
            return 2
        elif self.error_type == 'data':
            return 3
        else:
            return 3  # Default to data error