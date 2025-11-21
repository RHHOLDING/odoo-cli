# Odoo JSON-RPC CLI Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/RHHOLDING/odoo-cli)](https://github.com/RHHOLDING/odoo-cli/releases)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A high-performance, standalone command-line interface for Odoo using the modern JSON-RPC protocol. This tool provides direct access to Odoo functionality from your terminal, perfect for developers, administrators, and automation scripts.

**v1.4.0 - Quick Wins Bundle: LLM-optimized operations for efficiency!**

## Maintainer

**Andre Kremer** ([@actec-andre](https://github.com/actec-andre))
Creator and maintainer of odoo-cli

## Features

- ✨ **CRUD Commands** - Create, update, delete records with simple syntax (no JSON!)
- 📦 **Batch Operations** - Bulk create/update from JSON files with progress tracking
- 📊 **Aggregation Helper** - SUM, AVG, COUNT with optional GROUP BY
- ⚡ **Quick Wins Bundle** - Fast counting, name search, and payload optimization (NEW!)
- 🚀 **16 Commands** - All CRUD operations, batch processing, aggregation, and more
- ⚡ **High-Performance JSON-RPC** - 75% higher throughput than XML-RPC
- 🎯 **Auto Type Inference** - Automatic detection of int, float, bool, string types
- ✅ **Field Validation** - Pre-flight checks with helpful error messages
- 💾 **Smart Caching** - Automatic 24-hour cache for model definitions
- 🔄 **Automatic Retries** - Transient network failures handled gracefully
- 🤖 **LLM-Optimized** - JSON output mode for AI assistants and automation
- 🔒 **Secure** - Credentials management via environment variables or .env files
- 🎨 **Beautiful Output** - Rich tables and colored terminal output
- 🐍 **Interactive Shell** - Python REPL with pre-loaded Odoo client
- 📦 **Standalone** - No dependencies on Odoo installation
- 🔄 **Cross-Platform** - Works on macOS, Linux, and Windows
- 📊 **Odoo 14-17 Support** - Compatible with Odoo versions 14, 15, 16, and 17

## ⚠️ Disclaimer

**This tool directly modifies data in your Odoo database.**

Use at your own risk:
- ⚠️ **Always test in a development environment first** before using in production
- 💾 **Create backups before bulk operations** (create-bulk, update-bulk, delete)
- 🚫 **No liability for data loss, system damage, or downtime** - see MIT License
- 📋 **No warranty of any kind** - the software is provided "as is"

**Recommended approach:**
- Use read-only operations (search, read, get-fields, search-count) in production initially
- Test write operations (create, update, delete) in development environments
- Review domain filters carefully before destructive operations
- Use `--force` flags with caution

For security best practices, see [SECURITY.md](SECURITY.md).

## Quick Start

### Installation

#### macOS (Recommended)
```bash
# Using the installer script
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli
./install.sh
```

#### Using pip
```bash
# Install from GitHub
pip install git+https://github.com/RHHOLDING/odoo-cli.git

# Or for development
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli
pip install -e .
```

#### Using pipx (Best for CLI tools)
```bash
pipx install git+https://github.com/RHHOLDING/odoo-cli.git
```

### Configuration

⚠️ **Security Warning**: Never commit `.env` files to version control!

#### Option 1: Environment Variables
```bash
export ODOO_URL=https://your-instance.odoo.com
export ODOO_DB=your-database
export ODOO_USERNAME=admin@example.com
export ODOO_PASSWORD=your-password
```

#### Option 2: .env File
Create a `.env` file in your project directory:
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=admin@example.com
ODOO_PASSWORD=your-password

# Optional
ODOO_TIMEOUT=30
ODOO_NO_VERIFY_SSL=false
```

**Important**: Secure your .env file:
```bash
chmod 600 .env  # Restrict access to owner only
echo ".env" >> .gitignore  # Never commit to git
```

### Basic Usage

```bash
# Test connection
odoo-cli get-models

# ✨ NEW: Create records (simple syntax, no JSON!)
odoo-cli create res.partner -f name="John Doe" -f email="john@test.com"
odoo-cli create sale.order -f partner_id=123 -f date_order="2025-11-21"

# Search partners
odoo-cli search res.partner '[]' --limit 10

# Read specific records
odoo-cli read res.partner 1,2,3 --fields name,email

# Execute methods
odoo-cli execute res.partner search_count --args '[[]]'

# Interactive shell
odoo-cli shell
```

## Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| **`create`** ✨ | Create records (simple syntax) | `odoo-cli create res.partner -f name="Test" -f email="test@test.com"` |
| **`update`** ✨ | Update records (simple syntax) | `odoo-cli update res.partner 123 -f name="Updated"` |
| **`delete`** ✨ | Delete records (with confirmation) | `odoo-cli delete res.partner 123 --force` |
| **`create-bulk`** 📦 | Bulk create from JSON file | `odoo-cli create-bulk res.partner --file partners.json` |
| **`update-bulk`** 📦 | Bulk update from JSON file | `odoo-cli update-bulk res.partner --file updates.json` |
| **`aggregate`** 📊 | Aggregate data (sum/avg/count) | `odoo-cli aggregate sale.order '[]' --sum amount_total` |
| **`search-count`** ⚡ | Count records (no data transfer) | `odoo-cli search-count res.partner '[]'` |
| **`name-get`** ⚡ | Get display names for IDs | `odoo-cli name-get res.partner 1,2,3` |
| **`name-search`** ⚡ | Fuzzy name search (autocomplete) | `odoo-cli name-search res.partner "John"` |
| `execute` | Execute any model method | `odoo-cli execute ir.module.module button_immediate_upgrade --args '[[["name", "=", "sale"]]]'` |
| `search` | Search records with domain | `odoo-cli search res.partner '[["is_company", "=", true]]' --limit 10` |
| `read` | Read records by IDs | `odoo-cli read sale.order 1,2,3 --fields name,state` |
| `get-models` | List all available models | `odoo-cli get-models --filter sale` |
| `get-fields` | Get field definitions | `odoo-cli get-fields res.partner --field email --attributes type,string` |
| `search-employee` | Search employees by name | `odoo-cli search-employee "John" --limit 5` |
| `search-holidays` | Search time-off records | `odoo-cli search-holidays --state validate` |
| `shell` | Interactive Python shell | `odoo-cli shell` |

## CRUD Commands

### CREATE - Simple Syntax, No JSON Required

```bash
odoo-cli create res.partner -f name="John Doe" -f email="john@test.com" -f active=true
odoo-cli create sale.order -f partner_id=123 -f date_order="2025-11-21"
```

### UPDATE - Single or Multiple Records

```bash
# Update single record
odoo-cli update sale.order 123 -f state="done"

# Update multiple records
odoo-cli update res.partner 1,2,3 -f active=false
```

### DELETE - Safe with Confirmation

```bash
# Delete with confirmation prompt
odoo-cli delete res.partner 456

# Delete multiple (with confirmation)
odoo-cli delete res.partner 456,457,458

# Force delete (skip confirmation)
odoo-cli delete res.partner 456 --force
```

## Batch Operations

### Bulk Create from JSON

```bash
# Create 100s of records from file
odoo-cli create-bulk res.partner --file partners.json

# Custom batch size
odoo-cli create-bulk res.partner -f data.json --batch-size 50
```

**JSON Format (array):**
```json
[
  {"name": "Partner 1", "email": "p1@test.com"},
  {"name": "Partner 2", "email": "p2@test.com"}
]
```

### Bulk Update from JSON

```bash
# Update multiple records with field grouping optimization
odoo-cli update-bulk res.partner --file updates.json

# Custom batch size
odoo-cli update-bulk sale.order -f changes.json --batch-size 50
```

**JSON Format (object with ID keys):**
```json
{
  "123": {"name": "Updated Name 1"},
  "124": {"name": "Updated Name 2", "email": "new@test.com"}
}
```

## Data Aggregation

Calculate SUM, AVG, COUNT directly from CLI:

```bash
# Sum total sales
odoo-cli aggregate sale.order '[[\"date_order\",\">=\",\"2025-10-01\"]]' --sum amount_total

# Count orders by state
odoo-cli aggregate sale.order '[]' --count --group-by state

# Average order value
odoo-cli aggregate sale.order '[]' --avg amount_total --group-by partner_id

# Multiple aggregations
odoo-cli aggregate sale.order '[]' --sum amount_total --count --json
```

**Features:**
- ✅ Automatic batching for large datasets
- ✅ Progress bar for monitoring
- ✅ JSON output for LLM parsing
- ✅ GROUP BY single field
- ✅ Multiple SUM/AVG fields

## Quick Wins Bundle (NEW in v1.4.0)

High-value, low-effort commands optimized for LLM efficiency:

### search-count - Fast Record Counting

Count records without transferring data (~90% faster for large datasets):

```bash
# Count all partners
odoo-cli search-count res.partner '[]'
# Output: {"count": 102091, "model": "res.partner"}

# Count with domain filter
odoo-cli search-count sale.order '[["state","=","sale"]]'

# Include archived records
odoo-cli search-count product.product '[]' --context active_test=false
```

**Why faster?** Odoo counts server-side without sending IDs back to client.

### name-get - ID to Name Conversion

Get display names efficiently (2x faster than read() for name-only queries):

```bash
# Get names for specific IDs
odoo-cli name-get res.partner 1,2,3
# Output: [
#   {"id": 1, "name": "Azure Interior"},
#   {"id": 2, "name": "Deco Addict"},
#   {"id": 3, "name": "Gemini Furniture"}
# ]

# With language context
odoo-cli name-get product.product 100,101 --context lang=de_DE

# JSON mode for LLM parsing
odoo-cli name-get res.partner 1,2,3 --json
```

**Use Cases:**
- Quick validation of record IDs
- Dropdown/selection list generation
- Display name lookups without full record reads

### name-search - Fuzzy Name Search

Fuzzy search for autocomplete/selection lists (single API call vs search + read):

```bash
# Search by name pattern
odoo-cli name-search res.partner "John"
# Output: {
#   "results": [
#     {"id": 51887, "name": "(NEW) john"},
#     {"id": 52103, "name": "John Doe"},
#     {"id": 53214, "name": "Johnson Inc"}
#   ],
#   "count": 5
# }

# With additional domain filter
odoo-cli name-search res.partner "Azure" --domain '[["customer_rank",">",0]]'

# Limit results
odoo-cli name-search product.product "Desk" --limit 10

# Different operators
odoo-cli name-search res.country "Germany" --operator like
```

**Use Cases:**
- Autocomplete fields
- Quick record lookups by name
- Selection list generation for LLMs

### get-fields attributes - Payload Optimization

Filter field metadata to reduce response size (90-95% reduction for large models):

```bash
# Get only specific attributes
odoo-cli get-fields res.partner --attributes type,string,required

# Before (full metadata):
# Response size: ~1-2MB for res.partner

# After (filtered):
# Response size: ~50-100KB

# Get field type info only
odoo-cli get-fields product.product --attributes type,string --json

# Specific field with filtered attributes
odoo-cli get-fields sale.order --field amount_total --attributes type,readonly,help
```

**Use Cases:**
- Fast field type discovery for LLMs
- Reduced bandwidth for large models
- Quick validation of field properties

**Performance Benefits:**
- **search-count**: ~90% faster than `search` + count
- **name-get**: 2x faster than `read()` for names only
- **name-search**: Single call vs `search` + `read` pattern
- **fields_get attributes**: 90-95% payload reduction

### Context Management (NEW in v1.3.0)

Control Odoo behavior with context parameters:

```bash
# Include archived records
odoo-cli search product.product '[]' --context active_test=false

# Use German translations
odoo-cli search product.product '[]' --context lang=de_DE

# Multi-company operations
odoo-cli search sale.order '[]' --context allowed_company_ids=[1,2,3]

# Multiple context flags
odoo-cli search res.partner '[]' \
  --context lang=de_DE \
  --context tz=Europe/Berlin \
  --context active_test=false
```

**Common Context Keys:**

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `active_test` | bool | Include archived records | `active_test=false` |
| `lang` | string | User language | `lang=de_DE` |
| `tz` | string | Timezone | `tz=Europe/Berlin` |
| `allowed_company_ids` | list | Multi-company filter | `allowed_company_ids=[1,2]` |

### Global Options

| Option | Description | Example |
|--------|-------------|---------|
| `--context` | Odoo context key=value | `odoo-cli search res.partner '[]' --context active_test=false` |
| `--json` | Output pure JSON (LLM mode) | `odoo-cli search res.partner '[]' --json` |
| `--limit` | Limit number of records | `odoo-cli search res.partner '[]' --limit 50` |
| `--fields` | Specify fields to return | `odoo-cli read res.partner 1 --fields name,email,phone` |
| `--no-verify-ssl` | Disable SSL verification | `odoo-cli get-models --no-verify-ssl` |
| `--timeout` | Request timeout in seconds | `odoo-cli get-models --timeout 60` |

## LLM/AI Integration

The CLI is optimized for use with AI assistants like Claude, GPT, and others:

### JSON Output Mode
```bash
# Always use --json flag for parsing
odoo-cli search res.partner '[]' --json

# Output structure
{
  "success": true,
  "data": [...],
  "count": 150
}

# Error structure
{
  "success": false,
  "error": "Authentication failed",
  "error_type": "auth",
  "suggestion": "Check credentials"
}
```

### Exit Codes
- `0` - Success
- `1` - Connection error
- `2` - Authentication error
- `3` - Data/operation error

### Python Integration Example
```python
import subprocess
import json

def run_odoo_command(cmd_list):
    result = subprocess.run(
        cmd_list + ['--json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        return json.loads(result.stderr)

# Usage
data = run_odoo_command(['odoo', 'search', 'res.partner', '[]'])
if data['success']:
    print(f"Found {len(data['data'])} partners")
```

## Interactive Shell

The shell command provides an enhanced Python REPL:

```python
$ odoo-cli shell

Welcome to Odoo CLI Shell
Available objects:
  client - Configured Odoo client
  json, pprint, datetime - Utility modules

Examples:
>>> partners = client.search_read('res.partner', [('is_company', '=', True)], limit=5)
>>> pprint(partners)

>>> # Get all sale order fields
>>> fields = client.fields_get('sale.order')
>>> print(json.dumps(fields, indent=2))

>>> # Direct method execution
>>> count = client.execute('sale.order', 'search_count', [])
>>> print(f"Total orders: {count}")
```

## Large Dataset Handling

The CLI warns before fetching large datasets:

```bash
$ odoo-cli search sale.order '[]'
Warning: Query would return 1543 records.
Continue? (Y/n): n

# Force with higher limit
$ odoo-cli search sale.order '[]' --limit 1000

# In JSON mode, warnings are suppressed
$ odoo-cli search sale.order '[]' --json  # Auto-proceeds
```

## Troubleshooting

### Connection Issues
```bash
# Test with explicit configuration
odoo-cli get-models --url https://test.odoo.com --db test --username admin

# Debug mode (verbose output)
ODOO_DEBUG=1 odoo-cli get-models

# Check timeout for slow connections
odoo-cli get-models --timeout 60
```

### Authentication Errors
```bash
# Verify configuration
cat .env

# Test with environment variables
ODOO_USERNAME=test@example.com odoo-cli get-models
```

### SSL Certificate Issues
```bash
# For self-signed certificates
odoo-cli get-models --no-verify-ssl

# Or set globally
export ODOO_NO_VERIFY_SSL=true
```

## Security Best Practices

1. **Never commit credentials**:
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use read-only users when possible**:
   - Create dedicated API users with minimal permissions
   - Avoid using admin accounts for automation

3. **Secure file permissions**:
   ```bash
   chmod 600 .env  # Owner read/write only
   chmod 700 ~/.odoo_cli_history  # Protect shell history
   ```

4. **Use environment variables in CI/CD**:
   - Store credentials in secure CI/CD variables
   - Never hardcode credentials in scripts

5. **Rotate credentials regularly**:
   - Change passwords periodically
   - Monitor access logs for unusual activity

## Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=odoo_cli

# Run specific test file
pytest tests/unit/test_client.py
```

### Code Quality
```bash
# Format code
black odoo_cli tests

# Check linting
flake8 odoo_cli tests

# Type checking
mypy odoo_cli
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/RHHOLDING/odoo-cli/issues)
- **Documentation**: This README
- **Examples**: See `quickstart.md` in the docs folder

## Author

Andre Kremer (andre@solarcraft.gmbh)

---

**Note**: This tool is not officially affiliated with Odoo S.A.