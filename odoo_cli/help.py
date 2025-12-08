"""
LLM-optimized help for odoo-cli.

Provides structured JSON to help AI agents understand how to use the tool.
"""

import json
from datetime import datetime
from typing import Dict, Any


def get_llm_help() -> Dict[str, Any]:
    """Generate LLM-optimized help as JSON."""
    return {
        "cli_version": "1.7.3",
        "protocol": "JSON-RPC",
        "timestamp": datetime.now().isoformat(),

        # Primary usage
        "primary": {
            "command": "exec",
            "description": "Execute Python code with pre-authenticated Odoo client",
            "usage": [
                "odoo-cli exec -c \"result = client.search_count('res.partner', [])\" --json",
                "odoo-cli exec script.py --json",
                "odoo-cli --profile staging exec -c \"...\" --json"
            ],
            "namespace": {
                "client": "Authenticated OdooClient",
                "json": "JSON module",
                "datetime": "datetime, date, timedelta",
                "pprint": "Pretty printer",
                "result": "Set this for structured JSON output"
            },
            "output": "✓ human-readable summary first, then JSON"
        },

        # Profiles
        "profiles": {
            "description": "Switch between environments",
            "commands": {
                "list": "odoo-cli profiles list",
                "show": "odoo-cli profiles show NAME",
                "add": "odoo-cli profiles add NAME --url URL --db DB --username USER --password PASS",
                "use": "odoo-cli --profile NAME exec -c \"...\""
            },
            "protection": {
                "readonly": "Blocks create/write/unlink operations",
                "protected": "Blocks CLI modifications to profile"
            }
        },

        # Common patterns
        "patterns": {
            "count_records": {
                "code": "result = client.search_count('MODEL', DOMAIN)",
                "example": "result = client.search_count('res.partner', [])"
            },
            "search_read": {
                "code": "result = client.execute('MODEL', 'search_read', DOMAIN, FIELDS, OFFSET, LIMIT)",
                "example": "result = client.execute('res.partner', 'search_read', [['is_company', '=', True]], ['name', 'email'], 0, 10)"
            },
            "read_record": {
                "code": "result = client.execute('MODEL', 'read', [IDS], FIELDS)",
                "example": "result = client.execute('res.partner', 'read', [12], ['name', 'email'])"
            },
            "create": {
                "code": "result = client.execute('MODEL', 'create', VALUES)",
                "example": "result = client.execute('res.partner', 'create', {'name': 'Test', 'email': 'test@test.com'})"
            },
            "write": {
                "code": "client.execute('MODEL', 'write', [IDS], VALUES)",
                "example": "client.execute('res.partner', 'write', [12], {'name': 'Updated'})"
            },
            "unlink": {
                "code": "client.execute('MODEL', 'unlink', [IDS])",
                "example": "client.execute('res.partner', 'unlink', [12])"
            },
            "call_method": {
                "code": "result = client.execute('MODEL', 'METHOD', [IDS])",
                "example": "result = client.execute('sale.order', 'action_confirm', [order_id])"
            },
            "aggregate": {
                "code": """
records = client.execute('MODEL', 'search_read', DOMAIN, ['amount_field'])
result = {'count': len(records), 'total': sum(r['amount_field'] for r in records)}
""",
                "example": """
orders = client.execute('sale.order', 'search_read', [['state', '=', 'sale']], ['amount_total'])
result = {'count': len(orders), 'total': sum(o['amount_total'] for o in orders)}
"""
            }
        },

        # Schema discovery
        "discovery": {
            "list_models": "odoo-cli get-models --filter PATTERN --json",
            "list_fields": "odoo-cli get-fields MODEL --json",
            "models_alias": "odoo-cli models --filter PATTERN --json",
            "fields_alias": "odoo-cli fields MODEL --json"
        },

        # Helper commands (fallback)
        "helper_commands": [
            {"name": "search", "usage": "odoo-cli search MODEL DOMAIN --limit N --json"},
            {"name": "read", "usage": "odoo-cli read MODEL IDS --json"},
            {"name": "create", "usage": "odoo-cli create MODEL -f field=value --json"},
            {"name": "update", "usage": "odoo-cli update MODEL IDS -f field=value --json"},
            {"name": "delete", "usage": "odoo-cli delete MODEL IDS --force --json"},
            {"name": "search-count", "usage": "odoo-cli search-count MODEL DOMAIN --json"},
            {"name": "aggregate", "usage": "odoo-cli aggregate MODEL DOMAIN --sum FIELD --json"}
        ],

        # Error handling
        "errors": {
            "readonly_blocked": {
                "message": "Write operation blocked: profile is readonly",
                "solution": "Use global --force flag: odoo-cli --force <command>, or use non-readonly profile"
            },
            "invalid_domain": {
                "message": "unhashable type: 'list'",
                "solution": "Check domain format: [['field', 'op', 'value']]"
            },
            "model_not_found": {
                "message": "Model does not exist",
                "solution": "Run: odoo-cli get-models --filter PATTERN"
            },
            "field_not_found": {
                "message": "Invalid field",
                "solution": "Run: odoo-cli get-fields MODEL"
            },
            "connection_failed": {
                "message": "Connection refused",
                "solution": "Check profile URL and credentials"
            }
        },

        # Quick reference
        "quick_ref": {
            "domain_operators": ["=", "!=", "<", ">", "<=", ">=", "ilike", "in", "not in"],
            "domain_format": "[['field', 'operator', 'value']]",
            "json_output": "Always use --json for structured output",
            "profile_flag": "--profile NAME before command",
            "force_write": "Use 'odoo-cli --force <command>' to override readonly (GLOBAL flag)",
            "force_example": "odoo-cli --force update res.partner 1 -f name=\"Test\" --json",
            "agent_bootstrap": "Run 'odoo-cli agent-info' for quick tool orientation"
        },

        # Documentation
        "docs": {
            "readme": "README.md",
            "agents": "AGENTS.md",
            "changelog": "CHANGELOG.md"
        }
    }


def format_llm_help(output_format: str = "json") -> str:
    """Format LLM help for output."""
    help_data = get_llm_help()
    return json.dumps(help_data, indent=2)


def print_llm_help(output_format: str = "json"):
    """Print LLM help to stdout."""
    print(format_llm_help(output_format))
