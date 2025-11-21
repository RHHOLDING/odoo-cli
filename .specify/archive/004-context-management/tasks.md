# Implementation Tasks: Context Management

**Spec:** 004 - Context Management
**Target Version:** v1.3.0
**Estimated Time:** 2-3 days

---

## Phase 1: Client Implementation (Day 1)

### Task 1.1: Modify `_execute()` method
**File:** `odoo_cli/client.py`
**Effort:** 30 minutes

```python
def _execute(self, model: str, method: str, *args, context: Optional[Dict] = None, **kwargs):
    """Execute method with optional context parameter."""
    if context:
        # Merge with existing context (command context overrides)
        existing_context = kwargs.get('context', {})
        kwargs['context'] = {**existing_context, **context}

    return self._jsonrpc_call('execute_kw', {
        'model': model,
        'method': method,
        'args': args,
        'kwargs': kwargs
    })
```

**Test:**
```python
# tests/unit/test_client_context.py
def test_execute_with_context():
    client = OdooClient(...)
    context = {'active_test': False}

    with patch.object(client, '_jsonrpc_call') as mock:
        client._execute('product.product', 'search', [], context=context)
        assert mock.call_args[1]['kwargs']['context'] == {'active_test': False}
```

---

### Task 1.2: Update `search()` method
**File:** `odoo_cli/client.py`
**Effort:** 15 minutes

```python
def search(self, model: str, domain: List, context: Optional[Dict] = None,
           offset: int = 0, limit: Optional[int] = None,
           order: Optional[str] = None) -> List[int]:
    """Search with optional context."""
    kwargs = {'offset': offset}
    if limit is not None:
        kwargs['limit'] = limit
    if order:
        kwargs['order'] = order

    return self._execute(model, 'search', domain, context=context, **kwargs)
```

---

### Task 1.3: Update `read()` method
**File:** `odoo_cli/client.py`
**Effort:** 15 minutes

```python
def read(self, model: str, ids: List[int], fields: Optional[List[str]] = None,
         context: Optional[Dict] = None) -> List[Dict]:
    """Read with optional context."""
    args = [ids]
    kwargs = {}
    if fields:
        kwargs['fields'] = fields

    return self._execute(model, 'read', *args, context=context, **kwargs)
```

---

### Task 1.4: Update `create()` method
**File:** `odoo_cli/client.py`
**Effort:** 15 minutes

```python
def create(self, model: str, values: Dict, context: Optional[Dict] = None) -> int:
    """Create with optional context."""
    return self._execute(model, 'create', [values], context=context)
```

---

### Task 1.5: Update `update()` method
**File:** `odoo_cli/client.py`
**Effort:** 15 minutes

```python
def update(self, model: str, ids: List[int], values: Dict,
           context: Optional[Dict] = None) -> bool:
    """Update (write) with optional context."""
    return self._execute(model, 'write', [ids, values], context=context)
```

---

### Task 1.6: Update `delete()` method
**File:** `odoo_cli/client.py`
**Effort:** 15 minutes

```python
def delete(self, model: str, ids: List[int], context: Optional[Dict] = None) -> bool:
    """Delete (unlink) with optional context."""
    return self._execute(model, 'unlink', [ids], context=context)
```

---

### Task 1.7: Update `search_read()` method
**File:** `odoo_cli/client.py`
**Effort:** 15 minutes

```python
def search_read(self, model: str, domain: List = None,
                fields: Optional[List[str]] = None,
                context: Optional[Dict] = None,
                offset: int = 0, limit: Optional[int] = None,
                order: Optional[str] = None) -> List[Dict]:
    """Search and read with optional context."""
    domain = domain or []
    kwargs = {'offset': offset}
    if limit is not None:
        kwargs['limit'] = limit
    if order:
        kwargs['order'] = order
    if fields:
        kwargs['fields'] = fields

    return self._execute(model, 'search_read', [domain], context=context, **kwargs)
```

---

### Task 1.8: Write Unit Tests
**File:** `tests/unit/test_client_context.py` (NEW FILE)
**Effort:** 1 hour

