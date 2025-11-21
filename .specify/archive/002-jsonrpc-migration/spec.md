# Specification: JSON-RPC Migration & Performance Optimization

**Spec ID:** 002-jsonrpc-migration
**Status:** Planning
**Priority:** HIGH (Performance Critical)
**Created:** 2025-11-20
**Parent Spec:** 001-cli-implementation

## Executive Summary

Migrate the Odoo CLI from XML-RPC to **JSON-RPC only** to achieve **75% higher throughput** and **43% faster response times**. Complete replacement - no backward compatibility needed, simplifies codebase.

## Clarifications

### Session 2025-11-20
- Q: Retry logic strategy for failed JSON-RPC requests? → A: Fixed interval (2s delay, max 3 retries)
- Q: Connection pooling configuration? → A: Single persistent session per OdooJSONClient instance
- Q: Cache duration for get_models response? → A: 24 hours (models change rarely in production)
- Q: Which Odoo versions to officially support and test? → A: v14-17 (full range for maximum compatibility), primary focus on v16 odoo.sh
- Q: Migration rollout strategy? → A: **JSON-RPC only** - Complete replacement, remove all XML-RPC code, no backward compatibility, major version bump (v0.2.0 → v1.0.0)

## Problem Statement

### Current Issues
1. **Performance Bottleneck:** XML-RPC is significantly slower than JSON-RPC
   - XML-RPC: ~100 requests/second
   - JSON-RPC: ~175 requests/second (+75%)
   - Response time difference: 43% faster with JSON-RPC

2. **Data Overhead:** XML payloads are verbose compared to JSON
   - XML: Heavy parsing overhead
   - JSON: Native Python dict/list handling

3. **Modern Stack:** Industry is moving to JSON-RPC
   - odooly: Supports both, JSON-RPC recommended
   - Odoo Web Client: Uses JSON-RPC exclusively
   - REST APIs: JSON is standard

### Business Impact
- Faster CLI operations → Better UX
- Higher throughput → More scalable for automation
- Lower bandwidth → Cost savings
- Modern stack → Easier maintenance

## Goals

### Primary Goals
1. ✅ Replace XML-RPC client completely with JSON-RPC
2. ✅ Achieve 75% higher throughput and 43% faster response times
3. ✅ Simplify codebase - remove protocol switching logic
4. ✅ Add connection pooling and caching for performance
5. ✅ Update documentation and examples

### Success Metrics
- [ ] JSON-RPC client passes all existing tests
- [ ] Performance improvement: ≥70% higher throughput
- [ ] All commands work with JSON-RPC
- [ ] CI/CD tests on Odoo v14-17 (primary: v16 odoo.sh)
- [ ] Clean codebase - no legacy XML-RPC code

## Technical Architecture

### Components

#### 1. JSON-RPC Client (`odoo_cli/client.py`) - **REPLACES** existing OdooClient
```python
class OdooClient:
    """
    JSON-RPC client for Odoo (renamed from OdooJSONClient for simplicity)

    Direct replacement of XML-RPC client with same interface.
    All existing commands continue to work without changes.

    Uses a single persistent requests.Session per instance for:
    - HTTP Keep-Alive connection reuse
    - Automatic connection pooling
    - Cookie persistence
    - Optimal for sequential CLI operations
    """

    def __init__(self, url, db, username, password, timeout=30, verify_ssl=True)
    def connect(self) -> None
    def execute(self, model, method, *args, **kwargs) -> Any
    def search(self, model, domain, offset, limit, order) -> List[int]
    def read(self, model, ids, fields) -> List[Dict]
    def search_read(self, model, domain, fields, offset, limit, order) -> List[Dict]
    def search_count(self, model, domain) -> int
    def fields_get(self, model, allfields) -> Dict
    def get_models(self) -> List[str]  # with 24h cache
    def search_employees(self, name_pattern, limit) -> List[Dict]
    def search_holidays(self, employee_name, state, limit) -> List[Dict]
```

**Key Changes:**
- ❌ Remove `RedirectTransport` class (XML-RPC specific)
- ❌ Remove all `xmlrpc.client` imports
- ✅ Add `requests` library for HTTP
- ✅ Add session management with connection pooling
- ✅ Add retry logic decorator
- ✅ Add file-based caching for get_models

### Protocol Comparison (Why JSON-RPC?)

