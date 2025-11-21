"""
Search records with domain filter command
"""

import click
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json, output_error, parse_json_arg, format_table, confirm_large_dataset
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('search')
@click.argument('model', type=str)
@click.argument('domain', type=str)
@click.option('--fields', type=str, help='Comma-separated field names to retrieve')
@click.option('--limit', type=int, default=20, help='Maximum results to return')
@click.option('--offset', type=int, default=0, help='Skip first N results')
@click.option('--context', multiple=True, help='Context key=value (e.g., --context active_test=false)')
@click.pass_obj
def search(ctx: CliContext, model: str, domain: str, fields: str, limit: int, offset: int, context: tuple):
    """
    Search records with domain filter

    Examples:
        odoo search res.partner '[]'
        odoo search res.partner '[["is_company", "=", true]]' --fields name,email --limit 10
        odoo search sale.order '[["state", "=", "sale"]]' --json
    """
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

    # Search records
    try:
        # First get count if not in JSON mode
        if not ctx.json_mode:
            count = client.search_count(model, parsed_domain, context=parsed_context)
            if count > 500 and not confirm_large_dataset(count):
                ctx.console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Perform search_read
        results = client.search_read(
            model,
            domain=parsed_domain,
            fields=parsed_fields,
            offset=offset,
            limit=limit,
            context=parsed_context
        )

        if ctx.json_mode:
            # Get total count for JSON output
            count = client.search_count(model, parsed_domain, context=parsed_context)
            data = {
                'records': results,
                'count': count,
                'returned': len(results)
            }
            if count > 500:
                data['truncated'] = True
            output_json(data)
        else:
            if results:
                # Format as table
                # Use specified fields or all fields from first record
                display_columns = parsed_fields or list(results[0].keys())

                format_table(
                    results,
                    columns=display_columns,
                    title=f'Search results for "{model}"',
                    console=ctx.console
                )

                # Get and show total count
                count = client.search_count(model, parsed_domain, context=parsed_context)
                ctx.console.print(f"\n[dim]Showing {len(results)} of {count} record(s)[/dim]")
            else:
                ctx.console.print(f'[yellow]No records found for model "{model}" with given domain[/yellow]')

    except Exception as e:
        error_msg = str(e)
        suggestion = None

        if 'does not exist' in error_msg.lower():
            suggestion = "Use 'odoo get-models' to list available models"
        elif 'field' in error_msg.lower():
            suggestion = f"Use 'odoo get-fields {model}' to see available fields"

        output_error(
            f'Search failed for model "{model}"',
            error_type='data',
            details=error_msg,
            suggestion=suggestion,
            console=ctx.console,
            json_mode=ctx.json_mode,
            exit_code=3
        )
