"""
Get field definitions for a model command
"""

import click
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_json, output_error, format_table


@click.command('get-fields')
@click.argument('model', type=str)
@click.option('--field', type=str, help='Get specific field details')
@click.option('--attributes', type=str, help='Comma-separated list of attributes to include (reduces payload size)')
@click.option('--json', 'json_mode', is_flag=True, help='Output pure JSON')
@click.pass_obj
def get_fields(ctx: CliContext, model: str, field: str, attributes: str, json_mode: bool):
    """
    Get field definitions for a model

    Use --attributes to filter which field metadata to include,
    reducing payload size for large models.

    Examples:
        odoo get-fields res.partner
        odoo get-fields sale.order --field amount_total
        odoo get-fields res.partner --attributes type,string,required
        odoo get-fields product.product --attributes type,string --json
    """
    # Combine local and global json flags
    json_mode = json_mode or ctx.json_mode

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

    # Parse attributes
    parsed_attributes = None
    if attributes:
        parsed_attributes = [attr.strip() for attr in attributes.split(',')]

    # Get fields
    try:
        # Get field definitions
        allfields = [field] if field else None
        fields_def = client.fields_get(model, allfields=allfields, attributes=parsed_attributes)

        if json_mode:
            output_json(fields_def)
        else:
            if fields_def:
                # Format as table
                display_data = []
                for field_name, field_info in sorted(fields_def.items()):
                    display_data.append({
                        'Field': field_name,
                        'Type': field_info.get('type', ''),
                        'Required': '✓' if field_info.get('required') else '',
                        'Readonly': '✓' if field_info.get('readonly') else '',
                        'Description': field_info.get('string', ''),
                        'Help': (field_info.get('help', '') or '')[:50]  # Truncate long help text
                    })

                title = f'Fields for model "{model}"'
                if field:
                    title += f' (field: {field})'

                format_table(
                    display_data,
                    columns=['Field', 'Type', 'Required', 'Readonly', 'Description', 'Help'],
                    title=title,
                    console=ctx.console
                )
                ctx.console.print(f"\n[dim]Found {len(fields_def)} field(s)[/dim]")
            else:
                ctx.console.print(f'[yellow]No fields found for model "{model}"[/yellow]')

    except Exception as e:
        error_msg = str(e)
        suggestion = None

        if 'does not exist' in error_msg.lower() or 'not found' in error_msg.lower():
            suggestion = "Use 'odoo get-models' to list available models"

        output_error(
            f'Failed to retrieve fields for model "{model}"',
            error_type='data',
            details=error_msg,
            suggestion=suggestion,
            console=ctx.console,
            json_mode=json_mode,
            exit_code=3
        )
