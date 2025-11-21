# GEMINI.md

Quick guide for Google Gemini when working with this repository. Based on CLAUDE.md.

## Repository Overview

**odoo-cli** - LLM-friendly CLI tool for Odoo JSON-RPC operations
- Repository: https://github.com/RHHOLDING/odoo-cli
- License: MIT License
- Language: English (code, docs, commits)
- Python 3.10+ | CLI Framework: Click | Output: Rich + JSON

## Safety & Security

**PUBLIC repository - security rules:**
- ❌ No credentials in code/tests/docs
- ❌ No real customer data (use: Azure Interior, Deco Addict, Gemini Furniture)
- ✅ Credentials via environment variables or `~/.odoo-cli.yaml`
- ✅ `.env` files are gitignored

## Quick Start

### Installation
```bash
pip install git+https://github.com/RHHOLDING/odoo-cli.git
```

### Configuration (.env or environment variables)
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
```

## Command Structure

**All commands use `odoo-cli`:**

```bash
odoo-cli [command] [model] [arguments] [options]
```

**JSON Output Options (v1.4.1+):**
```bash
# Three ways to get JSON output:
odoo-cli search res.partner '[]' --json              # 1. Command-level (RECOMMENDED)
export ODOO_CLI_JSON=1; odoo-cli search ...         # 2. Environment variable
odoo-cli --json search res.partner '[]'              # 3. Global flag (legacy)
```

**Other Global options:**
- `--context key=value` - Odoo context (lang, company, timezone)
- `--limit N` - Limit results

## Core Commands (v1.4.1)

### CRUD Operations
```bash
# Create records (simple syntax)
odoo-cli create res.partner -f name="John Doe" -f email="john@example.com"

# Read records
odoo-cli read res.partner 1,2,3 --fields name,email

# Update records
odoo-cli update res.partner 123 -f name="Updated Name"

# Delete records (with confirmation)
odoo-cli delete res.partner 456 --force
```

### Quick Wins (LLM-Optimized)
```bash
# Count records (fast, no data transfer)
odoo-cli search-count res.partner '[]'

# Get display names
odoo-cli name-get res.partner 1,2,3

# Fuzzy name search
odoo-cli name-search res.partner "John"

# Get field metadata (filtered)
odoo-cli get-fields res.partner --attributes type,string,required
```

### Batch Operations
```bash
# Bulk create from JSON file
odoo-cli create-bulk res.partner --file partners.json

# Bulk update from JSON file
odoo-cli update-bulk res.partner --file updates.json
```

### Data Aggregation
```bash
# Sum, average, count
odoo-cli aggregate sale.order '[]' --sum amount_total --count
odoo-cli aggregate sale.order '[]' --avg amount_total --group-by state
```

### Discovery & Execution
```bash
# List models
odoo-cli get-models --filter sale

# Get field definitions
odoo-cli get-fields res.partner --field email

# Execute any method
odoo-cli execute res.partner search_count --args '[[]]'

# Search records
odoo-cli search res.partner '[[\"is_company\",\"=\",true]]' --limit 10

# Interactive shell
odoo-cli shell
```

## Context Management

Odoo context controls behavior (multi-company, translations, archived records):

```bash
# Include archived records
odoo-cli search product.product '[]' --context active_test=false

# Use translations
odoo-cli search res.partner '[]' --context lang=de_DE

# Multi-company operations
odoo-cli search sale.order '[]' --context allowed_company_ids=[1,2,3]
```

## LLM Integration Tips

**JSON output mode:**
```bash
# Always use --json for parsing
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
  "error": "Description",
  "error_type": "auth|connection|operation",
  "suggestion": "Actionable fix"
}
```

**Exit codes:**
- 0 = Success
- 1 = Connection error
- 2 = Authentication error
- 3 = Operation error

**LLM Help:**
```bash
odoo-cli --llm-help  # Comprehensive decision tree for LLMs
```

## Development Workflow

**Code Style:**
- Black (line length 120), isort
- Google-style docstrings
- Type hints where useful

**Testing:**
```bash
pytest                    # All tests
pytest --cov=odoo_cli    # With coverage
```

**Adding Commands:**
1. Create file in `odoo_cli/commands/your_command.py`
2. Register in `odoo_cli/cli.py`
3. Update `odoo_cli/help.py` (--llm-help)
4. Add tests in `tests/unit/`
5. Document in README.md

## Key Files

- `README.md` - User documentation
- `CLAUDE.md` - Canonical development guidelines (primary reference)
- `CODEX.md` - OpenAI/Codex specific guide
- `CHANGELOG.md` - Version history
- `.specify/` - BMAD feature specifications
- `odoo_cli/help.py` - LLM help system

## Current Version

**v1.4.0 - Quick Wins Bundle**
- 16 commands total
- CRUD + batch operations
- Aggregation helper
- Quick wins (search-count, name-get, name-search)
- Context management

**Next: v1.5.0 - Environment Profiles**
- Spec ready in `.specify/features/001_environment_profiles/`
- Easy prod/staging/dev switching

## Security & Disclaimer

⚠️ **This tool directly modifies Odoo databases**
- Always test in development first
- Create backups before bulk operations
- No liability for data loss or system damage
- See LICENSE (MIT) for full terms

## References

For comprehensive guidelines, refer to `CLAUDE.md` (canonical source).
For OpenAI/Codex specifics, see `CODEX.md`.
