"""
DELETE command - Delete Odoo records by ID.

Usage:
    odoo delete res.partner 123
    odoo delete sale.order 1,2,3 --force
"""

import sys
import json as json_lib

import click
from rich.console import Console

from odoo_cli.utils.context_parser import parse_context_flags


@click.command('delete')
@click.argument('model')
@click.argument('ids')
@click.option('--force', is_flag=True,
              help='Skip confirmation prompt')
@click.option('--context', multiple=True,
              help='Context key=value (e.g., --context active_test=false)')
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (LLM-friendly)')
@click.pass_context
def delete(ctx, model: str, ids: str, force: bool, context: tuple, output_json: bool):
    """
    Delete records by ID.

    MODEL: The Odoo model name (e.g., res.partner, sale.order)

    IDS: Comma-separated record IDs to delete (e.g., 123 or 1,2,3)

    ⚠️  WARNING: This operation is IRREVERSIBLE! Deleted records cannot be recovered.

    Examples:

        \b
        # Delete single record (with confirmation)
        odoo delete res.partner 123

        \b
        # Delete multiple records
        odoo delete sale.order 1,2,3

        \b
        # Skip confirmation
        odoo delete res.partner 456 --force

        \b
        # JSON output (no confirmation prompt)
        odoo delete res.partner 123 --json

    Safety Features:

        \b
        - Confirmation prompt required (unless --force or --json)
        - Clear warning about irreversibility
        - Lists record IDs before deletion
        - Returns count of deleted records
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

        # Confirmation prompt (unless --force or --json)
        if not force and not json_mode:
            console.print(f"\n[yellow]⚠️  WARNING:[/yellow] You are about to DELETE [red]{len(record_ids)}[/red] record(s)")
            console.print(f"  Model: [cyan]{model}[/cyan]")
            console.print(f"  IDs: [cyan]{', '.join(map(str, record_ids))}[/cyan]")
            console.print("\n[red]This operation is IRREVERSIBLE![/red]")

            if not click.confirm('\nDo you want to continue?', default=False):
                console.print("\n[yellow]Operation cancelled by user[/yellow]")
                sys.exit(130)

        # Delete records using Odoo's unlink method
        try:
            result = client.execute(model, 'unlink', record_ids, context=parsed_context)
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
                console.print("\n[yellow]Hint:[/yellow] Record may not exist or you lack delete permissions", err=True)
                sys.exit(3)

        # Output result
        if json_mode:
            output = {
                'success': True,
                'deleted': result,  # Odoo unlink() returns True on success
                'ids': record_ids,
                'count': len(record_ids),
                'model': model
            }
            click.echo(json_lib.dumps(output, indent=2))
        else:
            console.print(f"\n[green]✓ Success![/green] Deleted {len(record_ids)} {model} record(s)")
            console.print(f"  IDs: [cyan]{', '.join(map(str, record_ids))}[/cyan]")

    except KeyboardInterrupt:
        if not json_mode:
            console.print("\n[yellow]Operation cancelled by user[/yellow]", err=True)
        sys.exit(130)
