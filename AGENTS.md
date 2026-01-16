# Agent Guide for odoo-cli v2.0

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

## v2.0: exec-only Architecture

All Odoo operations go through the `exec` command. Write Python, get results.

**Available commands:**
```
exec            Execute Python code (PRIMARY - all Odoo operations)
config          Manage connection profiles (alias: profiles)
context         Project business context
agent-info      Complete API reference
```

## Profiles

```bash
odoo-cli config list
```

| Profile | Use Case | Protection |
|---------|----------|------------|
| `dev` | Local Docker development | None |
| `staging` | Odoo.sh branch testing | None |
| `production` | Live data (READ-ONLY) | readonly + protected |

## Client API

The `exec` command provides a pre-authenticated `client` object:

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
client.execute(model, method, *args)               # Call any Odoo method
```

## Common Patterns

### Count Records
```bash
odoo-cli --profile dev exec -c "result = client.search_count('res.partner', [])" --json
```

### Fetch Records
```bash
odoo-cli --profile dev exec -c "result = client.search_read('res.partner', [], ['name', 'email'], limit=10)" --json
```

### Read Specific Record
```bash
odoo-cli --profile dev exec -c "result = client.read('res.partner', [12], ['name', 'email'])" --json
```

### Search with Domain
```bash
odoo-cli --profile dev exec -c "
partners = client.search_read('res.partner', [['is_company', '=', True]], ['name'], limit=10)
result = partners
" --json
```

### Aggregate Data
```bash
odoo-cli --profile dev exec -c "
orders = client.search_read('sale.order', [['state', '=', 'sale']], ['amount_total'])
result = {'count': len(orders), 'total': sum(o['amount_total'] for o in orders)}
" --json
```

### Create Record
```bash
odoo-cli --profile dev exec -c "result = client.create('res.partner', {'name': 'Test', 'email': 'test@example.com'})" --json
```

### Update Record
```bash
odoo-cli --profile dev exec -c "client.write('res.partner', [123], {'name': 'Updated'}); result = {'updated': True}" --json
```

### Call Workflow Action
```bash
odoo-cli --profile dev exec -c "result = client.execute('sale.order', 'action_confirm', [order_id])" --json
```

### Get Field Definitions
```bash
odoo-cli --profile dev exec -c "result = client.fields_get('res.partner')" --json
```

### List Models
```bash
odoo-cli --profile dev exec -c "result = [m for m in client.get_models() if 'partner' in m]" --json
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
- `readonly` → Use staging/dev profile for writes, or use `--force`
- `deprecated_command` → Use exec instead, error shows migration
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
odoo-cli config list                              # Show all profiles
odoo-cli config show staging                      # Show details

# Execute Python
odoo-cli exec -c "result = client.search_count('res.partner', [])" --json
odoo-cli exec script.py --json                    # Script file
odoo-cli --profile prod exec -c "..."             # Specific profile
odoo-cli --force exec -c "..."                    # Override readonly

# Bootstrap for new agent
odoo-cli agent-info                               # Complete API reference
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
