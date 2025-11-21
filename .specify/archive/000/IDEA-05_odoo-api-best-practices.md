# Idea: Odoo API Best Practices & Missing Methods

> **STATUS:** ✅ **Quick Wins Bundle COMPLETED** (v1.4.0)
> **COMPLETED:** search-count, name-get, name-search, fields_get attributes
> **BRANCH:** `005-quick-wins-bundle`
> **LAST UPDATED:** 2025-11-21

## Problem
Current CLI implementation doesn't leverage all available Odoo RPC methods and patterns, missing optimization opportunities and functionality.

## Missing Odoo RPC Methods

### 1. name_get() - Display Names
**Purpose:** Get human-readable display names for records (not just IDs)

```python
# Instead of just IDs
[1, 2, 3]

# Get display names
Product.name_get([25])
# → [[25, '[FURN_8220] Four Person Desk']]
```

**CLI Proposal:**
```bash
# Current
odoo read res.partner 1 --fields id,name
# Output: {"id": 1, "name": "Azure Interior"}

# New: name_get command
odoo name-get res.partner 1,2,3
# Output: [[1, "Azure Interior"], [2, "Deco Addict"], [3, "Gemini Furniture"]]
```

**Use Cases:**
- Quick ID → Name lookups
- Dropdown/select options for LLMs
- Validation before operations

---

### 2. name_search() - Fuzzy Name Search
**Purpose:** Search records by name with fuzzy matching

```python
# Find partners whose name contains "azure"
Partner.name_search('azure', operator='ilike', limit=10)
# → [[1, 'Azure Interior'], [45, 'Azure Cloud Services']]
```

**CLI Proposal:**
```bash
odoo name-search res.partner "azure" --limit 10
# Output: [[1, "Azure Interior"], [45, "Azure Cloud Services"]]

# With domain filter
odoo name-search res.partner "azure" --domain '[["customer_rank",">",0]]'
```

**Better than search + read:**
```bash
# Old way (2 calls):
ids=$(odoo search res.partner '[["name","ilike","azure"]]')
odoo read res.partner $ids --fields name

# New way (1 call):
odoo name-search res.partner "azure"
```

---

### 3. search_count() - Count Without Fetching
**Purpose:** Get record count without retrieving IDs

**Currently:** We use search then count the IDs
```bash
odoo search res.partner '[]' --json | jq 'length'
# Fetches ALL IDs, then counts (slow for large datasets)
```

**Better:**
```bash
odoo search-count res.partner '[]'
# Output: 1247
# No IDs transferred, much faster!
```

**Already implemented in client.py!** (Line 349)
```python
def search_count(self, model: str, domain: List = None) -> int:
    domain = domain or []
    return self._execute(model, 'search_count', domain)
```

**Just needs CLI command wrapper!**

---

### 4. fields_get() with Attribute Filtering
**Purpose:** Get field metadata with selective attributes

**Current (get ALL attributes):**
```python
client.fields_get('res.partner')  # Returns EVERYTHING
```

**Optimized (only what you need):**
```python
client.fields_get('res.partner', attributes=['type', 'required', 'readonly'])
# Much smaller response!
```

**Already partially implemented!** (Line 363)
```python
def fields_get(self, model: str, allfields: Optional[List[str]] = None):
    kwargs = {}
    if allfields is not None:
        kwargs['allfields'] = allfields  # ← Filters FIELDS
```

**Missing:** `attributes` parameter to filter field ATTRIBUTES

**Proposed enhancement:**
```python
def fields_get(
    self,
    model: str,
    allfields: Optional[List[str]] = None,
    attributes: Optional[List[str]] = None  # ← NEW
) -> Dict[str, Dict[str, Any]]:
    kwargs = {}
    if allfields is not None:
        kwargs['allfields'] = allfields
    if attributes is not None:
        kwargs['attributes'] = attributes  # ← NEW
    return self._execute(model, 'fields_get', **kwargs)
```

---

