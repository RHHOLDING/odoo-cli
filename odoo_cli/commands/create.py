"""
Create command - Create new Odoo records with simple field=value syntax.
"""

import click
import json as json_lib
import sys
from typing import Tuple
from odoo_cli.field_utils import parse_field_values, validate_fields
from odoo_cli.utils.context_parser import parse_context_flags


@click.command('create')
@click.argument('model')
@click.option(
    '--fields', '-f',
    multiple=True,
    required=True,
    help='Field values as key=value pairs (can be specified multiple times)'
)
@click.option(
    '--no-validate',
    is_flag=True,
    help='Skip field validation (faster but less safe)'
)
@click.option(
    '--context',
    multiple=True,
    help='Context key=value (e.g., --context active_test=false)'
)
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (LLM-friendly)')
@click.pass_context
def create(ctx, model: str, fields: Tuple[str, ...], no_validate: bool, context: tuple, output_json: bool):
    """
    Create new record with simple field=value syntax.

    No JSON required - just specify fields directly:

    \b
    Examples:
        # Create partner with name and email
        odoo create res.partner --fields name="Test Partner" --fields email="test@test.com"

        # Create sale order (shorter syntax)
        odoo create sale.order -f partner_id=123 -f date_order="2025-11-21"

        # Create with multiple fields
        odoo create res.partner -f name="John Doe" -f email="john@test.com" -f phone="+49123"

        # Create with boolean and integer
        odoo create res.partner -f name="Active Partner" -f active=true -f partner_id=5

        # Skip validation for speed
        odoo create res.partner -f name="Test" --no-validate

        # JSON output for automation
        odoo create res.partner -f name="Test" --json

    \b
    Field Types (auto-detected):
        Strings:    name="Test" or name=Test (quotes optional)
        Integers:   partner_id=123
        Floats:     price=19.99
        Booleans:   active=true or active=false
        Lists:      category_ids=[1,2,3]
        Null:       parent_id=null or parent_id=false

    \b
    Notes:
        - Field validation is enabled by default (checks field existence and types)
        - Use --no-validate to skip validation (faster but risk errors from Odoo)
        - Quotes are optional for strings without spaces
        - Use --json for automation/scripting
    """
    # Determine JSON mode (command flag takes precedence over global)
    json_mode = output_json if output_json is not None else ctx.obj.json_mode

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
                click.echo(json_lib.dumps(error_response))
                sys.exit(1)
            else:
                console.print(f"[red]✗ Context Parsing Error:[/red] {e}")
                console.print("\n[yellow]Tip:[/yellow] Use format: --context key=value")
                sys.exit(1)

    try:
        # Parse field=value pairs
        try:
            field_dict = parse_field_values(fields)
        except ValueError as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'field_parsing',
                    'suggestion': 'Check field=value syntax. Example: name="Test"'
                }
                click.echo(json_lib.dumps(error_response))
                sys.exit(1)
            else:
                console.print(f"[red]✗ Field Parsing Error:[/red] {e}")
                console.print("\n[yellow]Tip:[/yellow] Use format: --fields key=value")
                console.print("Example: --fields name=\"Test\" --fields email=\"test@test.com\"")
                sys.exit(1)

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
                        'suggestion': 'Run: odoo get-fields ' + model
                    }
                    click.echo(json_lib.dumps(error_response))
                    sys.exit(1)
                else:
                    console.print(f"[red]✗ Validation Error:[/red]\n{e}")
                    console.print(f"\n[yellow]Tip:[/yellow] Run: [cyan]odoo get-fields {model}[/cyan]")
                    console.print("Or use [cyan]--no-validate[/cyan] to skip validation")
                    sys.exit(1)

        # Create record
        try:
            record_id = client.execute(model, 'create', field_dict, context=parsed_context)
        except Exception as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'odoo_error',
                    'suggestion': 'Check Odoo server logs or field values'
                }
                click.echo(json_lib.dumps(error_response))
                sys.exit(1)
            else:
                console.print(f"[red]✗ Odoo Error:[/red] {e}")
                console.print(f"\n[yellow]Tip:[/yellow] Check field values and Odoo server logs")
                sys.exit(1)

        # Output result
        if json_mode:
            result = {
                'success': True,
                'id': record_id,
                'model': model,
                'fields': field_dict
            }
            click.echo(json_lib.dumps(result, indent=2))
        else:
            console.print(f"[green]✓ Success![/green] Created {model} record")
            console.print(f"  ID: [cyan]{record_id}[/cyan]")
            console.print(f"\n[dim]To view: [/dim][cyan]odoo read {model} {record_id}[/cyan]")

    except KeyboardInterrupt:
        if not json_mode:
            console.print("\n[yellow]Cancelled[/yellow]")
        sys.exit(130)
