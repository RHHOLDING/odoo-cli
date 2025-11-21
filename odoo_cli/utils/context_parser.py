"""Context flag parser with type inference."""
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def parse_context_flags(context_list: List[str]) -> Dict[str, Any]:
    """
    Parse --context flags into dictionary.

    Uses lazy validation: invalid keys are passed to Odoo for validation.
    Only format (key=value) is checked by CLI.

    Examples:
        ['active_test=false'] → {'active_test': False}
        ['lang=de_DE', 'tz=Europe/Berlin'] → {'lang': 'de_DE', 'tz': 'Europe/Berlin'}
        ['allowed_company_ids=[1,2,3]'] → {'allowed_company_ids': [1, 2, 3]}

    Args:
        context_list: List of key=value strings

    Returns:
        Dictionary with parsed context

    Raises:
        ValueError: If format invalid
    """
    context = {}

    for item in context_list:
        if '=' not in item:
            raise ValueError(
                f"Invalid context format: '{item}'. "
                f"Expected format: key=value (e.g., active_test=false)"
            )

        key, value = item.split('=', 1)
        key = key.strip()

        if not key:
            raise ValueError(f"Empty context key in: '{item}'")

        context[key] = _parse_context_value(value.strip())

    # Note: Context key validation is delegated to Odoo (lazy validation)
    # Invalid keys will be rejected by Odoo with appropriate error messages

    # Log only if user explicitly provided context (clarification answer)
    if context:
        logger.debug(f"Applying user context: {context}")

    return context


def _parse_context_value(value: str) -> Any:
    """
    Auto-detect and parse context value type.

    Supports:
    - Boolean: true/false (case-insensitive)
    - List: [1,2,3]
    - Dict: {"key": "value"}
    - Integer: 42
    - Float: 3.14
    - String: "anything else"
    """
    # Boolean
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'

    # List/Dict (JSON)
    if (value.startswith('[') and value.endswith(']')) or \
       (value.startswith('{') and value.endswith('}')):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in context value: {value}. Error: {e}")

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # String (default)
    return value
