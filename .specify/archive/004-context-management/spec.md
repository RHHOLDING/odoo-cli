# Spec 004: Context Management (CRITICAL)

**Status:** Ready for Implementation
**Priority:** P0 - CRITICAL
**Effort:** 2-3 days
**Impact:** Fixes multi-company, translations, archived records

---

## Problem Statement

**WE SEND NO CONTEXT TO ODOO!**

This is a critical bug that breaks:
- ❌ **Multi-company operations** (missing `allowed_company_ids`)
- ❌ **Translations** (missing `lang`)
- ❌ **Timezone handling** (missing `tz`)
- ❌ **Archived record access** (missing `active_test`)
- ❌ **Default values** (missing `default_*` keys)

**All existing commands are affected!**

---

## Clarifications

### Session 2025-11-21

- Q: When Odoo rejects an invalid context key (e.g., `--context foo=bar`), what should the CLI do? → A: Pass to Odoo, let Odoo reject it (lazy validation) - CLI only shows Odoo's error message
- Q: Should context passing be logged for debugging/troubleshooting? → A: Log only non-default context - Only log when user explicitly provides `--context` flags
- Q: When both global context (`~/.odoo-cli/context.json`) and command-line `--context` flags specify the same key, which wins? → A: Command-line overrides global (explicit beats implicit)

---

## What is Odoo Context?

Context is a dictionary passed to every Odoo operation that controls behavior:

```python
context = {
    'lang': 'de_DE',              # User language
    'tz': 'Europe/Berlin',        # Timezone
    'uid': 2,                     # User ID
    'active_test': False,         # Include archived records
    'allowed_company_ids': [1,2], # Multi-company filter
    'default_type': 'company',    # Default field values
}
```

### Real-World Impact

**Without context (current state):**
```bash
odoo search product.product '[]'
# Returns only active products
# Always in en_US
# Only company #1 visible
```

**With context (fixed):**
```bash
odoo search product.product '[]' --context active_test=false
# Returns ALL products (including archived)

odoo search product.product '[]' --context lang=de_DE
# Returns German translations

odoo search product.product '[]' --context allowed_company_ids=[1,2,3]
# Returns products from multiple companies
```

---

## Solution Design

### Phase 1: Client Implementation (1 day)

**Modify `client.py` to accept context:**

```python
# odoo_cli/client.py

def _execute(self, model: str, method: str, *args, context: Optional[Dict] = None, **kwargs):
    """Execute method with optional context."""
    if context:
        # Merge with existing context (if any)
        kwargs['context'] = {**kwargs.get('context', {}), **context}

    return self._jsonrpc_call('execute_kw', {
        'model': model,
        'method': method,
        'args': args,
        'kwargs': kwargs
    })
```

**Update all helper methods:**
```python
def search(self, model: str, domain: List, context: Optional[Dict] = None, **kwargs):
    return self._execute(model, 'search', domain, context=context, **kwargs)

def read(self, model: str, ids: List[int], fields: List[str] = None,
         context: Optional[Dict] = None):
    return self._execute(model, 'read', ids, fields=fields, context=context)

def create(self, model: str, values: Dict, context: Optional[Dict] = None):
    return self._execute(model, 'create', [values], context=context)

# ... same for update, delete, search_read, etc.
```

---

### Phase 2: CLI Flags (1 day)

**Add `--context` flag to ALL commands:**

```python
# odoo_cli/commands/search.py

@click.command('search')
@click.argument('model')
@click.argument('domain', default='[]')
@click.option('--context', multiple=True,
              help='Context key=value pairs (e.g., active_test=false)')
@click.option('--json', 'json_mode', is_flag=True)
def search_cmd(model, domain, context, json_mode):
    client = get_odoo_client()

    # Parse context flags
    ctx = parse_context_flags(context) if context else None

    records = client.search(model, parse_domain(domain), context=ctx)

    if json_mode:
        console.print_json({"success": True, "data": records})
    else:
        console.print(records)
```

