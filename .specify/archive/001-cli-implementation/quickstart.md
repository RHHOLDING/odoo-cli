# Odoo CLI Quickstart Guide

## Installation

```bash
# Install from GitHub (standalone tool)
pip install git+https://github.com/RHHOLDING/odoo-cli.git

# Or for development
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli
pip install -e .
```

## Configuration

### Option 1: Environment Variables (Recommended for LLMs)
```bash
export ODOO_URL=https://your-instance.odoo.com
export ODOO_DB=your-database
export ODOO_USERNAME=admin@example.com
export ODOO_PASSWORD=your-password
```

### Option 2: .env File (Recommended for Humans)
Create a `.env` file in your working directory:

```bash
# .env
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=admin@example.com
ODOO_PASSWORD=your-password
```

⚠️ **Security**: Set proper permissions:
```bash
chmod 600 .env
```

## Basic Usage Examples

### 1. Test Connection
```bash
# List available models (good connectivity test)
odoo get-models

# With filter
odoo get-models --filter sale

# JSON output for parsing
odoo get-models --json
```

### 2. Search Operations
```bash
# Search all partners
odoo search res.partner '[]' --limit 10

# Search with domain filter
odoo search res.partner '[["is_company", "=", true]]' --fields name,email

# Search employees
odoo search-employee "John"

# Search holidays/time-off
odoo search-holidays --state validate --limit 20
```

### 3. Read Specific Records
```bash
# Read partners by ID
odoo read res.partner 1,2,3

# Read specific fields
odoo read sale.order 100 --fields name,amount_total,state
```

### 4. Execute Methods
```bash
# Get record count
odoo execute res.partner search_count --args '[[]]'

# Upgrade a module (admin only)
odoo execute ir.module.module button_immediate_upgrade \
  --args '[[["name", "=", "sale"]]]'
```

### 5. Explore Model Structure
```bash
# Get all fields of a model
odoo get-fields res.partner

# Get specific field details
odoo get-fields sale.order --field amount_total
```

### 6. Interactive Shell
```bash
# Start interactive Python shell
odoo shell

# In the shell:
>>> # Client is pre-loaded
>>> partners = client.search_read('res.partner', [('is_company', '=', True)], limit=5)
>>> pprint(partners)
>>>
>>> # Get model fields
>>> fields = client.execute('res.partner', 'fields_get')
>>> print(json.dumps(fields, indent=2))
>>>
>>> # Direct method execution
>>> count = client.execute('sale.order', 'search_count', [])
>>> print(f"Total sales orders: {count}")
```

## LLM/AI Assistant Usage

### JSON Mode for Parsing
```bash
# Always use --json flag for LLM parsing
odoo search res.partner '[]' --json | jq '.'

# Parse specific fields
odoo get-fields res.partner --json | jq '.data | keys'

# Error handling (errors go to stderr)
odoo search invalid.model '[]' --json 2>&1
```

### Example LLM Commands
```python
import subprocess
import json

def run_odoo_command(cmd):
    """Execute odoo CLI command and parse JSON output."""
    result = subprocess.run(
        cmd + ['--json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        error = json.loads(result.stderr) if result.stderr else None
        return error

# Search for partners
data = run_odoo_command(['odoo', 'search', 'res.partner', '[]'])
if data['success']:
    print(f"Found {len(data['data'])} partners")
```

## Common Workflows

### Developer Workflow: Debug Data Issue
```bash
# 1. Find the model
odoo get-models --filter invoice

# 2. Check model structure
odoo get-fields account.move

# 3. Search for specific record
odoo search account.move '[["name", "=", "INV/2024/001"]]'

# 4. Read full record
odoo read account.move 1234 --json | jq '.'
```

### Admin Workflow: Module Management
```bash
# 1. Find module
odoo search ir.module.module '[["name", "=", "sale"]]' --fields state

# 2. Update module list
odoo execute ir.module.module update_list

# 3. Upgrade module
odoo execute ir.module.module button_immediate_upgrade \
  --args '[[["name", "=", "sale"]]]'
```

### Power User Workflow: Bulk Operations
```bash
# 1. Check how many records would be affected
odoo execute res.partner search_count \
  --args '[[["customer_rank", ">", 0]]]'

# 2. If reasonable number, fetch them
odoo search res.partner '[["customer_rank", ">", 0]]' \
  --fields name,email --limit 100

# 3. Export to JSON for processing
odoo search res.partner '[["customer_rank", ">", 0]]' \
  --fields name,email,phone --json > customers.json
```

## Troubleshooting

### Connection Issues
```bash
# Test with explicit config
odoo get-models \
  --url https://test.odoo.com \
  --db test-db \
  --username admin \
  --json

# Check SSL issues
odoo get-models --no-verify-ssl

# Increase timeout for slow connections
odoo get-models --timeout 60
```

### Large Dataset Handling
```bash
# The CLI will warn before fetching >500 records
odoo search sale.order '[]'
# Warning: Query would return 1543 records.
# Continue? (Y/n): n

# Force with higher limit
odoo search sale.order '[]' --limit 1000

# Or use offset for pagination
odoo search sale.order '[]' --limit 100 --offset 0
odoo search sale.order '[]' --limit 100 --offset 100
```

### Authentication Errors
```bash
# Check current config
echo $ODOO_URL
echo $ODOO_DB
echo $ODOO_USERNAME

# Test with different user
ODOO_USERNAME=other@example.com odoo get-models
```

## Exit Codes

- `0` - Success
- `1` - Connection error (network, URL)
- `2` - Authentication error (bad credentials)
- `3` - Data error (invalid model, method, domain)

## Tips for LLM Integration

1. **Always use `--json` flag** for predictable parsing
2. **Check exit codes** before parsing stdout
3. **Errors go to stderr** in JSON format too
4. **Use environment variables** for configuration
5. **Set reasonable limits** to avoid huge responses
6. **Test with `get-models`** to verify connectivity

## Quick Reference

```bash
# Commands
odoo execute <model> <method> [--args JSON] [--kwargs JSON] [--json]
odoo search-employee <name> [--limit N] [--json]
odoo search-holidays [--employee NAME] [--state STATE] [--limit N] [--json]
odoo get-models [--filter TEXT] [--json]
odoo get-fields <model> [--field NAME] [--json]
odoo search <model> <domain> [--fields FIELDS] [--limit N] [--json]
odoo read <model> <ids> [--fields FIELDS] [--json]
odoo shell [--no-banner]

# Global options (work with all commands)
--config PATH     # Custom config file
--url URL        # Override Odoo URL
--db DATABASE    # Override database
--username USER  # Override username
--password PASS  # Override password
--no-verify-ssl  # Disable SSL verification
--timeout SECS   # Request timeout
--json          # JSON output mode
```

## Next Steps

1. Configure your Odoo connection
2. Test with `odoo get-models`
3. Explore your data with `search` and `read`
4. Use the `shell` for complex operations
5. Integrate with your tools using `--json` mode

For more details, see the full README documentation.