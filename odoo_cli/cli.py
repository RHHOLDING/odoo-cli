"""
Main CLI entry point for odoo-xml-cli
"""

import click
import sys
import os
from typing import Optional
from odoo_cli.models.context import CliContext
from odoo_cli.config import load_config, validate_config
from odoo_cli.help import print_llm_help
from rich.console import Console


@click.group(invoke_without_command=True)
@click.option('--json', is_flag=True, help='Output pure JSON to stdout')
@click.option('--llm-help', is_flag=True, help='Show LLM-optimized help (JSON format)')
@click.option('--profile', '-p', help='Environment profile (staging, production, dev)')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.option('--url', help='Odoo server URL')
@click.option('--db', help='Database name')
@click.option('--username', help='Login username')
@click.option('--password', help='Login password')
@click.option('--timeout', type=int, help='Connection timeout in seconds')
@click.option('--no-verify-ssl', is_flag=True, help='Disable SSL certificate verification')
@click.pass_context
def cli(ctx, json, llm_help, profile, config, url, db, username, password, timeout, no_verify_ssl):
    """
    Execute Python code against Odoo.

    \b
    PRIMARY USAGE (exec):
        odoo-cli exec -c "print(client.search_count('res.partner', []))"
        odoo-cli exec -c "result = client.search_read('res.partner', [], limit=5)" --json
        odoo-cli exec script.py --json

    \b
    The 'client' object is pre-authenticated and ready to use:
        client.search(model, domain)
        client.search_read(model, domain, fields, limit)
        client.read(model, ids, fields)
        client.create(model, values)  # blocked if profile is readonly
        client.write(model, ids, values)
        client.unlink(model, ids)

    \b
    SETUP:
        odoo-cli profiles add staging --url https://... --db mydb -u admin -p secret
        odoo-cli profiles list

    Helper commands (search, create, read, etc.) available for simple operations.
    """
    # Handle LLM help request (no credentials needed)
    if llm_help:
        print_llm_help(output_format="json")
        sys.exit(0)

    # Check for ODOO_CLI_JSON environment variable
    # This allows LLMs to set JSON mode once via export ODOO_CLI_JSON=1
    env_json = os.environ.get('ODOO_CLI_JSON', '').lower() in ('1', 'true', 'yes')
    json_mode = json or env_json

    # Initialize context
    console = Console(stderr=True) if not json_mode else Console(file=sys.stderr, stderr=True)

    # Load configuration
    try:
        config_dict = load_config(
            config_file=config,
            profile=profile,
            url=url,
            db=db,
            username=username,
            password=password,
            timeout=timeout,
            verify_ssl=not no_verify_ssl
        )
    except Exception as e:
        if json_mode:
            error_response = {
                'success': False,
                'error': str(e),
                'error_type': 'connection',
                'suggestion': 'Check configuration and connection settings'
            }
            import json as json_lib
            click.echo(json_lib.dumps(error_response))
            sys.exit(1)
        else:
            console.print(f"[red]✗ Configuration error:[/red] {e}")
            sys.exit(1)

    # Create and store context
    ctx.obj = CliContext(
        config=config_dict,
        json_mode=json_mode,
        console=console
    )

    # If no command specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Import commands to register them
from odoo_cli.commands import execute, search, read, get_models, get_fields
from odoo_cli.commands import search_employee, search_holidays, shell, create, update, delete, create_bulk, update_bulk, aggregate, search_count, name_get, name_search, context
from odoo_cli.commands import profiles, exec_code

# Register commands
cli.add_command(exec_code.exec_code)  # PRIMARY: Execute Python code
cli.add_command(create.create)  # User-friendly create command
cli.add_command(update.update)  # User-friendly update command
cli.add_command(delete.delete)  # User-friendly delete command
cli.add_command(create_bulk.create_bulk)  # Batch create command
cli.add_command(update_bulk.update_bulk)  # Batch update command
cli.add_command(aggregate.aggregate)  # Aggregation helper command
cli.add_command(execute.execute)
cli.add_command(search.search)
cli.add_command(search_count.search_count)  # Quick win: fast counting
cli.add_command(name_get.name_get)  # Quick win: ID to name conversion
cli.add_command(name_search.name_search)  # Quick win: fuzzy name search
cli.add_command(read.read)
cli.add_command(get_models.get_models)
cli.add_command(get_models.get_models, name='models')  # Alias: models = get-models
cli.add_command(get_fields.get_fields)
cli.add_command(get_fields.get_fields, name='fields')  # Alias: fields = get-fields
cli.add_command(search_employee.search_employee)
cli.add_command(search_holidays.search_holidays)
cli.add_command(shell.shell)
cli.add_command(context.context)  # Project context management
cli.add_command(profiles.profiles)  # Environment profile management


def main():
    """Main entry point for the CLI"""
    try:
        cli(standalone_mode=False)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except Exception as e:
        # Handle unexpected errors gracefully
        import traceback
        if '--json' in sys.argv:
            import json
            error_response = {
                'success': False,
                'error': str(e),
                'error_type': 'unknown',
                'details': traceback.format_exc()
            }
            click.echo(json.dumps(error_response))
            sys.exit(3)
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(3)


if __name__ == '__main__':
    main()