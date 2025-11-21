"""
Field parsing and validation utilities for CRUD commands.

Provides functions to parse field=value syntax and validate fields
before sending to Odoo.
"""

from typing import Dict, Any, Tuple, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from odoo_cli.client import OdooClient


def is_float(value: str) -> bool:
    """
    Check if string represents a float number.

    Args:
        value: String to check

    Returns:
        True if value is a valid float, False otherwise

    Examples:
        >>> is_float("123.45")
        True
        >>> is_float("123")
        True
        >>> is_float("abc")
        False
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def parse_field_values(fields: Tuple[str, ...]) -> Dict[str, Any]:
    """
    Parse field=value pairs into dict with type inference.

    Automatically infers types:
    - Quoted strings → str (quotes removed)
    - "true"/"false" → bool
    - Digits → int
    - Decimal numbers → float
    - Unquoted text → str

    Args:
        fields: Tuple of "key=value" strings

    Returns:
        Dict with parsed values and inferred types

    Raises:
        ValueError: If field format is invalid (missing '=')

    Examples:
        >>> parse_field_values(('name="Test"', 'partner_id=123', 'active=true'))
        {'name': 'Test', 'partner_id': 123, 'active': True}

        >>> parse_field_values(('price=19.99', 'qty=5', 'description=No quotes needed'))
        {'price': 19.99, 'qty': 5, 'description': 'No quotes needed'}
    """
    result = {}

    for field_str in fields:
        if '=' not in field_str:
            raise ValueError(
                f"Invalid field format: '{field_str}'. Expected key=value"
            )

        # Split only on first '=' to allow '=' in value
        key, value = field_str.split('=', 1)
        key = key.strip()
        value = value.strip()

        if not key:
            raise ValueError(
                f"Invalid field format: '{field_str}'. Field name cannot be empty"
            )

        # Type inference
        if value.lower() in ('true', 'false'):
            # Boolean
            result[key] = value.lower() == 'true'

        elif value.lower() == 'null' or value.lower() == 'none':
            # Null/None
            result[key] = False

        elif value.startswith('"') and value.endswith('"'):
            # Double-quoted string
            result[key] = value[1:-1]

        elif value.startswith("'") and value.endswith("'"):
            # Single-quoted string
            result[key] = value[1:-1]

        elif value.startswith('[') and value.endswith(']'):
            # List/array - parse as list of ints or strings
            # Simple implementation: comma-separated values
            list_content = value[1:-1].strip()
            if not list_content:
                result[key] = []
            else:
                # Try to parse as ints, fallback to strings
                items = [item.strip() for item in list_content.split(',')]
                try:
                    result[key] = [int(item) for item in items]
                except ValueError:
                    # Not all ints, keep as strings
                    result[key] = [item.strip('"\'') for item in items]

        elif value.isdigit():
            # Integer (positive)
            result[key] = int(value)

        elif value.startswith('-') and value[1:].isdigit():
            # Integer (negative)
            result[key] = int(value)

        elif is_float(value):
            # Float
            result[key] = float(value)

        else:
            # Default to string (no quotes needed)
            result[key] = value

    return result


def validate_fields(
    client: 'OdooClient',
    model: str,
    fields: Dict[str, Any],
    skip_readonly: bool = True
) -> None:
    """
    Validate field names and types before sending to Odoo.

    Checks:
    - Field exists on model
    - Field is not readonly (optional)
    - Basic type compatibility

    Args:
        client: Authenticated OdooClient instance
        model: Odoo model name (e.g., 'res.partner')
        fields: Dictionary of field_name: value to validate
        skip_readonly: If True, raise error for readonly fields (default: True)

    Raises:
        ValueError: If validation fails with helpful error message

    Examples:
        >>> validate_fields(client, 'res.partner', {'name': 'Test', 'email': 'test@test.com'})
        # Returns None if valid

        >>> validate_fields(client, 'res.partner', {'invalid_field': 'value'})
        ValueError: Field 'invalid_field' does not exist on model 'res.partner'.
        Run: odoo get-fields res.partner
    """
    # Get field definitions from Odoo (cached)
    try:
        field_defs = client.fields_get(model)
    except Exception as e:
        raise ValueError(
            f"Could not fetch field definitions for model '{model}': {e}\n"
            f"Run: odoo get-models --filter {model}"
        )

    for field_name, field_value in fields.items():
        # Check if field exists
        if field_name not in field_defs:
            # Provide helpful suggestion
            similar_fields = [
                f for f in field_defs.keys()
                if field_name.lower() in f.lower() or f.lower() in field_name.lower()
            ]

            error_msg = (
                f"Field '{field_name}' does not exist on model '{model}'.\n"
                f"Run: odoo get-fields {model}"
            )

            if similar_fields:
                error_msg += f"\n\nDid you mean one of these?\n  " + "\n  ".join(similar_fields[:5])

            raise ValueError(error_msg)

        field_def = field_defs[field_name]

        # Check if field is readonly
        if skip_readonly and field_def.get('readonly', False):
            # Check if it's a computed field with store=False
            if not field_def.get('store', True):
                raise ValueError(
                    f"Field '{field_name}' is readonly (computed) on model '{model}'"
                )

        # Basic type validation
        field_type = field_def.get('type')
        python_type = type(field_value).__name__

        # Type mapping for validation
        expected_types = {
            'integer': (int,),
            'float': (int, float),  # Allow int for float fields
            'monetary': (int, float),
            'boolean': (bool,),
            'char': (str,),
            'text': (str,),
            'html': (str,),
            'date': (str,),
            'datetime': (str,),
            'many2one': (int, bool),  # int for ID, False for clear
            'many2many': (list, bool),  # list of IDs, False for clear
            'one2many': (list, bool),
            'selection': (str,),
        }

        if field_type in expected_types:
            expected = expected_types[field_type]
            if not isinstance(field_value, expected):
                # Special case: allow False for relational fields (clears relation)
                if field_value is False and field_type in ('many2one', 'many2many', 'one2many'):
                    continue

                raise ValueError(
                    f"Field '{field_name}' expects {field_type} "
                    f"(Python type: {expected[0].__name__}), "
                    f"but got {python_type}.\n"
                    f"Value provided: {repr(field_value)}"
                )


def format_field_validation_error(error: Exception, model: str, field_name: str) -> str:
    """
    Format validation error with helpful suggestions.

    Args:
        error: The exception that was raised
        model: Model name
        field_name: Field name that caused the error

    Returns:
        Formatted error message with suggestions
    """
    error_msg = str(error)

    # Add context
    formatted = f"Validation Error for '{model}.{field_name}':\n"
    formatted += f"  {error_msg}\n\n"

    # Add helpful suggestions
    formatted += "Suggestions:\n"
    formatted += f"  1. Check field name: odoo get-fields {model} --field {field_name}\n"
    formatted += f"  2. Check field type: odoo get-fields {model}\n"
    formatted += "  3. Use --no-validate flag to skip validation\n"

    return formatted
