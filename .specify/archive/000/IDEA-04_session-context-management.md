# Idea: Session & Context Management

## Problem
Current implementation lacks session persistence and Odoo context handling, leading to repeated authentication and missing context-aware operations.

## Key Findings from Research

### 1. Session Management (OdooRPC Pattern)
**Currently Missing:** No session persistence, user re-authenticates every CLI call.

**OdooRPC has:**
```python
# Save session for reuse
odoo.save('production')
odoo.save('staging', filepath='~/.odoo-sessions')

# Load session (no re-auth needed)
odoo = odoorpc.ODOO.load('production')

# List available sessions
sessions = odoorpc.ODOO.list()  # ['production', 'staging', 'dev']

# Remove session
odoo.remove('old-session')
```

**Benefits:**
- No repeated authentication (faster)
- Switch between environments easily
- Session file: `~/.odoorpcrc` or custom path
- Credentials encrypted/stored securely

**Current CLI:**
```bash
# Every call re-authenticates!
odoo read res.partner 1
odoo update res.partner 1 --fields name="Test"
odoo delete res.partner 1
```

**With Sessions:**
```bash
# One-time setup
odoo session save production --url https://prod.odoo.com --db prod

# Fast subsequent calls (no auth)
odoo read res.partner 1 --session production
odoo update res.partner 1 --fields name="Test"  # Uses default session
```

---

### 2. Context Management (Critical Missing Feature!)

**We currently send NO context to Odoo!**

**Odoo Context includes:**
- `lang`: User language (e.g., 'de_DE', 'en_US')
- `tz`: Timezone (e.g., 'Europe/Berlin')
- `uid`: User ID
- `active_test`: Include/exclude archived records (default: True)
- `allowed_company_ids`: Multi-company filtering
- Custom keys: `default_type`, `search_default_*`, etc.

**Example Impact:**
```python
# Without context (lang defaults to en_US)
Product.name_get([25])  # → "Four Person Desk"

# With context (lang=fr_FR)
Product.with_context(lang='fr_FR').name_get([25])  # → "Bureau Quatre Personnes"
```

**Missing Features:**
```python
# Get ALL records including archived
Product.with_context(active_test=False).search([])

# Multi-company operations
Order.with_context(allowed_company_ids=[1,2]).search([])

# Set defaults for creation
Partner.with_context(default_type='company').create({...})
```

**Proposed CLI:**
```bash
# Set global context
odoo config set-context --lang de_DE --tz Europe/Berlin

# Per-command context
odoo search product.product '[]' --context active_test=false
odoo create res.partner --fields name="Test" --context default_type=company

# Show current context
odoo context show
```

---

### 3. Auto-Context Feature (OdooRPC)

**Toggle automatic user context propagation:**
```python
# Default: True (automatically includes user's lang, tz, etc.)
odoo.config['auto_context'] = True

# Disable for specific operations
odoo.config['auto_context'] = False
Product.name_get([25])  # Uses system defaults (en_US)
```

**CLI Equivalent:**
```bash
odoo config auto-context enable   # Include user context automatically
odoo config auto-context disable  # Use system defaults only
```

---

### 4. Async Batch Operations (Zenoo RPC Pattern)

**Performance optimization we're missing:**

**Current CLI (Sequential):**
```bash
# Each create = 1 HTTP call
odoo create res.partner --fields name="A"  # Call 1
odoo create res.partner --fields name="B"  # Call 2
odoo create res.partner --fields name="C"  # Call 3
# Total: 3 HTTP calls, ~300ms
```

**Zenoo RPC Pattern:**
```python
async with client.batch() as batch:
    batch.create("res.partner", {"name": "A"})
    batch.create("res.partner", {"name": "B"})
    batch.create("res.partner", {"name": "C"})
# Total: 1 HTTP call (batched), ~100ms
```

**Advanced Features:**
- **Chunking:** `chunk_size=100` (divide large batches)
- **Concurrency:** `max_concurrency=5` (parallel execution)
- **Progress callbacks:** Monitor long-running batches
- **Iterator pattern:** `create_many_iter()` for streaming results

