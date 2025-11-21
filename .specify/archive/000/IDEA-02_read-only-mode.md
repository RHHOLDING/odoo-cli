# Idea: Read-Only Mode Switch

## Problem
Need safe access to production environments - ability to read data only, while allowing write operations in dev/staging.

## Scope
- **Read-Only Mode:** Only `search`, `read`, `aggregate`, `get-*` commands allowed
- **Write Access:** `create`, `update`, `delete`, `create-bulk`, `update-bulk` allowed only when disabled
- **Configuration:** Environment variable (e.g., `ODOO_READ_ONLY=true/false`)
- **Use Cases:**
  - Production: `ODOO_READ_ONLY=true` → safe read-only queries
  - Dev/Staging: `ODOO_READ_ONLY=false` → full CRUD operations
- **Switch:** Simple toggle, one environment variable

## Key Questions
1. Is this even possible/practical to implement?
2. Should it block write commands or refuse to load config entirely?
3. Where in the stack do we enforce this? (CLI level? Client level?)
4. Does this require refactoring of command structure?

## Rough Ideas
- Check `ODOO_READ_ONLY` flag early in CLI initialization
- Unregister/disable write commands at startup if read-only enabled
- Error message if user tries write command in read-only mode
- Default: `ODOO_READ_ONLY=false` (allow all operations)

---
**Status:** Idea collection phase - feasibility TBD
