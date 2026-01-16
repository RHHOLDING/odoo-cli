"""
LLM-optimized help for odoo-cli v2.0 (exec-only architecture).

Provides structured JSON to help AI agents understand how to use the tool.
"""

import json
from datetime import datetime
from typing import Dict, Any


def get_llm_help() -> Dict[str, Any]:
    """Generate LLM-optimized help as JSON."""
    return {
        "cli_version": "2.0.0",
        "architecture": "exec-only",
        "protocol": "JSON-RPC",
        "timestamp": datetime.now().isoformat(),

        # Primary usage - exec is the only way to interact with Odoo
        "primary": {
            "command": "exec",
            "description": "Execute Python code with pre-authenticated Odoo client",
            "usage": [
                'odoo-cli exec -c "result = client.search_count(\'res.partner\', [])" --json',
                'odoo-cli exec -c "result = client.search_read(\'res.partner\', [], limit=5)" --json',
                "odoo-cli exec script.py --json",
                'odoo-cli --profile staging exec -c "..." --json'
            ],
            "namespace": {
                "client": "Authenticated OdooClient - use for ALL Odoo operations",
                "json": "JSON module (json.dumps, json.loads)",
                "datetime": "datetime module",
                "date": "date class",
                "timedelta": "timedelta class",
                "pprint": "Pretty printer",
                "result": "Set this for structured JSON output"
            },
            "critical": "Use 'client' NOT 'env'. This is JSON-RPC, not server-side Python.",
            "output": "Human-readable summary first, then JSON"
        },

        # Client API reference
        "client_api": {
            "query": {
                "search": "client.search(model, domain, offset=0, limit=None, order=None) -> List[int]",
                "read": "client.read(model, ids, fields=None) -> List[dict]",
                "search_read": "client.search_read(model, domain, fields=None, offset=0, limit=None, order=None) -> List[dict]",
                "search_count": "client.search_count(model, domain) -> int",
                "name_get": "client.name_get(model, ids) -> List[tuple]",
                "name_search": "client.name_search(model, name='', domain=None, operator='ilike', limit=100) -> List[tuple]",
                "fields_get": "client.fields_get(model, allfields=None, attributes=None) -> dict",
                "get_models": "client.get_models() -> List[str]"
            },
            "write": {
                "create": "client.create(model, values) -> int (new ID)",
                "write": "client.write(model, ids, values) -> bool",
                "unlink": "client.unlink(model, ids) -> bool"
            },
            "generic": "client.execute(model, method, *args, **kwargs) -> Any"
        },

        # Common patterns
        "patterns": {
            "count_records": {
                "code": "result = client.search_count('MODEL', DOMAIN)",
                "example": "result = client.search_count('res.partner', [['is_company', '=', True]])"
            },
            "fetch_records": {
                "code": "result = client.search_read('MODEL', DOMAIN, FIELDS, limit=LIMIT)",
                "example": "result = client.search_read('res.partner', [], ['name', 'email'], limit=10)"
            },
            "get_by_id": {
                "code": "result = client.read('MODEL', [IDS], FIELDS)",
                "example": "result = client.read('res.partner', [1, 2], ['name', 'email'])"
            },
            "create_record": {
                "code": "result = client.create('MODEL', VALUES)",
                "example": "result = client.create('res.partner', {'name': 'Test', 'email': 'test@example.com'})"
            },
            "update_record": {
                "code": "client.write('MODEL', [IDS], VALUES); result = {'updated': True}",
                "example": "client.write('res.partner', [1], {'name': 'Updated'}); result = {'updated': True}"
            },
            "delete_record": {
                "code": "client.unlink('MODEL', [IDS]); result = {'deleted': True}",
                "example": "client.unlink('res.partner', [1]); result = {'deleted': True}"
            },
            "call_action": {
                "code": "result = client.execute('MODEL', 'ACTION_METHOD', [IDS])",
                "example": "result = client.execute('sale.order', 'action_confirm', [order_id])"
            },
            "aggregate_sum": {
                "code": "records = client.search_read('MODEL', DOMAIN, ['amount_field']); result = sum(r['amount_field'] for r in records)",
                "example": "orders = client.search_read('sale.order', [['state', '=', 'sale']], ['amount_total']); result = sum(o['amount_total'] for o in orders)"
            },
            "get_schema": {
                "code": "result = client.fields_get('MODEL')",
                "example": "result = client.fields_get('res.partner')"
            },
            "list_models": {
                "code": "result = client.get_models()",
                "example": "result = [m for m in client.get_models() if 'partner' in m]"
            }
        },

        # Profile management
        "profiles": {
            "description": "Manage connection profiles",
            "commands": {
                "list": "odoo-cli config list --json",
                "show": "odoo-cli config show NAME --json",
                "add": "odoo-cli config add NAME --url URL --db DB -u USER -p PASS",
                "edit": "odoo-cli config edit NAME --url NEW_URL",
                "delete": "odoo-cli config delete NAME -y",
                "rename": "odoo-cli config rename OLD_NAME NEW_NAME",
                "test": "odoo-cli config test NAME --json",
                "current": "odoo-cli config current --json",
                "set-default": "odoo-cli config set-default NAME",
                "use": 'odoo-cli --profile NAME exec -c "..." --json'
            },
            "automation": {
                "delete_without_prompt": "Use -y/--yes to skip confirmation"
            },
            "protection": {
                "readonly": "Blocks create/write/unlink - use --force to override",
                "protected": "Blocks CLI modifications to profile config"
            }
        },

        # Available commands (v2.0)
        "commands": {
            "exec": "Execute Python code with client (PRIMARY)",
            "config": "Manage connection profiles (alias: profiles)",
            "context": "Show project business context",
            "agent-info": "Complete API reference and bootstrap"
        },

        # Domain syntax
        "domain_syntax": {
            "format": "[['field', 'operator', 'value'], ...]",
            "operators": ["=", "!=", "<", ">", "<=", ">=", "like", "ilike", "in", "not in", "child_of"],
            "boolean": {
                "AND": "[['a', '=', 1], ['b', '=', 2]]  # implicit",
                "OR": "['|', ['a', '=', 1], ['b', '=', 2]]",
                "NOT": "['!', ['a', '=', 1]]"
            },
            "examples": [
                "[]  # all records",
                "[['active', '=', True]]",
                "[['name', 'ilike', 'test']]",
                "[['id', 'in', [1, 2, 3]]]",
                "[['create_date', '>=', '2024-01-01']]"
            ]
        },

        # Error handling
        "errors": {
            "env_not_available": {
                "message": "'env' is not available",
                "cause": "Using Odoo server-side Python syntax",
                "fix": "Use 'client' instead of 'env'",
                "conversions": {
                    "env['model'].search()": "client.search('model', domain)",
                    "env['model'].browse(ids)": "client.read('model', ids, fields)",
                    "env.ref('xml_id')": "client.execute('ir.model.data', 'xmlid_to_res_id', 'module.xml_id')"
                }
            },
            "readonly_blocked": {
                "message": "Write operation blocked",
                "cause": "Profile is readonly",
                "fix": 'Use --force: odoo-cli --force exec -c "..."'
            },
            "deprecated_command": {
                "message": "Command 'X' is deprecated",
                "cause": "Using removed command (search, create, etc.)",
                "fix": "Use exec instead - error shows exact migration"
            },
            "model_not_found": {
                "message": "Model does not exist",
                "fix": "Check with: client.get_models()"
            },
            "field_not_found": {
                "message": "Invalid field",
                "fix": "Check with: client.fields_get('model')"
            }
        },

        # Quick reference
        "quick_ref": {
            "json_output": "Always use --json for structured output",
            "env_variable": "Set ODOO_CLI_JSON=1 for automatic JSON",
            "profile_flag": "--profile NAME (or -p NAME) before command",
            "force_write": "odoo-cli --force exec -c '...' (GLOBAL flag before command)",
            "agent_bootstrap": "Run 'odoo-cli agent-info' for complete API reference"
        }
    }


def format_llm_help(output_format: str = "json") -> str:
    """Format LLM help for output."""
    help_data = get_llm_help()
    return json.dumps(help_data, indent=2)


def print_llm_help(output_format: str = "json"):
    """Print LLM help to stdout."""
    print(format_llm_help(output_format))
