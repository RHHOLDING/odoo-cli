# Tasks: JSON-RPC Migration (Complete Replacement)

**Feature**: Replace XML-RPC with JSON-RPC for 75% performance improvement
**Spec**: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/specs/002-jsonrpc-migration/spec.md`
**Version**: v1.0.0 (breaking change from v0.1.0)

## Summary
Complete migration from XML-RPC to JSON-RPC protocol. This is a **replacement**, not an addition - XML-RPC code will be removed. All existing CLI commands continue to work with the same interface.

**Performance Targets:**
- 75% higher throughput (100 → 175 req/s)
- 43% faster response times (500ms → 285ms)

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Project root**: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/`
- **Source**: `odoo_cli/` (Python package)
- **Tests**: `tests/` (pytest structure)
- **Cache**: `~/.odoo-cli/cache/` (user home directory)

---

## Phase 1: Replace XML-RPC with JSON-RPC (Day 1-2)
**Goal:** Working JSON-RPC client that replaces existing XML-RPC client

### Setup & Backup
- [ ] T001 Backup existing XML-RPC client: Copy `odoo_cli/client.py` to `odoo_cli/client_xmlrpc_backup.py`
- [ ] T002 Update pyproject.toml: Add `requests>=2.31.0` to dependencies, update version to `1.0.0`, update description to mention JSON-RPC

### Core JSON-RPC Client Implementation
**File**: `odoo_cli/client.py` (complete rewrite)

- [ ] T003 Remove XML-RPC imports and add JSON-RPC imports in odoo_cli/client.py
  - Remove: `xmlrpc.client`, `http.client`, `socket`
  - Add: `requests`, `json`, `hashlib` (for caching), `time` (for retry)
  - Keep: `typing`, `os`, `re`, `urllib.parse`

- [ ] T004 Rewrite OdooClient.__init__ to use requests.Session
  - Initialize `self.session = requests.Session()`
  - Configure timeout and SSL verification on session
  - Remove XML-RPC transport setup
  - Keep same method signature: `__init__(url, db, username, password, timeout=30, verify_ssl=True)`

- [ ] T005 Implement JSON-RPC authentication in OdooClient.connect()
  - Endpoint: `POST {url}/jsonrpc`
  - Method: `call` with service=`common`, method=`login`
  - Request payload:
    ```json
    {
      "jsonrpc": "2.0",
      "method": "call",
      "params": {"service": "common", "method": "login", "args": [db, username, password]},
      "id": 1
    }
    ```
  - Store uid from response
  - Raise appropriate errors on auth failure

- [ ] T006 Implement JSON-RPC execute_kw wrapper in OdooClient._execute()
  - Endpoint: `POST {url}/jsonrpc`
  - Method: `call` with service=`object`, method=`execute_kw`
  - Request payload format:
    ```json
    {
      "jsonrpc": "2.0",
      "method": "call",
      "params": {
        "service": "object",
        "method": "execute_kw",
        "args": [db, uid, password, model, method, args, kwargs]
      },
      "id": <counter>
    }
    ```
  - Parse JSON response and extract `result`
  - Handle error responses (check for `error` key)

- [ ] T007 [P] Implement OdooClient.execute() method
  - Wrapper around `_execute()`
  - Keep same signature: `execute(model, method, *args, **kwargs)`
  - File: `odoo_cli/client.py` lines ~106-119

- [ ] T008 [P] Implement OdooClient.search() method
  - Uses `_execute(model, 'search', [domain], **kwargs)`
  - Keep same signature: `search(model, domain, offset, limit, order)`
  - File: `odoo_cli/client.py` lines ~121-149

- [ ] T009 [P] Implement OdooClient.read() method
  - Uses `_execute(model, 'read', ids, kwargs)`
  - Keep same signature: `read(model, ids, fields)`
  - File: `odoo_cli/client.py` lines ~151-172

- [ ] T010 [P] Implement OdooClient.search_read() method
  - Uses `_execute(model, 'search_read', [domain], **kwargs)`
  - Keep same signature: `search_read(model, domain, fields, offset, limit, order)`
  - File: `odoo_cli/client.py` lines ~174-209

- [ ] T011 [P] Implement OdooClient.search_count() method
  - Uses `_execute(model, 'search_count', [domain])`
  - Keep same signature: `search_count(model, domain)`
  - File: `odoo_cli/client.py` lines ~211-223