```python
import pytest
from unittest.mock import patch, MagicMock
from odoo_cli.client import OdooClient

@pytest.fixture
def mock_client():
    client = OdooClient(
        url='http://test.odoo.com',
        db='test',
        username='admin',
        password='admin'
    )
    client.uid = 2  # Mock authenticated
    return client

def test_search_with_context(mock_client):
    """Test context passed to search."""
    context = {'active_test': False}

    with patch.object(mock_client, '_jsonrpc_call') as mock_call:
        mock_call.return_value = [1, 2, 3]
        result = mock_client.search('product.product', [], context=context)

        assert result == [1, 2, 3]
        call_kwargs = mock_call.call_args[1]['kwargs']
        assert call_kwargs['context'] == {'active_test': False}

def test_read_with_context(mock_client):
    """Test context passed to read."""
    context = {'lang': 'de_DE'}

    with patch.object(mock_client, '_jsonrpc_call') as mock_call:
        mock_call.return_value = [{'id': 1, 'name': 'Test'}]
        result = mock_client.read('res.partner', [1], context=context)

        call_kwargs = mock_call.call_args[1]['kwargs']
        assert call_kwargs['context'] == {'lang': 'de_DE'}

def test_create_with_context(mock_client):
    """Test context passed to create."""
    context = {'default_type': 'company'}

    with patch.object(mock_client, '_jsonrpc_call') as mock_call:
        mock_call.return_value = 42
        result = mock_client.create('res.partner', {'name': 'Test'}, context=context)

        assert result == 42
        call_kwargs = mock_call.call_args[1]['kwargs']
        assert call_kwargs['context'] == {'default_type': 'company'}

def test_update_with_context(mock_client):
    """Test context passed to update."""
    context = {'tz': 'Europe/Berlin'}

    with patch.object(mock_client, '_jsonrpc_call') as mock_call:
        mock_call.return_value = True
        result = mock_client.update('res.partner', [1], {'name': 'Updated'}, context=context)

        assert result is True
        call_kwargs = mock_call.call_args[1]['kwargs']
        assert call_kwargs['context'] == {'tz': 'Europe/Berlin'}

def test_context_merging(mock_client):
    """Test context merging behavior."""
    context = {'active_test': False}

    with patch.object(mock_client, '_jsonrpc_call') as mock_call:
        # Pass context via kwargs AND context parameter
        mock_client._execute('test.model', 'search', [],
                            context=context,
                            context={'lang': 'de_DE'})

        # context parameter should override
        call_kwargs = mock_call.call_args[1]['kwargs']
        assert call_kwargs['context'] == {'lang': 'de_DE', 'active_test': False}
```

---

## Phase 2: CLI Implementation (Day 2)

### Task 2.1: Create Context Parser
**File:** `odoo_cli/utils/context_parser.py` (NEW FILE)
**Effort:** 1 hour

```python
"""Context flag parser with type inference."""
import json
from typing import Any, Dict, List

def parse_context_flags(context_list: List[str]) -> Dict[str, Any]:
    """Parse --context flags into dictionary.

    Examples:
        ['active_test=false'] → {'active_test': False}
        ['lang=de_DE', 'tz=Europe/Berlin'] → {'lang': 'de_DE', 'tz': 'Europe/Berlin'}
        ['allowed_company_ids=[1,2,3]'] → {'allowed_company_ids': [1, 2, 3]}

    Args:
        context_list: List of key=value strings

    Returns:
        Dictionary with parsed context

    Raises:
        ValueError: If format invalid
    """
    context = {}

    for item in context_list:
        if '=' not in item:
            raise ValueError(
                f"Invalid context format: '{item}'. "
                f"Expected format: key=value (e.g., active_test=false)"
            )

        key, value = item.split('=', 1)
        key = key.strip()

        if not key:
            raise ValueError(f"Empty context key in: '{item}'")

        context[key] = _parse_context_value(value.strip())

    return context

def _parse_context_value(value: str) -> Any:
    """Auto-detect and parse context value type.

    Supports:
    - Boolean: true/false (case-insensitive)
    - List: [1,2,3]
    - Integer: 42
    - String: "anything else"
    """
    # Boolean
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'

    # List/Dict (JSON)
    if (value.startswith('[') and value.endswith(']')) or \
       (value.startswith('{') and value.endswith('}')):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in context value: {value}. Error: {e}")

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # String (default)
    return value
```

