# odoo-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/RHHOLDING/odoo-cli)](https://github.com/RHHOLDING/odoo-cli/releases)

Fast, LLM-friendly command-line interface for Odoo.

**v1.6.1** - Profile protection & safety confirmations

```bash
pipx install git+https://github.com/RHHOLDING/odoo-cli.git
```

## Why this tool?

| Feature | Benefit |
|---------|---------|
| **JSON-RPC** | 75% faster than XML-RPC |
| **Simple syntax** | `--fields name="Test"` statt JSON |
| **Profile switching** | `--profile staging` / `--profile production` |
| **Readonly mode** | Safe production inspection |
| **LLM-optimized** | `--json` output for AI agents |

## Quick Start

```bash
# 1. Create profile
odoo-cli profiles add staging \
  --url https://your-instance.odoo.com \
  --db your-database \
  --username admin@example.com \
  --password secret

# 2. Use it
odoo-cli search res.partner '[]' --limit 5
odoo-cli create res.partner -f "name=Test" -f "email=test@example.com"
odoo-cli read res.partner 123
```

## Commands

```
search          Search records
read            Read records by ID
create          Create record with field=value syntax
update          Update records
delete          Delete records
execute         Call any Odoo method
get-models      List available models
get-fields      Show model fields
profiles        Manage environment profiles
```

Full command reference: `odoo-cli --help` or `odoo-cli <command> --help`

## Profiles

Switch between environments without editing config:

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
odoo-cli --profile production search res.partner '[]'  # Safe read
odoo-cli --profile staging create res.partner -f "name=Test"  # Write allowed
```

## For LLM Agents

```bash
# JSON output for parsing
odoo-cli search res.partner '[]' --json

# Or set once for all commands
export ODOO_CLI_JSON=1

# Structured errors
{
  "success": false,
  "error": "Field 'nam' not found",
  "error_type": "field_validation",
  "suggestion": "Did you mean: name?"
}
```

## Links

- [Releases](https://github.com/RHHOLDING/odoo-cli/releases)
- [Changelog](CHANGELOG.md)
- [License](LICENSE) (MIT)

---

Maintainer: [@actec-andre](https://github.com/actec-andre)
