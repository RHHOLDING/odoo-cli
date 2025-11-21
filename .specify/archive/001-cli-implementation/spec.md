# Feature Specification: Odoo XML-RPC CLI Tool

## Overview

Ein Command-Line Interface (CLI) Tool namens "odoo-xml-cli", das alle Funktionen des existierenden Odoo MCP Servers als Terminal-Commands verfügbar macht.

## Clarifications

### Session 2025-11-20
- Q: For a production CLI tool used by DevOps/Admins, how should credentials be handled? → A: Keep .env only - simple for development, document security risks in README
- Q: When a search could return thousands of records, what should happen? → A: Warn at 500+ records - ask user to confirm before fetching large result sets
- Q: How should the MCP client import path be handled for users installing from GitHub directly? → A: Standalone CLI tool - independent of ODOO-MAIN monorepo, package XML-RPC client code directly into odoo_cli/
- Q: Should the interactive shell include helpful utilities for LLM usage? → A: LLM-optimized - include example snippets banner, auto-complete hints, command history
- Q: How should --json flag behavior be implemented across different scenarios? → A: JSON-only mode - suppress all Rich formatting, warnings, prompts; pure JSON stdout, errors to stderr

## Business Context

### Problem Statement
Entwickler und Administratoren benötigen schnellen, direkten Zugriff auf Odoo XML-RPC Operationen ohne auf die Web-UI oder MCP-Tools angewiesen zu sein. Häufige Operationen wie Modul-Upgrades, Datenabfragen oder Debugging sollten direkt im Terminal möglich sein.

### Target Users
- **Entwickler**: Für schnelle Debugging-Sessions und Datenabfragen
- **DevOps/Admins**: Für Modul-Management und Systemoperationen
- **Power Users**: Für erweiterte Odoo-Operationen via Terminal

### Success Criteria
- ✅ Alle MCP-Funktionen sind als CLI-Commands verfügbar
- ✅ Installation mit einem Befehl (`pip install git+https://github.com/RHHOLDING/odoo-cli.git`)
- ✅ Schöne, lesbare Terminal-Ausgabe
- ✅ Standalone tool - works independently without ODOO-MAIN monorepo
- ✅ LLM-friendly - optimized for AI assistant usage with clear command structure

## Technical Requirements

### Dependencies & Technology Stack

**Core Dependencies:**
- **Click** (>=8.1.0) - CLI Framework für Command-Struktur
- **Rich** (>=13.0.0) - Terminal-Ausgabe (Tabellen, Farben)
- **python-dotenv** (>=1.0.0) - Config-Management aus .env
- **Bundled XML-RPC Client** - Extracted from MCP server, included in `odoo_cli/client.py`

**Python Version:** >=3.10 (kompatibel mit MCP Server)

### Architecture

```
odoo-xml-cli/                    # Standalone CLI tool (installable via pip from GitHub)
├── pyproject.toml              # Project definition & dependencies
├── README.md                   # User documentation
├── LICENSE                     # MIT License
└── odoo_cli/                   # Python package
    ├── __init__.py            # Package init
    ├── cli.py                 # Click CLI entry point
    ├── client.py              # Odoo XML-RPC client (extracted from MCP server)
    └── utils.py               # Helper functions (output formatting)
```

**Import Strategy:**
```python
# Use bundled XML-RPC client (no external dependencies)
from odoo_cli.client import OdooClient, get_odoo_client
```

**Note:** The XML-RPC client code is extracted from `/MCP/odoo/src/odoo_mcp/` and packaged directly into `odoo_cli/client.py` to make this tool fully standalone and installable via `pip install git+https://github.com/RHHOLDING/odoo-cli.git`

### CLI Commands Structure

**Main Command Group:**
```bash
odoo --help                     # Show all available commands
```

**Subcommands:**

1. **execute** - Execute arbitrary model methods
   ```bash
   odoo execute <model> <method> [--args JSON] [--kwargs JSON]
   # Example: odoo execute ir.module.module button_immediate_upgrade --args '[[("name", "=", "actec_helpdesk")]]'
   ```

2. **search-employee** - Search employees by name
   ```bash
   odoo search-employee <name> [--limit N]
   # Example: odoo search-employee "Andre Kremer"
   ```

3. **search-holidays** - Search time-off records
   ```bash
   odoo search-holidays [--employee NAME] [--state STATE] [--limit N]
   # Example: odoo search-holidays --employee "Andre" --state validate
   ```

