# Research & Technical Decisions

## XML-RPC Client Extraction Strategy

**Decision**: Copy and adapt the MCP server's XML-RPC client code into a standalone module

**Rationale**:
- Ensures 100% compatibility with existing MCP server functionality
- Removes dependency on ODOO-MAIN monorepo structure
- Allows independent versioning and distribution via pip

**Alternatives considered**:
- Import from parent path: Rejected - breaks standalone installation
- Rewrite from scratch: Rejected - unnecessary duplication, risk of incompatibility
- Git submodule: Rejected - complicates pip installation from GitHub

**Implementation approach**:
1. Extract `/MCP/odoo/src/odoo_mcp/odoo_client.py` core functionality
2. Remove MCP-specific imports and logging
3. Adapt configuration loading for standalone use
4. Bundle as `odoo_cli/client.py` with same public API

## Click Framework Patterns for LLM-Optimized CLIs

**Decision**: Use Click's command groups with consistent parameter patterns

**Rationale**:
- Click provides excellent help text generation for LLM understanding
- Supports both human-readable and machine-parsable output
- Built-in support for environment variable fallbacks

**Best practices identified**:
```python
# Consistent pattern for all commands
@click.command()
@click.argument('model')
@click.option('--json', is_flag=True, help='Output pure JSON to stdout')
@click.option('--limit', type=int, default=20, help='Maximum records to return')
def search(model, json, limit):
    """Search records in the specified model."""
    pass
```

**LLM optimization techniques**:
- Always include descriptive help strings
- Use consistent option names across commands
- Provide sensible defaults for all options
- Support `--json` flag on every command

## Rich Library Integration with JSON Output Modes

**Decision**: Conditional rendering based on --json flag

**Rationale**:
- Clean separation of human vs machine output
- No mixing of formatted and raw data
- Predictable behavior for LLM parsing

**Implementation pattern**:
```python
def output_results(data, is_json=False, console=None):
    if is_json:
        # Pure JSON to stdout
        print(json.dumps(data))
    else:
        # Rich formatting to stderr/console
        table = Table(title="Results")
        console.print(table)
```

**Error handling approach**:
- JSON mode: Errors as JSON to stderr
- Normal mode: Rich formatted errors to stderr
- Exit codes always consistent regardless of mode

## Shell Enhancement Techniques

**Decision**: Use Python's `code` module with readline support

**Rationale**:
- Built-in Python, no extra dependencies
- Readline provides history and basic completion
- Can pre-populate namespace with utilities

**Implementation approach**:
```python
import code
import readline
import rlcompleter

# Configure readline
readline.parse_and_bind("tab: complete")
histfile = os.path.expanduser("~/.odoo_cli_history")

# Pre-populate namespace
namespace = {
    'client': odoo_client,
    'json': json,
    'pprint': pprint,
    'datetime': datetime,
}

# Start interactive shell with banner
banner = '''
Odoo CLI Shell - Examples:
  >>> client.search('res.partner', [('is_company', '=', True)], limit=5)
  >>> client.execute('ir.module.module', 'search_read', [], {'limit': 10})
  >>> pprint(client.get_fields('sale.order'))
'''

code.interact(banner=banner, local=namespace)
```

**History persistence**:
- Save to `~/.odoo_cli_history` on exit
- Load on startup if file exists
- Limit to last 1000 commands

## Configuration Loading Strategy

**Decision**: Three-tier configuration with clear precedence

**Rationale**:
- Flexibility for different deployment scenarios
- LLM can set via environment variables
- Human users can use .env files

**Loading order**:
1. Environment variables (highest priority)
2. `.env` file in current directory
3. `~/.odoo_config` file (lowest priority)

**Security considerations**:
- Document chmod 600 requirement in README
- Never log passwords
- Support password-less config (prompt if missing)

## JSON Streaming for Large Datasets

**Decision**: Use generator-based approach with pagination hints

**Rationale**:
- Prevents memory exhaustion on large result sets
- Allows progressive display in non-JSON mode
- Maintains compatibility with existing XML-RPC

**Implementation**:
```python
def search_paginated(model, domain, limit=100):
    offset = 0
    while True:
        batch = client.search_read(model, domain,
                                   limit=limit, offset=offset)
        if not batch:
            break
        yield batch
        offset += limit

        # In interactive mode, check if user wants more
        if not json_mode and offset >= 500:
            if not click.confirm(f"Fetched {offset} records. Continue?"):
                break
```

## Error Message Structure

**Decision**: Consistent error format for both modes

**Rationale**:
- Predictable for LLM parsing
- Actionable for human users
- Traceable for debugging

**Format**:
```json
{
  "error": "Connection failed",
  "type": "connection",
  "details": "Unable to reach https://...",
  "suggestion": "Check network and URL configuration"
}
```

**Exit codes mapping**:
- 0: Success
- 1: Connection/network error
- 2: Authentication error
- 3: Data/operation error

## Testing Strategy

**Decision**: Three-tier testing approach

**Rationale**:
- Contract tests ensure API compatibility
- Integration tests verify end-to-end flows
- Unit tests for utilities and formatting

**Test structure**:
```
tests/
├── contract/
│   ├── test_execute_contract.py    # Mock XML-RPC responses
│   ├── test_search_contract.py     # Validate schemas
│   └── test_json_output.py         # JSON structure tests
├── integration/
│   ├── test_cli_commands.py        # Click command tests
│   ├── test_config_loading.py      # Configuration tests
│   └── test_error_handling.py      # Error scenarios
└── unit/
    ├── test_utils.py                # Formatting utilities
    └── test_client_extraction.py    # Client compatibility
```

## Package Distribution Strategy

**Decision**: Standard Python package with git installation support

**Rationale**:
- `pip install git+https://...` works out of the box
- PyPI publication possible later
- Development install with `pip install -e .`

**Package files**:
- `pyproject.toml`: Modern Python packaging
- `setup.py`: Only if needed for editable installs
- `MANIFEST.in`: Include non-Python files if needed

---

## Summary of Key Decisions

1. **Standalone architecture**: Bundle all dependencies for true independence
2. **LLM-first design**: JSON mode, consistent patterns, clear help text
3. **Security pragmatism**: Simple .env approach with documented risks
4. **Performance awareness**: 500-record threshold, pagination support
5. **Testing discipline**: Contract-first testing for reliability
6. **Standard Python packaging**: Easy installation via pip and git

All research items resolved. Ready for Phase 1 design.