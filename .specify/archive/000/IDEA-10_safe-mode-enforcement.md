# Idea: Safe Mode Enforcement

## Problem

Currently, only **Odoo permission-level** protection exists:
- Relies on User roles having correct permissions
- No CLI-level safeguards
- Easy to accidentally write to production if user has write access
- No way to enforce "read-only" at CLI level

**Scenario:** LLM Agent with write permissions makes a mistake and deletes 1000 records before realizing.

---

## Solution: Safe Mode Flag

Add `ODOO_SAFE_MODE` environment variable that blocks all write operations at CLI level:

```bash
# .env
ODOO_SAFE_MODE=true  # ← Blocks create/update/delete

# Attempting write operations fails at CLI level
$ odoo-cli create sale.order -f partner_id=1
❌ ERROR: Create operations blocked by ODOO_SAFE_MODE=true
   Set ODOO_SAFE_MODE=false to enable write operations
```

---

## Key Features

### 1. Environment-Based Control
```bash
# .env
ODOO_SAFE_MODE=true  # Block all writes

# Disable if needed (explicitly)
ODOO_SAFE_MODE=false
```

### 2. Selective Blocking
```bash
# Block only dangerous operations:
ODOO_SAFE_MODE=true

# Blocked (destructive):
❌ odoo-cli create sale.order ...
❌ odoo-cli update res.partner 123 ...
❌ odoo-cli delete stock.picking 456
❌ odoo-cli execute res.partner unlink [123]

# Allowed (safe reads):
✅ odoo-cli search sale.order [...]
✅ odoo-cli read res.partner 123
✅ odoo-cli get-fields stock.picking
```

### 3. Explicit Enforcement
```bash
# Prevent accidental changes even if user has permissions
$ odoo-cli update sale.order 999 -f state=done
❌ ERROR: Write operations blocked
   To enable: export ODOO_SAFE_MODE=false
   Reason: ODOO_SAFE_MODE=true in .env
```

### 4. Profile-Based Safe Mode (v1.6.0+)

```yaml
# ~/.odoo-cli.profiles.yaml
profiles:
  production-readonly:
    url: "https://your-instance.odoo.com"
    db: "production"
    username: "readonly_agent"
    password: "***"
    safe_mode: true  # Force safe mode for this profile

  production-admin:
    url: "https://your-instance.odoo.com"
    db: "production"
    username: "admin@example.com"
    password: "***"
    safe_mode: false  # Allow writes

  development:
    url: "https://dev.odoo.com"
    db: "development"
    username: "dev@example.com"
    password: "***"
    safe_mode: true  # Safe by default in dev
```

---

## Implementation

### 1. Core Safety Module
```python
# odoo_cli/safe_mode.py
import os

SAFE_MODE = os.environ.get('ODOO_SAFE_MODE', '').lower() == 'true'
DANGEROUS_OPERATIONS = {'create', 'update', 'delete', 'unlink', 'write'}

def check_safe_mode(operation):
    """Raise error if operation is dangerous and safe mode is enabled."""
    if SAFE_MODE and operation in DANGEROUS_OPERATIONS:
        raise SafeModeError(
            f"❌ {operation.upper()} operations blocked by ODOO_SAFE_MODE=true\n"
            f"   Set ODOO_SAFE_MODE=false to enable write operations"
        )
```

### 2. Integration in Commands
```python
# odoo_cli/commands/create.py
from odoo_cli.safe_mode import check_safe_mode

@click.command()
def create(ctx, model, fields):
    check_safe_mode('create')  # ← Raises error if safe mode enabled
    # ... rest of create logic
```

### 3. Help Output
```bash
$ odoo-cli --help | grep -i safe
  --safe-mode               Override ODOO_SAFE_MODE for this command
  --unsafe                  Force disable safe mode (requires confirmation)
```

### 4. Status Indicator
```bash
$ odoo-cli search stock.picking '[]'
[Safe Mode: ON] Found 42 pickings
```

---

## Configuration Options

### Option 1: Environment Variable (Recommended)
```bash
# .env
ODOO_SAFE_MODE=true  # Recommended for LLM agents
```