### 5. copy() - Duplicate Records
**Purpose:** Copy/duplicate existing records with optional overrides

```python
# Copy record 42 with new name
new_id = Partner.copy(42, default={'name': 'Copy of Partner'})
```

**CLI Proposal:**
```bash
odoo copy res.partner 42 --override name="Copy of Partner"
# Output: {"success": true, "id": 123, "message": "Record copied"}

# Copy without changes
odoo copy res.partner 42
```

**Use Cases:**
- Duplicate templates (products, quotes, etc.)
- Create variations of existing records
- Testing/staging data duplication

---

### 6. default_get() - Get Default Values
**Purpose:** Retrieve default values for new records (as defined in model)

```python
# Get defaults for new sale order
defaults = SaleOrder.default_get(['partner_id', 'date_order', 'warehouse_id'])
# → {'date_order': '2025-11-21', 'warehouse_id': 1}
```

**CLI Proposal:**
```bash
odoo default-get sale.order partner_id,date_order,warehouse_id
# Output: {"date_order": "2025-11-21", "warehouse_id": 1}
```

**Use Cases:**
- LLMs can pre-fill forms with correct defaults
- Validation before create
- Understanding model behavior

---

### 7. onchange() - Trigger Field Dependencies
**Purpose:** Emulate UI onchange events (field updates trigger other field updates)

**Example:** When you select a partner in a sale order, Odoo auto-fills:
- Delivery address
- Invoice address
- Payment terms
- Pricelist

**Current CLI:** Can't trigger these behaviors!

**OdooRPC Pattern:**
```python
def on_change(record, method, args=None, kwargs=None):
    """Emulate on_change method"""
    res = record._odoo.execute_kw(record._name, method, args, kwargs)
    for k, v in res['value'].items():
        setattr(record, k, v)

# Usage
order = odoo.get('sale.order').browse(42)
on_change(order, 'onchange_partner_id', args=[...])
```

**Challenge:** onchange methods are complex, UI-specific
**Question:** Do we need this for CLI/LLM usage?

---

## Performance Patterns from Research

### 1. Connection Pooling (Already Implemented! ✅)
```python
# Line 110-113 in client.py
adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1)
self.session.mount('http://', adapter)
self.session.mount('https://', adapter)
```

### 2. Response Caching (Partially Implemented)
```python
# Line 396-401 in client.py - Only for get_models()
cache_key = get_cache_key_for_models(self.url, self.db)
cached_models = get_cached(cache_key, ttl_seconds=86400)
```

**Missing:** Caching for:
- `fields_get()` - Field definitions rarely change
- `search()` with same domain - Short TTL (60s?)
- `read()` for static data - Configuration records

**Proposed:**
```bash
odoo config cache enable --ttl 3600
odoo config cache clear
odoo config cache stats
```

### 3. Batch read() Instead of Individual
```python
# Bad (N queries)
for id in [1,2,3,4,5]:
    record = client.read('res.partner', [id])

# Good (1 query)
records = client.read('res.partner', [1,2,3,4,5])
```

**CLI already does this right!** ✅
```bash
odoo read res.partner 1,2,3,4,5  # Single call
```

---

## Odoo-Specific Error Handling

### Access Control Exceptions
```python
from odoo.exceptions import AccessError, MissingError

try:
    order.check_access_rights('write')
    order.check_access_rule('write')
except AccessError:
    # User doesn't have permission
except MissingError:
    # Record doesn't exist
```

**CLI should catch and translate:**
```json
{
  "success": false,
  "error": "Access denied: You don't have write permission on 'sale.order'",
  "error_type": "access_denied",
  "error_code": 403,
  "suggestion": "Contact administrator for 'Sales / User: All Documents' group"
}
```

---

## Odoo Domain Patterns (Advanced)

### We support basic domains:
```bash
odoo search res.partner '[["name","=","Azure"]]'
```

