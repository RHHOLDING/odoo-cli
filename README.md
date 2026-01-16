# odoo-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/RHHOLDING/odoo-cli)](https://github.com/RHHOLDING/odoo-cli/releases)

Execute Python code against Odoo. Built for LLM agents.

**v2.0.0** - exec-only architecture. All Odoo operations through Python code.

```bash
pipx install git+https://github.com/RHHOLDING/odoo-cli.git
```

## The Idea

LLM agents write Python, this tool executes it against Odoo:

```bash
odoo-cli exec -c "
invoices = client.search_read('account.move', [['state', '=', 'posted']], ['amount_total'], limit=100)
result = {'count': len(invoices), 'total': sum(i['amount_total'] for i in invoices)}
" --json
```

```
✓ count=100, total=146,268.87
{"success": true, "result": {"count": 100, "total": 146268.87}}
```

Human-readable summary first, full JSON below.

## Quick Start

```bash
# 1. Setup profile
odoo-cli config add staging \
  --url https://your-instance.odoo.com \
  --db your-database \
  --username admin@example.com \
  --password secret

# 2. Execute code
odoo-cli exec -c "result = client.search_count('res.partner', [])" --json
```

## Python Execution

The `exec` command provides a pre-authenticated `client` object:

```python
client      # Authenticated OdooClient
json        # JSON module
datetime    # datetime, date, timedelta
pprint      # Pretty printer

# Set 'result' for structured output
result = {"key": "value"}
```

> **Note:** Use `client`, not `env`. This is JSON-RPC, not server-side Python.
> Code using `env['model']` or `self.env` will fail with a helpful error message.

### Client API

```python
# Query methods
client.search(model, domain, limit=None)           # Returns IDs
client.read(model, ids, fields=None)               # Returns records
client.search_read(model, domain, fields, limit)   # Combined (most efficient)
client.search_count(model, domain)                 # Returns count
client.fields_get(model)                           # Returns field definitions
client.get_models()                                # Returns all model names

# Write methods (blocked if profile is readonly)
client.create(model, values)                       # Returns new ID
client.write(model, ids, values)                   # Returns True
client.unlink(model, ids)                          # Returns True

# Generic method call
client.execute(model, method, *args, **kwargs)     # Call any Odoo method
```

### Examples

```bash
# Count records
odoo-cli exec -c "result = client.search_count('res.partner', [])" --json

# Fetch records with fields
odoo-cli exec -c "result = client.search_read('res.partner', [], ['name', 'email'], limit=10)" --json

# Top customers by revenue
odoo-cli exec -c "
sales = client.search_read('sale.order', [['state', '=', 'sale']], ['partner_id', 'amount_total'])
by_partner = {}
for s in sales:
    name = s['partner_id'][1]
    by_partner[name] = by_partner.get(name, 0) + s['amount_total']
result = dict(sorted(by_partner.items(), key=lambda x: -x[1])[:5])
" --json

# Create a record
odoo-cli exec -c "result = client.create('res.partner', {'name': 'New Partner', 'email': 'new@example.com'})" --json

# Update a record
odoo-cli exec -c "client.write('res.partner', [123], {'name': 'Updated'}); result = {'updated': True}" --json

# Call workflow action
odoo-cli exec -c "result = client.execute('sale.order', 'action_confirm', [order_id])" --json
```

## Profiles

```yaml
# ~/.config/odoo-cli/config.yaml
profiles:
  staging:
    url: https://staging.odoo.com
    db: staging-db
    username: admin@example.com
    password: secret
    default: true
  production:
    url: https://production.odoo.com
    db: prod-db
    username: admin@example.com
    password: secret
    readonly: true    # Blocks write operations
    protected: true   # Blocks CLI modifications
```

```bash
# Use specific profile
odoo-cli --profile production exec -c "result = client.search_count('res.partner', [])" --json

# Override readonly protection with global --force flag
odoo-cli --force --profile production exec -c "result = client.create('res.partner', {'name': 'Test'})" --json
```

### Profile Management

```bash
odoo-cli config list                    # List all profiles
odoo-cli config add NAME --url ...      # Add new profile
odoo-cli config edit NAME --readonly    # Set profile to readonly
odoo-cli config delete NAME -y          # Delete profile
odoo-cli config test NAME               # Test connection
```

## For LLM Agents

```bash
# Complete API reference and bootstrap
odoo-cli agent-info

# LLM-optimized help (JSON format)
odoo-cli --llm-help
```

The `agent-info` command provides structured JSON with:
- Connection status and active profile
- Complete client API reference
- Common code patterns
- Domain syntax reference
- Error handling guide

## Commands (v2.0)

```
exec            Execute Python code (PRIMARY - all Odoo operations)
config          Manage connection profiles (alias: profiles)
context         Project business context
agent-info      Complete API reference for LLM agents

# Global flags (before command):
--force         Override readonly profile protection
--profile NAME  Use specific profile
--json          Output JSON format
```

## JSON Output

```bash
# Per-command flag
odoo-cli exec -c "..." --json

# Environment variable (recommended for automation)
export ODOO_CLI_JSON=1
odoo-cli exec -c "..."  # Automatic JSON output
```

---

[Changelog](CHANGELOG.md) | Maintainer: [@actec-andre](https://github.com/actec-andre)
