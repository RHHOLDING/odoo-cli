# odoo-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/RHHOLDING/odoo-cli)](https://github.com/RHHOLDING/odoo-cli/releases)

Execute Python code against Odoo. Built for LLM agents.

**v1.7.0** - Agent Experience: `agent-info` command + `--force` for readonly profiles

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
client      # Authenticated OdooClient
json        # JSON module
datetime    # datetime, date, timedelta
pprint      # Pretty printer

# Set 'result' for structured output
result = {"key": "value"}
```

### Examples

```bash
# Count records
odoo-cli exec -c "result = client.search_count('res.partner', [])" --json
# ✓ 98,559

# Top customers by revenue
odoo-cli exec -c "
sales = client.search_read('sale.order', [['state', '=', 'sale']], ['partner_id', 'amount_total'])
by_partner = {}
for s in sales:
    name = s['partner_id'][1]
    by_partner[name] = by_partner.get(name, 0) + s['amount_total']
result = dict(sorted(by_partner.items(), key=lambda x: -x[1])[:5])
" --json
# ✓ ACME Corp=480,317.58, Globex=69,562.24, Initech=19,420.65, ...+2 more

# Overdue invoices
odoo-cli exec -c "
from datetime import date, timedelta
cutoff = (date.today() - timedelta(days=30)).isoformat()
overdue = client.search_read('account.move', [
    ['move_type', '=', 'out_invoice'],
    ['payment_state', '!=', 'paid'],
    ['invoice_date', '<', cutoff]
], ['amount_residual'])
result = {'overdue_count': len(overdue), 'total': sum(i['amount_residual'] for i in overdue)}
" --json
# ✓ overdue_count=30,928, total=486,580,420.26
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
odoo-cli --profile production exec -c "print(client.search_count('res.partner', []))"

# Override readonly protection with --force
odoo-cli --profile production update res.partner 123 -f "name=Test" --force
```

## For LLM Agents

```bash
# Quick tool orientation
odoo-cli agent-info

# LLM-optimized help (full JSON reference)
odoo-cli --llm-help
```

The `agent-info` command provides structured JSON with:
- Connection status and active profile
- Available commands grouped by capability (read/write/meta)
- Quick-start examples
- Important flags (`--json`, `--force`, `--profile`)

## Commands

```
exec            Execute Python code (PRIMARY)
search          Search records
read            Read by ID
create/update   Modify records (use --force for readonly profiles)
delete          Delete records (use --force for readonly profiles)
profiles        Manage environments
agent-info      Quick orientation for LLM agents
```

---

[Changelog](CHANGELOG.md) | Maintainer: [@actec-andre](https://github.com/actec-andre)
