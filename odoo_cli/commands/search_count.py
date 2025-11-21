"""
Count records matching a domain filter command
"""

import click
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json, output_error, parse_json_arg
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('search-count')
@click.argument('model', type=str)
@click.argument('domain', type=str)
@click.option('--context', multiple=True, help='Context key=value (e.g., --context active_test=false)')
@click.option('--json', 'json_mode', is_flag=True, help='Output pure JSON')
@click.pass_obj
def search_count(ctx: CliContext, model: str, domain: str, context: tuple, json_mode: bool):
    """
    Count records matching a domain filter

    Fast counting operation without transferring record data.
    Useful for checking dataset sizes before performing operations.

    Examples:
        odoo search-count res.partner '[]'
        odoo search-count sale.order '[["state", "=", "sale"]]' --json
        odoo search-count product.product '[]' --context active_test=false
    """
    # Combine local and global json flags
    json_mode = json_mode or ctx.json_mode

    # Parse domain
    try:
        parsed_domain = parse_json_arg(domain, 'domain')
        if not isinstance(parsed_domain, list):
            raise ValueError("Domain must be a JSON array")
    except ValueError as e:
        output_error(
            str(e),
            error_type='data',
            suggestion='Domain must be a valid JSON array, e.g., \'[["name", "=", "test"]]\'',
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
                suggestion='Context must be in format key=value (e.g., active_test=false)',
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

    # Count records
    try:
        count = client.search_count(model, parsed_domain, context=parsed_context)

        if json_mode:
            output_json({'count': count, 'model': model})
        else:
            ctx.console.print(f'[bold cyan]{count}[/bold cyan] record(s) found in [bold]{model}[/bold]')

    except Exception as e:
        error_msg = str(e)
        suggestion = None

        if 'does not exist' in error_msg.lower():
            suggestion = "Use 'odoo get-models' to list available models"

        output_error(
            f'Count failed for model "{model}"',
            error_type='data',
            details=error_msg,
            suggestion=suggestion,
            console=ctx.console,
            json_mode=json_mode,
            exit_code=3
        )
