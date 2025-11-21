# Idea: Project Context Layer for LLMs

## Problem
LLMs using this CLI have no knowledge of:
- Your specific Odoo setup (company structure, warehouses, teams)
- Custom fields and modules
- Business workflows and processes
- Important record IDs (default warehouse, main company, etc.)
- Naming conventions and data model extensions
- Integration points and dependencies

**Result:** LLMs have to ask many questions or make wrong assumptions.

## Goal
Enable users to define a **project-specific context file** that LLMs can read to understand the Odoo instance better.

Think of it as: **"A README for LLMs about YOUR Odoo setup"**

---

## Use Cases

### Example 1: Multi-Company Setup
```yaml
# .odoo-context.yaml
companies:
  main:
    id: 1
    name: "SOLARCRAFT GmbH"
    purpose: "Solar products, European multi-language sales"
    currency: EUR

  subsidiary_1:
    id: 2
    name: "AC TEC GmbH"
    purpose: "Main operations, marketplace hub (Amazon, eBay)"
    currency: EUR

  subsidiary_2:
    id: 3
    name: "ANANDA GmbH"
    purpose: "Import/export, dual-warehouse logistics"
    warehouses: [1, 2]
```

**LLM Benefit:** Now knows which company to use for different operations without asking.

---

### Example 2: Important IDs
```yaml
key_records:
  warehouses:
    main_eu:
      id: 1
      name: "Main Warehouse Europe"
      location_id: 8
      company_id: 1

    main_us:
      id: 2
      name: "US Distribution Center"
      location_id: 15
      company_id: 1

  sales_teams:
    default:
      id: 1
      name: "Direct Sales"

    amazon:
      id: 5
      name: "Amazon Integration Team"

  payment_terms:
    standard:
      id: 1
      name: "Immediate Payment"

    net_30:
      id: 3
      name: "30 Days Net"
```

**LLM Benefit:** Can auto-select correct warehouse/team without trial-and-error.

---

### Example 3: Custom Fields & Modules
```yaml
custom_modules:
  actec_helpdesk_enh:
    models:
      - helpdesk.ticket
      - helpdesk.team
    custom_fields:
      helpdesk.ticket:
        - x_legacy_ticket_id: "Migration ID from old system"
        - x_customer_priority: "VIP status (selection: normal/high/vip)"
        - x_sla_deadline: "Custom SLA deadline (datetime)"

  actec_product_labels:
    purpose: "Custom product labeling and barcode generation"
    dependencies: ["product", "stock"]

  queue_job_custom:
    purpose: "Async job processing for heavy operations"
    note: "Always use for batch imports >100 records"
```

**LLM Benefit:** Knows about custom fields, can use them in searches/creates.

---

### Example 4: Business Workflows
```yaml
workflows:
  sales_order_approval:
    description: "Orders >5000 EUR require manager approval"
    trigger: "amount_total > 5000"
    approval_team_id: 10

  product_creation:
    description: "New products must have category, supplier, and min 1 image"
    required_fields: [categ_id, seller_ids, image_1920]
    validation: "Use product.template model, not product.product"

  inventory_adjustment:
    description: "Only warehouse managers can adjust stock"
    required_group: "stock.group_stock_manager"
    location: "Physical Locations > Inventory Adjustment (ID 5)"
```

**LLM Benefit:** Understands business rules, can validate operations.

---

### Example 5: Integration Points
```yaml
integrations:
  amazon_connector:
    module: "marketplace_connector"
    marketplace_id: 1
    product_sync: "Every 6 hours via queue job"
    order_import: "Real-time webhook"

  magento2:
    module: "magento2_connector"
    website_id: 2
    stock_sync_warehouse_id: 1

  sentry_monitoring:
    enabled: true
    environment: "production"
    note: "All errors auto-tracked, check Sentry for issues"
```

**LLM Benefit:** Knows which systems are connected, how data flows.

---

### Example 6: Data Conventions
```yaml
conventions:
  product_naming:
    pattern: "[CATEGORY_CODE] Product Name"
    example: "[FURN_8220] Four Person Desk"

  reference_numbers:
    sales_orders: "SO followed by sequence (SO00001)"
    purchase_orders: "PO followed by sequence (PO00001)"
    invoices: "INV/2025/00001 (year-based)"

  record_states:
    sale.order: ["draft", "sent", "sale", "done", "cancel"]
    purchase.order: ["draft", "sent", "purchase", "done", "cancel"]

  archived_records:
    note: "We heavily use archiving instead of deletion"
    search_tip: "Always use context active_test=false to find archived records"
```

**LLM Benefit:** Follows naming conventions, understands state flows.

---

## File Format

