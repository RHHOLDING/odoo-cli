"""
List all available Odoo models command
"""

import click
import re
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json, output_error, format_table


@click.command('get-models')
@click.option('--filter', 'filter_pattern', type=str, help='Filter models by name pattern (supports regex)')
@click.pass_obj
def get_models(ctx: CliContext, filter_pattern: str):
    """
    List all available Odoo models

    Examples:
        odoo get-models
        odoo get-models --filter sale
        odoo get-models --filter "^account\\." --json
    """
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

    # Get models
    try:
        models = client.get_models()

        # Apply filter if specified
        if filter_pattern:
            try:
                pattern = re.compile(filter_pattern, re.IGNORECASE)
                models = [m for m in models if pattern.search(m)]
            except re.error as e:
                output_error(
                    'Invalid regex pattern',
                    error_type='data',
                    details=str(e),
                    suggestion='Check your regex syntax',
                    console=ctx.console,
                    json_mode=ctx.json_mode,
                    exit_code=3
                )

        if ctx.json_mode:
            output_json(models)
        else:
            if models:
                # Format as table with model names
                display_data = [{'Model': model} for model in models]

                title = 'Available Odoo Models'
                if filter_pattern:
                    title += f' (filtered by "{filter_pattern}")'

                format_table(
                    display_data,
                    columns=['Model'],
                    title=title,
                    console=ctx.console
                )
                ctx.console.print(f"\n[dim]Found {len(models)} model(s)[/dim]")
            else:
                filter_text = f' matching "{filter_pattern}"' if filter_pattern else ''
                ctx.console.print(f'[yellow]No models found{filter_text}[/yellow]')

    except Exception as e:
        output_error(
            'Failed to retrieve models',
            error_type='data',
            details=str(e),
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=3
        )