| Aspect | XML-RPC (OLD) | JSON-RPC (NEW) |
|--------|---------------|----------------|
| **Endpoint** | `/xmlrpc/2/common`, `/xmlrpc/2/object` | `/jsonrpc` (single endpoint) |
| **Request Format** | XML payload (verbose) | JSON payload (compact) |
| **Response Format** | XML parsing (slow) | Native JSON (fast) |
| **Performance** | Baseline (100 req/s) | **+75% throughput (175 req/s)** |
| **Latency** | ~500ms per request | **~285ms (-43% faster)** |
| **Payload Size** | Larger (verbose XML tags) | Smaller (compact JSON) |
| **Python Library** | `xmlrpc.client` (stdlib, limited features) | `requests` (modern, full-featured) |
| **Connection Pooling** | ❌ Not available | ✅ Built-in with Session |
| **Retry Logic** | ❌ Manual implementation | ✅ Easy with requests |
| **Compatibility** | All Odoo versions | Odoo 8.0+ (covers v14-17) |

**Decision: JSON-RPC only** - Performance benefits are too significant to maintain dual protocol support.

## Implementation Plan

### Phase 1: Replace XML-RPC with JSON-RPC (Day 1-2)
**Goal:** Working JSON-RPC client that replaces existing XML-RPC client

**Tasks:**
- [ ] **Backup existing client:** Copy `odoo_cli/client.py` to `odoo_cli/client_xmlrpc_backup.py`
- [ ] **Replace client.py:** Rewrite `OdooClient` class to use JSON-RPC
  - [ ] Remove `xmlrpc.client`, `http.client` imports
  - [ ] Add `requests` library
  - [ ] Implement `/jsonrpc` endpoint calls
  - [ ] Keep exact same method signatures (search, read, execute, etc.)
- [ ] **Authentication:** Implement JSON-RPC login flow
- [ ] **Core methods:** execute_kw, search, read, search_read, search_count, fields_get
- [ ] **Add requests to pyproject.toml:** `requests>=2.31.0`

**Deliverables:**
- ✅ Functional JSON-RPC client with same interface
- ✅ All existing commands work without modification
- ✅ XML-RPC code archived (not deleted yet)

### Phase 2: Performance Optimizations (Day 2-3)
**Goal:** Maximize JSON-RPC performance with connection pooling and caching

**Tasks:**
- [ ] **Connection pooling:** Use `requests.Session` per client instance
- [ ] **Retry logic:** Decorator for automatic retry (2s delay, max 3 retries)
  ```python
  @retry_on_network_error(max_retries=3, delay=2)
  def _jsonrpc_call(self, payload):
      ...
  ```
- [ ] **Response caching for get_models:**
  - Cache location: `~/.odoo-cli/cache/models_{url}_{db}_hash.json`
  - TTL: 24 hours
  - Auto-expire on read
- [ ] **Timeout handling:** Proper timeout configuration (30s default)
- [ ] **SSL verification:** Configurable SSL verification

**Deliverables:**
- ✅ Connection pooling active
- ✅ Automatic retry on network errors
- ✅ Model list caching (24h)
- ✅ Performance boost confirmed

### Phase 3: Testing & Validation (Day 3-4)
**Goal:** Ensure all functionality works correctly with JSON-RPC

**Tasks:**
- [ ] **Unit tests:** All client methods
- [ ] **Integration tests:** Test against real Odoo v16 odoo.sh instance
- [ ] **Command tests:** Run all CLI commands (execute, search, read, get-models, etc.)
- [ ] **Performance benchmarks:**
  ```bash
  # Before (XML-RPC): ~500ms
  time odoo search-count res.partner
  # After (JSON-RPC): ~285ms (target)
  ```
- [ ] **Error handling tests:** Network errors, auth errors, invalid requests
- [ ] **Multi-version testing:** Test on v14, 15, 16, 17 (focus on v16)

**Deliverables:**
- ✅ All tests passing
- ✅ Performance improvement ≥70% confirmed
- ✅ Works on Odoo v14-17

### Phase 4: Documentation & Release (Day 4-5)
**Goal:** Document changes and release v1.0.0

**Tasks:**
- [ ] **Update README:**
  - Mention JSON-RPC (not XML-RPC)
  - Update performance claims
  - Installation instructions
- [ ] **CHANGELOG.md:** Document breaking change (v0.2.0 → v1.0.0)
- [ ] **Migration note:** Simple notice that v1.0.0 uses JSON-RPC
- [ ] **Delete old XML-RPC code:** Remove `client_xmlrpc_backup.py`
- [ ] **Update examples:** Ensure all examples work
- [ ] **Version bump:** Update to v1.0.0 in pyproject.toml

**Deliverables:**
- ✅ Complete documentation
- ✅ v1.0.0 release ready
- ✅ Clean codebase (no XML-RPC legacy code)

## Technical Details

