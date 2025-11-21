# Idea: Enhanced Error Messages & Field Suggestions

## Problem

Current error messages are **cryptic and unhelpful**:

```bash
$ odoo-cli search stock.picking --fields name,x_last_warehouse_check
ERROR: Field 'x_last_warehouse_check' does not exist
```

**What's missing:**
- No suggestion of what fields ARE available
- No indication if field name is typo
- User has to run `get-fields` separately to debug
- Not LLM-friendly (no actionable suggestions)

---

## Solution: Smart Error Messages

### Before (Current)
```bash
$ odoo-cli search stock.picking --fields name,custom_field_xyz
ERROR: Invalid field custom_field_xyz in leaf ('custom_field_xyz')
```

### After (Enhanced)
```bash
$ odoo-cli search stock.picking --fields name,custom_field_xyz
❌ ERROR: Field not found on model 'stock.picking'
   Field requested: custom_field_xyz

   Did you mean one of these?
   - x_custom_field_1
   - x_custom_field_2
   - custom_field (without _xyz)

   Available fields with "custom":
   odoo-cli get-fields stock.picking --filter custom

   Full field list:
   odoo-cli get-fields stock.picking
```

---

## Key Features

### 1. Fuzzy Field Matching
```bash
$ odoo-cli search stock.picking --fields "x_warehose_check"
❌ Field not found: x_warehose_check
   Did you mean: x_warehouse_check? (similarity: 90%)

   Similar fields:
   - x_warehouse_id
   - x_warehouse_notes
```

### 2. Helpful Suggestions
```bash
$ odoo-cli search stock.picking --fields origin
❌ Field 'origin' does not exist on stock.picking

   This field exists on similar models:
   - sale.order (origin)
   - stock.move (origin)
   - purchase.order (origin)

   Did you mean to search 'sale.order' instead?
```

### 3. Custom Field Discovery
```bash
$ odoo-cli search sale.order --fields x_unknown
❌ Field 'x_unknown' not found

   Custom fields (x_*) on this model:
   - x_customer_priority (selection)
   - x_legacy_ticket_id (char)
   - x_sla_deadline (datetime)

   To see all fields:
   odoo-cli get-fields sale.order
```

### 4. Domain Error Messages
```bash
$ odoo-cli search stock.picking '[["warehouse_code", "=", "WH1"]]'
❌ Invalid field in domain: warehouse_code

   Did you mean: warehouse_id?

   Fields with "warehouse":
   - warehouse_id (many2one)
   - warehouse_name (char, read-only)

   Example search:
   odoo-cli search stock.picking '[["warehouse_id", "=", 1]]'
```

### 5. Validation Errors with Context
```bash
$ odoo-cli create sale.order -f partner_id=invalid
❌ Field validation failed
   Field: partner_id
   Value: invalid
   Type: integer (many2one)
   Error: Value must be integer ID, got: invalid

   To find partner IDs:
   odoo-cli search res.partner --domain "[['name', 'like', 'invalid']]"
```

### 6. Required Field Reminders
```bash
$ odoo-cli create sale.order
❌ Required field missing: partner_id

   Sale orders require:
   - partner_id (many2one to res.partner)
   - date_order (datetime)

   Example:
   odoo-cli create sale.order -f partner_id=1 -f date_order="2025-11-21"
```

### 7. Authentication Errors with Remediation
```bash
$ odoo-cli search sale.order
❌ Authentication failed

   Possible causes:
   1. Invalid credentials
   2. User does not exist
   3. Password changed

   Check your configuration:
   - ODOO_URL: https://your-instance.odoo.com (set)
   - ODOO_DB: your-database (set)
   - ODOO_USERNAME: admin@example.com (set)
   - ODOO_PASSWORD: *** (set)

   Test connection:
   odoo-cli get-models --limit 1
```

---

## Implementation

### 1. Field Suggestion Engine
```python
# odoo_cli/suggestions.py
from difflib import SequenceMatcher

def suggest_field(model, field_name, available_fields):
    """Find similar field names using fuzzy matching."""
    matches = []
    for avail_field in available_fields:
        similarity = SequenceMatcher(None, field_name, avail_field).ratio()
        if similarity > 0.7:  # 70% match threshold
            matches.append((avail_field, int(similarity * 100)))

    return sorted(matches, key=lambda x: x[1], reverse=True)[:3]
```

