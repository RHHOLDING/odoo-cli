"""
AGGREGATE command - Aggregate Odoo records (sum, average, count).

Usage:
    odoo aggregate sale.order '[["date_order",">=","2025-10-01"]]' --sum amount_total
    odoo aggregate sale.order '[]' --count --group-by state
"""

import sys
import json as json_lib
from typing import List, Dict, Any
from collections import defaultdict

import click
from rich.progress import Progress
from rich.table import Table
from rich.console import Console

from odoo_cli.utils.context_parser import parse_context_flags


def parse_domain_string(domain_str: str) -> List:
    """Parse domain string to Python list."""
    try:
        return json_lib.loads(domain_str)
    except json_lib.JSONDecodeError as e:
        raise ValueError(f"Invalid domain JSON: {str(e)}")


@click.command('aggregate')
@click.argument('model')
@click.argument('domain')
@click.option('--sum', 'sum_fields', multiple=True,
              help='Fields to sum')
@click.option('--avg', 'avg_fields', multiple=True,
              help='Fields to average')
@click.option('--count', 'count_flag', is_flag=True,
              help='Count records')
@click.option('--group-by', 'group_by_field',
              help='Field to group by')
@click.option('--batch-size', type=int, default=1000,
              help='Number of records per batch (default: 1000)')