### JSON-RPC Request Format
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute_kw",
    "args": [
      "database_name",
      123,  // uid
      "password",
      "res.partner",
      "search_read",
      [[["is_company", "=", true]]],
      {"limit": 10, "fields": ["name", "email"]}
    ]
  },
  "id": 1
}
```

### JSON-RPC Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": [
    {"id": 1, "name": "Partner A", "email": "a@example.com"},
    {"id": 2, "name": "Partner B", "email": "b@example.com"}
  ]
}
```

### Error Handling

**Retry Strategy:**
- **Method:** Fixed interval retry
- **Delay:** 2 seconds between attempts
- **Max Retries:** 3 attempts total
- **Scope:** All network/timeout errors
- **Non-retryable:** Authentication errors, invalid request format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": 200,
    "message": "Odoo Server Error",
    "data": {
      "name": "odoo.exceptions.AccessError",
      "message": "Access Denied",
      "debug": "Traceback..."
    }
  }
}
```

## Testing Strategy

### Unit Tests
- [ ] JSON-RPC client initialization
- [ ] Authentication flow (`/jsonrpc` endpoint, login method)
- [ ] All CRUD operations (execute_kw, search, read, search_read, search_count, fields_get)
- [ ] Error handling (network errors, auth errors, Odoo exceptions)
- [ ] Retry logic (2s delay, max 3 retries)
- [ ] Timeout handling (30s default)
- [ ] SSL verification (configurable)
- [ ] Connection pooling (Session reuse)
- [ ] Cache functionality (get_models 24h TTL)

### Integration Tests
- [ ] Test against real Odoo v16 odoo.sh instance (primary target)
- [ ] Test on v14, v15, v17 (compatibility check)
- [ ] All CLI commands work (execute, search, read, get-models, etc.)
- [ ] Large dataset handling (1000+ records)
- [ ] Connection failures and retry behavior
- [ ] Cache hit/miss behavior

### Performance Tests
- [ ] Response time measurement (target: ~285ms average)
- [ ] Throughput test (target: 175 req/s)
- [ ] Memory usage (should be similar or better than XML-RPC)
- [ ] Connection pooling benefit (measure session reuse)
- [ ] Cache performance (get_models should be instant on cache hit)

### Benchmarking
```bash
# Before migration (v0.1.0 XML-RPC baseline)
time odoo execute res.partner search_count --args '[[]]'
# Expected: ~500ms

# After migration (v1.0.0 JSON-RPC)
time odoo execute res.partner search_count --args '[[]]'
# Target: ~285ms (43% faster)

# Throughput test
for i in {1..100}; do odoo execute res.partner search_count --args '[[]]' & done; wait
# Target: Complete in <1 second (175 req/s)
```

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing workflows | MEDIUM | HIGH | **Accepted** - Major version bump (v1.0.0), clear CHANGELOG, same CLI interface |
| JSON-RPC incompatibility | MEDIUM | LOW | Test across Odoo 14.0, 15.0, 16.0, 17.0 (primary: v16 odoo.sh) |
| Increased dependencies | LOW | HIGH | `requests` is industry standard, stable, well-maintained |
| Performance not as expected | LOW | LOW | Research shows 75% improvement, will benchmark to confirm |
| Users need XML-RPC | LOW | LOW | Can stay on v0.1.0, but JSON-RPC works for all modern Odoo (v14+) |
| Migration resistance | LOW | LOW | Same CLI interface + better performance = easy sell |

## Dependencies

### New Dependencies
```toml
# pyproject.toml
[project]
name = "odoo-xml-cli"  # Keep name for PyPI compatibility
version = "1.0.0"  # MAJOR version bump (breaking change)
description = "High-performance JSON-RPC CLI tool for Odoo"  # Updated description

dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
    "requests>=2.31.0",  # NEW: For JSON-RPC (replaces xmlrpc.client)
]
```

**Removed dependencies:**
- ❌ `xmlrpc.client` - Was stdlib, now removed (use `requests` instead)
- ❌ `http.client` - Was stdlib, now removed (use `requests` instead)

### Version Compatibility
- Odoo: 14.0, 15.0, 16.0, 17.0 (full range for maximum compatibility)
  - **Primary Target:** v16 on odoo.sh (SaaS platform)
  - **Testing Priority:** v16 > v17 > v14 > v15
- Python: 3.10+ (existing)
- requests: 2.31.0+

## Configuration

### Environment Variables
```bash
# .env file - Same as before, no changes needed
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
ODOO_TIMEOUT=30
```

**Note:** `ODOO_PROTOCOL` is removed - JSON-RPC is now the only protocol.

### CLI Usage
```bash
# All commands use JSON-RPC automatically
odoo get-models
odoo search res.partner --domain '[["is_company", "=", true]]'
odoo execute res.partner search_count --args '[[]]'