**Tests:**
```python
# tests/unit/test_context_parser.py

def test_parse_boolean():
    result = parse_context_flags(['active_test=false'])
    assert result == {'active_test': False}

    result = parse_context_flags(['active=TRUE'])
    assert result == {'active': True}

def test_parse_list():
    result = parse_context_flags(['allowed_company_ids=[1,2,3]'])
    assert result == {'allowed_company_ids': [1, 2, 3]}

def test_parse_integer():
    result = parse_context_flags(['uid=42'])
    assert result == {'uid': 42}

def test_parse_string():
    result = parse_context_flags(['lang=de_DE'])
    assert result == {'lang': 'de_DE'}

def test_multiple_flags():
    result = parse_context_flags([
        'active_test=false',
        'lang=de_DE',
        'allowed_company_ids=[1,2]'
    ])
    assert result == {
        'active_test': False,
        'lang': 'de_DE',
        'allowed_company_ids': [1, 2]
    }

def test_invalid_format():
    with pytest.raises(ValueError, match="Invalid context format"):
        parse_context_flags(['invalid'])

def test_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_context_flags(['ids=[1,2,'])
```

---

### Task 2.2: Update `search` command
**File:** `odoo_cli/commands/search.py`
**Effort:** 30 minutes

```python
@click.command('search')
@click.argument('model')
@click.argument('domain', default='[]')
@click.option('--limit', type=int, help='Maximum records to return')
@click.option('--offset', type=int, default=0, help='Number of records to skip')
@click.option('--context', multiple=True,
              help='Context key=value (e.g., --context active_test=false)')
@click.option('--json', 'json_mode', is_flag=True, help='Output JSON')
def search(model, domain, limit, offset, context, json_mode):
    """Search for record IDs matching domain."""
    try:
        client = get_odoo_client()

        # Parse context
        ctx = parse_context_flags(context) if context else None

        # Parse domain
        domain_list = parse_domain(domain)

        # Search
        ids = client.search(model, domain_list, context=ctx,
                          offset=offset, limit=limit)

        if json_mode:
            console.print_json({"success": True, "data": ids, "count": len(ids)})
        else:
            console.print(f"Found {len(ids)} records: {ids}")

    except Exception as e:
        handle_error(e, json_mode)
        sys.exit(3)
```

---

### Task 2.3: Update ALL other commands
**Files:** All command files in `odoo_cli/commands/`
**Effort:** 2 hours

Add `--context` option to:
- [ ] `read.py`
- [ ] `create.py`
- [ ] `update.py`
- [ ] `delete.py`
- [ ] `execute.py`
- [ ] `create_bulk.py`
- [ ] `update_bulk.py`
- [ ] `aggregate.py`
- [ ] `search_employee.py`
- [ ] `search_holidays.py`

**Pattern (same for all):**
```python
@click.option('--context', multiple=True,
              help='Context key=value (e.g., --context active_test=false)')

def command_func(..., context, ...):
    ctx = parse_context_flags(context) if context else None
    client.method(model, ..., context=ctx)
```

---

### Task 2.4: Integration Tests
**File:** `tests/integration/test_context_cli.py` (NEW FILE)
**Effort:** 1 hour

```python
"""Integration tests for context support."""
import subprocess
import json

def run_cli(*args):
    """Run CLI and return result."""
    result = subprocess.run(
        ['odoo'] + list(args),
        capture_output=True,
        text=True
    )
    return result

def test_search_with_context():
    """Test search with context flag."""
    result = run_cli(
        'search', 'product.product', '[]',
        '--context', 'active_test=false',
        '--json'
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data['success'] is True

def test_create_with_context():
    """Test create with default context."""
    result = run_cli(
        'create', 'res.partner',
        '-f', 'name=Test Company',
        '--context', 'default_type=company',
        '--json'
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data['success'] is True

def test_multiple_context_flags():
    """Test multiple context flags."""
    result = run_cli(
        'search', 'res.partner', '[]',
        '--context', 'lang=de_DE',
        '--context', 'tz=Europe/Berlin',
        '--context', 'active_test=false',
        '--json'
    )
    assert result.returncode == 0
```

