# Idea: JSON-RPC Batch Requests & Protocol Optimization

## Problem
Current implementation uses individual sequential RPC calls. JSON-RPC 2.0 supports true batch requests that could significantly improve performance and reduce latency for multi-operation workflows.

## Scope

### 1. True Batch Requests (JSON-RPC 2.0 Native)
Send multiple requests in a single HTTP call, process in parallel on server:
```json
[
  {"jsonrpc": "2.0", "method": "create", "params": ["model", "vals"], "id": 1},
  {"jsonrpc": "2.0", "method": "create", "params": ["model", "vals"], "id": 2},
  {"jsonrpc": "2.0", "method": "create", "params": ["model", "vals"], "id": 3}
]
```

**Current:** 3 HTTP calls → 3 round trips
**With Batching:** 1 HTTP call → 1 round trip

### 2. Notifications (Fire-and-Forget)
Skip response waiting for operations where result isn't needed:
```json
{
  "jsonrpc": "2.0",
  "method": "create",
  "params": ["model", "vals"]
  // No "id" field = no response expected
}
```
**Use Cases:** Logging operations, background sync, non-critical writes

### 3. search_read() Consolidation
Replace two-call pattern (search + read) with single RPC:
```python
# Current (2 calls):
ids = execute('model', 'search', domain)
records = execute('model', 'read', ids)

# Optimized (1 call):
records = execute('model', 'search_read', domain)
```

### 4. JSON-RPC Standard Error Codes
Map to spec-compliant error codes instead of custom codes:
- `-32700`: Parse error
- `-32600`: Invalid Request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000 to -32099`: Server errors (Odoo-specific)

Current: Custom codes (1, 2, 3) → Less interoperable

### 5. Context & Kwargs Optimization
Use `execute_kw()` with explicit kwargs instead of positional args:
```python
# Better context propagation and clarity
execute_kw(model, method, args=[], kwargs={'context': {}, 'company_id': 1})
```

### 6. fields_get() Attribute Filtering
Only fetch needed field metadata instead of everything:
```python
# Only get type, required, readonly instead of all attributes
fields_get(attributes=['type', 'required', 'readonly'])
```

### 7. name_get() / name_search()
Leverage Odoo's display name methods for better UX:
- `name_get()`: Get display names for records
- `name_search()`: Search by name with fuzzy matching

---

## Key Questions

1. **Batch Request Implementation:**
   - Should we automatically batch consecutive operations?
   - Batch size limit? (Max payload size?)
   - Should it be opt-in or default behavior?

2. **Notification Usage:**
   - Which operations should be fire-and-forget?
   - How do we handle errors if no response expected?
   - User control (--async flag)?

3. **Backward Compatibility:**
   - Can we transparently use `search_read()` instead of `search` + `read`?
   - Does this break error handling patterns?

4. **Error Code Mapping:**
   - Should we keep both custom and standard codes?
   - How do we document the mapping?

5. **Implementation Complexity:**
   - Requires refactoring of client execute logic?
   - Need buffering/queueing system?
   - Testing complexity?

---

## Performance Impact Estimate

**Scenario:** CREATE-BULK with 100 records, batch size 10
- **Current:** 10 HTTP calls (10 round trips) + 1 final commit = ~1000ms (estimate)
- **With Batching:** 1 HTTP call (1 round trip) = ~100ms (estimate)
- **Potential:** 10x faster

**Scenario:** search_read on 1000 records
- **Current:** 2 HTTP calls (search + read) = ~200ms
- **With search_read():** 1 HTTP call = ~100ms
- **Potential:** 2x faster

---

## Rough Ideas

- [ ] Create `batch_executor` utility that queues operations
- [ ] Auto-detect consecutive operations and batch them
- [ ] Add `--async` flag for fire-and-forget operations
- [ ] Replace `search()` + `read()` with `search_read()` internally
- [ ] Map custom error codes to JSON-RPC standard codes
- [ ] Support `fields_get()` attribute filtering in validation logic
- [ ] Document Notifications pattern in help.py

---

**Status:** Optimization exploration phase - not yet prioritized
**Affects:** Performance, protocol compliance, code complexity
**Priority:** Medium-High (performance gains are significant)
