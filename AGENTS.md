# Agent Guide for odoo-cli

This guide is for AI agents (Claude, GPT, etc.) working with Odoo systems.

## TL;DR

```bash
# Query Odoo data - use this, not docker exec
odoo-cli --profile dev exec -c "result = client.search_count('res.partner', [])" --json
# ✓ 98,559
```

## Why odoo-cli?

| Approach | Speed | Output | Works Remote |
|----------|-------|--------|--------------|
| `docker exec odoo shell` | Slow (loads 382 modules) | Verbose logs | No |
| `odoo-cli exec` | Fast (JSON-RPC) | Clean `✓ 98,559` | Yes |

## Profiles

Three environments pre-configured:

```bash
odoo-cli profiles list
```

| Profile | Use Case | Protection |
|---------|----------|------------|
| `dev` | Local Docker development | None |
| `staging` | Odoo.sh branch testing | None |
| `production` | Live data (READ-ONLY) | readonly + protected |

## Common Patterns

### Count Records
```bash
odoo-cli --profile dev exec -c "result = client.search_count('res.partner', [])" --json
# ✓ 98,559
```

### Read Specific Record
```bash
odoo-cli --profile dev exec -c "result = client.execute('res.partner', 'read', [12], ['name', 'email'])" --json
# ✓ 1 records
```

### Search with Domain
```bash
odoo-cli --profile dev exec -c "
partners = client.execute('res.partner', 'search_read', [['is_company', '=', True]], ['name'], 0, 10)
result = partners
" --json
# ✓ 10 records
```

### Aggregate Data
```bash
odoo-cli --profile dev exec -c "
orders = client.execute('sale.order', 'search_read', [['state', '=', 'sale']], ['amount_total'])
result = {'count': len(orders), 'total': sum(o['amount_total'] for o in orders)}
" --json
# ✓ count=1,234, total=567,890.12
```

### Compare Environments
```bash
# Run both in parallel
odoo-cli --profile production exec -c "result = client.search_count('sale.order', [])" --json
odoo-cli --profile staging exec -c "result = client.search_count('sale.order', [])" --json
```

### Custom Models
```bash
odoo-cli --profile dev exec -c "result = client.execute('access.management', 'read', [70])" --json
# ✓ id=70, name='Remove from company // AC TEC', ...
```

## Error Handling

The tool returns structured errors:

```json
{
  "success": false,
  "error": "Write operation 'create' blocked: profile is configured as readonly.",
  "error_type": "execution"
}
```

**Common errors:**
- `readonly` → Use staging/dev profile for writes
- `protected` → Profile can't be modified via CLI
- `connection` → Check URL/credentials
- `execution` → Fix Python code

## When to Use Docker Instead

| Task | Tool |
|------|------|
| View Odoo logs | `docker logs -f odoo-main-dev` |
| Restart Odoo | `docker restart odoo-main-dev` |
| Update module | `docker exec ... odoo -u module_name --stop-after-init` |
| Direct SQL | `docker exec odoo-main-db psql -U odoo -d odoo_main` |
| Debug with breakpoints | `docker exec ... odoo shell` |

## Quick Reference

```bash
# Profiles
odoo-cli profiles list                    # Show all
odoo-cli profiles show staging            # Show details

# Execute Python
odoo-cli exec -c "print('hello')"         # Inline code
odoo-cli exec script.py --json            # Script file
odoo-cli --profile prod exec -c "..."     # Specific profile

# Helper commands (fallback)
odoo-cli search res.partner '[]' --limit 5
odoo-cli read res.partner 12
odoo-cli get-fields sale.order
```

## Output Format

With `--json`, output is:
```
✓ human-readable summary
{JSON data}
```

The summary line shows:
- **Dict:** `✓ count=100, total=1,234.56`
- **List:** `✓ 10 records`
- **Number:** `✓ 98,559`

This lets you see results at a glance without expanding collapsed output.