---

## Phase 3: Documentation (Day 3 Morning)

### Task 3.1: Update README.md
**File:** `README.md`
**Effort:** 30 minutes

Add Context section after "Global Options":

```markdown
### Context Management

Control Odoo behavior with context parameters:

```bash
# Include archived records
odoo search product.product '[]' --context active_test=false

# Use German translations
odoo search product.product '[]' --context lang=de_DE

# Multi-company operations
odoo search sale.order '[]' --context allowed_company_ids=[1,2,3]

# Set default values
odoo create res.partner -f name="Test" --context default_type=company

# Multiple context flags
odoo search res.partner '[]' \
  --context lang=de_DE \
  --context tz=Europe/Berlin
```

**Common Context Keys:**

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `active_test` | bool | Include archived records | `active_test=false` |
| `lang` | string | User language | `lang=de_DE` |
| `tz` | string | Timezone | `tz=Europe/Berlin` |
| `allowed_company_ids` | list | Multi-company filter | `allowed_company_ids=[1,2]` |
| `default_*` | any | Default field values | `default_type=company` |
```

---

### Task 3.2: Update CHANGELOG.md
**File:** `CHANGELOG.md`
**Effort:** 15 minutes

```markdown
## [1.3.0] - 2025-11-XX

### Added
- **Context Management** - All commands now support `--context` flag
  - Multi-company operations with `allowed_company_ids`
  - Translations with `lang` parameter
  - Archived record access with `active_test=false`
  - Default values with `default_*` keys
- Auto type inference for context values (bool, int, list, string)

### Fixed
- Multi-company operations now work correctly
- Translations now accessible via context
- Archived records can be queried

### Breaking Changes
- None (backward compatible)
```

---

### Task 3.3: Update Command Help Text
**Effort:** 30 minutes

Update all command docstrings to mention context:

```python
@click.command('search')
def search(...):
    """Search for record IDs matching domain.

    Context can be used to control behavior:
      --context active_test=false  (include archived)
      --context lang=de_DE         (German translations)
      --context allowed_company_ids=[1,2]  (multi-company)

    Examples:
      odoo search product.product '[]' --context active_test=false
      odoo search res.partner '[]' --context lang=de_DE
    """
```

---

## Testing Checklist

### Unit Tests
- [ ] `test_client_context.py` - All client methods accept context
- [ ] `test_context_parser.py` - Parser handles all types correctly
- [ ] Context merging logic works
- [ ] Invalid context raises proper errors

### Integration Tests
- [ ] All commands accept `--context` flag
- [ ] Context passed to Odoo correctly
- [ ] Multiple context flags work together
- [ ] Invalid context shows helpful error

### Manual Testing
- [ ] Multi-company: `--context allowed_company_ids=[1,2]`
- [ ] Archived records: `--context active_test=false`
- [ ] Translations: `--context lang=de_DE`
- [ ] Defaults: `--context default_type=company`
- [ ] Test with real Odoo instance

---

## Deployment

### Pre-Release
- [ ] All tests passing (80%+ coverage)
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped to 1.3.0

### Release
- [ ] Create release branch `release/v1.3.0`
- [ ] Tag: `git tag -a v1.3.0 -m "Add context management"`
- [ ] Push: `git push origin v1.3.0`
- [ ] GitHub release with notes

### Post-Release
- [ ] Monitor for issues
- [ ] Update project board
- [ ] Announce in relevant channels

---

## Time Estimate

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1: Client | 1.1-1.8 | 1 day |
| Phase 2: CLI | 2.1-2.4 | 1 day |
| Phase 3: Docs | 3.1-3.3 | 0.5 days |
| **Total** | | **2.5 days** |

---

## Success Criteria

✅ All commands support `--context` flag
✅ Context parser handles bool, int, list, string
✅ Multi-company operations work
✅ Archived records accessible
✅ Translations work
✅ Zero breaking changes
✅ 80%+ test coverage
✅ Documentation complete

---

**Ready to implement!** 🚀