# No protocol flag needed - JSON-RPC is the only option
```

### Migration from v0.1.0 (XML-RPC) to v1.0.0 (JSON-RPC)

**Breaking Change:** v1.0.0 completely replaces XML-RPC with JSON-RPC.

**What changes:**
- ✅ **For users:** Nothing! Same commands, same CLI interface
- ✅ **Performance:** Automatic 75% throughput improvement
- ❌ **XML-RPC removed:** If you specifically need XML-RPC, stay on v0.1.0

**Migration steps:**
```bash
# 1. Backup your current installation (optional)
pip show odoo-xml-cli  # Check current version

# 2. Update to v1.0.0
pip install --upgrade odoo-xml-cli

# 3. Test - commands work exactly the same
odoo get-models

# That's it! 75% faster automatically.
```

**Why JSON-RPC only?**
- 🚀 75% higher throughput (100 → 175 req/s)
- ⚡ 43% faster response times (500ms → 285ms)
- 🎯 Simpler codebase, easier maintenance
- 🏢 Industry standard (Odoo web client uses JSON-RPC exclusively)

## Documentation Updates

### README.md
- [ ] Update description: "JSON-RPC CLI tool for Odoo" (remove XML-RPC mention)
- [ ] Add performance claims: 75% higher throughput, 43% faster
- [ ] Update installation instructions (no changes needed, works the same)
- [ ] Add "Why JSON-RPC?" section with comparison table
- [ ] Mention Odoo v14-17 compatibility (primary: v16 odoo.sh)

### CHANGELOG.md
```markdown
## [1.0.0] - 2025-11-XX

### 🚀 Breaking Changes
- **Complete migration to JSON-RPC** - XML-RPC removed
- 75% higher throughput (100 → 175 requests/second)
- 43% faster response times (500ms → 285ms average)

### ✨ Added
- Connection pooling with persistent `requests.Session`
- Automatic retry logic (2s delay, max 3 retries)
- Response caching for get_models (24h TTL, file-based)
- Tested on Odoo v14-17 (primary target: v16 odoo.sh)

### 🔧 Changed
- Replaced `xmlrpc.client` with `requests` library
- Single `/jsonrpc` endpoint (was `/xmlrpc/2/common` and `/xmlrpc/2/object`)
- Updated `pyproject.toml` dependency: `requests>=2.31.0`

### ❌ Removed
- XML-RPC protocol support (use v0.1.0 if specifically needed)
- `--protocol` flag (JSON-RPC is now the only option)
- `ODOO_PROTOCOL` environment variable (no longer needed)
- `RedirectTransport` class (XML-RPC specific)

### 📝 Note
**Migration from v0.1.0:** CLI commands work exactly the same way. Simply upgrade and enjoy 75% better performance. No configuration changes needed.
```

## Future Enhancements

### Phase 5 (Future)
- [ ] WebSocket support for real-time updates
- [ ] GraphQL-style query language
- [ ] Batch request API
- [ ] Extended caching layer (beyond get_models)
- [ ] Cache invalidation commands (`odoo cache clear`)

### Caching Strategy

**get_models Response Caching:**
- **Duration:** 24 hours (86400 seconds)
- **Storage:** File-based cache in `~/.odoo-cli/cache/`
- **Key:** Hash of `(url, db)` tuple
- **Rationale:** Model lists rarely change in production; maximize cache benefit
- **Invalidation:** Automatic expiry after 24h, or manual via future cache commands

## References

- [Perplexity Research: JSON-RPC vs XML-RPC Performance](internal)
- [Odoo JSON-RPC Documentation](https://www.odoo.com/documentation/16.0/developer/reference/external_api.html)
- [odooly Implementation](https://github.com/tinyerp/odooly)
- [Odoo Web Client Source](https://github.com/odoo/odoo/blob/16.0/addons/web/static/src/core/network/rpc.js)

## Approval & Sign-off

- [x] Technical review complete - Clarifications answered (5/5)
- [x] Architecture approved - JSON-RPC only, simplified approach
- [ ] Performance benchmarks validated - Will validate during Phase 3
- [ ] Documentation complete - Will complete during Phase 4
- [x] Ready for implementation - Spec is clear and comprehensive

---

**Next Steps:**
1. ✅ Review this specification - **COMPLETE** (clarified 5 questions)
2. Create feature branch: `feature/002-jsonrpc-migration` (already exists: `002-jsonrpc-migration`)
3. Begin Phase 1: Replace XML-RPC with JSON-RPC (Day 1-2)
4. Implementation timeline: **4-5 days total**
   - Phase 1: Day 1-2 (Core JSON-RPC client)
   - Phase 2: Day 2-3 (Performance optimizations)
   - Phase 3: Day 3-4 (Testing & validation)
   - Phase 4: Day 4-5 (Documentation & release v1.0.0)
