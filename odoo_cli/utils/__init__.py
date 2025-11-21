"""Utility modules for odoo-cli."""

# Re-export all utility functions for backward compatibility
# Commands expect to import from odoo_cli.utils

from .output import (
    format_table,
    output_json,
    output_error,
    parse_json_arg,
    confirm_large_dataset
)

from .context_parser import parse_context_flags

__all__ = [
    'format_table',
    'output_json',
    'output_error',
    'parse_json_arg',
    'confirm_large_dataset',
    'parse_context_flags'
]