### Option A: YAML (Human-Friendly)
```yaml
# .odoo-context.yaml
project:
  name: "RH Holding Production"
  odoo_version: "16.0"
  environment: "production"
  last_updated: "2025-11-21"

companies: {...}
key_records: {...}
custom_modules: {...}
workflows: {...}
integrations: {...}
conventions: {...}
```

**Pros:** Easy to read/write, supports comments
**Cons:** Need YAML parser

---

### Option B: JSON (Machine-Friendly)
```json
{
  "project": {
    "name": "RH Holding Production",
    "odoo_version": "16.0"
  },
  "companies": {...},
  "key_records": {...}
}
```

**Pros:** Native Python support, faster parsing
**Cons:** No comments, less human-friendly

---

### Option C: Markdown (Documentation-Friendly)
```markdown
# RH Holding Odoo Context

## Companies
- **SOLARCRAFT GmbH** (ID: 1) - Solar products, European sales
- **AC TEC GmbH** (ID: 2) - Main operations, marketplaces

## Key Records
### Warehouses
- Main Warehouse Europe (ID: 1, Company: 1)
```

**Pros:** Very readable, can include long descriptions
**Cons:** Harder to parse programmatically

---

### Recommendation: YAML + JSON Support
- Primary: `.odoo-context.yaml` (human editing)
- Alternative: `.odoo-context.json` (auto-generated)
- CLI converts YAML → JSON for LLM consumption

---

## CLI Integration

### 1. Auto-Discovery
```bash
# CLI looks for context file in order:
1. Current directory: ./.odoo-context.yaml
2. Project root (git): $(git rev-parse --show-toplevel)/.odoo-context.yaml
3. Home directory: ~/.odoo-context.yaml
4. Environment variable: $ODOO_CONTEXT_FILE
```

### 2. Explicit Loading
```bash
# Load specific context file
odoo --context-file ./custom-context.yaml read res.partner 1

# Disable context loading
odoo --no-context read res.partner 1
```

### 3. Show Current Context
```bash
# Display loaded project context
odoo context show

# Output (JSON):
{
  "context_loaded": true,
  "file_path": "/path/to/.odoo-context.yaml",
  "project": {
    "name": "RH Holding Production",
    "companies": 4,
    "custom_modules": 12,
    "workflows": 3
  }
}
```

### 4. Validate Context File
```bash
# Check context file for errors
odoo context validate .odoo-context.yaml

# Output:
✓ Valid YAML syntax
✓ All referenced IDs exist in Odoo
✗ Warning: Company ID 5 not found
✓ Custom modules: 10/12 installed
```

### 5. Generate Template
```bash
# Create starter template
odoo context init

# Output: .odoo-context.yaml created with common sections
# User fills in their specific values
```

---

## LLM Help Integration

### Current `odoo llm-help` Output:
```json
{
  "cli_version": "1.2.0",
  "commands": [...],
  "decision_tree": {...}
}
```

### Enhanced with Project Context:
```json
{
  "cli_version": "1.2.0",
  "project_context": {
    "loaded": true,
    "file": "/path/to/.odoo-context.yaml",
    "summary": {
      "companies": [
        {"id": 1, "name": "SOLARCRAFT GmbH"},
        {"id": 2, "name": "AC TEC GmbH"}
      ],
      "key_warehouses": [
        {"id": 1, "name": "Main Warehouse Europe"}
      ],
      "custom_modules": [
        "actec_helpdesk_enh",
        "actec_product_labels"
      ],
      "workflows": {
        "sales_order_approval": "Orders >5000 EUR need approval"
      }
    }
  },
  "commands": [...],
  "decision_tree": {...}
}
```

**LLM reads this and knows:**
- Which companies exist
- Which warehouses to use
- Which custom modules are available
- Which workflows to follow

---

## Schema Definition

**File:** `.odoo-context.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "project": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "odoo_version": {"type": "string"},
        "environment": {"enum": ["production", "staging", "development"]},
        "last_updated": {"type": "string", "format": "date"}
      },
      "required": ["name"]
    },
    "companies": {
      "type": "object",
      "patternProperties": {
        "^[a-z_]+$": {
          "type": "object",
          "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "purpose": {"type": "string"},
            "currency": {"type": "string"}
          },
          "required": ["id", "name"]
        }
      }
    },
    "key_records": {
      "type": "object",
      "properties": {
        "warehouses": {"type": "object"},
        "sales_teams": {"type": "object"},
        "payment_terms": {"type": "object"}
      }
    },
    "custom_modules": {
      "type": "object",
      "patternProperties": {
        "^[a-z_]+$": {
          "type": "object",
          "properties": {
            "models": {"type": "array", "items": {"type": "string"}},
            "custom_fields": {"type": "object"},
            "purpose": {"type": "string"}
          }
        }
      }
    },
    "workflows": {"type": "object"},
    "integrations": {"type": "object"},
    "conventions": {"type": "object"}
  }
}
```

