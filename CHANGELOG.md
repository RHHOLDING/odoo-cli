# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - Project Context Layer for LLM Agents

### Added
- **Business context feature** - Help LLM agents understand your Odoo setup
  - `context show` - Display project-specific business metadata
  - `context guide --task` - Get task-specific guidance (4 predefined tasks)
  - `context validate` - Validate context files (normal and strict modes)
- **`.odoo-context.json` support** - Manually-maintained context file for LLM integration
  - Defines companies, warehouses, workflows, critical modules, business rules
  - `.odoo-context.json5.example` template with comprehensive inline documentation
  - Automatically gitignored to prevent credential exposure
- **JSON Schema validation** - `odoo_cli/schemas/context_schema.json` for strict mode validation
- **Security scanning** - Automatic detection of literal "password"/"token" strings in context files

### LLM Integration
- LLM agents can query business context without analyzing Odoo API
- Task mappings: create-sales-order, manage-inventory, purchase-approval, production-workflow
- All context commands support `--json` for LLM-friendly output
- Clear error messages and validation suggestions for misconfigured files

### New Files
- `odoo_cli/context.py` - ContextManager class
- `odoo_cli/commands/context.py` - Context CLI commands
- `.odoo-context.json5.example` - Template with examples and security guidance
- `odoo_cli/schemas/context_schema.json` - JSON Schema for validation

### Documentation
- README.md updated with "Business Context for LLM Agents" section
- Comprehensive example context file with Azure Interior demo data
- Security best practices guide for context files
- Decision trees in `--llm-help` for context command usage

## [1.4.1] - 2025-11-21

### Added
- **ODOO_CLI_JSON environment variable** - Enable JSON output by default for LLM-friendly automation
  - Set `export ODOO_CLI_JSON=1` once to get JSON output for all commands
  - Added to `.env.example` as recommended configuration for LLMs
- **Command-level --json flag** - `--json` can now be placed at end of command (more intuitive)
  - Both work: `odoo-cli --json search ...` AND `odoo-cli search ... --json`
  - Command-level flag takes precedence over global flag

### Changed
- Updated `search` command with command-level `--json` option
- Priority order: Command `--json` > `ODOO_CLI_JSON` env > Global `--json` > Default (Rich output)

### LLM Integration
- **3 ways to get JSON output:**
  1. `odoo-cli search res.partner '[]' --json` (command-level, most intuitive)
  2. `export ODOO_CLI_JSON=1` (set once, affects all commands)
  3. `odoo-cli --json search res.partner '[]'` (global flag, original method)

## [1.4.0] - 2025-11-21

### Added
- **search-count command** - Count records without data transfer (~90% faster for large datasets)
- **name-get command** - Convert IDs to display names (2x faster than read() for name-only queries)
- **name-search command** - Fuzzy name search for autocomplete/selection lists (single API call vs search + read)
- **get-fields --attributes flag** - Filter field metadata to reduce payload by 90-95%

### Changed
- All new commands support `--json` flag for LLM integration
- All new commands support `--context` flag for multi-company/translation operations

### Performance
- search-count: ~90% faster than search + count for large datasets
- name-get: 2x faster than read() when only names needed
- name-search: Single API call vs search + read pattern
- fields_get attributes: 90-95% payload reduction for large models

## [1.3.0] - 2025-11-21

### Added
- **Context management** - `--context` flag for all commands
  - Multi-company operations: `--context allowed_company_ids=[1,2,3]`
  - Translations: `--context lang=de_DE`
  - Archived records: `--context active_test=false`
  - Timezone handling: `--context tz=Europe/Berlin`
- Context parser utility with automatic type inference
- Lazy validation for context keys
- Debug logging for user-provided context

### Changed
- Updated all 10 CLI commands with `--context` support:
  - read, create, update, delete, execute
  - aggregate, create-bulk, update-bulk
  - search-employee, search-holidays

## [1.2.0] - 2025-11-21

### Added
- **update command** - Update single/multiple records with field=value syntax
- **delete command** - Delete records with safety confirmation (--force to skip)
- **create-bulk command** - Bulk create from JSON file with progress bar
- **update-bulk command** - Bulk update with field grouping optimization
- **aggregate command** - SUM/AVG/COUNT with optional GROUP BY

