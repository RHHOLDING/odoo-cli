"""
Read specific records by IDs command
"""

import click
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json, output_error, format_table
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('read')
@click.argument('model', type=str)
@click.argument('ids', type=str)
@click.option('--fields', type=str, help='Comma-separated field names to retrieve')
@click.option('--context', multiple=True, help='Context key=value (e.g., --context active_test=false)')
@click.pass_obj
def read(ctx: CliContext, model: str, ids: str, fields: str, context: tuple):
    """
    Read specific records by IDs

    Examples:
        odoo read res.partner 1,2,3
        odoo read sale.order 100 --fields name,amount_total,state
        odoo read res.partner 1,2,3 --json
    """
    # Parse IDs
    try:
        parsed_ids = [int(id_str.strip()) for id_str in ids.split(',')]
    except ValueError as e:
        output_error(
            'Invalid IDs format',
            error_type='data',
            details=str(e),
            suggestion='IDs must be comma-separated integers, e.g., "1,2,3"',
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=3
        )

    # Parse fields
    parsed_fields = None
    if fields:
        parsed_fields = [f.strip() for f in fields.split(',')]

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

    # Read records
    try:
        results = client.read(model, parsed_ids, fields=parsed_fields, context=parsed_context)

        if ctx.json_mode:
            output_json(results)
        else:
            if results:
                # Format as table
                # Use specified fields or all fields from first record
                display_columns = parsed_fields or list(results[0].keys())

                format_table(
                    results,
                    columns=display_columns,
                    title=f'Records from "{model}"',
                    console=ctx.console
                )
                ctx.console.print(f"\n[dim]Retrieved {len(results)} record(s)[/dim]")
            else:
                ctx.console.print(f'[yellow]No records found with IDs: {ids}[/yellow]')

    except Exception as e:
        error_msg = str(e)
        suggestion = None

        if 'does not exist' in error_msg.lower():
            suggestion = "Use 'odoo get-models' to list available models"
        elif 'field' in error_msg.lower():
            suggestion = f"Use 'odoo get-fields {model}' to see available fields"

        output_error(
            f'Read failed for model "{model}"',
            error_type='data',
            details=error_msg,
            suggestion=suggestion,
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=3
        )