### Missing advanced patterns:
```python
# OR condition
["|", ("name", "=", "Azure"), ("name", "=", "Deco")]

# NOT condition
["!", ("active", "=", False)]

# Nested AND/OR
["&", "|", ("name", "=", "A"), ("name", "=", "B"), ("customer_rank", ">", 0)]
```

**CLI Challenge:** Escaping in bash is painful!

**Proposed:** Domain builder syntax?
```bash
odoo search res.partner --where "name=Azure OR name=Deco"
# CLI converts to: ["|", ["name","=","Azure"], ["name","=","Deco"]]
```

---

## Priority Implementation

| Method | Impact | Complexity | Priority | Status |
|--------|--------|-----------|----------|--------|
| **search_count** | High | Low | ✅ v1.4.0 | COMPLETED |
| **name_get/name_search** | High | Low | ✅ v1.4.0 | COMPLETED |
| **copy** | Medium | Low | ⚡ Medium | Pending |
| **default_get** | Medium | Low | ⚡ Medium | Pending |
| **fields_get attributes** | Low | Low | ✅ v1.4.0 | COMPLETED |
| **onchange** | Low | High | 💡 Very Low | Future |
| **Advanced domains** | Medium | Medium | ⚡ Medium | Future |

---

## Quick Wins

### 1. search-count command (5 minutes)
```python
# odoo_cli/commands/search_count.py
@click.command('search-count')
@click.argument('model')
@click.argument('domain', default='[]')
def search_count_cmd(model, domain):
    client = get_odoo_client()
    count = client.search_count(model, parse_domain(domain))
    console.print(count)
```

### 2. name-get command (10 minutes)
```python
# Add to client.py
def name_get(self, model: str, ids: List[int]) -> List[Tuple[int, str]]:
    return self._execute(model, 'name_get', ids)
```

### 3. name-search command (10 minutes)
```python
def name_search(
    self, model: str, name: str = '',
    domain: List = None, operator: str = 'ilike',
    limit: int = 100
) -> List[Tuple[int, str]]:
    domain = domain or []
    kwargs = {'operator': operator, 'limit': limit}
    if domain:
        kwargs['args'] = domain
    return self._execute(model, 'name_search', name, **kwargs)
```

---

## Implementation Status

**✅ COMPLETED (v1.4.0) - Quick Wins Bundle:**
1. ✅ **search-count command** - Fast counting without data transfer
   - File: `odoo_cli/commands/search_count.py`
   - Client method already existed, added CLI wrapper
   - Example: `odoo search-count res.partner '[]'` → `{"count": 102091}`

2. ✅ **name-get command** - ID to name conversion in 1 call
   - File: `odoo_cli/commands/name_get.py`
   - Added `client.name_get()` method (lines 403-423)
   - Example: `odoo name-get res.partner 1,2,3` → `[{"id": 1, "name": "SOLARCRAFT GmbH"}, ...]`

3. ✅ **name-search command** - Fuzzy name search for autocomplete
   - File: `odoo_cli/commands/name_search.py`
   - Added `client.name_search()` method (lines 425-462)
   - Example: `odoo name-search res.partner John` → `{"results": [...], "count": 5}`

4. ✅ **fields_get attributes** - Filter field metadata to reduce payload
   - Updated: `odoo_cli/commands/get_fields.py` (added `--attributes` option)
   - Updated: `client.fields_get()` with attributes parameter (lines 376-401)
   - Example: `odoo get-fields res.partner --attributes type,string,required`

**⏳ PENDING - Phase 2:**
- ⏳ **copy command** - Duplicate records with overrides
- ⏳ **default_get command** - Get default values for new records
- ⏳ **Advanced domain builder** - Simplified domain syntax

**💡 FUTURE - Low Priority:**
- 💡 **onchange support** - Emulate UI field dependencies (complex)
- 💡 **Response caching** - Cache fields_get(), search() results

---

**Status:** ✅ **Quick Wins Bundle COMPLETED** (v1.4.0)
**Related:** IDEA-04 (Context - COMPLETED v1.3.0), IDEA-03 (Batching - pending)