### Changed
- Field grouping optimization for update-bulk (reduces API calls)
- Automatic batching for large datasets (1000 records default)
- Progress bars with real-time feedback

### Testing
- 140+ unit tests passing (100% success rate)
  - 41 tests for field parser
  - 28 tests for CREATE command
  - 24 tests for UPDATE command
  - 22 tests for DELETE command
  - 17 tests for CREATE-BULK
  - 17 tests for UPDATE-BULK
  - 23 tests for AGGREGATE command

## [1.1.0] - 2025-11-21

### Added
- **create command** - User-friendly record creation with field=value syntax
  - No JSON required! Use intuitive `--fields key=value` syntax
  - Automatic type inference (int, float, bool, string, list)
  - Field validation with helpful error messages
  - Returns created record ID for immediate use

### Added (Utilities)
- Field Parser Utility (`field_parser.py`)
  - `parse_field_values()` - Parse field=value syntax with auto type detection
  - `validate_fields()` - Pre-flight validation against Odoo field definitions
  - Helpful suggestions when field names are similar but incorrect

### Testing
- 69 unit tests passing (100% success rate)
  - 41 tests for field parser (99% coverage)
  - 28 tests for CREATE command (comprehensive scenarios)
- Real Odoo instance validation

## [1.0.0] - 2025-11-20

### Changed
- **BREAKING**: Complete migration from XML-RPC to JSON-RPC protocol
- Single `/jsonrpc` endpoint (replaced `/xmlrpc/2/common` and `/xmlrpc/2/object`)
- Migrated from legacy `xmlrpc.client` to modern `requests` library

### Added
- Connection pooling - Persistent HTTP sessions with automatic connection reuse
- Automatic retry logic - Transient network failures retried automatically (2s delay, max 3 retries)
- Response caching - Model definitions cached for 24 hours in `~/.odoo-cli/cache/`
- Modern HTTP library with better error handling

### Removed
- XML-RPC protocol support (use v0.1.0 if specifically needed)
- `RedirectTransport` class (XML-RPC specific)
- Legacy protocol detection logic

### Performance
- Response time: 500ms (XML-RPC) → 285ms (JSON-RPC) - **43% improvement**
- Throughput: 100 req/s (XML-RPC) → 175 req/s (JSON-RPC) - **75% improvement**
- Cache hit: <100ms for cached model definitions
- Payload size: JSON is more compact than XML

### Testing
- 31 unit tests passing (100%)
- 94% coverage for cache module
- 59% coverage for client module
- Integration tests against real Odoo v16 instance
- Multi-version compatibility verified (v14-17)

### Compatibility
- Odoo versions: 14.0, 15.0, 16.0, 17.0
- Python: 3.10+
- Platforms: macOS, Linux, Windows
- All CLI commands work exactly the same (no configuration changes needed)

## [0.1.0] - 2025-11-15

### Added
- Initial CLI implementation with XML-RPC protocol
- 8 core commands:
  - execute, search, read
  - get-models, get-fields
  - search-employee, search-holidays
  - shell (interactive Python REPL)
- LLM-optimized JSON output mode
- Environment-based configuration
- Rich terminal output formatting
- Cross-platform support (macOS, Linux, Windows)
- Secure credential management via environment variables

### Features
- Command-line interface for Odoo operations
- Direct model interaction via XML-RPC
- JSON output mode for automation
- Beautiful terminal tables with Rich library
- Interactive Python shell with pre-loaded Odoo client

---

## Links

- [Repository](https://github.com/RHHOLDING/odoo-cli)
- [Releases](https://github.com/RHHOLDING/odoo-cli/releases)
- [Issues](https://github.com/RHHOLDING/odoo-cli/issues)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

[1.4.1]: https://github.com/RHHOLDING/odoo-cli/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/RHHOLDING/odoo-cli/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/RHHOLDING/odoo-cli/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/RHHOLDING/odoo-cli/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/RHHOLDING/odoo-cli/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/RHHOLDING/odoo-cli/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/RHHOLDING/odoo-cli/releases/tag/v0.1.0