4. **get-models** - List all available Odoo models
   ```bash
   odoo get-models [--filter TEXT]
   # Example: odoo get-models --filter helpdesk
   ```

5. **get-fields** - Get field definitions for a model
   ```bash
   odoo get-fields <model> [--field NAME]
   # Example: odoo get-fields res.partner --field email
   ```

6. **search** - Search records with domain
   ```bash
   odoo search <model> <domain> [--fields FIELDS] [--limit N]
   # Example: odoo search res.partner '[("is_company", "=", true)]' --limit 10
   ```

7. **read** - Read records by IDs
   ```bash
   odoo read <model> <ids> [--fields FIELDS]
   # Example: odoo read res.partner 1,2,3 --fields name,email
   ```

8. **shell** - Interactive Python shell with Odoo client (LLM-optimized)
   ```bash
   odoo shell
   # Starts Python shell with:
   # - Pre-loaded 'client' variable
   # - Example snippets banner showing common operations
   # - Auto-complete hints for client methods
   # - Command history (readline support)
   # - Preloaded utilities: json, pprint, datetime
   ```

### Configuration

**Config Loading Priority:**
1. Environment variables (`ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`)
2. Parent `.env` file (`ODOO-MAIN/.env`)
3. `~/.odoo_config.json` (fallback)

**Security Note:** Credentials are stored in plain text in `.env` files for development convenience. README must document security risks and recommend appropriate file permissions (chmod 600) for production use.

**Example .env:**
```bash
ODOO_URL=https://rhholding-ac-mail-deploy-25766690.dev.odoo.com
ODOO_DB=rhholding-ac-mail-deploy-25766690
ODOO_USERNAME=mcp@ananda.gmbh
ODOO_PASSWORD=mcp88
```

### Output Formatting (Rich)

**Tables for Record Lists:**
```python
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(title="Search Results")
table.add_column("ID", style="cyan")
table.add_column("Name", style="green")
table.add_column("Email", style="yellow")

for record in records:
    table.add_row(str(record['id']), record['name'], record.get('email', 'N/A'))

console.print(table)
```

**Color-coded Messages:**
- ✅ Success: `[green]✓[/green] Operation completed`
- ❌ Error: `[red]✗[/red] Error: {message}`
- ℹ️ Info: `[blue]ℹ[/blue] {info}`

**JSON Output Mode (`--json` flag):**
```bash
odoo search res.partner '[]' --json  # Raw JSON output for scripting/LLM parsing
```

**JSON Mode Behavior:**
- **stdout**: Pure JSON data only (no Rich formatting, colors, or tables)
- **stderr**: All errors, warnings, and status messages
- **Prompts**: Suppressed (e.g., large result set warnings auto-confirmed)
- **Exit codes**: Same as normal mode (0=success, 1=connection, 2=auth, 3=data)
- **Use case**: Optimized for LLM parsing and shell piping

## Implementation Details

### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "odoo-xml-cli"
version = "0.1.0"
description = "CLI tool for Odoo XML-RPC operations"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Andre Kremer", email = "andre@actec-solar.de"}
]
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
    # readline for shell command history (usually built-in on Unix)
]

[project.scripts]
odoo = "odoo_cli.cli:main"

[project.urls]
Homepage = "https://github.com/RHHOLDING/odoo-cli"
```

### Error Handling

**Normal Mode (Rich output):**
```python
try:
    client = get_odoo_client()
except Exception as e:
    console.print(f"[red]✗ Connection failed:[/red] {e}", file=sys.stderr)
    sys.exit(1)
```

**JSON Mode (`--json` flag):**
```python
try:
    client = get_odoo_client()
except Exception as e:
    # Errors to stderr, data to stdout
    print(json.dumps({"error": str(e), "type": "connection"}), file=sys.stderr)
    sys.exit(1)

# Success output to stdout only
result = client.execute_method(model, method, *args)
print(json.dumps(result))  # Pure JSON, no extra messages
```

**Exit Codes:**
- `0`: Success
- `1`: Connection error (network, URL, timeout)
- `2`: Authentication error (invalid credentials)
- `3`: Data/operation error (invalid model, method, domain, etc.)

## Installation & Usage

### Installation
```bash
cd /Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli
pip install -e .
```

### Quick Start Examples

**Upgrade a module:**
```bash
odoo execute ir.module.module button_immediate_upgrade \
  --args '[[("name", "=", "actec_helpdesk")]]'
