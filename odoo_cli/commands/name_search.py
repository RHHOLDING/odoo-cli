"""
Search records by name command
"""

import click
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json as print_json, output_error, parse_json_arg
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('name-search')
@click.argument('model', type=str)
@click.argument('name', type=str, default='')
@click.option('--domain', type=str, help='Additional domain filter (JSON array)')
@click.option('--operator', type=str, default='ilike', help='Comparison operator (default: ilike)')
@click.option('--limit', type=int, default=100, help='Maximum results to return')
@click.option('--context', multiple=True, help='Context key=value (e.g., --context lang=de_DE)')
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (LLM-friendly)')
@click.pass_obj
def name_search(ctx: CliContext, model: str, name: str, domain: str, operator: str, limit: int, context: tuple, output_json: bool):
    """
    Search records by name (fuzzy search)

    Performs fuzzy name matching, ideal for autocomplete/selection lists.
    Returns (id, display_name) tuples without full record data.

    Examples:
        odoo name-search res.partner John
        odoo name-search product.product "Desk" --limit 10 --json
        odoo name-search res.partner Smith --domain '[["is_company", "=", true]]'
        odoo name-search res.country Germany --operator like
    """
    # Combine local and global json flags
    json_mode = output_json if output_json is not None else ctx.json_mode

    # Parse domain if provided
    parsed_domain = None
    if domain:
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

    # Search by name
    try:
        results = client.name_search(
            model,
            name=name,
            domain=parsed_domain,
            operator=operator,
            limit=limit,
            context=parsed_context
        )

        if json_mode:
            # Convert tuples to dict for JSON
            data = [{'id': id, 'name': display_name} for id, display_name in results]
            print_json({'results': data, 'count': len(data)})
        else:
            if results:
                ctx.console.print(f'[bold]Search results for "{name}" in {model}:[/bold]\n')
                for id, display_name in results:
                    ctx.console.print(f'  [cyan]{id}[/cyan]: {display_name}')
                ctx.console.print(f'\n[dim]Found {len(results)} result(s)[/dim]')
            else:
                ctx.console.print(f'[yellow]No records found matching "{name}"[/yellow]')

    except Exception as e:
        error_msg = str(e)
        suggestion = None

        if 'does not exist' in error_msg.lower():
            suggestion = "Use 'odoo get-models' to list available models"

        output_error(
            f'name_search failed for model "{model}"',
            error_type='data',
            details=error_msg,
            suggestion=suggestion,
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=3
        )
