# Idea: Python SDK/Library for odoo-cli

## Problem

Currently, odoo-cli is **CLI-only**. Developers who want to use it in Python scripts must:
1. Use `subprocess.run()` to call CLI commands
2. Parse JSON output manually
3. OR fall back to raw `xmlrpc.client` (boilerplate-heavy)

```python
# What developers currently must do (boilerplate-heavy)
import xmlrpc.client
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
uid = common.authenticate(db, username, password, {})
results = models.execute_kw(db, uid, password, 'stock.picking', 'search_read', ...)
```

**Pain Points:**
- No Python API - forces raw xmlrpc.client usage
- No connection pooling/caching
- No automatic `.env` loading
- Manual error handling
- No ORM-style convenience

**Result:** Developers avoid the tool for automation/scripts. They use xmlrpc.client directly.

---

## Solution: Python SDK

Provide a clean Python library:

```python
from odoo_cli.client import OdooClient

# Auto-load from .env
client = OdooClient.from_env()

# Simple CRUD
pickings = client.search('stock.picking',
    domain=[('state', '!=', 'cancel')],
    fields=['name', 'partner_id', 'create_date'])

# Create
new_order = client.create('sale.order', {
    'partner_id': 43150,
    'date_order': '2025-11-21'
})

# Update
client.update('sale.order', new_order['id'], {'state': 'sent'})

# Delete
client.delete('stock.picking', 803996)

# Get single record
picking = client.get('stock.picking', 803996)
print(picking)  # {'id': 803996, 'name': 'DO-2025-001234', ...}
```

---

## Key Features

### 1. Auto-Loading from .env
```python
client = OdooClient.from_env()
# Reads: ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
```

### 2. Connection Pooling
```python
# Connections cached - no re-auth on every call
client = OdooClient.from_env()
for i in range(100):
    results = client.search(...)  # Reuses connection
```

### 3. Context Management
```python
# With context handling
with client.session() as session:
    pickings = session.search('stock.picking', ...)
    orders = session.search('sale.order', ...)
    # Single auth for multiple operations
```

### 4. Field Discovery
```python
# Get field metadata
fields = client.get_fields('stock.picking')
for field in fields:
    print(f"{field['name']}: {field['type']}")

# Get specific field
email_field = client.get_field('res.partner', 'email')
```

### 5. Batch Operations
```python
# Bulk create
client.create_bulk('stock.picking', [
    {'name': 'DO-001', ...},
    {'name': 'DO-002', ...},
])

# With pagination
all_pickings = client.search_all('stock.picking',
    domain=[],
    batch_size=100)  # Auto-paginate, fetch all
```

### 6. Error Handling
```python
try:
    client.search('stock.picking', domain=[...])
except OdooFieldError as e:
    print(f"Field not found: {e.field_name}")
    print(f"Available fields: {e.available_fields}")
except OdooAuthError as e:
    print("Authentication failed")
```

---

## Implementation Plan

### Phase 1: Core SDK (4-6 hours)
- `OdooClient` class with CRUD operations
- `.from_env()` method
- Basic error wrapping
- Connection pooling

### Phase 2: Advanced Features (3-4 hours)
- `get_fields()` and field discovery
- `search_all()` with pagination
- Batch operations (create_bulk, update_bulk)
- Session context manager

### Phase 3: Future Enhancements (later)
- Relation navigation: `picking.sale_id.partner_id`
- ORM-style query builder
- Transaction support
- Caching layer

---

## File Structure

```
odoo_cli/
├── client.py           # Main OdooClient class
├── exceptions.py       # Custom exceptions (OdooFieldError, OdooAuthError, etc)
├── connection.py       # Connection pooling/caching
├── builders.py         # Query builder (future)
└── models/             # Model-specific helpers (future)
    └── stock.py

tests/
├── unit/
│   └── test_client.py
├── integration/
│   └── test_client_integration.py
```

---

## Usage Examples

### Example 1: Simple Query
```python
from odoo_cli.client import OdooClient

client = OdooClient.from_env()
pickings = client.search('stock.picking',
    domain=[('state', '!=', 'cancel')],
    limit=20)
print(f"Found {len(pickings)} pickings")
```

### Example 2: Automation Script
```python
from odoo_cli.client import OdooClient

client = OdooClient.from_env()

# Find all pending pickings from Plentymarkets
pending = client.search('stock.picking',
    domain=[
        ('origin', '=', 'Plenty_162552'),
        ('state', '=', 'assigned')
    ])

# Process each
for picking_id in pending:
    picking = client.get('stock.picking', picking_id)

    # Do something
    if picking['weight'] > 30:
        client.update('stock.picking', picking_id, {
            'carrier_id': 5  # UPS for heavy items
        })
```

### Example 3: Batch Operation
```python
from odoo_cli.client import OdooClient

client = OdooClient.from_env()

# Create multiple orders
orders_data = [
    {'partner_id': 1, 'amount_total': 500},
    {'partner_id': 2, 'amount_total': 1200},
    {'partner_id': 3, 'amount_total': 300},
]

new_ids = client.create_bulk('sale.order', orders_data)
print(f"Created {len(new_ids)} orders: {new_ids}")
```

---

## Benefits

### For Users
- ✅ Clean Python API instead of xmlrpc boilerplate
- ✅ Automatic `.env` loading
- ✅ Built-in error handling with suggestions
- ✅ Connection pooling (faster automation)
- ✅ Batch operations with progress tracking

### For the CLI Tool
- ✅ Expands use cases beyond CLI to automation/scripts
- ✅ Can reuse CLI logic (validation, error handling)
- ✅ Increases adoption among developers
- ✅ Better for CI/CD pipelines

---

## Priority

**Impact:** Very High - Unlocks scripting/automation use cases
**Effort:** Medium (6-10 hours total)
**Complexity:** Medium
**Dependencies:** Existing CLI infrastructure

**Recommendation:** P1 for v2.0.0
- Release as major version (API change)
- Maintain backward compatibility with CLI
- Can deprecate raw xmlrpc.client usage

---

## Backward Compatibility

✅ **CLI remains unchanged** - SDK is additive
✅ **Existing behavior preserved** - Same behavior, just Python API
✅ **Gradual adoption** - Users can use CLI + SDK interchangeably

```python
# CLI usage unchanged
subprocess.run(['odoo-cli', 'search', 'stock.picking', ...])

# OR use SDK
from odoo_cli.client import OdooClient
client = OdooClient.from_env()
client.search('stock.picking', ...)
```

---

## Related Features

- **IDEA-02:** Read-only mode (enforce in SDK)
- **IDEA-03:** Batch operations (implements this)
- **IDEA-04:** Session management (implements this)
- **IDEA-10:** Safe mode enforcement (SDK can respect this)

---

**Status:** Proposed for v2.0.0
**Next Action:** Define SDK interface, create core OdooClient class
