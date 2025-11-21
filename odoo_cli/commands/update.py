"""
UPDATE command - Update existing Odoo records with simple field=value syntax.

Usage:
    odoo update res.partner 123 --fields name="New Name"
    odoo update sale.order 1,2,3 --fields state="done"
"""

import sys
import json as json_lib
from typing import Tuple, List

import click
from rich.console import Console

from odoo_cli.field_utils import parse_field_values, validate_fields
from odoo_cli.field_utils.field_parser import format_field_validation_error
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('update')
@click.argument('model')
@click.argument('ids')
@click.option('--fields', '-f', multiple=True, required=True,
              help='Field values as key=value pairs (e.g., name="Test" or active=true)')
@click.option('--no-validate', is_flag=True,
              help='Skip field validation (faster but less safe)')
@click.option('--json', 'json_mode', is_flag=True,
              help='Output result as JSON')
@click.option('--context', multiple=True,
              help='Context key=value (e.g., --context active_test=false)')
@click.pass_context
def update(ctx, model: str, ids: str, fields: Tuple[str, ...], no_validate: bool, json_mode: bool, context: tuple):
    """
    Update existing records with simple field=value syntax.

    MODEL: The Odoo model name (e.g., res.partner, sale.order)

    IDS: Comma-separated record IDs to update (e.g., 123 or 1,2,3)

    Examples:

        \b
        # Update single record
        odoo update res.partner 123 -f name="Updated Name"

        \b
        # Update multiple records
        odoo update sale.order 1,2,3 -f state="done"

        \b
        # Multiple fields
        odoo update res.partner 123 -f name="Test" -f email="new@test.com" -f active=false

        \b
        # Skip validation for speed
        odoo update res.partner 123 -f name="Quick" --no-validate

        \b
        # JSON output
        odoo update res.partner 123 -f name="Test" --json

    Field Syntax:

        \b
        Strings:  name="Test" or name=Test (quotes optional)
        Integers: partner_id=123
        Floats:   price=19.99
        Booleans: active=true or active=false
        Lists:    category_ids=[1,2,3]
        Null:     parent_id=null or parent_id=false
    """
    cli_context = ctx.obj
    client = cli_context.client
    console = cli_context.console

    # Parse context
    parsed_context = None
    if context:
        try:
            parsed_context = parse_context_flags(list(context))
        except ValueError as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'context_parsing',
                    'suggestion': 'Context must be in format key=value (e.g., active_test=false)'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Context Parsing Error:[/red] {e}", err=True)
                console.print("\n[yellow]Tip:[/yellow] Use format: --context key=value", err=True)
                sys.exit(3)

    try:
        # Parse comma-separated IDs into list of integers
        try:
            record_ids = [int(id_str.strip()) for id_str in ids.split(',')]
        except ValueError as e:
            error_msg = f"Invalid IDs: '{ids}'. Expected comma-separated integers (e.g., 123 or 1,2,3)"
            if json_mode:
                error_response = {
                    'success': False,
                    'error': error_msg,
                    'error_type': 'invalid_ids',
                    'suggestion': 'Provide record IDs as comma-separated integers'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Error:[/red] {error_msg}", err=True)
                sys.exit(3)

        # Parse field=value pairs
        try:
            field_dict = parse_field_values(fields)
        except ValueError as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'field_parsing',
                    'suggestion': 'Check field=value syntax. Use quotes for strings: name="Test"'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Parse Error:[/red] {str(e)}", err=True)
                console.print("\n[yellow]Hint:[/yellow] Use field=value syntax (e.g., name=\"Test\")", err=True)
                sys.exit(3)

        # Validate fields (unless --no-validate)
        if not no_validate:
            try:
                validate_fields(client, model, field_dict)
            except ValueError as e:
                if json_mode:
                    error_response = {
                        'success': False,
                        'error': str(e),
                        'error_type': 'field_validation',
                        'suggestion': f'Run: odoo get-fields {model}'
                    }
                    click.echo(json_lib.dumps(error_response, indent=2), err=True)
                    sys.exit(3)
                else:
                    formatted_error = format_field_validation_error(e, model, list(field_dict.keys())[0])
                    console.print(formatted_error, err=True)
                    sys.exit(3)

        # Update records using Odoo's write method
        try:
            result = client.execute(model, 'write', record_ids, field_dict, context=parsed_context)
        except Exception as e:
            error_msg = str(e)
            if json_mode:
                error_response = {
                    'success': False,
                    'error': error_msg,
                    'error_type': 'odoo_error',
                    'model': model,
                    'ids': record_ids
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Odoo Error:[/red] {error_msg}", err=True)
                sys.exit(3)

        # Output result
        if json_mode:
            output = {
                'success': True,
                'updated': result,  # Odoo write() returns True on success
                'ids': record_ids,
                'count': len(record_ids),
                'model': model,
                'fields': field_dict
            }
            click.echo(json_lib.dumps(output, indent=2))
        else:
            console.print(f"[green]✓ Success![/green] Updated {len(record_ids)} {model} record(s)")
            console.print(f"  IDs: [cyan]{', '.join(map(str, record_ids))}[/cyan]")
            console.print(f"  Fields: {', '.join(field_dict.keys())}")

    except KeyboardInterrupt:
        if not json_mode:
            console.print("\n[yellow]Operation cancelled by user[/yellow]", err=True)
        sys.exit(130)
