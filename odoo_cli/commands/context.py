"""
Context management commands for accessing project-specific business context
"""

import click
from rich.console import Console
from rich.table import Table
from rich import box

from odoo_cli.context import ContextManager
from odoo_cli.models.context import CliContext
from odoo_cli.utils.output import output_json, output_error


# Hardcoded task-to-section mappings for context guide
TASK_MAPPINGS = {
    'create-sales-order': ['companies', 'warehouses'],
    'manage-inventory': ['warehouses', 'modules'],
    'purchase-approval': ['workflows', 'companies'],
    'production-workflow': ['modules', 'workflows']
}


@click.group(name='context')
def context():
    """Manage project-specific business context for LLM agents"""
    pass


@context.command()
@click.option(
    '--section',
    type=str,
    help='Filter by section (companies, warehouses, workflows, modules, notes)'
)
@click.option('--json', 'output_json_flag', is_flag=True, default=None, help='Output as JSON')
@click.pass_obj
def show(ctx: CliContext, section: str, output_json_flag: bool) -> None:
    """Display business context for LLM agents

    Examples:
        odoo-cli context show
        odoo-cli context show --section companies
        odoo-cli context show --section warehouses --json
    """
    # Determine JSON mode (command flag takes precedence over global)
    json_mode = output_json_flag if output_json_flag is not None else ctx.json_mode

    manager = ContextManager()
    context_data = manager.load()

    if not context_data:
        if json_mode:
            output_json({'context': {}, 'message': 'No context file found in current directory'})
        else:
            ctx.console.print('[yellow]No .odoo-context.json file found in current directory[/yellow]')
        return

    # Filter by section if requested
    if section:
        if section in context_data:
            filtered_data = {section: context_data[section]}
        else:
            filtered_data = {section: []}
    else:
        filtered_data = context_data

    # Output
    if json_mode:
        output_json({'context': filtered_data})
    else:
        # Rich formatting
        _display_context_rich(filtered_data, ctx.console)


@context.command()
@click.option(
    '--task',
    required=True,
    type=click.Choice(list(TASK_MAPPINGS.keys())),
    help='Task name for context-aware guidance'
)
@click.option('--json', 'output_json_flag', is_flag=True, default=None, help='Output as JSON')
@click.pass_obj
def guide(ctx: CliContext, task: str, output_json_flag: bool) -> None:
    """Get context-aware guidance for common tasks

    Available tasks:
        - create-sales-order: Guidance for creating sales orders
        - manage-inventory: Guidance for inventory management
        - purchase-approval: Guidance for purchase workflows
        - production-workflow: Guidance for production workflows

    Examples:
        odoo-cli context guide --task create-sales-order
        odoo-cli context guide --task manage-inventory --json
    """
    # Determine JSON mode
    json_mode = output_json_flag if output_json_flag is not None else ctx.json_mode

    manager = ContextManager()
    context_data = manager.load()

    if not context_data:
        if json_mode:
            output_json({'task': task, 'guide': {}, 'message': 'No context file found'})
        else:
            ctx.console.print('[yellow]No context file found in current directory[/yellow]')
        return

    # Get relevant sections for this task
    relevant_sections = TASK_MAPPINGS.get(task, [])
    guide_data = {}
    for section in relevant_sections:
        guide_data[section] = manager.get_section(section)

    # Output
    if json_mode:
        output_json({'task': task, 'guide': guide_data})
    else:
        # Rich formatting
        _display_guide_rich(task, guide_data, ctx.console)


@context.command()
@click.option(
    '--strict',
    is_flag=True,
    help='Enforce strict validation (schema + completeness)'
)
@click.option('--json', 'output_json_flag', is_flag=True, default=None, help='Output as JSON')
@click.pass_obj
def validate(ctx: CliContext, strict: bool, output_json_flag: bool) -> None:
    """Validate context file against schema and check for issues

    Normal mode: Checks JSON syntax, warns about potential security issues
    Strict mode: Enforces schema validation, requires all sections, fails on warnings

    Examples:
        odoo-cli context validate
        odoo-cli context validate --strict
        odoo-cli context validate --json
    """
    # Determine JSON mode
    json_mode = output_json_flag if output_json_flag is not None else ctx.json_mode

    manager = ContextManager()
    result = manager.validate(strict=strict)

    # Determine exit code
    exit_code = 0 if result['valid'] else 3

    # Output
    if json_mode:
        output_json(result)
    else:
        # Rich formatting
        _display_validation_rich(result, strict, ctx.console)

    # Set exit code
    ctx.obj.exit_code = exit_code


def _display_context_rich(context_data: dict, console: Console) -> None:
    """Display context in Rich format (human-readable)"""
    if not context_data:
        console.print('[yellow]No context to display[/yellow]')
        return

    for section, data in context_data.items():
        if not data:
            console.print(f'[dim]{section}: (empty)[/dim]')
            continue

        console.print(f'\n[bold cyan]{section.title()}[/bold cyan]')

        if isinstance(data, list):
            if not data:
                console.print('  (empty)')
                continue
            for item in data:
                if isinstance(item, dict):
                    _display_dict_items(item, console, indent='  ')
                else:
                    console.print(f'  - {item}')
        elif isinstance(data, dict):
            _display_dict_items(data, console, indent='  ')


def _display_dict_items(item: dict, console: Console, indent: str = '') -> None:
    """Helper to display dictionary items with indentation"""
    for key, value in item.items():
        if isinstance(value, (list, dict)):
            console.print(f'{indent}{key}:')
            if isinstance(value, list):
                for v in value:
                    console.print(f'{indent}  - {v}')
            else:
                for k, v in value.items():
                    console.print(f'{indent}  {k}: {v}')
        else:
            console.print(f'{indent}{key}: {value}')


def _display_guide_rich(task: str, guide_data: dict, console: Console) -> None:
    """Display task-specific guidance in Rich format"""
    console.print(f'\n[bold blue]Guidance for: {task}[/bold blue]')

    if not guide_data or all(not v for v in guide_data.values()):
        console.print('[yellow]No context available for this task[/yellow]')
        return

    for section, data in guide_data.items():
        if not data:
            continue

        console.print(f'\n[bold cyan]{section.title()}[/bold cyan]')

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if 'name' in item:
                        console.print(f'  • {item["name"]}')
                        if 'context' in item:
                            console.print(f'    {item["context"]}')
                    else:
                        _display_dict_items(item, console, indent='  ')
                else:
                    console.print(f'  • {item}')


def _display_validation_rich(result: dict, strict: bool, console: Console) -> None:
    """Display validation result in Rich format"""
    is_valid = result['valid']
    errors = result.get('errors', [])
    warnings = result.get('warnings', [])

    mode = '[bold yellow]STRICT[/bold yellow]' if strict else 'Normal'
    status = '[bold green]✓ Valid[/bold green]' if is_valid else '[bold red]✗ Invalid[/bold red]'

    console.print(f'\n{status} (Mode: {mode})\n')

    if errors:
        console.print('[bold red]Errors:[/bold red]')
        for error in errors:
            console.print(f'  [red]•[/red] {error}')

    if warnings:
        console.print('\n[bold yellow]Warnings:[/bold yellow]')
        for warning in warnings:
            console.print(f'  [yellow]•[/yellow] {warning}')

    if is_valid and not warnings:
        console.print('[green]Context file is valid and ready to use[/green]')