### Option 2: Command-Line Flag
```bash
# Override for single command
odoo-cli --unsafe update sale.order 999 -f state=done
# ⚠️  Requires interactive confirmation:
# "This command is DANGEROUS and disabled by ODOO_SAFE_MODE.
#  Type 'yes' to proceed: "
```

### Option 3: Profile-Based (v1.6.0+)
```bash
# Automatically apply safe mode per environment
odoo-cli --profile production-readonly search ...  # Safe mode ON
odoo-cli --profile production-admin update ...     # Safe mode OFF
```

---

## Error Messages

### Example 1: Blocked Create
```bash
$ odoo-cli create sale.order -f partner_id=1
❌ ERROR: Write operation blocked
   Operation: CREATE on model sale.order
   Reason: ODOO_SAFE_MODE=true in ~/.env

   To enable writes:
   1. Review the operation carefully
   2. Set ODOO_SAFE_MODE=false in .env
   3. Re-run the command

   For one-time override:
   $ ODOO_SAFE_MODE=false odoo-cli create ...
```

### Example 2: Blocked Delete
```bash
$ odoo-cli delete stock.picking 803996
❌ ERROR: Destructive operation blocked
   Operation: DELETE on model stock.picking
   Record ID: 803996

   Safe Mode is ENABLED. This prevents accidental data loss.

   If you're sure, disable with:
   $ export ODOO_SAFE_MODE=false
```

---

## Use Cases

### Use Case 1: LLM Agent (Production Read-Only)
```bash
# .env for LLM agent
ODOO_URL=https://production.odoo.com
ODOO_DB=production
ODOO_USERNAME=llm_readonly_agent
ODOO_PASSWORD=***
ODOO_SAFE_MODE=true  # ← Prevent accidental writes

# Agent can only read:
odoo-cli search stock.picking [...]  ✅
odoo-cli read sale.order 123         ✅
odoo-cli create sale.order ...       ❌ BLOCKED
```

### Use Case 2: Development (Safe by Default)
```bash
# .env for development
ODOO_URL=https://dev.odoo.com
ODOO_DB=development
ODOO_SAFE_MODE=true  # Safe by default

# Testing queries first:
odoo-cli search stock.picking [...]  ✅

# When ready to write:
ODOO_SAFE_MODE=false odoo-cli create ...
```

### Use Case 3: CI/CD Pipeline (Automated Safety)
```bash
# ci-env
ODOO_SAFE_MODE=true  # Enforce in CI

# Queries work:
odoo-cli search sale.order [...]  ✅

# Write attempts fail (prevents accidental data corruption):
odoo-cli update sale.order 999 -f state=done  ❌ BLOCKED
```

---

## Benefits

### For Users
- ✅ Sleep better knowing writes are blocked
- ✅ LLM agents can't accidentally destroy data
- ✅ Clear error messages with remediation
- ✅ Works with existing permissions as second layer

### For LLM Integration
- ✅ Agents can operate in production safely
- ✅ No need to create read-only users (though recommended)
- ✅ Double protection: User perms + CLI safe mode

### For Teams
- ✅ Enforce safety policies per environment
- ✅ Prevent "oops" moments
- ✅ Works across CLI and SDK (v2.0.0+)

---

## Implementation Effort

**Phase 1 (Quick Win):** Basic Safe Mode (1-2 hours)
- Add `ODOO_SAFE_MODE` env var check
- Block create/update/delete operations
- Simple error messages

**Phase 2 (Enhancement):** Better UX (1 hour)
- Colored error output
- Suggestion in help text
- Status indicator in output

**Phase 3 (v1.6.0):** Profile-Based Safe Mode (1 hour)
- Integrate with environment profiles
- Per-profile safe mode settings

---

## Priority

**Impact:** High - Prevents accidental data loss
**Effort:** Low (1-2 hours for Phase 1)
**Complexity:** Low
**Dependencies:** None

**Recommendation:** P1 for v1.5.2 (Quick patch release)
- Easy to implement
- Massive safety improvement
- No breaking changes

---

## Related Ideas

- **IDEA-01:** Environment Profiles (integrates with safe mode)
- **IDEA-02:** Read-Only Mode (complements this)
- **IDEA-09:** Python SDK (respects safe mode)

---

**Status:** Ready for v1.5.2 implementation
**Next Action:** Implement basic safe mode check in all write commands
