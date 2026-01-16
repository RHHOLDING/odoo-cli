"""
AGENT-INFO command - Complete bootstrap for LLM agents.

Provides everything an LLM needs to start working with Odoo:
- Connection status
- Complete client API reference
- Common code patterns
- Domain syntax reference
- Error handling guide
"""

import json as json_lib
import click


@click.command('agent-info')
@click.option('--json', 'output_json', is_flag=True, default=None, help='Output pure JSON (always enabled)')
@click.pass_context
def agent_info(ctx, output_json: bool):
    """
    Complete bootstrap for LLM agents.

    Provides connection status, client API reference, and code patterns.
    This command always outputs JSON for LLM consumption.

    Examples:

        \b
        # Get complete API reference
        odoo-cli agent-info

        \b
        # Explicit JSON output
        odoo-cli agent-info --json
    """
    from odoo_cli import __version__

    cli_context = ctx.obj
    client = cli_context.client
    config = cli_context.config

    # Get profile information
    profile_info = {
        "name": config.get('profile_name', 'default'),
        "readonly": config.get('readonly', False),
    }

    # Test connection status
    connection_status = "unknown"
    server_version = None
    user_id = None
    try:
        if client.uid:
            connection_status = "connected"
            user_id = client.uid
            try:
                version_info = client.version()
                server_version = version_info.get('server_version', 'unknown')
            except Exception:
                pass
        else:
            connection_status = "not_authenticated"
    except Exception as e:
        connection_status = f"error: {str(e)}"

    # Build comprehensive response
    response = {
        "tool": "odoo-cli",
        "version": __version__,
        "architecture": "exec-only (v2.0)",
        "description": "LLM-friendly Odoo JSON-RPC interface",

        # Connection info
        "connection": {
            "status": connection_status,
            "server_version": server_version,
            "url": client.url if hasattr(client, 'url') else None,
            "database": client.db if hasattr(client, 'db') else None,
            "user_id": user_id,
        },

        # Profile info
        "profile": {
            "name": profile_info["name"],
            "readonly": profile_info["readonly"],
            "force_required": profile_info["readonly"],
        },

        # PRIMARY: exec command
        "primary_command": {
            "name": "exec",
            "description": "Execute Python code with pre-authenticated Odoo client",
            "usage": [
                'odoo-cli exec -c "result = client.search_count(\'res.partner\', [])" --json',
                'odoo-cli exec -c "result = client.search_read(\'res.partner\', [], limit=5)" --json',
                'odoo-cli exec script.py --json',
            ],
            "namespace": {
                "client": "Authenticated OdooClient - use this for ALL Odoo operations",
                "json": "JSON module (json.dumps, json.loads)",
                "datetime": "datetime module",
                "date": "date class from datetime",
                "timedelta": "timedelta class from datetime",
                "pprint": "Pretty printer for debugging",
                "result": "Set this variable for structured JSON output",
            },
            "critical": "Use 'client' NOT 'env'. This is JSON-RPC, not server-side Python.",
        },

        # Complete client API reference
        "client_api": {
            "query_methods": {
                "search": {
                    "signature": "client.search(model, domain, offset=0, limit=None, order=None)",
                    "returns": "List[int] - record IDs only",
                    "example": "ids = client.search('res.partner', [['is_company', '=', True]], limit=10)",
                },
                "read": {
                    "signature": "client.read(model, ids, fields=None)",
                    "returns": "List[dict] - record data for given IDs",
                    "example": "records = client.read('res.partner', [1, 2], ['name', 'email'])",
                },
                "search_read": {
                    "signature": "client.search_read(model, domain, fields=None, offset=0, limit=None, order=None)",
                    "returns": "List[dict] - combined search+read (most efficient)",
                    "example": "partners = client.search_read('res.partner', [], ['name', 'email'], limit=10)",
                    "note": "Preferred method for fetching records with data",
                },
                "search_count": {
                    "signature": "client.search_count(model, domain)",
                    "returns": "int - count of matching records",
                    "example": "count = client.search_count('res.partner', [['active', '=', True]])",
                },
                "name_get": {
                    "signature": "client.name_get(model, ids)",
                    "returns": "List[tuple] - [(id, display_name), ...]",
                    "example": "names = client.name_get('res.partner', [1, 2, 3])",
                },
                "name_search": {
                    "signature": "client.name_search(model, name='', domain=None, operator='ilike', limit=100)",
                    "returns": "List[tuple] - [(id, name), ...] matching pattern",
                    "example": "matches = client.name_search('res.partner', 'Azure')",
                },
                "fields_get": {
                    "signature": "client.fields_get(model, allfields=None, attributes=None)",
                    "returns": "dict - field definitions {field_name: {type, string, required, ...}}",
                    "example": "fields = client.fields_get('res.partner')",
                },
                "get_models": {
                    "signature": "client.get_models()",
                    "returns": "List[str] - all available model names",
                    "example": "models = client.get_models()",
                },
            },
            "write_methods": {
                "create": {
                    "signature": "client.create(model, values)",
                    "returns": "int - new record ID",
                    "example": "new_id = client.create('res.partner', {'name': 'Test', 'email': 'test@example.com'})",
                    "note": "Blocked if profile is readonly, use --force to override",
                },
                "write": {
                    "signature": "client.write(model, ids, values)",
                    "returns": "bool - True on success",
                    "example": "client.write('res.partner', [1], {'name': 'Updated Name'})",
                    "note": "Blocked if profile is readonly, use --force to override",
                },
                "unlink": {
                    "signature": "client.unlink(model, ids)",
                    "returns": "bool - True on success",
                    "example": "client.unlink('res.partner', [1])",
                    "note": "Blocked if profile is readonly, use --force to override",
                },
            },
            "generic_execute": {
                "signature": "client.execute(model, method, *args, **kwargs)",
                "description": "Call any Odoo model method",
                "examples": [
                    "client.execute('sale.order', 'action_confirm', [order_id])",
                    "client.execute('account.move', 'action_post', [invoice_id])",
                    "client.execute('stock.picking', 'button_validate', [picking_id])",
                    "client.execute('res.partner', 'create', {'name': 'Test'})",
                ],
            },
        },

        # Common patterns
        "patterns": {
            "count_records": {
                "task": "Count records matching a condition",
                "code": "result = client.search_count('MODEL', DOMAIN)",
                "example": "result = client.search_count('res.partner', [['is_company', '=', True]])",
            },
            "fetch_records": {
                "task": "Fetch records with specific fields",
                "code": "result = client.search_read('MODEL', DOMAIN, FIELDS, limit=LIMIT)",
                "example": "result = client.search_read('res.partner', [], ['name', 'email'], limit=10)",
            },
            "aggregate_sum": {
                "task": "Calculate sum of a field",
                "code": "records = client.search_read('MODEL', DOMAIN, ['amount_field'])\nresult = {'total': sum(r['amount_field'] for r in records), 'count': len(records)}",
                "example": "orders = client.search_read('sale.order', [['state', '=', 'sale']], ['amount_total'])\nresult = {'total': sum(o['amount_total'] for o in orders)}",
            },
            "create_record": {
                "task": "Create a new record",
                "code": "result = client.create('MODEL', VALUES)",
                "example": "result = client.create('res.partner', {'name': 'New Partner', 'email': 'new@example.com'})",
            },
            "update_record": {
                "task": "Update existing records",
                "code": "client.write('MODEL', [IDS], VALUES)\nresult = {'updated': True}",
                "example": "client.write('res.partner', [1], {'name': 'Updated'})\nresult = {'updated': True}",
            },
            "call_action": {
                "task": "Call a workflow action",
                "code": "result = client.execute('MODEL', 'ACTION_METHOD', [IDS])",
                "example": "result = client.execute('sale.order', 'action_confirm', [order_id])",
            },
            "get_schema": {
                "task": "Discover model fields",
                "code": "result = client.fields_get('MODEL')",
                "example": "result = client.fields_get('res.partner')",
            },
        },

        # Domain syntax reference
        "domain_reference": {
            "format": "[['field', 'operator', 'value'], ...]",
            "operators": {
                "=": "Equals",
                "!=": "Not equals",
                "<": "Less than",
                ">": "Greater than",
                "<=": "Less than or equal",
                ">=": "Greater than or equal",
                "like": "Pattern match (case-sensitive)",
                "ilike": "Pattern match (case-insensitive)",
                "in": "Value in list",
                "not in": "Value not in list",
                "child_of": "Hierarchical child of",
            },
            "boolean_operators": {
                "implicit AND": "[['field1', '=', 'a'], ['field2', '=', 'b']]",
                "OR": "['|', ['field1', '=', 'a'], ['field2', '=', 'b']]",
                "NOT": "['!', ['field', '=', 'value']]",
            },
            "examples": [
                "[]  # all records",
                "[['active', '=', True]]",
                "[['name', 'ilike', 'test']]",
                "[['id', 'in', [1, 2, 3]]]",
                "[['create_date', '>=', '2024-01-01']]",
                "['|', ['state', '=', 'draft'], ['state', '=', 'sent']]",
            ],
        },

        # Available commands
        "commands": {
            "exec": "Execute Python code with client (PRIMARY)",
            "config": "Manage connection profiles (alias: profiles)",
            "context": "Show project business context",
            "agent-info": "This command - complete API reference",
        },

        # Error handling
        "error_handling": {
            "exit_codes": {
                "0": "Success",
                "1": "Connection error",
                "2": "Authentication error",
                "3": "Operation error (validation, Odoo error, deprecated command)",
            },
            "common_errors": {
                "env_not_available": {
                    "cause": "Using env['model'] instead of client",
                    "fix": "Replace env[...] with client.search_read(), client.execute(), etc.",
                },
                "readonly_blocked": {
                    "cause": "Write operation on readonly profile",
                    "fix": "Use --force flag: odoo-cli --force exec -c \"...\"",
                },
                "model_not_found": {
                    "cause": "Invalid model name",
                    "fix": "Check with: client.get_models()",
                },
                "field_not_found": {
                    "cause": "Invalid field name",
                    "fix": "Check with: client.fields_get('model')",
                },
                "deprecated_command": {
                    "cause": "Using removed command (search, create, etc.)",
                    "fix": "Use exec instead - error message shows exact migration",
                },
            },
        },

        # Quick start
        "quick_start": [
            "1. Test connection: odoo-cli agent-info",
            "2. List models: odoo-cli exec -c \"result = client.get_models()\" --json",
            "3. Get fields: odoo-cli exec -c \"result = client.fields_get('res.partner')\" --json",
            "4. Search: odoo-cli exec -c \"result = client.search_read('res.partner', [], limit=5)\" --json",
            "5. For complex ops: Write a .py script and run: odoo-cli exec script.py --json",
        ],

        # Important flags
        "important_flags": {
            "--json": "Output structured JSON (set ODOO_CLI_JSON=1 for automatic)",
            "--force": "GLOBAL flag (before exec) - override readonly protection",
            "--profile NAME": "Use specific connection profile",
            "-p NAME": "Short form of --profile",
        },

        # Readonly note
        "readonly_note": (
            f"Profile is {'READONLY - use: odoo-cli --force exec -c \"...\"' if profile_info['readonly'] else 'writable'}"
        ),
    }

    # Always output JSON (this command is for agents)
    click.echo(json_lib.dumps(response, indent=2))
