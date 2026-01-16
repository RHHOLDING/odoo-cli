"""
Deprecation handling for v2.0 exec-only architecture.

Provides helpful migration guidance when agents use deprecated commands.
All deprecated commands return structured JSON that helps LLMs migrate to exec.
"""

import json
import sys
from typing import Dict, Any, Optional

import click


# Commands that are kept in v2.0
KEPT_COMMANDS = {
    "exec": "Primary command for all Odoo operations",
    "profiles": "Environment profile management (add, edit, delete, list, etc.)",
    "config": "Alias for profiles",
    "context": "Project business context for LLM agents",
    "agent-info": "Quick bootstrap and API reference for LLM agents",
}


# Complete deprecation map: old command -> migration info
DEPRECATED_COMMANDS: Dict[str, Dict[str, Any]] = {
    # Query commands
    "search": {
        "category": "query",
        "exec_equivalent": "result = client.search_read('MODEL', DOMAIN, fields=FIELDS, limit=LIMIT)",
        "example": {
            "old": "odoo-cli search res.partner '[]' --limit 10 --json",
            "new": "odoo-cli exec -c \"result = client.search_read('res.partner', [], limit=10)\" --json"
        },
        "hint": "Use client.search_read() for combined search+read, or client.search() for IDs only"
    },
    "read": {
        "category": "query",
        "exec_equivalent": "result = client.read('MODEL', [IDS], fields=FIELDS)",
        "example": {
            "old": "odoo-cli read res.partner 1 --json",
            "new": "odoo-cli exec -c \"result = client.read('res.partner', [1])\" --json"
        },
        "hint": "Use client.read() with a list of IDs"
    },
    "search-count": {
        "category": "query",
        "exec_equivalent": "result = client.search_count('MODEL', DOMAIN)",
        "example": {
            "old": "odoo-cli search-count res.partner '[]' --json",
            "new": "odoo-cli exec -c \"result = client.search_count('res.partner', [])\" --json"
        },
        "hint": "Direct method call on client"
    },
    "name-get": {
        "category": "query",
        "exec_equivalent": "result = client.name_get('MODEL', [IDS])",
        "example": {
            "old": "odoo-cli name-get res.partner 1,2,3 --json",
            "new": "odoo-cli exec -c \"result = client.name_get('res.partner', [1, 2, 3])\" --json"
        },
        "hint": "Returns [(id, display_name), ...]"
    },
    "name-search": {
        "category": "query",
        "exec_equivalent": "result = client.name_search('MODEL', 'PATTERN', limit=LIMIT)",
        "example": {
            "old": "odoo-cli name-search res.partner 'Azure' --json",
            "new": "odoo-cli exec -c \"result = client.name_search('res.partner', 'Azure')\" --json"
        },
        "hint": "Fuzzy search on name field"
    },
    "aggregate": {
        "category": "query",
        "exec_equivalent": "records = client.search_read('MODEL', DOMAIN, ['field']); result = sum(r['field'] for r in records)",
        "example": {
            "old": "odoo-cli aggregate sale.order '[]' --sum amount_total --json",
            "new": "odoo-cli exec -c \"orders = client.search_read('sale.order', [], ['amount_total']); result = sum(o['amount_total'] for o in orders)\" --json"
        },
        "hint": "Compute aggregations in Python code"
    },

    # Schema commands
    "get-models": {
        "category": "schema",
        "exec_equivalent": "result = client.get_models()",
        "example": {
            "old": "odoo-cli get-models --filter partner --json",
            "new": "odoo-cli exec -c \"result = [m for m in client.get_models() if 'partner' in m]\" --json"
        },
        "hint": "client.get_models() returns cached list of model names"
    },
    "models": {
        "category": "schema",
        "alias_of": "get-models",
        "exec_equivalent": "result = client.get_models()",
        "example": {
            "old": "odoo-cli models --json",
            "new": "odoo-cli exec -c \"result = client.get_models()\" --json"
        },
        "hint": "Alias of get-models"
    },
    "get-fields": {
        "category": "schema",
        "exec_equivalent": "result = client.fields_get('MODEL')",
        "example": {
            "old": "odoo-cli get-fields res.partner --json",
            "new": "odoo-cli exec -c \"result = client.fields_get('res.partner')\" --json"
        },
        "hint": "Returns field definitions with type, string, required, etc."
    },
    "fields": {
        "category": "schema",
        "alias_of": "get-fields",
        "exec_equivalent": "result = client.fields_get('MODEL')",
        "example": {
            "old": "odoo-cli fields res.partner --json",
            "new": "odoo-cli exec -c \"result = client.fields_get('res.partner')\" --json"
        },
        "hint": "Alias of get-fields"
    },

    # Write commands
    "create": {
        "category": "write",
        "exec_equivalent": "result = client.create('MODEL', VALUES)",
        "example": {
            "old": "odoo-cli create res.partner name=\"Test\" --json",
            "new": "odoo-cli exec -c \"result = client.create('res.partner', {'name': 'Test'})\" --json"
        },
        "hint": "Returns new record ID. Use --force if profile is readonly."
    },
    "update": {
        "category": "write",
        "exec_equivalent": "result = client.write('MODEL', [IDS], VALUES)",
        "example": {
            "old": "odoo-cli update res.partner 1 name=\"Updated\" --json",
            "new": "odoo-cli exec -c \"result = client.write('res.partner', [1], {'name': 'Updated'})\" --json"
        },
        "hint": "Returns True on success. Use --force if profile is readonly."
    },
    "delete": {
        "category": "write",
        "exec_equivalent": "result = client.unlink('MODEL', [IDS])",
        "example": {
            "old": "odoo-cli delete res.partner 1 --json",
            "new": "odoo-cli exec -c \"result = client.unlink('res.partner', [1])\" --json"
        },
        "hint": "Returns True on success. Use --force if profile is readonly."
    },
    "create-bulk": {
        "category": "write",
        "exec_equivalent": "result = [client.create('MODEL', vals) for vals in data]",
        "example": {
            "old": "odoo-cli create-bulk res.partner data.json --json",
            "new": "odoo-cli exec -c \"import json; data = json.load(open('data.json')); result = [client.create('res.partner', v) for v in data]\" --json"
        },
        "hint": "Loop over values list in Python"
    },
    "update-bulk": {
        "category": "write",
        "exec_equivalent": "for item in data: client.write('MODEL', [item['id']], item['values'])",
        "example": {
            "old": "odoo-cli update-bulk res.partner updates.json --json",
            "new": "odoo-cli exec script_bulk_update.py --json"
        },
        "hint": "Write a script for complex bulk operations"
    },

    # Execute command
    "execute": {
        "category": "advanced",
        "exec_equivalent": "result = client.execute('MODEL', 'METHOD', *ARGS)",
        "example": {
            "old": "odoo-cli execute sale.order action_confirm '[1]' --json",
            "new": "odoo-cli exec -c \"result = client.execute('sale.order', 'action_confirm', [1])\" --json"
        },
        "hint": "client.execute() is the universal method caller"
    },

    # Domain-specific commands
    "search-employee": {
        "category": "domain",
        "exec_equivalent": "result = client.search_read('hr.employee', [['name', 'ilike', 'PATTERN']], ['name', 'work_email'])",
        "example": {
            "old": "odoo-cli search-employee 'John' --json",
            "new": "odoo-cli exec -c \"result = client.search_read('hr.employee', [['name', 'ilike', 'John']], ['name', 'work_email', 'department_id'])\" --json"
        },
        "hint": "Standard search_read on hr.employee model"
    },
    "search-holidays": {
        "category": "domain",
        "exec_equivalent": "result = client.search_read('hr.leave', DOMAIN, ['employee_id', 'date_from', 'date_to', 'state'])",
        "example": {
            "old": "odoo-cli search-holidays --json",
            "new": "odoo-cli exec -c \"result = client.search_read('hr.leave', [], ['employee_id', 'date_from', 'date_to', 'state'])\" --json"
        },
        "hint": "Standard search_read on hr.leave model"
    },

    # Shell command
    "shell": {
        "category": "interactive",
        "exec_equivalent": "Use exec with a script file for complex operations",
        "example": {
            "old": "odoo-cli shell",
            "new": "odoo-cli exec script.py --json"
        },
        "hint": "Interactive shell removed in v2.0. Use exec with script files instead."
    },
}