**Context Parser:**
```python
# odoo_cli/utils/context_parser.py

def parse_context_flags(context_list: List[str]) -> Dict[str, Any]:
    """Parse --context flags into dictionary.

    Uses lazy validation: invalid keys are passed to Odoo for validation.
    Only format (key=value) is checked by CLI.

    Examples:
        ['active_test=false'] → {'active_test': False}
        ['lang=de_DE', 'tz=Europe/Berlin'] → {'lang': 'de_DE', 'tz': 'Europe/Berlin'}
        ['allowed_company_ids=[1,2,3]'] → {'allowed_company_ids': [1, 2, 3]}
    """
    context = {}
    for item in context_list:
        if '=' not in item:
            raise ValueError(f"Invalid context format: {item}. Expected key=value")

        key, value = item.split('=', 1)
        context[key] = _parse_context_value(value)

    # Note: Context key validation is delegated to Odoo (lazy validation)
    # Invalid keys will be rejected by Odoo with appropriate error messages
    return context

def _parse_context_value(value: str) -> Any:
    """Auto-detect and parse context value type."""
    # Boolean
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'

    # List [1,2,3]
    if value.startswith('[') and value.endswith(']'):
        return json.loads(value)

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # String (default)
    return value
```

---

### Phase 3: Global Context Config (Optional - 0.5 days)

**Store default context in config:**

```bash
# Set global context
odoo config set-context lang=de_DE tz=Europe/Berlin

# Show current context
odoo config show-context
# Output:
# Global Context:
#   lang: de_DE
#   tz: Europe/Berlin
#   active_test: true

# Clear context
odoo config clear-context
```

**Implementation:**
```python
# odoo_cli/config.py

import json
from pathlib import Path

CONFIG_DIR = Path.home() / '.odoo-cli'
CONTEXT_FILE = CONFIG_DIR / 'context.json'

def save_global_context(context: Dict[str, Any]):
    """Save global context to ~/.odoo-cli/context.json"""
    CONFIG_DIR.mkdir(exist_ok=True)
    CONTEXT_FILE.write_text(json.dumps(context, indent=2))

def load_global_context() -> Optional[Dict[str, Any]]:
    """Load global context if exists."""
    if CONTEXT_FILE.exists():
        return json.loads(CONTEXT_FILE.read_text())
    return None

def merge_context(global_ctx: Dict, command_ctx: Dict) -> Dict:
    """Merge contexts with command-line override priority.

    Command-line flags take precedence over global config (explicit beats implicit).
    Example: Global has lang=de_DE, command has --context lang=en_US → Result: en_US
    """
    return {**global_ctx, **command_ctx}
```

---

## CLI Examples

### Per-Command Context

```bash
# Include archived products
odoo search product.product '[]' --context active_test=false

# German translations
odoo search product.product '[]' --context lang=de_DE

# Multi-company
odoo search sale.order '[]' --context allowed_company_ids=[1,2,3]

# Set defaults for creation
odoo create res.partner -f name="Test" --context default_type=company

# Multiple context flags
odoo search res.partner '[]' \
  --context lang=de_DE \
  --context tz=Europe/Berlin \
  --context active_test=false
```

### Global Context (Phase 3)

```bash
# Set once
odoo config set-context lang=de_DE tz=Europe/Berlin

# All subsequent commands use global context
odoo search product.product '[]'  # Uses de_DE lang

# Override per-command
odoo search product.product '[]' --context lang=en_US  # Overrides to en_US
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_context.py

def test_context_passed_to_execute():
    client = OdooClient(...)
    context = {'active_test': False}

    with patch.object(client, '_jsonrpc_call') as mock_call:
        client.search('product.product', [], context=context)

        # Verify context in kwargs
        call_args = mock_call.call_args[1]
        assert call_args['kwargs']['context'] == {'active_test': False}

def test_context_parser():
    result = parse_context_flags(['active_test=false', 'lang=de_DE'])
    assert result == {'active_test': False, 'lang': 'de_DE'}

    result = parse_context_flags(['allowed_company_ids=[1,2,3]'])
    assert result == {'allowed_company_ids': [1, 2, 3]}
```

