"""
Shared decorators for odoo-cli commands

This module provides reusable decorators for command options,
making the CLI more consistent and LLM-friendly.
"""

import click
from functools import wraps


def json_output_option(f):
    """
    Decorator to add --json flag to commands.

    This allows both patterns to work:
    - Global: odoo-cli --json search ...
    - Command: odoo-cli search ... --json

    The command-level flag takes precedence if both are specified.
    This makes the CLI more LLM-friendly and intuitive.

    Usage:
        @click.command()
        @json_output_option
        @click.pass_context
        def my_command(ctx, output_json, ...):
            json_mode = output_json if output_json is not None else ctx.obj.json_mode
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return click.option(
        '--json',
        'output_json',
        is_flag=True,
        default=None,
        help='Output pure JSON (LLM-friendly)'
    )(wrapper)


def context_option(f):
    """
    Decorator to add --context flag to commands.

    Allows passing Odoo context values like:
    - --context lang=de_DE
    - --context active_test=false
    - --context allowed_company_ids=[1,2,3]

    Usage:
        @click.command()
        @context_option
        @click.pass_context
        def my_command(ctx, context, ...):
            # context is already parsed dict
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return click.option(
        '--context',
        multiple=True,
        help='Odoo context key=value pairs (e.g., --context lang=de_DE)'
    )(wrapper)