**Example:**
```python
# Create 10,000 records with progress tracking
async for chunk_result in batch.create_many_iter(
    ResPartner,
    dataset,
    chunk_size=100
):
    print(f"Processed: {len(chunk_result.records)} records")
```

---

### 5. Access Control Checks (Missing Security!)

**Odoo has built-in access checks we should use:**
```python
# Check if user CAN write to model
order.check_access_rights('write')  # Raises AccessError if not allowed

# Check if user can access THIS specific record
order.check_access_rule('write')    # Checks record rules
```

**Why important:**
- Better error messages BEFORE operation fails
- Pre-flight validation
- Security best practice

**Proposed CLI:**
```bash
# Check access before operation
odoo check-access res.partner write  # Exit 0 = allowed, 1 = denied

# Auto-check in operations (with --strict flag)
odoo update res.partner 1 --fields name="Test" --strict
# → First checks access, then performs update
```

---

### 6. Odoo Has TWO API Types!

**We only use JSON-RPC, but Odoo also has HTTP endpoints:**

| Type | Current Usage | Purpose | Auth |
|------|---------------|---------|------|
| `type='json'` | ✅ Yes | Internal RPC calls | `auth='user'` |
| `type='http'` | ❌ No | REST APIs, webhooks | `auth='api_key'` |

**HTTP endpoints examples:**
- `/api/orders/{id}` - REST API with API key
- `/my/orders` - Customer portal (auth='user')
- `/my/orders/{id}/download` - Generate PDF
- Custom webhooks

**Do we need HTTP support?**
- For REST API access (external integrations)
- For webhooks/callbacks
- For public endpoints (with tokens)

**Proposed:**
```bash
# JSON-RPC (current)
odoo read res.partner 1

# HTTP REST API (new?)
odoo http GET /api/orders/123 --api-key xyz

# Download endpoint
odoo http GET /my/orders/456/download --output order.pdf
```

---

## Priority Ranking

| Feature | Impact | Complexity | Priority |
|---------|--------|-----------|----------|
| **Context Management** | High | Medium | 🔥 Critical |
| **Session Persistence** | High | Low | 🔥 High |
| **Access Control Checks** | Medium | Low | ⚡ Medium |
| **Async Batching (Zenoo)** | High | High | ⚡ Medium |
| **HTTP Endpoint Support** | Low | Medium | 💡 Low |
| **Auto-Context Toggle** | Low | Low | 💡 Low |

---

## Questions

1. **Session Management:**
   - Store in `~/.odoo-cli/sessions.json` or `~/.odoorpcrc`?
   - Encrypt credentials or use system keyring?
   - Default session vs named sessions?

2. **Context Management:**
   - Global context (config file) vs per-command?
   - Auto-detect user's lang/tz from system?
   - Context inheritance rules?

3. **Async Batching:**
   - Requires Python `async/await` - breaking change?
   - Keep sync CLI + optional async mode?
   - Worth the complexity for performance?

4. **Access Checks:**
   - Always check (slower) or opt-in `--strict`?
   - Cache access rights for session?

---

## Implementation Ideas

### Phase 1: Context Support (Critical)
```bash
odoo config set-context lang=de_DE tz=Europe/Berlin
odoo search product.product '[]' --context active_test=false
```

### Phase 2: Session Management
```bash
odoo session save prod --url https://prod.odoo.com
odoo session list
odoo read res.partner 1 --session prod
```

### Phase 3: Access Control
```bash
odoo check-access res.partner write
odoo update res.partner 1 --strict --fields name="Test"
```

### Phase 4: Async Batching (Optional)
- Requires architectural refactor
- Consider separate `odoo-async` CLI or `--async` flag

---

**Status:** ✅ **Phase 1 COMPLETED** (v1.3.0) - Context Management implemented
- ✅ Client context support (`_execute()`, all helper methods)
- ✅ CLI `--context` flag on all 10 commands
- ✅ Context parser with type inference
- ✅ Documentation updated (README, CHANGELOG)
- ⏳ Phase 2: Session Management - pending
- ⏳ Phase 3: Access Control - pending
- ⏳ Phase 4: Async Batching - future

**Related:** IDEA-03 (Batch Requests) - overlaps with async batching
