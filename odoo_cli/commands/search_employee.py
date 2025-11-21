"""
Search employees by name command
"""

import click
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json as print_json, output_error, format_table
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('search-employee')
@click.argument('name', type=str)
@click.option('--limit', type=int, default=20, help='Maximum results to return')
@click.option('--context', multiple=True, help='Context key=value (e.g., --context active_test=false)')
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (LLM-friendly)')
@click.pass_obj
def search_employee(ctx: CliContext, name: str, limit: int, context: tuple, output_json: bool):
    """
    Search employees by name

    Examples:
        odoo search-employee "John"
        odoo search-employee "John Doe" --limit 5 --json
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

    # Search employees
    try:
        results = client.search_employees(name, limit=limit, context=parsed_context)

        if json_mode:
            print_json(results)
        else:
            if results:
                # Format results for display
                display_data = []
                for emp in results:
                    display_data.append({
                        'ID': emp.get('id'),
                        'Name': emp.get('name'),
                        'Department': emp.get('department_id', ['', ''])[1] if emp.get('department_id') else '',
                        'Email': emp.get('work_email', ''),
                        'Job': emp.get('job_id', ['', ''])[1] if emp.get('job_id') else ''
                    })

                format_table(
                    display_data,
                    columns=['ID', 'Name', 'Department', 'Email', 'Job'],
                    title=f'Employees matching "{name}"',
                    console=ctx.console
                )
                ctx.console.print(f"\n[dim]Found {len(results)} employee(s)[/dim]")
            else:
                ctx.console.print(f'[yellow]No employees found matching "{name}"[/yellow]')

    except Exception as e:
        output_error(
            'Employee search failed',
            error_type='data',
            details=str(e),
            suggestion='Check if hr.employee model is available',
            console=ctx.console,
            json_mode=json_mode,
            exit_code=3
        )
