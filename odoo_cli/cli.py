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
@click.option('--force', is_flag=True, help='Override readonly profile protection for write operations')
@click.option('--profile', '-p', help='Environment profile (staging, production, dev)')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.option('--url', help='Odoo server URL')
@click.option('--db', help='Database name')
@click.option('--username', help='Login username')
@click.option('--password', help='Login password')
@click.option('--timeout', type=int, help='Connection timeout in seconds')
@click.option('--no-verify-ssl', is_flag=True, help='Disable SSL certificate verification')
@click.pass_context
def cli(ctx, json, llm_help, force, profile, config, url, db, username, password, timeout, no_verify_ssl):
    """
    LLM-friendly Odoo JSON-RPC interface (v2.0 - exec-only architecture).

    \b
    PRIMARY USAGE:
        odoo-cli exec -c "result = client.search_read('res.partner', [], limit=5)" --json
        odoo-cli exec script.py --json

    \b
    The 'client' object is pre-authenticated and ready to use:
        client.search(model, domain)
        client.search_read(model, domain, fields, limit)
        client.read(model, ids, fields)
        client.create(model, values)
        client.write(model, ids, values)
        client.unlink(model, ids)
        client.execute(model, method, *args)

    \b
    SETUP:
        odoo-cli config add staging --url https://... --db mydb -u admin -p secret
        odoo-cli config list

    \b
    LLM BOOTSTRAP:
        odoo-cli agent-info
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
        console=console,
        force_mode=force
    )

    # If no command specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Import v2.0 commands (exec-only architecture)
from odoo_cli.commands import context, profiles, exec_code, agent_info
from odoo_cli.deprecation import DEPRECATED_COMMANDS, create_deprecation_handler

# Register v2.0 commands
cli.add_command(exec_code.exec_code)  # PRIMARY: Execute Python code
cli.add_command(context.context)  # Project context management
cli.add_command(profiles.profiles)  # Environment profile management
cli.add_command(profiles.profiles, name='config')  # Alias: config = profiles
cli.add_command(agent_info.agent_info)  # Agent orientation/bootstrap

# Register deprecation handlers for removed commands
# These provide helpful migration guidance instead of "No such command" errors
for cmd_name in DEPRECATED_COMMANDS:
    cli.add_command(create_deprecation_handler(cmd_name), name=cmd_name)


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