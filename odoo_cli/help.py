"""
LLM-optimized help generation for Odoo CLI.

Provides structured JSON output to help AI assistants (LLMs) understand:
- When to use CLI vs Python scripts
- How to handle different data sizes
- Error patterns and solutions
- Command capabilities
"""

import json
from datetime import datetime
from typing import Dict, Any


def get_llm_help() -> Dict[str, Any]:
    """
    Generate comprehensive LLM-optimized help as JSON.

    Returns:
        Dictionary with recommendations, commands, error patterns, and limits
    """
    return {
        "cli_version": "1.4.0",
        "protocol": "JSON-RPC",
        "mode": "llm_help",
        "timestamp": datetime.now().isoformat(),

        # Decision Tree for LLMs
        "decision_tree": {
            "create_records": {
                "trigger": "Need to create new Odoo records",
                "recommendation": "USE_CREATE_COMMAND",
                "command": "odoo create MODEL --fields key=value",
                "examples": [
                    "odoo create res.partner -f name=\"John Doe\" -f email=\"john@test.com\"",
                    "odoo create sale.order -f partner_id=123 -f date_order=\"2025-11-21\""
                ],
                "advantages": [
                    "No JSON syntax required",
                    "Automatic type inference (int, float, bool, string)",
                    "Field validation with helpful error messages",
                    "Returns created record ID for immediate use"
                ],
                "use_python_when": "Creating 100+ records (batch operations)",
                "validation": "Use --no-validate to skip field checks for speed"
            },
            "aggregation": {
                "trigger": "Need to aggregate (SUM/AVG/COUNT) records",
                "recommendation": "USE_CLI: odoo aggregate",
                "command": "odoo aggregate MODEL DOMAIN [--sum FIELD] [--avg FIELD] [--count] [--group-by FIELD]",
                "reason": [
                    "Built-in batching handles large datasets efficiently",
                    "LLM-friendly JSON output",
                    "Automatic progress tracking",
                    "Structured error handling",
                    "Works for 95% of aggregation needs"
                ],
                "examples": [
                    "odoo aggregate sale.order '[]' --sum amount_total",
                    "odoo aggregate sale.order '[[\"date_order\",\">=\",\"2025-10-01\"]]' --sum amount_total",
                    "odoo aggregate sale.order '[]' --count --group-by state"
                ],
                "fallback": "Only generate Python if GROUP BY multiple fields or custom logic needed"
            },
            "fast_counting": {
                "trigger": "Need to count records without fetching data",
                "recommendation": "USE_SEARCH_COUNT",
                "command": "odoo search-count MODEL DOMAIN",
                "reason": [
                    "~90% faster than search + count for large datasets",
                    "No data transfer, only count",
                    "Server-side counting",
                    "Supports context (e.g., active_test=false)"
                ],
                "examples": [
                    "odoo search-count res.partner '[]'",
                    "odoo search-count sale.order '[[\"state\",\"=\",\"sale\"]]'",
                    "odoo search-count product.product '[]' --context active_test=false"
                ],
                "use_case": "Dataset size checks, validation, statistics",
                "llm_note": "NEW in v1.4.0 - Preferred over search when only count is needed"
            },
            "id_to_name_lookup": {
                "trigger": "Need display names for record IDs",
                "recommendation": "USE_NAME_GET",
                "command": "odoo name-get MODEL IDS",
                "reason": [
                    "2x faster than read() for names only",
                    "Single API call",
                    "Returns (id, name) tuples",
                    "Context-aware (translations)"
                ],
                "examples": [
                    "odoo name-get res.partner 1,2,3",
                    "odoo name-get product.product 100,101,102 --json",
                    "odoo name-get res.partner 1,2,3 --context lang=de_DE"
                ],
                "use_case": "Validation, dropdowns, display formatting",
                "llm_note": "NEW in v1.4.0 - More efficient than read() when only names needed"
            },
            "autocomplete_search": {
                "trigger": "Need fuzzy name search for autocomplete/selection",
                "recommendation": "USE_NAME_SEARCH",
                "command": "odoo name-search MODEL NAME [--domain FILTER] [--limit N]",
                "reason": [
                    "Single API call (vs search + read)",
                    "Fuzzy matching (ilike operator)",
                    "Returns (id, name) tuples",
                    "Perfect for selection lists"
                ],
                "examples": [
                    "odoo name-search res.partner \"John\"",
                    "odoo name-search product.product \"Desk\" --limit 10",
                    "odoo name-search res.partner \"Azure\" --domain '[[\"customer_rank\",\">\",0]]'"
                ],
                "use_case": "Autocomplete, search-as-you-type, record selection",
                "llm_note": "NEW in v1.4.0 - Replaces search + read pattern for name lookups"
            },
            "context_operations": {
                "trigger": "Need multi-company, translations, or archived records",
                "recommendation": "USE_CONTEXT_FLAGS",
                "command": "odoo COMMAND --context key=value",
                "reason": [
                    "Controls Odoo behavior",
                    "Multi-company filtering",
                    "Language/timezone",
                    "Archived record access"
                ],
                "examples": [
                    "odoo search product.product '[]' --context active_test=false",
                    "odoo read res.partner 1 --context lang=de_DE",
                    "odoo search sale.order '[]' --context allowed_company_ids=[1,2,3]"
                ],
                "common_keys": {
                    "active_test": "Include archived records (false)",
                    "lang": "User language (de_DE, fr_FR, etc.)",
                    "tz": "Timezone (Europe/Berlin)",
                    "allowed_company_ids": "Multi-company filter ([1,2,3])"
                },
                "llm_note": "NEW in v1.3.0 - ALL commands support --context flags"
            },
            "simple_query": {
                "trigger": "record_count < 100 OR simple_filter",
                "recommendation": "USE_CLI_COMMAND",
                "example": "odoo search res.partner '[[\"is_company\", \"=\", true]]' --limit 10",
                "performance": "Immediate, no batching needed"
            },
            "complex_business_logic": {
                "trigger": "Multiple queries OR conditional logic OR data transformation",
                "recommendation": "GENERATE_PYTHON_SCRIPT",
                "reason": "Python allows complex logic that CLI cannot express",
                "template": "docs/examples/aggregation_script.py"
            },
            "error_investigation": {
                "trigger": "Error encountered",
                "recommendation": "CHECK_ERROR_TYPE",
                "process": [
                    "1. Look at 'error_type' field in JSON response",
                    "2. Find matching pattern in error_patterns below",
                    "3. Apply suggested fix",
                    "4. Retry operation"
                ]
            }
        },

        # Commands and capabilities
        "commands": [
            {
                "name": "create",
                "description": "Create new records with simple field=value syntax",
                "llm_note": "NEW in v1.1.0 - No JSON required! Use simple field=value syntax",
                "usage": "odoo create MODEL_NAME --fields key=value [--fields key=value ...] [--json] [--no-validate]",
                "examples": [
                    "odoo create res.partner -f name=\"Test\" -f email=\"test@test.com\"",
                    "odoo create sale.order -f partner_id=123 -f date_order=\"2025-11-21\"",
                    "odoo create res.partner -f name=\"Quick\" --no-validate"
                ],
                "field_syntax": {
                    "strings": "name=\"Test\" or name=Test (quotes optional)",
                    "integers": "partner_id=123",
                    "floats": "price=19.99",
                    "booleans": "active=true or active=false",
                    "lists": "category_ids=[1,2,3]",
                    "null": "parent_id=null or parent_id=false"
                },
                "validation": "Enabled by default (checks field existence and types)",
                "flags": {
                    "--no-validate": "Skip validation for speed",
                    "--json": "Output JSON instead of rich console"
                },
                "batch_safe": False,
                "aggregation_capable": False,
                "use_python_when": "Creating 100+ records (use future create-bulk command)",
                "advantages": [
                    "No JSON syntax required",
                    "Automatic type inference",
                    "Field validation with helpful errors",
                    "Returns created record ID"
                ]
            },
            {
                "name": "search",
                "description": "Find records matching a domain filter",
                "llm_note": "Domain format is critical: [['field', 'operator', 'value']]",
                "usage": "odoo search MODEL_NAME 'DOMAIN' [--limit N] [--offset M] [--fields F1,F2]",
                "domain_format": {
                    "example": "[['date_order', '>=', '2025-10-01'], ['state', '=', 'sale']]",
                    "operators": ["=", "!=", "<", ">", "<=", ">=", "ilike", "in", "not in"],
                    "common_mistake": "Forgetting outer [] brackets or using string instead of list"
                },
                "batch_safe": True,
                "aggregation_capable": False,
                "use_python_when": "aggregating results (sum, average, etc.)"
            },
            {
                "name": "read",
                "description": "Get full record data by IDs",
                "usage": "odoo read MODEL_NAME 'ID1,ID2,ID3' [--fields F1,F2]",
                "batch_safe": True,
                "max_per_call": 2000,
                "recommended_batch": 1000,
                "aggregation_capable": False
            },
            {
                "name": "execute",
                "description": "Call any method on a model",
                "usage": "odoo execute MODEL_NAME METHOD_NAME --args 'JSON_ARRAY' [--kwargs 'JSON_OBJECT']",
                "examples": [
                    "search_count - Count records",
                    "read_group - Group by field (returns per-group, not sum)",
                    "create - Create new record",
                    "write - Update records"
                ],
                "batch_safe": True,
                "aggregation_capable": False,
                "llm_note": "read_group returns per-record grouping, not aggregated sums. Use 'odoo aggregate' command instead."
            },
            {
                "name": "aggregate",
                "description": "Aggregate records (sum, average, count with optional grouping)",
                "llm_note": "NEW in v1.1.0 - Preferred way to aggregate data",
                "usage": "odoo aggregate MODEL DOMAIN [--sum FIELD] [--avg FIELD] [--count] [--group-by FIELD] [--batch-size N] [--json]",
                "examples": [
                    "odoo aggregate sale.order '[]' --sum amount_total",
                    "odoo aggregate sale.order '[]' --count --group-by state",
                    "odoo aggregate sale.order '[[\"date_order\",\">=\",\"2025-10-01\"]]' --sum amount_total"
                ],
                "features": [
                    "SUM: Calculate total for fields",
                    "AVG: Calculate average for fields",
                    "COUNT: Count records",
                    "GROUP BY: Group results by single field",
                    "Automatic batching for large datasets",
                    "Progress bar and JSON output"
                ],
                "aggregation_capable": True,
                "batch_safe": True,
                "use_python_when": "GROUP BY multiple fields or custom aggregation logic"
            },
            {
                "name": "get-models",
                "description": "List all available models",
                "usage": "odoo get-models [--filter PATTERN]",
                "caching": "24 hours (automatic)",
                "use_case": "Discover available models and data sources"
            },
            {
                "name": "get-fields",
                "description": "Get field definitions for a model",
                "usage": "odoo get-fields MODEL_NAME [--field FIELD_NAME]",
                "use_case": "Discover field names and types before querying"
            },
            {
                "name": "shell",
                "description": "Interactive Python shell with pre-loaded client",
                "usage": "odoo shell",
                "available_vars": ["client", "json", "pprint", "datetime"],
                "use_case": "Complex multi-step operations or debugging"
            },
            {
                "name": "update",
                "description": "Update existing records with simple field=value syntax",
                "llm_note": "NEW in v1.2.0 - Update single or multiple records",
                "usage": "odoo update MODEL IDS --fields key=value [--fields key=value ...]",
                "examples": [
                    "odoo update res.partner 123 -f name=\"Updated Name\"",
                    "odoo update sale.order 456 -f state=\"done\" -f date_order=\"2025-11-21\"",
                    "odoo update res.partner 1,2,3 -f active=false"
                ],
                "field_syntax": "Same as create command",
                "batch_safe": True,
                "use_python_when": "Updating 100+ records (use update-bulk command)"
            },
            {
                "name": "delete",
                "description": "Delete records by ID with safety confirmation",
                "llm_note": "NEW in v1.2.0 - Safe deletion with --force to skip confirmation",
                "usage": "odoo delete MODEL IDS [--force]",
                "examples": [
                    "odoo delete res.partner 123",
                    "odoo delete res.partner 1,2,3 --force",
                    "odoo delete sale.order 456 --json"
                ],
                "safety": "Prompts for confirmation unless --force is used",
                "batch_safe": True,
                "use_python_when": "Complex deletion logic or conditional deletes"
            },
            {
                "name": "create-bulk",
                "description": "Create multiple records from JSON file with progress tracking",
                "llm_note": "NEW in v1.2.0 - Batch creation with automatic batching",
                "usage": "odoo create-bulk MODEL --file PATH [--batch-size N]",
                "examples": [
                    "odoo create-bulk res.partner --file partners.json",
                    "odoo create-bulk product.product --file products.json --batch-size 500"
                ],
                "input_format": "JSON array of record objects",
                "features": ["Progress bar", "Automatic batching", "Error handling"],
                "batch_safe": True,
                "recommended_batch": 1000
            },
            {
                "name": "update-bulk",
                "description": "Update multiple records from JSON file with field grouping",
                "llm_note": "NEW in v1.2.0 - Optimized bulk updates with field grouping",
                "usage": "odoo update-bulk MODEL --file PATH [--batch-size N]",
                "examples": [
                    "odoo update-bulk res.partner --file updates.json",
                    "odoo update-bulk sale.order --file orders.json --batch-size 500"
                ],
                "input_format": "JSON array of {id, fields} objects",
                "optimization": "Groups records by field updates to reduce API calls",
                "batch_safe": True,
                "recommended_batch": 1000
            },
            {
                "name": "search-count",
                "description": "Count records matching domain without data transfer",
                "llm_note": "NEW in v1.4.0 - ~90% faster than search for counting",
                "usage": "odoo search-count MODEL DOMAIN [--context key=value]",
                "examples": [
                    "odoo search-count res.partner '[]'",
                    "odoo search-count sale.order '[[\"state\",\"=\",\"sale\"]]'",
                    "odoo search-count product.product '[]' --context active_test=false"
                ],
                "performance": "Server-side counting, no ID transfer",
                "use_case": "Dataset size checks, validation, statistics",
                "batch_safe": True,
                "aggregation_capable": False
            },
            {
                "name": "name-get",
                "description": "Get display names for record IDs (efficient)",
                "llm_note": "NEW in v1.4.0 - 2x faster than read() for names",
                "usage": "odoo name-get MODEL IDS [--context key=value]",
                "examples": [
                    "odoo name-get res.partner 1,2,3",
                    "odoo name-get product.product 100,101,102 --json",
                    "odoo name-get res.partner 1,2,3 --context lang=de_DE"
                ],
                "returns": "List of (id, name) tuples",
                "use_case": "ID validation, dropdown generation, display formatting",
                "batch_safe": True,
                "aggregation_capable": False
            },
            {
                "name": "name-search",
                "description": "Fuzzy name search for autocomplete/selection lists",
                "llm_note": "NEW in v1.4.0 - Single call for name-based search",
                "usage": "odoo name-search MODEL [NAME] [--domain FILTER] [--operator OP] [--limit N]",
                "examples": [
                    "odoo name-search res.partner \"John\"",
                    "odoo name-search product.product \"Desk\" --limit 10",
                    "odoo name-search res.partner \"Azure\" --domain '[[\"customer_rank\",\">\",0]]'",
                    "odoo name-search res.country \"Germany\" --operator like"
                ],
                "returns": "List of (id, name) tuples matching search",
                "use_case": "Autocomplete, search-as-you-type, record selection",
                "operators": ["ilike (default)", "like", "="],
                "batch_safe": True,
                "aggregation_capable": False
            },
            {
                "name": "search-employee",
                "description": "Search employees by name (convenience wrapper)",
                "usage": "odoo search-employee NAME [--limit N]",
                "examples": [
                    "odoo search-employee \"John\"",
                    "odoo search-employee \"Smith\" --limit 5 --json"
                ],
                "use_case": "Quick employee lookup",
                "batch_safe": True
            },
            {
                "name": "search-holidays",
                "description": "Search time-off/holiday records (convenience wrapper)",
                "usage": "odoo search-holidays [--state STATE] [--employee-id ID]",
                "examples": [
                    "odoo search-holidays",
                    "odoo search-holidays --state validate",
                    "odoo search-holidays --employee-id 42 --json"
                ],
                "use_case": "Time-off management and reporting",
                "batch_safe": True
            }
        ],

        # Limits and constraints
        "limits": {
            "max_records_per_read": 2000,
            "recommended_batch_size": 1000,
            "timeout_default_seconds": 30,
            "large_dataset_threshold": 1000,
            "connection_pool_size": 1,
            "cache_ttl_seconds": 86400,
            "retry_attempts": 3,
            "retry_delay_seconds": 2
        },

        # Aggregation guidance
        "aggregation": {
            "cli_command": {
                "method": "odoo aggregate MODEL DOMAIN [--sum FIELD] [--avg FIELD] [--count] [--group-by FIELD]",
                "capability": "SUM, AVG, COUNT with optional GROUP BY",
                "performance": "Efficient batching, O(n/1000) API calls",
                "reliability": "100% reliable, LLM-friendly JSON output",
                "recommendation": "USE_CLI for most aggregation needs",
                "examples": [
                    "odoo aggregate sale.order '[]' --sum amount_total",
                    "odoo aggregate sale.order '[]' --count --group-by state",
                    "odoo aggregate sale.order '[]' --avg amount_total --group-by partner_id"
                ]
            },
            "python_fallback": {
                "trigger": "GROUP BY multiple fields OR custom aggregation logic",
                "method": "search + read in batches + custom Python logic",
                "recommendation": "GENERATE_PYTHON_SCRIPT only if CLI doesn't cover it",
                "note": "Rarely needed - aggregate command handles 95% of use cases"
            }
        },

        # Error handling
        "error_patterns": [
            {
                "pattern": "unhashable type: 'list'",
                "category": "domain",
                "root_cause": "Domain double-wrapped (extra [] brackets)",
                "solution": "Remove extra wrapping - should be [['field', 'op', 'value']]",
                "confidence": 0.99,
                "example_wrong": "[[[['date', '>=', '2025-01-01']]]]",
                "example_right": "[['date', '>=', '2025-01-01']]"
            },
            {
                "pattern": "tuple index out of range",
                "category": "domain",
                "root_cause": "Domain condition incomplete (missing operator or value)",
                "solution": "Each condition needs 3 parts: [field, operator, value]",
                "confidence": 0.95,
                "example_wrong": "[['field']] or [['field', '=']]",
                "example_right": "[['field', '=', 'value']]"
            },
            {
                "pattern": "Domains to normalize must have a 'domain' form",
                "category": "domain",
                "root_cause": "Domain is string instead of list",
                "solution": "Always use lists: [['field', 'op', 'value']] not 'string'",
                "confidence": 0.98
            },
            {
                "pattern": "Invalid field",
                "category": "field",
                "root_cause": "Field doesn't exist on model",
                "solution": "Run: odoo get-fields MODEL_NAME to see available fields",
                "confidence": 0.95,
                "llm_action": "Automatically suggest get-fields command"
            },
            {
                "pattern": "Model.*does not exist|has no attribute",
                "category": "model",
                "root_cause": "Model name typo or doesn't exist in instance",
                "solution": "Run: odoo get-models --filter PATTERN to find models",
                "confidence": 0.95,
                "llm_action": "Automatically suggest get-models command"
            },
            {
                "pattern": "Access denied|not authorized",
                "category": "permission",
                "root_cause": "User lacks permission for operation",
                "solution": "Use admin user or check access control rules",
                "confidence": 0.90
            },
            {
                "pattern": "Authentication failed|Invalid.*password",
                "category": "auth",
                "root_cause": "Wrong credentials",
                "solution": "Check ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD in .env",
                "confidence": 0.98
            },
            {
                "pattern": "Connection refused|Cannot reach|timeout",
                "category": "connection",
                "root_cause": "Cannot connect to Odoo server",
                "solution": "Check ODOO_URL is correct, server is running, network is up",
                "confidence": 0.95,
                "debug": "Try: curl https://your-url.odoo.com"
            }
        ],

        # Recommendations for LLMs
        "recommendations": {
            "when_uncertain": "Check record_count first: odoo search-count MODEL '[]' (NEW v1.4.0)",
            "before_large_operation": "Validate domain with small test first",
            "for_counting": "Use search-count instead of search + count (90% faster)",
            "for_name_lookup": "Use name-get instead of read() when only names needed (2x faster)",
            "for_autocomplete": "Use name-search for fuzzy name matching (single API call)",
            "for_context": "Use --context flags for multi-company, translations, archived records (v1.3.0)",
            "for_debugging": "Check docs/ERROR-HANDLING.md for error solutions",
            "for_development": "Read docs/guides/LLM-DEVELOPMENT.md for best practices",
            "for_aggregation": "Use docs/examples/aggregation_script.py as template"
        },

        # Quick reference
        "quick_reference": {
            "decision": "record_count > 1000 OR needs_aggregation? → Python | else → CLI",
            "domain_syntax": "[['field', 'operator', 'value']]",
            "operators": "=, !=, <, >, <=, >=, ilike, in, not in",
            "batch_size": "1000 records per read",
            "error_debug": "Check 'error_type' field in JSON response"
        },

        # Documentation links
        "documentation": {
            "main": "docs/README.md",
            "llm_guide": "docs/guides/LLM-DEVELOPMENT.md",
            "error_handling": "docs/ERROR-HANDLING.md",
            "implementation": "docs/IMPLEMENTATION-SUMMARY.md",
            "audit": "docs/AUDIT-REPORT.md",
            "examples": "docs/examples/aggregation_script.py"
        }
    }


def format_llm_help(output_format: str = "json") -> str:
    """
    Format LLM help for output.

    Args:
        output_format: Format to use ("json" or "yaml")

    Returns:
        Formatted help string
    """
    help_data = get_llm_help()

    if output_format == "json":
        return json.dumps(help_data, indent=2)
    elif output_format == "yaml":
        import yaml
        return yaml.dump(help_data, default_flow_style=False, allow_unicode=True)
    else:
        # Default to JSON
        return json.dumps(help_data, indent=2)


def print_llm_help(output_format: str = "json"):
    """
    Print LLM help to stdout.

    Args:
        output_format: Format to use ("json" or "yaml")
    """
    print(format_llm_help(output_format))
