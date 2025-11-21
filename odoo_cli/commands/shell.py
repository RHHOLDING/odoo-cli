"""
Interactive Python shell with Odoo client
"""

import click
import code
import os
import sys
import json
from pprint import pprint
from datetime import datetime, date, timedelta
from odoo_cli.client import OdooClient
from odoo_cli.models.context import CliContext
from odoo_cli.utils import output_error


BANNER_TEXT = """
[bold cyan]Odoo XML-RPC Shell[/bold cyan]

Available in shell:
  [green]client[/green]    - Authenticated OdooClient instance
  [green]json[/green]      - JSON module for data parsing
  [green]pprint[/green]    - Pretty-print for complex objects
  [green]datetime[/green]  - datetime, date, timedelta

Quick examples:
  >>> client.search_count('res.partner', [])
  >>> partners = client.search_read('res.partner', [], limit=5)
  >>> pprint(partners)
  >>> client.execute('res.partner', 'search', [['is_company', '=', True]], {'limit': 10})

Type [yellow]exit()[/yellow] or [yellow]Ctrl+D[/yellow] to exit.
"""


@click.command('shell')
@click.option('--no-banner', is_flag=True, help='Skip the examples banner')
@click.pass_obj
def shell(ctx: CliContext, no_banner: bool):
    """
    Interactive Python shell with Odoo client

    Examples:
        odoo shell
        odoo shell --no-banner
    """
    # Create client
    try:
        client = OdooClient(
            url=ctx.config['url'],
            db=ctx.config['db'],
            username=ctx.config['username'],
            password=ctx.config['password'],
            timeout=ctx.config.get('timeout', 30),
            verify_ssl=ctx.config.get('verify_ssl', True)
        )
        client.connect()
    except ConnectionError as e:
        output_error(
            'Failed to connect to Odoo',
            error_type='connection',
            details=str(e),
            suggestion='Check URL and network connectivity',
            console=ctx.console,
            json_mode=False,
            exit_code=1
        )
    except ValueError as e:
        output_error(
            'Authentication failed',
            error_type='auth',
            details=str(e),
            suggestion='Verify credentials in configuration',
            console=ctx.console,
            json_mode=False,
            exit_code=2
        )

    # Setup shell namespace
    namespace = {
        'client': client,
        'json': json,
        'pprint': pprint,
        'datetime': datetime,
        'date': date,
        'timedelta': timedelta,
    }

    # Show banner
    if not no_banner:
        ctx.console.print(BANNER_TEXT)
        ctx.console.print(f"[dim]Connected to: {client.url} ({client.db})[/dim]\n")

    # Setup history file
    history_file = os.path.expanduser('~/.odoo_cli_history')

    # Try to setup readline for history and tab completion
    try:
        import readline
        import rlcompleter

        # Setup tab completion
        readline.set_completer(rlcompleter.Completer(namespace).complete)
        readline.parse_and_bind("tab: complete")

        # Load history
        if os.path.exists(history_file):
            try:
                readline.read_history_file(history_file)
            except Exception:
                pass  # Ignore history read errors

        # Save history on exit
        import atexit
        atexit.register(lambda: save_history(readline, history_file))

    except ImportError:
        # readline not available (Windows)
        pass

    # Start interactive console
    console = code.InteractiveConsole(namespace)
    try:
        console.interact(banner='', exitmsg='')
    except SystemExit:
        pass


def save_history(readline_module, history_file: str):
    """Save readline history to file"""
    try:
        readline_module.set_history_length(1000)
        readline_module.write_history_file(history_file)
    except Exception:
        pass  # Ignore save errors
