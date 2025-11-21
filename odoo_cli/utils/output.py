"""
Utility functions for output formatting and JSON handling
"""

import json
import sys
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich import box


def format_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
    console: Optional[Console] = None
) -> None:
    """
    Format data as a Rich table

    Args:
        data: List of dictionaries to display
        columns: Column names to display (None for all)
        title: Table title
        console: Rich console instance (stderr)
    """
    if not data:
        if console:
            console.print("[yellow]No results found[/yellow]")
        return

    console = console or Console(stderr=True)

    # Determine columns
    if columns is None:
        columns = list(data[0].keys())

    # Create table
    table = Table(
        title=title,
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan"
    )

    # Add columns
    for col in columns:
        table.add_column(col.replace('_', ' ').title())

    # Add rows
    for row in data:
        values = []
        for col in columns:
            value = row.get(col, '')

            # Handle special types
            if isinstance(value, (list, tuple)):
                if len(value) == 2 and isinstance(value[0], int):
                    # Many2one field: [id, name]
                    value = value[1] if len(value) > 1 else str(value[0])
                else:
                    value = ', '.join(map(str, value))
            elif value is None:
                value = ''
            elif isinstance(value, bool):
                value = '✓' if value else '✗'
            else:
                value = str(value)

            values.append(value)

        table.add_row(*values)

    console.print(table)


def output_json(data: Any, success: bool = True, error: Optional[str] = None) -> None:
    """
    Output JSON to stdout

    Args:
        data: Data to output
        success: Success flag
        error: Error message (if failure)
    """
    if success:
        result = {
            'success': True,
            'data': data
        }
    else:
        result = {
            'success': False,
            'error': error or 'Unknown error'
        }

    print(json.dumps(result, default=str, indent=2))


def output_error(
    message: str,
    error_type: str = 'unknown',
    details: Optional[str] = None,
    suggestion: Optional[str] = None,
    console: Optional[Console] = None,
    json_mode: bool = False,
    exit_code: int = 3
) -> None:
    """
    Output error message

    Args:
        message: Error message
        error_type: Type of error (connection, auth, data, unknown)
        details: Additional details
        suggestion: Suggestion for fixing
        console: Rich console for non-JSON output
        json_mode: Whether to output JSON
        exit_code: Exit code to use
    """
    if json_mode:
        error_data = {
            'success': False,
            'error': message,
            'error_type': error_type
        }
        if details:
            error_data['details'] = details
        if suggestion:
            error_data['suggestion'] = suggestion

        print(json.dumps(error_data, indent=2))
    else:
        console = console or Console(stderr=True)
        console.print(f"[red]✗ Error:[/red] {message}")
        if details:
            console.print(f"  [dim]{details}[/dim]")
        if suggestion:
            console.print(f"  [yellow]→[/yellow] {suggestion}")

    sys.exit(exit_code)


def parse_json_arg(value: str, arg_name: str = 'argument') -> Any:
    """
    Parse JSON argument

    Args:
        value: JSON string
        arg_name: Argument name for error messages

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {arg_name}: {e}")


def confirm_large_dataset(count: int, threshold: int = 500) -> bool:
    """
    Prompt user to confirm large dataset retrieval

    Args:
        count: Number of records
        threshold: Warning threshold

    Returns:
        True if user confirms, False otherwise
    """
    if count <= threshold:
        return True

    console = Console(stderr=True)
    console.print(f"[yellow]⚠ Warning:[/yellow] Query would return {count} records.")

    try:
        response = input("Continue? (Y/n): ").strip().lower()
        return response in ('', 'y', 'yes')
    except (KeyboardInterrupt, EOFError):
        return False
