"""
UPDATE-BULK command - Update multiple Odoo records from a JSON file.

Usage:
    odoo update-bulk res.partner --file updates.json
    odoo update-bulk sale.order -f changes.json --batch-size 50
"""

import sys
import json as json_lib
from pathlib import Path
from typing import Dict, List, Any

import click
from rich.progress import Progress
from rich.console import Console

from odoo_cli.utils.context_parser import parse_context_flags


def group_by_fields(updates: Dict[str, Dict]) -> Dict[str, List[int]]:
    """
    Group record IDs by their field updates for optimization.
    Records with identical field updates are grouped together.

    Returns: {field_tuple: [id1, id2, ...], ...}
    """
    field_groups = {}

    for record_id_str, fields in updates.items():
        record_id = int(record_id_str)
        # Create hashable key from fields
        field_key = tuple(sorted(fields.items()))

        if field_key not in field_groups:
            field_groups[field_key] = []
        field_groups[field_key].append(record_id)

    return field_groups


@click.command('update-bulk')
@click.argument('model')
@click.option('--file', '-f', required=True, type=click.Path(exists=True),
              help='JSON file with record updates')
@click.option('--batch-size', type=int, default=100,
              help='Number of records per batch (default: 100)')
@click.option('--json', 'json_mode', is_flag=True,
              help='Output result as JSON')
@click.option('--context', multiple=True,
              help='Context key=value (e.g., --context active_test=false)')
@click.pass_context
def update_bulk(ctx, model: str, file: str, batch_size: int, json_mode: bool, context: tuple):
    """
    Update multiple records from a JSON file.

    MODEL: The Odoo model name (e.g., res.partner, sale.order)

    FILE: Path to JSON file containing record updates

    File Format (object with ID keys):

        \b
        {
          "123": {"name": "Updated Name 1"},
          "124": {"name": "Updated Name 2", "email": "new@test.com"},
          ...
        }

    Examples:

        \b
        # Update partners from JSON file
        odoo update-bulk res.partner --file updates.json

        \b
        # Custom batch size
        odoo update-bulk res.partner -f changes.json --batch-size 50

        \b
        # JSON output
        odoo update-bulk res.partner -f changes.json --json

    Optimization:

        \b
        - Automatically groups records by identical field updates
        - Reduces API calls for bulk operations
        - Preserves order within groups
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
        # Load JSON file
        try:
            file_path = Path(file)
            with open(file_path, 'r') as f:
                updates = json_lib.load(f)
        except FileNotFoundError:
            error_msg = f"File not found: '{file}'"
            if json_mode:
                error_response = {
                    'success': False,
                    'error': error_msg,
                    'error_type': 'file_not_found'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Error:[/red] {error_msg}", err=True)
                sys.exit(3)
        except json_lib.JSONDecodeError as e:
            error_msg = f"Invalid JSON in file: {str(e)}"
            if json_mode:
                error_response = {
                    'success': False,
                    'error': error_msg,
                    'error_type': 'invalid_json'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Parse Error:[/red] {error_msg}", err=True)
                sys.exit(3)

        # Validate file format
        if not isinstance(updates, dict):
            error_msg = "JSON must be an object with record IDs as keys"
            if json_mode:
                error_response = {
                    'success': False,
                    'error': error_msg,
                    'error_type': 'invalid_format'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Error:[/red] {error_msg}", err=True)
                sys.exit(3)

        if not updates:
            error_msg = "JSON object is empty"
            if json_mode:
                error_response = {
                    'success': False,
                    'error': error_msg,
                    'error_type': 'empty_file'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Error:[/red] {error_msg}", err=True)
                sys.exit(3)

        # Group updates by common fields (optimization)
        field_groups = group_by_fields(updates)
        total_records = len(updates)
        total_groups = len(field_groups)
        updated_ids = []

        try:
            if json_mode:
                # Batch processing without progress bar in JSON mode
                group_num = 0
                for field_tuple, record_ids in field_groups.items():
                    group_num += 1
                    fields_dict = dict(field_tuple)

                    # Process this group in batches
                    for batch_start in range(0, len(record_ids), batch_size):
                        batch_ids = record_ids[batch_start:batch_start + batch_size]

                        try:
                            client.execute(model, 'write', batch_ids, fields_dict, context=parsed_context)
                            updated_ids.extend(batch_ids)
                        except Exception as e:
                            error_response = {
                                'success': False,
                                'error': str(e),
                                'error_type': 'batch_error',
                                'group_number': group_num,
                                'updated_so_far': len(updated_ids)
                            }
                            click.echo(json_lib.dumps(error_response, indent=2), err=True)
                            sys.exit(3)
            else:
                # Batch processing with progress bar
                with Progress() as progress:
                    task = progress.add_task(
                        f"[cyan]Updating {model} records...",
                        total=total_records
                    )

                    group_num = 0
                    for field_tuple, record_ids in field_groups.items():
                        group_num += 1
                        fields_dict = dict(field_tuple)

                        # Process this group in batches
                        for batch_start in range(0, len(record_ids), batch_size):
                            batch_ids = record_ids[batch_start:batch_start + batch_size]

                            try:
                                client.execute(model, 'write', batch_ids, fields_dict, context=parsed_context)
                                updated_ids.extend(batch_ids)
                            except Exception as e:
                                progress.stop()
                                console.print(f"[red]✗ Batch Error (group #{group_num}):[/red] {str(e)}", err=True)
                                console.print(f"[yellow]Updated so far:[/yellow] {len(updated_ids)} records", err=True)
                                sys.exit(3)

                            progress.update(task, advance=len(batch_ids))

        except Exception as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'odoo_error',
                    'updated_so_far': len(updated_ids)
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
            else:
                console.print(f"[red]✗ Error:[/red] {str(e)}", err=True)
            sys.exit(3)

        # Output result
        if json_mode:
            output = {
                'success': True,
                'updated': len(updated_ids),
                'ids': sorted(updated_ids),
                'model': model,
                'groups': total_groups,
                'batch_size': batch_size
            }
            click.echo(json_lib.dumps(output, indent=2))
        else:
            console.print(f"\n[green]✓ Success![/green] Updated {len(updated_ids)} {model} record(s)")
            console.print(f"  Optimization: {total_groups} field group(s)")
            if updated_ids:
                id_summary = ', '.join(map(str, sorted(updated_ids)[:5]))
                if len(updated_ids) > 5:
                    id_summary += f", ... (+{len(updated_ids) - 5} more)"
                console.print(f"  IDs: [cyan]{id_summary}[/cyan]")

    except KeyboardInterrupt:
        if not json_mode:
            console.print("\n[yellow]Operation cancelled by user[/yellow]", err=True)
        sys.exit(130)