### Integration Tests

```bash
# Test archived record access
odoo create product.product -f name="Test Product" -f active=false
odoo search product.product '[["name","=","Test Product"]]'
# Should NOT find it (active_test=true by default)

odoo search product.product '[["name","=","Test Product"]]' --context active_test=false
# Should find it!
```

---

## Observability

**Logging Strategy:** Log only non-default (user-provided) context

```python
# odoo_cli/commands/search.py

def search_cmd(model, domain, context, json_mode):
    client = get_odoo_client()

    # Parse context
    ctx = parse_context_flags(context) if context else None

    # Log only if user explicitly provided context
    if ctx:
        _logger.debug(f"Applying user context: {ctx}")

    records = client.search(model, parse_domain(domain), context=ctx)
```

**Rationale:**
- Minimal log noise (no logging when context not used)
- Visible in debug mode: `ODOO_DEBUG=1 odoo search ...`
- Helps troubleshoot context-related issues
- Error messages from Odoo will include context validation failures

---

## Migration Guide

**NO BREAKING CHANGES!**

- Context is optional - all existing commands work unchanged
- `--context` flag is additive
- Global config is opt-in

**Backward Compatible:**
```bash
# Old way (still works)
odoo search res.partner '[]'

# New way (with context)
odoo search res.partner '[]' --context active_test=false
```

---

## Performance Impact

**Minimal overhead:**
- Context is just a dict passed to Odoo
- No additional HTTP calls
- Negligible serialization cost

---

## Security Considerations

**Context cannot bypass security!**

- Odoo validates all context keys
- Access rights still enforced
- Record rules still apply
- Cannot escalate privileges via context

**Example:**
```bash
# This will still fail if user lacks permission!
odoo update sale.order 123 -f state="done" --context uid=1
# Odoo ignores uid override attempts
```

---

## Dependencies

**None!** This is a standalone feature.

---

## Blocks

- Multi-company features
- Translation support
- Archived record access
- Default value handling

**This must be implemented FIRST before other features!**

---

## Implementation Checklist

### Phase 1: Client (1 day)
- [ ] Modify `_execute()` to accept `context` parameter
- [ ] Update all helper methods (search, read, create, update, delete)
- [ ] Add unit tests for context passing
- [ ] Verify context merging logic

### Phase 2: CLI Flags (1 day)
- [ ] Add `--context` flag to all commands:
  - [ ] search
  - [ ] read
  - [ ] create
  - [ ] update
  - [ ] delete
  - [ ] search-read
  - [ ] execute
- [ ] Implement `parse_context_flags()`
- [ ] Implement `_parse_context_value()` (type inference)
- [ ] Add CLI integration tests
- [ ] Update command help text

### Phase 3: Global Config (0.5 days - OPTIONAL)
- [ ] Create `config.py` module
- [ ] Implement `save_global_context()`
- [ ] Implement `load_global_context()`
- [ ] Add `config set-context` command
- [ ] Add `config show-context` command
- [ ] Add `config clear-context` command
- [ ] Document global context in README

### Documentation (0.5 days)
- [ ] Update README.md with context examples
- [ ] Add context section to `docs/quickstart.md`
- [ ] Update CHANGELOG.md for v1.3.0
- [ ] Add context patterns to LLM help

---

## Success Metrics

✅ **All existing commands accept `--context` flag**
✅ **Multi-company operations work correctly**
✅ **Archived records accessible with `active_test=false`**
✅ **Translations work with `lang=*`**
✅ **Zero breaking changes**
✅ **80%+ test coverage**

---

## Release Plan

**Target:** v1.3.0
**Timeline:** 2-3 days
**Breaking Changes:** None

**Versioning:**
- MINOR version bump (1.2.0 → 1.3.0)
- New feature, backward compatible