```

**Search for employees:**
```bash
odoo search-employee "Andre"
```

**Get all models with 'sale' in name:**
```bash
odoo get-models --filter sale
```

**Interactive shell:**
```bash
odoo shell
>>> client.search_read('res.partner', [('is_company', '=', True)], limit=5)
```

## Testing Strategy

### Manual Testing Checklist
- [ ] All commands execute successfully
- [ ] Config loading from .env works
- [ ] Error messages are clear and helpful
- [ ] Rich output renders correctly in terminal
- [ ] Shell command provides interactive access

### Test Commands
```bash
# Test connection
odoo get-models --filter res.partner

# Test search
odoo search res.partner '[("id", "=", 1)]'

# Test execute
odoo execute res.partner search_count --args '[[]]'

# Test shell
odoo shell
```

## Non-Functional Requirements

### Performance
- Commands should respond within 2-5 seconds (network dependent)
- No unnecessary client reconnections
- Efficient JSON parsing for large datasets
- Large result set handling: When search would return 500+ records, display warning with record count and require user confirmation (Y/n) before fetching. User can cancel and refine search filters.

### Usability
- Clear `--help` text for all commands
- Intuitive argument naming
- Sensible defaults (e.g., limit=20 for searches)

### LLM-Friendliness (AI Assistant Optimization)
- **Consistent command structure**: All commands follow same pattern for predictable LLM usage
- **JSON output mode**: `--json` flag on all commands for programmatic parsing
  - Pure JSON to stdout, errors/warnings to stderr
  - No prompts or interactive elements in JSON mode
  - Consistent error format: `{"error": "message", "type": "category"}`
- **Shell enhancements**:
  - Startup banner with example code snippets (search, read, execute patterns)
  - Auto-complete for client methods and model names
  - Command history persisted between sessions (~/.odoo_cli_history)
  - Pre-imported utilities (json, pprint, datetime) for quick data inspection
- **Error messages**: Structured format with actionable suggestions for common mistakes
- **Exit codes**: Meaningful codes (0=success, 1=connection, 2=auth, 3=data error) for scripting
- **Deterministic behavior**: Same input always produces same output (no random variations)

### Maintainability
- DRY principle: No duplicate code from MCP client
- Clear separation: CLI logic in `cli.py`, formatting in `utils.py`
- Well-documented code with docstrings

## Future Enhancements

### Phase 2 (Optional)
- [ ] Bash/Zsh completion scripts
- [ ] Config file support (`~/.odoo-cli.toml`)
- [ ] Batch operations from file
- [ ] Export results to CSV/JSON files
- [ ] Module development helpers (`odoo scaffold`, `odoo lint`)

### Phase 3 (Optional)
- [ ] Watch mode for continuous queries
- [ ] Interactive TUI for complex operations
- [ ] Plugin system for custom commands

## Dependencies on Existing Code

**Source for Initial Implementation:**
- `/MCP/odoo/src/odoo_mcp/odoo_client.py` - XML-RPC client code to be extracted and packaged into `odoo_cli/client.py`
- `/MCP/odoo/src/odoo_mcp/__init__.py` - Reference for client initialization patterns

**After Extraction:**
- No runtime dependencies on ODOO-MAIN monorepo
- Standalone package with bundled XML-RPC client
- Configuration via .env files or environment variables (user's own setup)

**Must remain compatible with:**
- Python 3.10+
- Standard .env structure (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
- Odoo XML-RPC API (v16+ compatible)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| XML-RPC client bugs after extraction | Medium | Thorough testing, maintain compatibility with original MCP client behavior |
| .env not found | Medium | Clear error messages, document config setup, support multiple config sources |
| Rich not rendering in all terminals | Low | Provide `--json` flag as fallback |
| Odoo API changes (future versions) | Low | Version compatibility documentation, test against v16+ instances |

## Acceptance Criteria

- [x] All 8 main commands implemented and working
- [x] Rich output for tables and colored messages
- [x] Config loading from parent .env
- [x] MCP Client successfully imported and reused
- [x] `pip install -e .` makes `odoo` command available globally
- [x] README with usage examples
- [x] No duplicate XML-RPC code
- [x] Error handling with user-friendly messages

## Documentation

**README.md sections:**
1. Installation
2. Configuration (including security warnings about .env file permissions)
3. Command Reference (all 8 commands with examples)
4. Development Setup
5. Troubleshooting

**Inline documentation:**
- Docstrings for all Click commands
- Type hints where applicable
- Comments for complex logic

---

**Specification Status:** Ready for Implementation
**Last Updated:** 2025-11-20
**Author:** Andre Kremer
