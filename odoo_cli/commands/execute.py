"""
Execute arbitrary model method command
"""

import click
import sys
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json, output_error, parse_json_arg, format_table
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('execute')
@click.argument('model', type=str)
@click.argument('method', type=str)
@click.option('--args', type=str, help='JSON array of positional arguments')
@click.option('--kwargs', type=str, help='JSON object of keyword arguments')
@click.option('--context', multiple=True, help='Context key=value (e.g., --context active_test=false)')
@click.pass_obj
def execute(ctx: CliContext, model: str, method: str, args: str, kwargs: str, context: tuple):
    """
    Execute arbitrary model method

    Examples:
        odoo execute ir.module.module button_immediate_upgrade --args '[[("name", "=", "sale")]]'
        odoo execute res.partner search_count --args '[[]]' --json
    """
    # Parse JSON arguments
    parsed_args = []
    parsed_kwargs = {}

    try:
        if args:
            parsed_args = parse_json_arg(args, '--args')
            if not isinstance(parsed_args, list):
                raise ValueError("--args must be a JSON array")

        if kwargs:
            parsed_kwargs = parse_json_arg(kwargs, '--kwargs')
            if not isinstance(parsed_kwargs, dict):
                raise ValueError("--kwargs must be a JSON object")

    except ValueError as e:
        output_error(
            str(e),
            error_type='data',
            suggestion='Ensure JSON is properly formatted',
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=3
        )

    # Parse context
    parsed_context = None
    if context:
        try:
            parsed_context = parse_context_flags(list(context))
        except ValueError as e:
            output_error(
                str(e),
                error_type='data',
                suggestion='Context must be in format key=value (e.g., active_test=false)',
                console=ctx.console,
                json_mode=ctx.json_mode,
                exit_code=3
            )

    # Create client
    try:
        client = OdooClient(
            url=ctx.config['url'],
            db=ctx.config['db'],
            username=ctx.config['username'],
            password=ctx.config['password'],
            timeout=ctx.config.get('timeout', 30),
            verify_ssl=ctx.config.get('verify_ssl', True)
        )
        client.connect()
    except ConnectionError as e:
        output_error(
            'Failed to connect to Odoo',
            error_type='connection',
            details=str(e),
            suggestion='Check URL and network connectivity',
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=1
        )
    except ValueError as e:
        output_error(
            'Authentication failed',
            error_type='auth',
            details=str(e),
            suggestion='Verify credentials in configuration',
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=2
        )

    # Execute method
    try:
        result = client.execute(model, method, *parsed_args, context=parsed_context, **parsed_kwargs)

        if ctx.json_mode:
            output_json(result)
        else:
            # Format output based on result type
            if isinstance(result, list) and result and isinstance(result[0], dict):
                # List of records - show as table
                format_table(result, console=ctx.console)
            elif isinstance(result, dict):
                # Single record or dict - show as table with one row
                format_table([result], console=ctx.console)
            else:
                # Simple value - just print
                ctx.console.print(f"[green]Result:[/green] {result}")

    except Exception as e:
        error_msg = str(e)
        suggestion = None

        # Provide helpful suggestions based on error
        if 'does not exist' in error_msg.lower():
            suggestion = "Use 'odoo get-models' to list available models"
        elif 'has no attribute' in error_msg.lower():
            suggestion = f"Check if method '{method}' exists on model '{model}'"

        output_error(
            f'Method execution failed',
            error_type='data',
            details=error_msg,
            suggestion=suggestion,
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=3
        )
