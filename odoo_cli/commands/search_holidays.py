"""
Search time-off/holiday records command
"""

import click
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json as print_json, output_error, format_table
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('search-holidays')
@click.option('--employee', type=str, help='Filter by employee name')
@click.option(
    '--state',
    type=click.Choice(['draft', 'confirm', 'validate', 'refuse'], case_sensitive=False),
    help='Filter by holiday state'
)
@click.option('--limit', type=int, default=20, help='Maximum results to return')
@click.option('--context', multiple=True, help='Context key=value (e.g., --context active_test=false)')
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (LLM-friendly)')
@click.pass_obj
def search_holidays(ctx: CliContext, employee: str, state: str, limit: int, context: tuple, output_json: bool):
    """
    Search time-off/holiday records

    Examples:
        odoo search-holidays --employee "John" --state validate
        odoo search-holidays --limit 50 --json
    """
    # Determine JSON mode (command flag takes precedence over global)
    json_mode = output_json if output_json is not None else ctx.json_mode

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

    # Search holidays
    try:
        results = client.search_holidays(
            employee_name=employee,
            state=state,
            limit=limit,
            context=parsed_context
        )

        if json_mode:
            print_json(results)
        else:
            if results:
                # Format results for display
                display_data = []
                for holiday in results:
                    display_data.append({
                        'Employee': holiday.get('employee_id', ['', ''])[1] if holiday.get('employee_id') else '',
                        'Type': holiday.get('holiday_status_id', ['', ''])[1] if holiday.get('holiday_status_id') else '',
                        'Start': holiday.get('date_from', ''),
                        'End': holiday.get('date_to', ''),
                        'Days': holiday.get('number_of_days', 0),
                        'State': holiday.get('state', '').title()
                    })

                title_parts = ['Time-off Records']
                if employee:
                    title_parts.append(f'for "{employee}"')
                if state:
                    title_parts.append(f'[{state}]')

                format_table(
                    display_data,
                    columns=['Employee', 'Type', 'Start', 'End', 'Days', 'State'],
                    title=' '.join(title_parts),
                    console=ctx.console
                )
                ctx.console.print(f"\n[dim]Found {len(results)} time-off record(s)[/dim]")
            else:
                filters = []
                if employee:
                    filters.append(f'employee "{employee}"')
                if state:
                    filters.append(f'state "{state}"')

                filter_text = ' and '.join(filters) if filters else 'the given criteria'
                ctx.console.print(f'[yellow]No time-off records found for {filter_text}[/yellow]')

    except Exception as e:
        output_error(
            'Holiday search failed',
            error_type='data',
            details=str(e),
            suggestion='Check if hr.leave model is available',
            console=ctx.console,
            json_mode=json_mode,
            exit_code=3
        )