- [ ] T012 [P] Implement OdooClient.fields_get() method
  - Uses `_execute(model, 'fields_get', [], kwargs)`
  - Keep same signature: `fields_get(model, allfields)`
  - File: `odoo_cli/client.py` lines ~225-244

- [ ] T013 Implement OdooClient.get_models() method (without caching yet)
  - Uses search + read on 'ir.model'
  - Keep same signature: `get_models()`
  - File: `odoo_cli/client.py` lines ~246-258
  - Note: Caching will be added in Phase 2

- [ ] T014 [P] Implement OdooClient.search_employees() method
  - Uses `search_read()` on 'hr.employee'
  - Keep same signature: `search_employees(name_pattern, limit)`
  - File: `odoo_cli/client.py` lines ~260-274

- [ ] T015 [P] Implement OdooClient.search_holidays() method
  - Uses `search()` and `search_read()` on 'hr.leave'
  - Keep same signature: `search_holidays(employee_name, state, limit)`
  - File: `odoo_cli/client.py` lines ~276-312

- [ ] T016 Delete RedirectTransport class (XML-RPC specific)
  - Remove lines ~315-375 in odoo_cli/client.py
  - This class is not needed for JSON-RPC

- [ ] T017 Keep get_odoo_client() factory function unchanged
  - Should work as-is with new OdooClient
  - File: `odoo_cli/client.py` lines ~378-430

### Validation
- [ ] T018 Manual test: Verify all CLI commands work with JSON-RPC client
  ```bash
  odoo get-models
  odoo search res.partner --domain '[["is_company", "=", true]]' --limit 5
  odoo execute res.partner search_count --args '[[]]'
  odoo search-employee "John"
  ```

---

## Phase 2: Performance Optimizations (Day 2-3)
**Goal:** Maximize JSON-RPC performance with connection pooling, retry logic, and caching

### Connection Pooling
- [ ] T019 Configure requests.Session for connection pooling in OdooClient.__init__()
  - Session is already created in T004
  - Configure adapter with pool settings:
    ```python
    from requests.adapters import HTTPAdapter
    adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1)
    self.session.mount('http://', adapter)
    self.session.mount('https://', adapter)
    ```
  - File: `odoo_cli/client.py`

### Retry Logic
- [ ] T020 Create retry decorator in odoo_cli/client.py
  - Decorator: `retry_on_network_error(max_retries=3, delay=2)`
  - Catches: `requests.exceptions.ConnectionError`, `requests.exceptions.Timeout`
  - Retries with 2s delay between attempts
  - Does NOT retry: Authentication errors, 4xx client errors
  - Add to top of odoo_cli/client.py

- [ ] T021 Apply retry decorator to OdooClient._execute() method
  - Wrap the `session.post()` call with retry decorator
  - File: `odoo_cli/client.py`

### Response Caching for get_models
- [ ] T022 Create cache utility module in odoo_cli/cache.py
  - Function: `get_cached(cache_key: str, ttl_seconds: int) -> Optional[Any]`
  - Function: `set_cached(cache_key: str, data: Any, ttl_seconds: int) -> None`
  - Cache location: `~/.odoo-cli/cache/`
  - File format: JSON files named `{cache_key}.json`
  - Include timestamp in cache file for TTL check
  - Create cache directory if not exists

- [ ] T023 Implement caching in OdooClient.get_models() method
  - Cache key: `models_{hash(url + db)}`
  - TTL: 24 hours (86400 seconds)
  - Check cache before executing search/read
  - Store result in cache after successful fetch
  - File: `odoo_cli/client.py`

### Timeout & SSL Configuration
- [ ] T024 Configure timeout on requests.Session in OdooClient.__init__()
  - Should already be configured in T004
  - Verify: `timeout` parameter is passed to `session.post()` calls
  - Default: 30 seconds
  - File: `odoo_cli/client.py`

- [ ] T025 Configure SSL verification on requests.Session in OdooClient.__init__()
  - Should already be configured in T004
  - Verify: `verify` parameter is passed to `session.post()` calls
  - Based on `verify_ssl` constructor parameter
  - File: `odoo_cli/client.py`

### Performance Validation
- [ ] T026 Benchmark JSON-RPC performance against targets
  ```bash
  # Response time test (target: ~285ms)
  time odoo execute res.partner search_count --args '[[]]'

  # Throughput test (target: 175 req/s)
  # Run 100 requests concurrently, should complete in <1s
  for i in {1..100}; do odoo execute res.partner search_count --args '[[]]' & done; wait
  ```
  - Document results in spec.md
  - Compare against XML-RPC baseline (~500ms, 100 req/s)

