"""
Enhanced error handling for Odoo JSON-RPC client.

Provides intelligent error categorization, suggestion generation,
and formatted error output for better LLM debugging.
"""

from typing import Optional, Dict, Any, Tuple
import re


class OdooError(Exception):
    """Base exception for Odoo API errors"""

    def __init__(
        self,
        message: str,
        error_type: str = 'unknown',
        details: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        self.message = message
        self.error_type = error_type
        self.details = details
        self.suggestion = suggestion
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON output"""
        result = {
            'success': False,
            'error': self.message,
            'error_type': self.error_type
        }
        if self.details:
            result['details'] = self.details
        if self.suggestion:
            result['suggestion'] = self.suggestion
        return result


class ErrorAnalyzer:
    """Analyzes Odoo errors and provides intelligent suggestions"""

    # Error patterns and their handlers
    ERROR_PATTERNS = {
        # Domain-related errors
        r'unhashable type': {
            'type': 'domain',
            'message': 'Domain format error - check list wrapping',
            'suggestion': 'Ensure domain is a list of lists: [["field", "=", "value"]]'
        },
        r'tuple index out of range': {
            'type': 'domain',
            'message': 'Domain format error - incomplete condition',
            'suggestion': 'Each domain condition needs 3 parts: ["field", "operator", "value"]'
        },
        r'Domains to normalize must have': {
            'type': 'domain',
            'message': 'Domain must be a list or tuple',
            'suggestion': 'Use: [["field", "=", "value"]] not "string"'
        },

        # Field-related errors
        r'has no attribute.*field': {
            'type': 'field',
            'message': 'Field does not exist on this model',
            'suggestion': 'Use "odoo get-fields MODEL_NAME" to see available fields'
        },
        r'[Ii]nvalid field': {
            'type': 'field',
            'message': 'Field is not valid for this model',
            'suggestion': 'Check field name spelling and use "odoo get-fields MODEL_NAME"'
        },

        # Model-related errors
        r'Model.*does not exist': {
            'type': 'model',
            'message': 'Model does not exist in this Odoo instance',
            'suggestion': 'Use "odoo get-models" to list available models'
        },
        r'does not exist': {
            'type': 'model',
            'message': 'Resource not found',
            'suggestion': 'Check the model/record name and try again'
        },

        # Method-related errors
        r'has no attribute.*method': {
            'type': 'method',
            'message': 'Method does not exist',
            'suggestion': 'Check method name spelling and model capabilities'
        },
        r'got multiple values for argument': {
            'type': 'argument',
            'message': 'Argument passed in wrong format (positional vs keyword)',
            'suggestion': 'Check argument wrapping - use **kwargs to unpack dicts'
        },

        # Permission-related errors
        r'[Aa]ccess denied': {
            'type': 'permission',
            'message': 'User lacks permission for this operation',
            'suggestion': 'Use an admin user or check access control rules'
        },
        r'[Aa]uthentication failed': {
            'type': 'auth',
            'message': 'Invalid credentials',
            'suggestion': 'Check ODOO_USERNAME and ODOO_PASSWORD environment variables'
        },

        # Connection errors
        r'[Cc]onnection refused': {
            'type': 'connection',
            'message': 'Cannot connect to Odoo server',
            'suggestion': 'Check ODOO_URL is correct and server is running'
        },
        r'[Tt]imeout': {
            'type': 'timeout',
            'message': 'Request timed out',
            'suggestion': 'Increase timeout with --timeout option or reduce data size'
        },
    }

    @classmethod
    def analyze(cls, error_message: str) -> Tuple[str, str, Optional[str]]:
        """
        Analyze error message and return categorized error info.

        Args:
            error_message: Raw error message from Odoo

        Returns:
            Tuple of (error_type, message, suggestion)
        """
        # Try to match against known patterns
        for pattern, info in cls.ERROR_PATTERNS.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                return (
                    info.get('type', 'unknown'),
                    info.get('message', error_message),
                    info.get('suggestion')
                )

        # Default: return as-is
        return ('unknown', error_message, None)

    @classmethod
    def extract_odoo_error(cls, error_message: str) -> str:
        """Extract the actual Odoo error from JSON-RPC wrapper"""
        # Look for pattern: "Odoo Server Error: [actual error]"
        match = re.search(r'Odoo Server Error: (.+?)(?:\n|$)', error_message)
        if match:
            return match.group(1)

        # Look for pattern: "Odoo error: [actual error]"
        match = re.search(r'Odoo error: (.+?)(?:\n|$)', error_message)
        if match:
            return match.group(1)

        return error_message


class ConnectionError(OdooError):
    """Connection-related errors"""

    def __init__(self, message: str, details: Optional[str] = None):
        suggestion = 'Check ODOO_URL is correct and server is running'
        super().__init__(
            message,
            error_type='connection',
            details=details,
            suggestion=suggestion
        )


class AuthenticationError(OdooError):
    """Authentication-related errors"""

    def __init__(self, message: str = 'Authentication failed', details: Optional[str] = None):
        suggestion = 'Check ODOO_USERNAME and ODOO_PASSWORD environment variables'
        super().__init__(
            message,
            error_type='auth',
            details=details,
            suggestion=suggestion
        )


class DomainError(OdooError):
    """Domain format errors"""

    def __init__(self, message: str, details: Optional[str] = None):
        suggestion = 'Domain must be a list of conditions: [["field", "op", "value"]]'
        super().__init__(
            message,
            error_type='domain',
            details=details,
            suggestion=suggestion
        )


class ModelError(OdooError):
    """Model-related errors"""

    def __init__(self, model_name: str, message: str = None, details: Optional[str] = None):
        if not message:
            message = f'Model "{model_name}" not found or inaccessible'

        suggestion = 'Use "odoo get-models" to list available models'
        super().__init__(
            message,
            error_type='model',
            details=details,
            suggestion=suggestion
        )


class FieldError(OdooError):
    """Field-related errors"""

    def __init__(self, model_name: str, field_name: str = None, details: Optional[str] = None):
        message = f'Field error on model "{model_name}"'
        if field_name:
            message += f': "{field_name}"'

        suggestion = f'Use "odoo get-fields {model_name}" to see available fields'
        super().__init__(
            message,
            error_type='field',
            details=details,
            suggestion=suggestion
        )


class PermissionError(OdooError):
    """Permission-related errors"""

    def __init__(self, message: str = 'Access denied', details: Optional[str] = None):
        suggestion = 'Use an admin user or check access control rules'
        super().__init__(
            message,
            error_type='permission',
            details=details,
            suggestion=suggestion
        )


def create_error_from_odoo(odoo_error_message: str) -> OdooError:
    """
    Create appropriate error instance from Odoo error message.

    Args:
        odoo_error_message: Raw error message from Odoo

    Returns:
        Appropriate OdooError subclass instance
    """
    error_type, message, suggestion = ErrorAnalyzer.analyze(odoo_error_message)

    # Create specific error type based on analysis
    if error_type == 'domain':
        return DomainError(message)
    elif error_type == 'model':
        return ModelError('unknown', message)
    elif error_type == 'field':
        return FieldError('unknown', details=message)
    elif error_type == 'auth':
        return AuthenticationError(message)
    elif error_type == 'connection':
        return ConnectionError(message)
    elif error_type == 'permission':
        return PermissionError(message)
    else:
        return OdooError(message, error_type=error_type, suggestion=suggestion)
