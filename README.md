# odoo-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/RHHOLDING/odoo-cli)](https://github.com/RHHOLDING/odoo-cli/releases)

Execute Python code against Odoo. Built for LLM agents.

**v1.6.2** - Python execution command

```bash
pipx install git+https://github.com/RHHOLDING/odoo-cli.git
```

## The Idea

LLM agents are great at writing code. This tool lets them execute it against Odoo:

```bash
odoo-cli exec -c "
partners = client.search_read('res.partner', [['is_company', '=', True]], ['name'], limit=5)
result = {'companies': [p['name'] for p in partners]}
" --json
```

```json
{"success": true, "result": {"companies": ["ACME Corp", "Globex", "Initech"]}}
```

## Quick Start

```bash
# 1. Setup profile
odoo-cli profiles add staging \
  --url https://your-instance.odoo.com \
  --db your-database \
  --username admin@example.com \
  --password secret

# 2. Execute code
odoo-cli exec -c "print(client.search_count('res.partner', []))"
```

## Python Execution

The `exec` command provides a pre-authenticated `client` object:

```python
# Available in your code:
client      # Authenticated OdooClient
json        # JSON module
datetime    # datetime, date, timedelta
pprint      # Pretty printer

# Set 'result' for structured JSON output
result = {"key": "value"}
```

### Examples

```bash
# Inline code
odoo-cli exec -c "print(client.search_count('res.partner', []))"

# Script file
odoo-cli exec script.py --json

# Complex query with result
odoo-cli exec -c "
invoices = client.search_read('account.move', [['state', '=', 'posted']], ['amount_total'], limit=100)
result = {'average': sum(i['amount_total'] for i in invoices) / len(invoices)}
" --json
```

### Example Script

```python
# avg_sales.py - Calculate average sales order value
orders = client.search_read(
    'sale.order',
    [['state', 'in', ['sale', 'done']]],
    ['name', 'amount_total'],
    limit=1000
)

if orders:
    avg = sum(o['amount_total'] for o in orders) / len(orders)
    result = {
        "order_count": len(orders),
        "average_value": round(avg, 2),
        "total_value": round(sum(o['amount_total'] for o in orders), 2)
    }
else:
    result = {"order_count": 0}
```

```bash
odoo-cli exec avg_sales.py --json
```

## Profiles

Switch between environments:

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
odoo-cli --profile production exec -c "print(client.search_count('res.partner', []))"
```

## Helper Commands

For simple operations without writing code:

```
exec            Execute Python code (PRIMARY)
search          Search records
read            Read by ID
create          Create record
update          Update records
delete          Delete records
profiles        Manage profiles
```

## Links

- [Releases](https://github.com/RHHOLDING/odoo-cli/releases)
- [Changelog](CHANGELOG.md)

---

Maintainer: [@actec-andre](https://github.com/actec-andre)