---

## Phase 3: Testing & Validation (Day 3-4)
**Goal:** Ensure all functionality works correctly with JSON-RPC

### Unit Tests for JSON-RPC Client
- [ ] T027 [P] Unit test: OdooClient initialization in tests/unit/test_client_init.py
  - Test: Session created
  - Test: Timeout configured
  - Test: SSL verification configured
  - Test: URL normalization (add https:// if missing)

- [ ] T028 [P] Unit test: JSON-RPC authentication in tests/unit/test_client_auth.py
  - Test: Successful login returns uid
  - Test: Failed login raises ValueError
  - Test: Network error raises ConnectionError
  - Mock: requests.Session.post()

- [ ] T029 [P] Unit test: execute_kw wrapper in tests/unit/test_client_execute.py
  - Test: Correct JSON-RPC payload format
  - Test: Result extraction from response
  - Test: Error handling (Odoo exceptions)
  - Mock: requests.Session.post()

- [ ] T030 [P] Unit test: Retry logic in tests/unit/test_client_retry.py
  - Test: Retries on ConnectionError (max 3 times)
  - Test: 2s delay between retries
  - Test: Does not retry on 4xx errors
  - Test: Does not retry on auth errors
  - Mock: requests.Session.post() with side effects

- [ ] T031 [P] Unit test: Cache utilities in tests/unit/test_cache.py
  - Test: Cache hit returns data
  - Test: Cache miss returns None
  - Test: Expired cache returns None
  - Test: Cache directory created if not exists

- [ ] T032 [P] Unit test: get_models caching in tests/unit/test_client_get_models.py
  - Test: First call hits Odoo API
  - Test: Second call hits cache (no API call)
  - Test: Cache expires after 24 hours
  - Mock: OdooClient._execute() and cache utilities

### Integration Tests (Real Odoo v16 Instance)
- [ ] T033 [P] Integration test: All CRUD operations in tests/integration/test_jsonrpc_crud.py
  - Test against: `https://rhholding-ac-mail-deploy-25766690.dev.odoo.com`
  - Test: search() returns IDs
  - Test: read() returns records
  - Test: search_read() returns records
  - Test: search_count() returns count
  - Test: fields_get() returns field definitions
  - Use: Real credentials from .env

- [ ] T034 [P] Integration test: CLI commands work in tests/integration/test_cli_commands_jsonrpc.py
  - Test: `odoo get-models` returns model list
  - Test: `odoo search res.partner` returns partners
  - Test: `odoo execute res.partner search_count` returns count
  - Test: `odoo search-employee "John"` returns employees
  - Use: subprocess to run CLI commands

- [ ] T035 [P] Integration test: Large dataset handling in tests/integration/test_large_dataset.py
  - Test: 1000+ records handled correctly
  - Test: No memory issues
  - Test: Performance acceptable
  - Model: stock.picking (likely has many records)

- [ ] T036 [P] Integration test: Connection failures and retry in tests/integration/test_connection_retry.py
  - Test: Retry on network timeout (mock timeout)
  - Test: Proper error message on auth failure
  - Test: Graceful handling of invalid URL

### Multi-Version Testing (v14, v15, v16, v17)
- [ ] T037 Multi-version compatibility test in tests/integration/test_multi_version.py
  - Test: JSON-RPC works on v14 (if instance available)
  - Test: JSON-RPC works on v15 (if instance available)
  - Test: JSON-RPC works on v16 (primary target, already tested)
  - Test: JSON-RPC works on v17 (if instance available)
  - Note: May need separate .env configs or skip tests if instances not available

### Performance Benchmarking
- [ ] T038 Performance benchmark suite in tests/performance/test_benchmarks.py
  - Benchmark: Response time for search_count (target: ~285ms)
  - Benchmark: Throughput for 100 concurrent requests (target: <1s)
  - Benchmark: Memory usage for large dataset (1000+ records)
  - Benchmark: Cache performance (get_models should be <10ms on cache hit)
  - Compare: Against XML-RPC baseline (if backup client available)
  - Generate: Performance report markdown

### Test Coverage
- [ ] T039 Run pytest with coverage report
  ```bash
  pytest --cov=odoo_cli --cov-report=term-missing --cov-report=html
  ```
  - Target: ≥80% coverage for odoo_cli/client.py
  - Target: ≥70% coverage overall
  - Review: Coverage report and add tests for uncovered lines

---

## Phase 4: Documentation & Release (Day 4-5)
**Goal:** Document changes and release v1.0.0

### Update README
- [ ] T040 Update README.md description and overview
  - Change: "XML-RPC CLI tool" → "High-performance JSON-RPC CLI tool"
  - Add: Performance claims (75% faster throughput, 43% faster response)
  - Add: Odoo version compatibility (v14-17, primary: v16)
  - Keep: Installation instructions (same as before)
  - File: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/README.md`

- [ ] T041 Add "Why JSON-RPC?" section to README.md
  - Include: Protocol comparison table from spec.md
  - Explain: Performance benefits
  - Explain: Industry standard (Odoo web client uses JSON-RPC)
  - File: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/README.md`

### Create CHANGELOG
- [ ] T042 Create CHANGELOG.md with v1.0.0 release notes
  - Section: Breaking Changes (XML-RPC → JSON-RPC)
  - Section: Added (connection pooling, retry, caching)
  - Section: Changed (requests library, single endpoint)
  - Section: Removed (XML-RPC support, --protocol flag)
  - Section: Migration guide (simple: upgrade and test)
  - File: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/CHANGELOG.md`

### Update Examples
- [ ] T043 Verify all examples in README work with JSON-RPC
  - Test: Installation example
  - Test: Configuration example (.env)
  - Test: CLI usage examples
  - Update: Any examples that reference XML-RPC
  - File: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/README.md`

### Version Bump & Cleanup
- [ ] T044 Update version to 1.0.0 in pyproject.toml
  - Change: `version = "0.1.0"` → `version = "1.0.0"`
  - Verify: Dependencies include `requests>=2.31.0`
  - Verify: Description mentions JSON-RPC
  - File: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/pyproject.toml`

- [ ] T045 Delete XML-RPC backup file
  - Delete: `odoo_cli/client_xmlrpc_backup.py`
  - This file was created in T001 as a backup
  - After successful testing, it's no longer needed

### Documentation Polish
- [ ] T046 [P] Update docstrings in odoo_cli/client.py
  - Update: Class docstring to mention JSON-RPC (not XML-RPC)
  - Verify: Method docstrings are accurate
  - Add: Examples in docstrings where helpful

- [ ] T047 [P] Create migration guide document in MIGRATION.md
  - Section: What changed (XML-RPC → JSON-RPC)
  - Section: What stayed the same (CLI interface)
  - Section: How to upgrade (pip install --upgrade)
  - Section: Troubleshooting
  - File: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/MIGRATION.md`

### Final Testing
- [ ] T048 End-to-end smoke test of all CLI commands
  ```bash
  # Test all commands with real Odoo instance
  odoo get-models
  odoo get-fields res.partner
  odoo search res.partner --domain '[["is_company", "=", true]]' --limit 5
  odoo read res.partner --ids 1,2,3
  odoo execute res.partner search_count --args '[[]]'
  odoo search-employee "John"
  odoo search-holidays --employee "John"
  odoo shell  # Interactive shell test
  ```

- [ ] T049 Verify installation from clean environment
  ```bash
  # In fresh Python 3.10+ venv
  pip install -e .
  odoo --help
  odoo get-models  # Should work
  ```

---

## Phase 5: Release (Day 5)
**Goal:** Release v1.0.0 to production

### Git Workflow
- [ ] T050 Commit all changes to 002-jsonrpc-migration branch
  - Include: All code changes
  - Include: All documentation updates
  - Include: CHANGELOG.md
  - Message format: See commit message template in spec.md

- [ ] T051 Push 002-jsonrpc-migration branch to GitHub
  ```bash
  git push origin 002-jsonrpc-migration
  ```

- [ ] T052 Create Pull Request: 002-jsonrpc-migration → v16 (main branch)
  - Title: "JSON-RPC Migration v1.0.0 - Complete XML-RPC Replacement"
  - Body: Include summary from CHANGELOG.md
  - Body: Include performance benchmarks
  - Body: Link to spec.md
  - Reviewers: Add appropriate reviewers

- [ ] T053 After PR approval: Merge to v16 branch
  - Merge strategy: Squash or merge commit (as per project policy)
  - Delete: 002-jsonrpc-migration branch after merge

- [ ] T054 Tag release v1.0.0 on v16 branch
  ```bash
  git tag -a v1.0.0 -m "JSON-RPC migration - 75% performance improvement"
  git push origin v1.0.0
  ```

### PyPI Release (if applicable)
- [ ] T055 Build distribution packages
  ```bash
  python -m build
  # Creates dist/odoo-xml-cli-1.0.0.tar.gz and .whl
  ```

- [ ] T056 Upload to PyPI (if project is published)
  ```bash
  python -m twine upload dist/*
  # Note: Requires PyPI credentials
  ```

---

## Parallel Execution Examples

### Phase 1 - Core Methods (T007-T015)
All these methods can be implemented in parallel since they're independent:
```bash
# Terminal 1
claude code "Implement T007: OdooClient.execute()"

# Terminal 2
claude code "Implement T008: OdooClient.search()"

# Terminal 3
claude code "Implement T009: OdooClient.read()"
```

### Phase 3 - Unit Tests (T027-T032)
All unit tests can be written in parallel:
```bash
# Terminal 1
claude code "Implement T027: Unit test client initialization"

# Terminal 2
claude code "Implement T028: Unit test authentication"

# Terminal 3
claude code "Implement T029: Unit test execute_kw"
```

### Phase 3 - Integration Tests (T033-T036)
Integration tests can run in parallel with different models:
```bash
# Terminal 1
claude code "Implement T033: Integration test CRUD operations"

# Terminal 2
claude code "Implement T034: Integration test CLI commands"
```

---

## Dependencies Between Tasks

### Critical Path (Must be sequential)
1. T001-T002 (Setup) → T003-T006 (Core client) → T007-T017 (Methods) → T018 (Validation)
2. T019 (Session) must be done before T020-T021 (Retry)
3. T022 (Cache module) must be done before T023 (Use cache)
4. T027-T032 (Unit tests) must be done before T033-T038 (Integration tests)
5. T040-T047 (Documentation) can happen anytime after T018 (Basic validation)
6. T050-T054 (Git workflow) must be last

### Independent Workstreams
- **Workstream A**: T003-T017 (Client implementation)
- **Workstream B**: T022 (Cache module) - can start anytime
- **Workstream C**: T027-T032 (Unit tests) - can start after T003-T006
- **Workstream D**: T040-T047 (Documentation) - can start after T018

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All CLI commands work with JSON-RPC client
- [ ] No XML-RPC code in active use (only backup exists)
- [ ] All 13 client methods implemented and working

### Phase 2 Complete When:
- [ ] Connection pooling configured and working
- [ ] Retry logic in place (verified with network error test)
- [ ] get_models returns instantly on cache hit (<10ms)
- [ ] Performance target met: ≥70% throughput improvement

### Phase 3 Complete When:
- [ ] All unit tests passing (≥80% coverage)
- [ ] All integration tests passing
- [ ] Multi-version compatibility confirmed (v14-17)
- [ ] Performance benchmarks documented

### Phase 4 Complete When:
- [ ] README updated with JSON-RPC information
- [ ] CHANGELOG.md created with v1.0.0 notes
- [ ] All examples tested and working
- [ ] Version bumped to 1.0.0
- [ ] XML-RPC backup deleted

### Phase 5 Complete When:
- [ ] PR merged to v16 branch
- [ ] Release v1.0.0 tagged
- [ ] PyPI package published (if applicable)

---

## Notes

### Key Design Decisions
1. **JSON-RPC only** - No XML-RPC backward compatibility
2. **Major version bump** - v0.1.0 → v1.0.0 (breaking change)
3. **Same CLI interface** - Users don't need to change commands
4. **Connection pooling** - Single persistent Session per client instance
5. **Retry logic** - Fixed interval (2s delay, max 3 retries)
6. **Caching** - Only for get_models (24h TTL)

### Testing Strategy
- **Unit tests first** - Mock all HTTP calls
- **Integration tests second** - Real Odoo v16 instance
- **Multi-version last** - If instances available
- **Performance always** - Benchmark at every step

### Performance Targets
- **Throughput**: 175 req/s (75% improvement from 100 req/s)
- **Latency**: ~285ms (43% improvement from ~500ms)
- **Cache hit**: <10ms (get_models)
- **Memory**: Similar or better than XML-RPC

### Risk Mitigation
- **Backup created** (T001) - Can rollback if needed
- **Tests first** (Phase 3) - Catch issues early
- **Manual testing** (T018, T048) - Verify real-world usage
- **Multi-version testing** (T037) - Ensure compatibility

---

**Total Tasks**: 56 (T001-T056)
**Estimated Time**: 4-5 days
**Parallelizable**: 23 tasks marked [P]
**Critical Path**: ~30 tasks (must be sequential)
