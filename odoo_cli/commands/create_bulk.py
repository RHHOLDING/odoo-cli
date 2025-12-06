"""
CREATE-BULK command - Create multiple Odoo records from a JSON file.

Usage:
    odoo create-bulk res.partner --file partners.json
    odoo create-bulk res.partner -f data.json --batch-size 50
"""

import sys
import json as json_lib
from pathlib import Path
from typing import List, Dict, Any

import click
from rich.progress import Progress
from rich.console import Console

from odoo_cli.utils.context_parser import parse_context_flags


@click.command('create-bulk')
@click.argument('model')
@click.option('--file', '-f', required=True, type=click.Path(exists=True),
              help='JSON file with array of records to create')
@click.option('--batch-size', type=int, default=100,
              help='Number of records per batch (default: 100)')
@click.option('--context', multiple=True,
              help='Context key=value (e.g., --context active_test=false)')
@click.option('--force', is_flag=True, help='Override readonly profile protection')
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (LLM-friendly)')
@click.pass_context
def create_bulk(ctx, model: str, file: str, batch_size: int, context: tuple, force: bool, output_json: bool):
    """
    Create multiple records from a JSON file.

    MODEL: The Odoo model name (e.g., res.partner, sale.order)

    FILE: Path to JSON file containing array of records

    File Format:

        \b
        [
          {"name": "Partner 1", "email": "p1@test.com"},
          {"name": "Partner 2", "email": "p2@test.com"},
          ...
        ]

    Examples:

        \b
        # Create partners from JSON file
        odoo create-bulk res.partner --file partners.json

        \b
        # Custom batch size
        odoo create-bulk res.partner -f data.json --batch-size 50

        \b
        # JSON output
        odoo create-bulk res.partner -f data.json --json

    Performance Tips:

        \b
        - Default batch size 100 is optimal for most cases
        - Reduce batch size if hitting timeout errors
        - Larger batches = fewer API calls but higher memory
    """
    # Determine JSON mode (command flag takes precedence over global)
    json_mode = output_json if output_json is not None else ctx.obj.json_mode

    cli_context = ctx.obj
    client = cli_context.client
    console = cli_context.console

    # Enable force write if --force flag is used
    if force:
        client._force_write = True

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
                records = json_lib.load(f)
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
        if not isinstance(records, list):
            error_msg = "JSON must be an array of records"
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

        if not records:
            error_msg = "JSON array is empty"
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

        # Process records in batches
        created_ids = []
        total_records = len(records)
        total_batches = (total_records + batch_size - 1) // batch_size

        try:
            if json_mode:
                # Batch processing without progress bar in JSON mode
                for batch_num in range(total_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min(start_idx + batch_size, total_records)
                    batch = records[start_idx:end_idx]

                    try:
                        # Create records in this batch
                        ids = client.execute(model, 'create', batch, context=parsed_context)
                        # Handle both single ID and list of IDs
                        if isinstance(ids, list):
                            created_ids.extend(ids)
                        else:
                            created_ids.append(ids)
                    except Exception as e:
                        error_response = {
                            'success': False,
                            'error': str(e),
                            'error_type': 'batch_error',
                            'batch_number': batch_num + 1,
                            'created_so_far': len(created_ids)
                        }
                        click.echo(json_lib.dumps(error_response, indent=2), err=True)
                        sys.exit(3)
            else:
                # Batch processing with progress bar
                with Progress() as progress:
                    task = progress.add_task(
                        f"[cyan]Creating {model} records...",
                        total=total_records
                    )

                    for batch_num in range(total_batches):
                        start_idx = batch_num * batch_size
                        end_idx = min(start_idx + batch_size, total_records)
                        batch = records[start_idx:end_idx]

                        try:
                            # Create records in this batch
                            ids = client.execute(model, 'create', batch, context=parsed_context)
                            # Handle both single ID and list of IDs
                            if isinstance(ids, list):
                                created_ids.extend(ids)
                            else:
                                created_ids.append(ids)
                        except Exception as e:
                            progress.stop()
                            console.print(f"[red]✗ Batch Error (#{batch_num + 1}):[/red] {str(e)}", err=True)
                            console.print(f"[yellow]Created so far:[/yellow] {len(created_ids)} records", err=True)
                            sys.exit(3)

                        # Update progress
                        progress.update(task, advance=len(batch))

        except Exception as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'odoo_error',
                    'created_so_far': len(created_ids)
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
            else:
                console.print(f"[red]✗ Error:[/red] {str(e)}", err=True)
            sys.exit(3)

        # Output result
        if json_mode:
            output = {
                'success': True,
                'created': len(created_ids),
                'ids': created_ids,
                'model': model,
                'batches': total_batches,
                'batch_size': batch_size
            }
            click.echo(json_lib.dumps(output, indent=2))
        else:
            console.print(f"\n[green]✓ Success![/green] Created {len(created_ids)} {model} record(s)")
            console.print(f"  Batches: {total_batches} × {batch_size} records")
            if created_ids:
                id_summary = ', '.join(map(str, created_ids[:5]))
                if len(created_ids) > 5:
                    id_summary += f", ... (+{len(created_ids) - 5} more)"
                console.print(f"  IDs: [cyan]{id_summary}[/cyan]")

    except KeyboardInterrupt:
        if not json_mode:
            console.print("\n[yellow]Operation cancelled by user[/yellow]", err=True)
        sys.exit(130)
