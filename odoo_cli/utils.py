"""
Utility functions for output formatting and JSON handling

DEPRECATED: This module has been moved to odoo_cli.utils.output
This file is kept for backward compatibility.
All new code should import from odoo_cli.utils instead.
"""

# Re-export everything from the utils package
from odoo_cli.utils.output import (
    format_table,
    output_json,
    output_error,
    parse_json_arg,
    confirm_large_dataset
)

__all__ = [
    'format_table',
    'output_json',
    'output_error',
    'parse_json_arg',
    'confirm_large_dataset'
]