### 2. Enhanced Error Class
```python
# odoo_cli/exceptions.py
class OdooFieldError(Exception):
    def __init__(self, model, field, available_fields, suggestions):
        self.model = model
        self.field = field
        self.available_fields = available_fields
        self.suggestions = suggestions

    def __str__(self):
        msg = f"❌ Field '{self.field}' not found on {self.model}\n"

        if self.suggestions:
            msg += f"\n   Did you mean:\n"
            for suggestion, score in self.suggestions:
                msg += f"   - {suggestion} ({score}% match)\n"

        msg += f"\n   To see all fields:\n"
        msg += f"   odoo-cli get-fields {self.model}\n"

        return msg
```

### 3. Integration in Commands
```python
# odoo_cli/commands/search.py
from odoo_cli.suggestions import suggest_field
from odoo_cli.exceptions import OdooFieldError

def search(ctx, model, domain, fields):
    # Validate fields before search
    available = ctx.client.get_fields(model)
    available_names = [f['name'] for f in available]

    for field in fields.split(','):
        if field not in available_names:
            suggestions = suggest_field(model, field, available_names)
            raise OdooFieldError(model, field, available_names, suggestions)

    # Safe to search now
    results = ctx.client.search(model, domain, fields)
```

---

## Error Categories

### 1. Field Errors (Validation)
- Field not found
- Wrong field type
- Field read-only
- Field belongs to different model

### 2. Value Errors (Input Validation)
- Value wrong type (string instead of integer)
- Value out of range
- Related record not found
- Invalid choice

### 3. Permission Errors
- User lacks permissions
- Model access denied
- Field access denied
- Record locked

### 4. Connection Errors
- Server unreachable
- Authentication failed
- Database not found
- Network timeout

### 5. Domain Errors
- Invalid field in domain
- Invalid operator
- Malformed domain syntax

---

## Configuration

### Enable/Disable Suggestions
```bash
# .env
ODOO_CLI_SUGGESTIONS=true   # Enable smart suggestions (default)
ODOO_CLI_VERBOSE_ERRORS=true  # Extra detail in error messages
```

### Context for Better Errors
```bash
# Uses context file for better suggestions
ODOO_CONTEXT_FILE=/path/to/.odoo-context.json

# Errors can reference custom modules/fields from context:
# "Custom field x_sla_deadline exists in module actec_helpdesk_enh"
```

---

## Examples

### Example 1: Typo Detection
```bash
$ odoo-cli search stock.picking --fields "locaton_id"
❌ Field not found: locaton_id
   Did you mean: location_id? (95% match)

   odoo-cli search stock.picking --fields "location_id"
```

### Example 2: Custom Field Lookup
```bash
$ odoo-cli search sale.order --fields "x_costmer_priority"
❌ Field not found: x_costmer_priority
   Did you mean: x_customer_priority? (96% match)

   This is a custom field in module: actec_helpdesk_enh
   Values: normal, high, vip
```

### Example 3: Model Confusion
```bash
$ odoo-cli search stock.picking --fields "barcode"
❌ Field 'barcode' not found on stock.picking

   This field exists on:
   - product.product (barcode)
   - product.template (barcode)

   Did you mean to search 'product.product'?
```

---

## Benefits

### For Users
- ✅ Faster debugging (no need to run get-fields separately)
- ✅ Clear error messages with actionable steps
- ✅ Catch typos immediately
- ✅ Learn Odoo field structure naturally

### For LLMs
- ✅ Structured error responses with suggestions
- ✅ Can auto-correct mistakes and retry
- ✅ Better understanding of model structure
- ✅ Reduce trial-and-error cycles

### For the CLI
- ✅ More professional UX
- ✅ Better user satisfaction
- ✅ Less support requests ("what fields exist?")
- ✅ LLM-friendly structured errors

---

## Implementation Effort

**Phase 1 (Quick Win):** Basic Suggestions (2-3 hours)
- Fuzzy field matching
- Basic error messages with suggestions
- Integration in main commands

**Phase 2 (Enhancement):** Advanced Features (2 hours)
- Custom field detection from context
- Permission error improvements
- Domain error parsing

**Phase 3 (Polish):** Fine-tuning (1 hour)
- Color coding for output
- Structured JSON error format for LLMs
- Documentation

---

## Priority

**Impact:** High - Dramatically improves user experience
**Effort:** Low-Medium (2-3 hours for Phase 1)
**Complexity:** Low
**Dependencies:** None (can be added independently)

**Recommendation:** P2 for v1.5.2 (Nice-to-have enhancement)
- Quick to implement
- High user-visible impact
- No breaking changes

---

## Related Ideas

- **IDEA-09:** Python SDK (should use same error handling)
- **IDEA-007:** Project Context Layer (provides custom field context)

---

**Status:** Ready for implementation (Phase 1)
**Next Action:** Implement fuzzy matching for field suggestions