**Validation:**
```bash
odoo context validate .odoo-context.yaml --schema .odoo-context.schema.json
```

---

## Example: Full Context File

**File:** `.odoo-context.yaml`

```yaml
# Odoo Project Context for LLMs
# This file helps AI assistants understand your specific Odoo setup

project:
  name: "RH Holding Production"
  odoo_version: "16.0"
  environment: "production"
  database: "your-instance-db-12345"
  url: "https://your-instance.odoo.com"
  last_updated: "2025-11-21"
  maintainer: "andre@ananda.gmbh"

companies:
  solarcraft:
    id: 1
    name: "SOLARCRAFT GmbH"
    purpose: "Solar products, European multi-language sales"
    currency: EUR
    country: DE

  actec:
    id: 2
    name: "AC TEC GmbH"
    purpose: "Main operations, marketplace hub (Amazon, eBay)"
    currency: EUR
    country: DE

  ananda:
    id: 3
    name: "ANANDA GmbH"
    purpose: "Import/export, dual-warehouse logistics"
    currency: EUR
    warehouses: [1, 2]

  hantech:
    id: 4
    name: "HANTECH GmbH"
    purpose: "Technology focus, premium B2B products"
    currency: EUR

key_records:
  warehouses:
    main_eu:
      id: 1
      name: "Main Warehouse Europe"
      company_id: 3  # ANANDA
      location_id: 8

    secondary_eu:
      id: 2
      name: "Secondary Warehouse"
      company_id: 3

  sales_teams:
    direct_sales:
      id: 1
      name: "Direct Sales"
      company_id: 2

    amazon_team:
      id: 5
      name: "Amazon Integration Team"
      company_id: 2

  product_categories:
    electronics:
      id: 1
      name: "Electronics"

    furniture:
      id: 2
      name: "Furniture"

    solar:
      id: 10
      name: "Solar Equipment"
      company_id: 1  # SOLARCRAFT specific

custom_modules:
  actec_helpdesk_enh:
    purpose: "Enhanced helpdesk with SLA tracking"
    models:
      - helpdesk.ticket
      - helpdesk.team
    custom_fields:
      helpdesk.ticket:
        x_legacy_ticket_id:
          type: char
          description: "Migration ID from old support system"
        x_customer_priority:
          type: selection
          values: [normal, high, vip]
          description: "Customer VIP status"
        x_sla_deadline:
          type: datetime
          description: "Custom SLA deadline"

  actec_product_labels:
    purpose: "Custom product labeling and barcode generation"
    models:
      - product.label
    dependencies: [product, stock]

  queue_job_custom:
    purpose: "Async job processing for heavy operations"
    note: "Always use queue jobs for batch operations >100 records"
    trigger: "batch_size > 100"

workflows:
  sales_order_approval:
    description: "High-value orders require manager approval"
    trigger: "amount_total > 5000 EUR"
    required_group: "sales_team.group_sale_manager"
    approval_team_id: 10
    state_flow: "draft → sent → sale (needs approval) → done"

  product_creation:
    description: "All new products must meet quality standards"
    required_fields: [categ_id, seller_ids, image_1920, list_price]
    validation_rules:
      - "Must have at least one supplier"
      - "Must have product image"
      - "Price must be > 0"
    model: "product.template"
    note: "Use product.template for creation, NOT product.product"

  inventory_adjustment:
    description: "Stock adjustments restricted to warehouse managers"
    required_group: "stock.group_stock_manager"
    location_id: 5  # Inventory Adjustment location
    note: "All adjustments logged and audited"

integrations:
  amazon_connector:
    module: "marketplace_connector"
    marketplace_id: 1
    sync_schedule:
      products: "Every 6 hours (queue job)"
      orders: "Real-time webhook"
      stock: "Every hour"
    warehouse_mapping:
      amazon_fba: 1  # Main Warehouse

  magento2:
    module: "magento2_connector"
    website_id: 2
    stock_sync_warehouse: 1
    company_id: 1  # SOLARCRAFT

  sentry_monitoring:
    enabled: true
    environment: "production"
    dsn: "https://...@sentry.io/..."
    note: "All errors auto-tracked at https://sentry.io/organizations/actec"

conventions:
  product_naming:
    pattern: "[CATEGORY_CODE] Product Name"
    examples:
      - "[FURN_8220] Four Person Desk"
      - "[ELEC_5100] USB-C Cable 2m"
    note: "Category codes maintained in product.category"

  reference_numbers:
    sales_orders: "SO + sequence (SO00001, SO00002, ...)"
    purchase_orders: "PO + sequence"
    invoices: "INV/YYYY/NNNNN (year-based)"
    delivery_orders: "WH/OUT/NNNNN"

  record_states:
    sale.order: [draft, sent, sale, done, cancel]
    purchase.order: [draft, sent, purchase, done, cancel]
    helpdesk.ticket: [new, in_progress, waiting, solved, closed]

  data_management:
    archiving: "We archive instead of delete (active=False)"
    search_archived: "Use context: active_test=false"
    bulk_operations: "Use queue jobs for >100 records"

  multi_language:
    primary: "de_DE"
    supported: [en_US, fr_FR, de_DE]
    product_translations: "All products must have EN and DE names"

notes:
  - "Production database - be careful with write operations!"
  - "Always test bulk operations on staging first"
  - "Sentry monitoring active - check errors at sentry.io"
  - "Queue jobs run every 5 minutes"
  - "Backup runs daily at 02:00 UTC"

security:
  read_only_groups:
    - "base.group_portal"  # Portal users
    - "base.group_public"  # Public users

  restricted_models:
    - "res.users"  # User management
    - "res.groups"  # Group management
    - "ir.config_parameter"  # System parameters

  note: "Write operations require appropriate user groups"
```

