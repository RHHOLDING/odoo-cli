"""
Get display names for record IDs command
"""

import click
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json, output_error
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('name-get')
@click.argument('model', type=str)
@click.argument('ids', type=str)
@click.option('--context', multiple=True, help='Context key=value (e.g., --context lang=de_DE)')
@click.option('--json', 'json_mode', is_flag=True, help='Output pure JSON')
@click.pass_obj
def name_get(ctx: CliContext, model: str, ids: str, context: tuple, json_mode: bool):
    """
    Get display names for record IDs

    More efficient than read() when you only need names.
    Converts IDs to their text representation in one API call.

    Examples:
        odoo name-get res.partner 1,2,3
        odoo name-get product.product 100 --json
        odoo name-get res.partner 1,2,3 --context lang=de_DE
    """
    # Combine local and global json flags
    json_mode = json_mode or ctx.json_mode

    # Parse IDs
    try:
        id_list = [int(id.strip()) for id in ids.split(',')]
        if not id_list:
            raise ValueError("At least one ID must be provided")
    except ValueError as e:
        output_error(
            f'Invalid IDs: {e}',
            error_type='data',
            suggestion='IDs must be comma-separated integers, e.g., "1,2,3"',
            console=ctx.console,
            json_mode=json_mode,
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
                suggestion='Context must be in format key=value (e.g., lang=de_DE)',
                console=ctx.console,
                json_mode=json_mode,
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
            json_mode=json_mode,
            exit_code=1
        )
    except ValueError as e:
        output_error(
            'Authentication failed',
            error_type='auth',
            details=str(e),
            suggestion='Verify credentials in configuration',
            console=ctx.console,
            json_mode=json_mode,
            exit_code=2
        )

    # Get names
    try:
        results = client.name_get(model, id_list, context=parsed_context)

        if json_mode:
            # Convert tuples to dict for JSON
            data = [{'id': id, 'name': name} for id, name in results]
            output_json(data)
        else:
            if results:
                ctx.console.print(f'[bold]Display names for {model}:[/bold]\n')
                for id, name in results:
                    ctx.console.print(f'  [cyan]{id}[/cyan]: {name}')
            else:
                ctx.console.print(f'[yellow]No records found for IDs: {ids}[/yellow]')

    except Exception as e:
        error_msg = str(e)
        suggestion = None

        if 'does not exist' in error_msg.lower():
            suggestion = "Use 'odoo get-models' to list available models"

        output_error(
            f'name_get failed for model "{model}"',
            error_type='data',
            details=error_msg,
            suggestion=suggestion,
            console=ctx.console,
            json_mode=json_mode,
            exit_code=3
        )