@click.option('--context', multiple=True,
              help='Context key=value (e.g., --context active_test=false)')
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (LLM-friendly)')
@click.pass_context
def aggregate(ctx, model: str, domain: str, sum_fields: tuple, avg_fields: tuple,
              count_flag: bool, group_by_field: str, batch_size: int, context: tuple, output_json: bool):
    """
    Aggregate records by sum, average, or count.

    MODEL: The Odoo model name (e.g., sale.order, res.partner)

    DOMAIN: Search domain filter (JSON format)

    Examples:

        \b
        # Sum October 2025 sales
        odoo aggregate sale.order '[["date_order",">=","2025-10-01"]]' --sum amount_total

        \b
        # Count orders by state
        odoo aggregate sale.order '[]' --count --group-by state

        \b
        # Average order value by partner
        odoo aggregate sale.order '[]' --avg amount_total --group-by partner_id

        \b
        # Multiple aggregations
        odoo aggregate sale.order '[]' --sum amount_total --avg amount_total --count

    Output:

        \b
        Non-JSON mode: Rich formatted table
        JSON mode: Structured JSON with results
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
        # Parse domain
        try:
            domain_list = parse_domain_string(domain)
        except ValueError as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'domain_parse'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Domain Error:[/red] {str(e)}", err=True)
                sys.exit(3)

        # Validate at least one aggregation is requested
        if not (sum_fields or avg_fields or count_flag):
            error_msg = "Specify at least one: --sum, --avg, or --count"
            if json_mode:
                error_response = {
                    'success': False,
                    'error': error_msg,
                    'error_type': 'no_aggregation'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Error:[/red] {error_msg}", err=True)
                sys.exit(3)

        # Search for matching records
        try:
            record_ids = client.search(model, domain_list, limit=None, context=parsed_context)
        except Exception as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'search_error'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Search Error:[/red] {str(e)}", err=True)
                sys.exit(3)

        if not record_ids:
            if json_mode:
                output = {
                    'success': True,
                    'records': 0,
                    'groups': 0,
                    'results': []
                }
                click.echo(json_lib.dumps(output, indent=2))
            else:
                console.print("[yellow]No records found matching domain[/yellow]")
            return

        # Determine fields to read
        fields_to_read = set()
        if sum_fields:
            fields_to_read.update(sum_fields)
        if avg_fields:
            fields_to_read.update(avg_fields)
        if group_by_field:
            fields_to_read.add(group_by_field)

        # Read records in batches
        all_records = []
        total_records = len(record_ids)

        try:
            if json_mode:
                # Batch processing without progress bar in JSON mode
                for batch_start in range(0, total_records, batch_size):
                    batch_ids = record_ids[batch_start:batch_start + batch_size]
                    batch_records = client.read(model, batch_ids, list(fields_to_read), context=parsed_context)
                    all_records.extend(batch_records)
            else:
                # Batch processing with progress bar
                with Progress() as progress:
                    task = progress.add_task(
                        f"[cyan]Reading {total_records} records...",
                        total=total_records
                    )

                    for batch_start in range(0, total_records, batch_size):
                        batch_ids = record_ids[batch_start:batch_start + batch_size]
                        batch_records = client.read(model, batch_ids, list(fields_to_read), context=parsed_context)
                        all_records.extend(batch_records)
                        progress.update(task, advance=len(batch_ids))

        except Exception as e:
            if json_mode:
                error_response = {
                    'success': False,
                    'error': str(e),
                    'error_type': 'read_error'
                }
                click.echo(json_lib.dumps(error_response, indent=2), err=True)
                sys.exit(3)
            else:
                console.print(f"[red]✗ Read Error:[/red] {str(e)}", err=True)
                sys.exit(3)

        # Perform aggregations
        if group_by_field:
            # Group by field
            groups = defaultdict(lambda: {'count': 0, 'sums': {}, 'avgs': {}})

            for record in all_records:
                group_key = record.get(group_by_field, 'N/A')

                # Count
                groups[group_key]['count'] += 1

                # Sum
                for field in sum_fields:
                    value = record.get(field, 0)
                    if isinstance(value, (int, float)):
                        groups[group_key]['sums'][field] = groups[group_key]['sums'].get(field, 0) + value

                # Average (track sum and count separately)
                for field in avg_fields:
                    value = record.get(field, 0)
                    if isinstance(value, (int, float)):
                        if field not in groups[group_key]['avgs']:
                            groups[group_key]['avgs'][field] = {'sum': 0, 'count': 0}
                        groups[group_key]['avgs'][field]['sum'] += value
                        groups[group_key]['avgs'][field]['count'] += 1

            # Format results
            results = []
            for group_key, data in sorted(groups.items()):
                result = {group_by_field: group_key}

                if count_flag:
                    result['count'] = data['count']

                for field in sum_fields:
                    result[f'{field}_sum'] = data['sums'].get(field, 0)

                for field in avg_fields:
                    avg_data = data['avgs'].get(field, {})
                    if avg_data.get('count', 0) > 0:
                        result[f'{field}_avg'] = avg_data['sum'] / avg_data['count']
                    else:
                        result[f'{field}_avg'] = 0

                results.append(result)
        else:
            # Global aggregation
            results = [{}]

            if count_flag:
                results[0]['count'] = len(all_records)

            for field in sum_fields:
                total = sum(record.get(field, 0) for record in all_records
                           if isinstance(record.get(field), (int, float)))
                results[0][f'{field}_sum'] = total

            for field in avg_fields:
                values = [record.get(field) for record in all_records
                         if isinstance(record.get(field), (int, float))]
                if values:
                    results[0][f'{field}_avg'] = sum(values) / len(values)
                else:
                    results[0][f'{field}_avg'] = 0

        # Output results
        if json_mode:
            output = {
                'success': True,
                'records': total_records,
                'groups': len(results),
                'results': results
            }
            click.echo(json_lib.dumps(output, indent=2))
        else:
            # Display as Rich table
            if results:
                table = Table(title=f"Aggregation Results ({total_records} records)")

                # Add columns
                for key in results[0].keys():
                    table.add_column(str(key), style="cyan")

                # Add rows
                for result in results:
                    row_values = [str(result.get(key, '')) for key in results[0].keys()]
                    table.add_row(*row_values)

                console.print(table)
                console.print(f"\n[green]✓[/green] Processed [cyan]{total_records}[/cyan] record(s)")

    except KeyboardInterrupt:
        if not json_mode:
            console.print("\n[yellow]Operation cancelled by user[/yellow]", err=True)
        sys.exit(130)
    except Exception as e:
        if json_mode:
            error_response = {
                'success': False,
                'error': str(e),
                'error_type': 'unknown'
            }
            click.echo(json_lib.dumps(error_response, indent=2), err=True)
        else:
            console.print(f"[red]✗ Error:[/red] {str(e)}", err=True)
        sys.exit(3)