---

## Implementation

### Phase 1: Basic Support (1-2 days)
1. ✅ Define YAML schema
2. ✅ Add context file auto-discovery
3. ✅ Load context in `odoo llm-help`
4. ✅ Add `odoo context show` command
5. ✅ Add `odoo context init` template generator

### Phase 2: Validation (1 day)
6. ✅ Add `odoo context validate` command
7. ✅ Check referenced IDs exist in Odoo
8. ✅ Verify module installation
9. ✅ Warn about misconfigurations

### Phase 3: Enhanced Integration (1-2 days)
10. ✅ Use context in field validation (suggest custom fields)
11. ✅ Use context in model discovery (show custom modules)
12. ✅ Use context in error messages (reference workflows)

---

## LLM Usage Example

**Scenario:** LLM wants to create a sale order for SOLARCRAFT

**Without Project Context:**
```
LLM: What company should I use?
User: SOLARCRAFT
LLM: What's the company ID?
User: 1
LLM: What warehouse?
User: Main Warehouse
LLM: What's the warehouse ID?
User: 1
```

**With Project Context:**
```
LLM reads .odoo-context.yaml
→ Knows SOLARCRAFT = company_id 1
→ Knows Main Warehouse = warehouse_id 1
→ Creates order directly with correct IDs
```

**Massive time saving!**

---

## Benefits

### For Users
- ✅ Fewer questions from LLM
- ✅ Correct IDs on first try
- ✅ LLM understands business workflows
- ✅ Documentation doubles as LLM knowledge base

### For LLMs
- ✅ Pre-loaded project knowledge
- ✅ No trial-and-error for IDs
- ✅ Understand custom fields/modules
- ✅ Follow business rules automatically

### For Projects
- ✅ Living documentation
- ✅ Onboarding new developers
- ✅ Knowledge base in version control
- ✅ Environment-specific configs

---

## Priority

**Impact:** Very High - Dramatically improves LLM effectiveness
**Effort:** Medium (2-4 days)
**Complexity:** Low-Medium
**Dependencies:** None

**Recommendation:** P1 - High Priority
- Implement after Context Management (Spec 004)
- Before Session Management (less critical)

**Quick Win:** Template generator (1 hour)
```bash
odoo context init
# Creates .odoo-context.yaml with sections + comments
# User fills in their values
```

---

## Open Questions

1. **Validation Frequency:**
   - Validate on every CLI call? (slow)
   - Validate on first load, cache? (faster)
   - Manual validation only?

2. **ID Synchronization:**
   - Auto-update IDs when records change?
   - Warn when referenced IDs don't exist?
   - Fetch IDs dynamically vs static config?

3. **Multi-Environment:**
   - Separate contexts for prod/staging/dev?
   - `.odoo-context.prod.yaml`, `.odoo-context.staging.yaml`?
   - Environment variable: `ODOO_ENV=staging`?

4. **Version Control:**
   - Commit context file to git? (YES for shared knowledge)
   - `.gitignore` for sensitive values? (credentials already in .env)
   - Template + local overrides pattern?

---

**Status:** Project-specific context layer for LLMs - High value feature
**Related:** Spec 004 (Context Management) - complementary features
**Next Action:** Define YAML schema, implement auto-discovery
