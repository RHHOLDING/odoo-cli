"""
AGENT-INFO command - Quick orientation for LLM agents.

Provides a structured overview of tool capabilities, connection status,
and next steps for agents encountering this tool for the first time.
"""

import json as json_lib
import click


@click.command('agent-info')
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (always enabled for this command)')
@click.pass_context
def agent_info(ctx, output_json: bool):
    """
    Quick orientation for LLM agents.

    Provides a structured overview of odoo-cli capabilities,
    current connection status, and recommended next steps.

    This command always outputs JSON for LLM consumption.

    Examples:

        \b
        # Get quick orientation
        odoo-cli agent-info

        \b
        # Explicit JSON output
        odoo-cli agent-info --json
    """
    from odoo_cli import __version__

    cli_context = ctx.obj
    client = cli_context.client
    console = cli_context.console

    # Get profile information
    profile_info = {
        "name": getattr(cli_context, 'profile_name', 'default'),
        "readonly": getattr(client, 'readonly', False),
    }

    # Test connection status
    connection_status = "unknown"
    server_version = None
    try:
        if client.uid:
            connection_status = "connected"
            # Try to get server version
            try:
                version_info = client.version()
                server_version = version_info.get('server_version', 'unknown')
            except Exception:
                pass
        else:
            connection_status = "not_authenticated"
    except Exception as e:
        connection_status = f"error: {str(e)}"

    # Build structured response
    response = {
        "tool": "odoo-cli",
        "version": __version__,
        "description": "LLM-friendly Odoo JSON-RPC interface",
        "connection": {
            "status": connection_status,
            "server_version": server_version,
            "url": client.url if hasattr(client, 'url') else None,
            "database": client.db if hasattr(client, 'db') else None,
        },
        "profile": profile_info,
        "capabilities": {
            "read": [
                "search - Search records by domain",
                "read - Read record by ID",
                "search-count - Count matching records",
                "get-fields - List model fields",
                "get-models - List available models",
                "name-search - Search by name pattern",
                "name-get - Get display names"
            ],
            "write": [
                "create - Create single record (use --force for readonly profiles)",
                "update - Update records (use --force for readonly profiles)",
                "delete - Delete records (use --force for readonly profiles)",
                "create-bulk - Bulk create from JSON file",
                "update-bulk - Bulk update from JSON file"
            ],
            "advanced": [
                "exec - Execute Python code with client access",
                "execute - Call any Odoo method",
                "aggregate - Aggregation queries"
            ],
            "meta": [
                "profiles - Manage connection profiles",
                "context - Show project business context",
                "agent-info - This command"
            ]
        },
        "quick_start": {
            "list_models": "odoo-cli get-models --json",
            "search_partners": "odoo-cli search res.partner '[]' --limit 10 --json",
            "read_record": "odoo-cli read res.partner 1 --json",
            "get_fields": "odoo-cli get-fields res.partner --json",
            "create_record": "odoo-cli create res.partner -f name=\"Test\" --json",
            "update_record": "odoo-cli update res.partner 1 -f name=\"Updated\" --json"
        },
        "important_flags": {
            "--json": "Always use for structured output (LLM-friendly)",
            "--force": "Override readonly profile protection for writes",
            "--profile NAME": "Use specific connection profile",
            "--llm-help": "Full command reference as JSON"
        },
        "readonly_profile_note": (
            f"Current profile is {'READONLY - use --force flag to write' if profile_info['readonly'] else 'writable'}"
        ),
        "next_steps": [
            "Run 'odoo-cli get-models --json' to see available models",
            "Run 'odoo-cli context show --json' for project business context",
            "Use --json flag on all commands for structured output",
            "Use --force flag to write on readonly profiles"
        ]
    }

    # Always output JSON (this command is for agents)
    click.echo(json_lib.dumps(response, indent=2))