def get_deprecation_response(command: str) -> dict:
    """
    Generate a helpful deprecation response for a deprecated command.

    Returns structured JSON that helps LLMs migrate to exec.
    """
    if command not in DEPRECATED_COMMANDS:
        return {
            "success": False,
            "error": f"Unknown command: {command}",
            "error_type": "unknown_command",
            "suggestion": "Run 'odoo-cli agent-info' for available commands",
            "available_commands": list(KEPT_COMMANDS.keys()),
        }

    info = DEPRECATED_COMMANDS[command]

    return {
        "success": False,
        "error": f"Command '{command}' is deprecated in v2.0",
        "error_type": "deprecated_command",
        "migration": {
            "old_command": info["example"]["old"],
            "new_command": info["example"]["new"],
            "exec_pattern": info["exec_equivalent"],
            "hint": info["hint"],
        },
        "category": info["category"],
        "suggestion": "Run 'odoo-cli agent-info' for complete client API reference",
    }


def create_deprecation_handler(cmd_name: str):
    """
    Create a Click command that returns deprecation info instead of executing.

    This allows old commands to provide helpful migration guidance.
    """
    @click.command(
        cmd_name,
        context_settings={
            "allow_extra_args": True,
            "allow_interspersed_args": False,
            "ignore_unknown_options": True,
        }
    )
    @click.pass_context
    def deprecated_handler(ctx):
        # Determine JSON mode from parent context or --json in args
        json_mode = False
        if ctx.obj and hasattr(ctx.obj, 'json_mode'):
            json_mode = ctx.obj.json_mode
        if '--json' in sys.argv:
            json_mode = True

        response = get_deprecation_response(cmd_name)

        if json_mode:
            click.echo(json.dumps(response, indent=2))
        else:
            # Rich console output for humans
            click.echo(f"\nCommand '{cmd_name}' is deprecated in v2.0", err=True)
            click.echo("\nMigration:", err=True)
            click.echo(f"  Old: {response['migration']['old_command']}", err=True)
            click.echo(f"  New: {response['migration']['new_command']}", err=True)
            click.echo(f"\nHint: {response['migration']['hint']}", err=True)
            click.echo("\nRun 'odoo-cli agent-info' for the complete API reference.", err=True)

        sys.exit(3)  # Operation error exit code

    # Copy the original command's help text for discoverability
    deprecated_handler.__doc__ = f"[DEPRECATED] Use 'exec' instead. Run for migration guide."

    return deprecated_handler
