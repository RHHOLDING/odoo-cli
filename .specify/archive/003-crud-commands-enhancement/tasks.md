# Implementation Tasks: User-Friendly CRUD Commands & Batch Operations

**Spec:** 003-crud-commands-enhancement
**Created:** 2025-11-21
**Est. Duration:** 7 days

---

## Phase 1: Foundation & Field Parsing (Day 1)

### T001: Create Field Parser Utility
**File:** `odoo_cli/utils/field_parser.py`
**Priority:** HIGH
**Dependencies:** None
**Est:** 2 hours

**Tasks:**
- [ ] Create `parse_field_values()` function with type inference
  - Parse `key=value` syntax
  - Detect types: int, float, bool, string
  - Handle quoted strings
  - Support comma-separated lists
- [ ] Create `validate_fields()` function for pre-flight checks
  - Check field existence via `fields_get()`
  - Validate field types match
  - Check readonly constraints
  - Provide helpful error messages
- [ ] Create `is_float()` helper for float detection
- [ ] Add comprehensive docstrings and examples

**Acceptance Criteria:**
- ✅ Parses `name="Test"` → `{'name': 'Test'}`
- ✅ Parses `partner_id=123` → `{'partner_id': 123}`
- ✅ Parses `active=true` → `{'active': True}`
- ✅ Validates field existence before sending
- ✅ Raises clear errors for invalid fields

---

### T002: Unit Tests for Field Parser
**File:** `tests/unit/test_field_parser.py`
**Priority:** HIGH
**Dependencies:** T001
**Est:** 1 hour

**Tasks:**
- [ ] Test `parse_field_values()` with various inputs
  - String fields with quotes
  - Integer fields
  - Boolean fields (true/false)
  - Float fields
  - Edge cases (empty, malformed)
- [ ] Test `validate_fields()` function
  - Valid fields pass
  - Invalid fields raise ValueError
  - Readonly fields raise ValueError
  - Type mismatches detected
- [ ] Mock `fields_get()` responses for testing
- [ ] Achieve 100% coverage on field_parser.py

**Acceptance Criteria:**
- ✅ All test cases pass
- ✅ 100% code coverage
- ✅ Edge cases handled

---

## Phase 2: CREATE Command (Day 1-2)

### T003: Implement CREATE Command
**File:** `odoo_cli/commands/create.py`
**Priority:** HIGH
**Dependencies:** T001
**Est:** 3 hours

**Tasks:**
- [ ] Create `create.py` with Click command decorator
- [ ] Add `--fields` option (multiple values supported)
- [ ] Add `--json` flag for JSON output
- [ ] Add `--no-validate` flag to skip validation
- [ ] Implement field parsing logic
- [ ] Implement field validation (optional)
- [ ] Call `client.execute(model, 'create', field_dict)`
- [ ] Add rich console output with success indicators
- [ ] Add error handling with helpful messages
- [ ] Add comprehensive docstring with examples

**Command Syntax:**
```bash
odoo create MODEL --fields key=value [--fields key=value ...] [--json] [--no-validate]
```

**Examples:**
```bash
odoo create res.partner --fields name="Test" email="test@test.com"
odoo create sale.order --fields partner_id=123 date_order="2025-11-21"
```

**Acceptance Criteria:**
- ✅ Command creates record successfully
- ✅ Returns record ID
- ✅ Validates fields by default
- ✅ JSON mode outputs valid JSON
- ✅ Helpful error messages on failure

---

### T004: Unit Tests for CREATE Command
**File:** `tests/unit/test_commands_create.py`
**Priority:** HIGH
**Dependencies:** T003
**Est:** 2 hours

**Tasks:**
- [ ] Test successful record creation
- [ ] Test multiple `--fields` options
- [ ] Test field validation (valid/invalid fields)
- [ ] Test `--no-validate` flag
- [ ] Test `--json` output format
- [ ] Test error handling (invalid model, network errors)
- [ ] Mock `client.execute()` and `fields_get()`
- [ ] Achieve 90% coverage

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ 90% code coverage
- ✅ Mock Odoo client used

---

### T005: Register CREATE Command
**File:** `odoo_cli/cli.py`
**Priority:** HIGH
**Dependencies:** T003
**Est:** 15 minutes

**Tasks:**
- [ ] Import `create` command from `odoo_cli.commands.create`
- [ ] Add `cli.add_command(create.create)` registration
- [ ] Verify command appears in `odoo --help`
- [ ] Test command execution

**Acceptance Criteria:**
- ✅ `odoo create` command available
- ✅ Help text displays correctly
- ✅ Command executes without errors

---

## Phase 3: UPDATE Command (Day 2)

### T006: Implement UPDATE Command
**File:** `odoo_cli/commands/update.py`
**Priority:** HIGH
**Dependencies:** T001
**Est:** 3 hours

**Tasks:**
- [ ] Create `update.py` with Click command decorator
- [ ] Add `MODEL` and `IDS` arguments (comma-separated IDs)
- [ ] Add `--fields` option (multiple values supported)
- [ ] Add `--json` flag for JSON output
- [ ] Add `--no-validate` flag to skip validation
- [ ] Parse comma-separated IDs into list
- [ ] Implement field parsing logic
- [ ] Implement field validation (optional)
- [ ] Call `client.execute(model, 'write', ids, field_dict)`
- [ ] Add rich console output with success indicators
- [ ] Add error handling with helpful messages

**Command Syntax:**
```bash
odoo update MODEL ID[,ID,...] --fields key=value [--fields key=value ...] [--json] [--no-validate]
```

**Examples:**
```bash
odoo update sale.order 123 --fields state="done"
odoo update res.partner 1,2,3 --fields active=false
```

**Acceptance Criteria:**
- ✅ Command updates single record
- ✅ Command updates multiple records
- ✅ Validates fields by default
- ✅ JSON mode outputs valid JSON
- ✅ Helpful error messages on failure

---

### T007: Unit Tests for UPDATE Command
**File:** `tests/unit/test_commands_update.py`
**Priority:** HIGH
**Dependencies:** T006
**Est:** 2 hours

**Tasks:**
- [ ] Test single record update
- [ ] Test multiple record update (comma-separated IDs)
- [ ] Test field validation
- [ ] Test `--no-validate` flag
- [ ] Test `--json` output format
- [ ] Test error handling (invalid IDs, network errors)
- [ ] Mock `client.execute()` and `fields_get()`
- [ ] Achieve 90% coverage

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ 90% code coverage
- ✅ Mock Odoo client used

---

### T008: Register UPDATE Command
**File:** `odoo_cli/cli.py`
**Priority:** HIGH
**Dependencies:** T006
**Est:** 15 minutes

**Tasks:**
- [ ] Import `update` command from `odoo_cli.commands.update`
- [ ] Add `cli.add_command(update.update)` registration
- [ ] Verify command appears in `odoo --help`
- [ ] Test command execution

**Acceptance Criteria:**
- ✅ `odoo update` command available
- ✅ Help text displays correctly
- ✅ Command executes without errors

---

## Phase 4: DELETE Command (Day 2)

### T009: Implement DELETE Command
**File:** `odoo_cli/commands/delete.py`
**Priority:** HIGH
**Dependencies:** T001
**Est:** 2 hours

**Tasks:**
- [ ] Create `delete.py` with Click command decorator
- [ ] Add `MODEL` and `IDS` arguments (comma-separated IDs)
- [ ] Add `--force` flag to skip confirmation
- [ ] Add `--json` flag for JSON output
- [ ] Parse comma-separated IDs into list
- [ ] Add confirmation prompt (unless `--force` or `--json`)
- [ ] Call `client.execute(model, 'unlink', ids)`
- [ ] Add rich console output with success indicators
- [ ] Add error handling with helpful messages

**Command Syntax:**
```bash
odoo delete MODEL ID[,ID,...] [--force] [--json]
```

**Examples:**
```bash
odoo delete res.partner 456
odoo delete res.partner 456,457,458
odoo delete sale.order 123 --force
```

**Acceptance Criteria:**
- ✅ Command deletes single record
- ✅ Command deletes multiple records
- ✅ Confirmation prompt shown (unless --force)
- ✅ JSON mode outputs valid JSON
- ✅ Helpful error messages on failure

---

### T010: Unit Tests for DELETE Command
**File:** `tests/unit/test_commands_delete.py`
**Priority:** HIGH
**Dependencies:** T009
**Est:** 1.5 hours

**Tasks:**
- [ ] Test single record deletion
- [ ] Test multiple record deletion
- [ ] Test confirmation prompt (mock `click.confirm()`)
- [ ] Test `--force` flag bypasses confirmation
- [ ] Test `--json` output format
- [ ] Test error handling (invalid IDs, network errors)
- [ ] Mock `client.execute()`
- [ ] Achieve 90% coverage

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ 90% code coverage
- ✅ Confirmation logic tested

---

### T011: Register DELETE Command
**File:** `odoo_cli/cli.py`
**Priority:** HIGH
**Dependencies:** T009
**Est:** 15 minutes

**Tasks:**
- [ ] Import `delete` command from `odoo_cli.commands.delete`
- [ ] Add `cli.add_command(delete.delete)` registration
- [ ] Verify command appears in `odoo --help`
- [ ] Test command execution

**Acceptance Criteria:**
- ✅ `odoo delete` command available
- ✅ Help text displays correctly
- ✅ Command executes without errors

---

## Phase 5: Manual Testing & Integration (Day 3)

### T012: Manual Testing on Real Odoo Instance
**Priority:** HIGH
**Dependencies:** T005, T008, T011
**Est:** 3 hours

**Test Scenarios:**

1. **CREATE Partner:**
   ```bash
   odoo create res.partner --fields name="Test Partner" email="test@test.com" phone="+49123"
   ```
   - ✅ Verify partner created with correct fields
   - ✅ Verify ID returned

2. **UPDATE Partner:**
   ```bash
   odoo update res.partner {ID} --fields name="Updated Name"
   ```
   - ✅ Verify partner name updated
   - ✅ Verify success message

3. **UPDATE Multiple Partners:**
   ```bash
   odoo update res.partner {ID1},{ID2},{ID3} --fields active=false
   ```
   - ✅ Verify all partners deactivated
   - ✅ Verify count correct

4. **DELETE Partner:**
   ```bash
   odoo delete res.partner {ID}
   ```
   - ✅ Verify confirmation prompt shown
   - ✅ Verify partner deleted after confirmation

5. **DELETE with --force:**
   ```bash
   odoo delete res.partner {ID} --force
   ```
   - ✅ Verify no confirmation prompt
   - ✅ Verify immediate deletion

6. **Field Validation:**
   ```bash
   odoo create res.partner --fields invalid_field="Test"
   ```
   - ✅ Verify error message: "Field 'invalid_field' does not exist"
   - ✅ Verify suggestion: "Run: odoo get-fields res.partner"

7. **Type Validation:**
   ```bash
   odoo create res.partner --fields name=123  # Should be string
   ```
   - ✅ Verify type conversion or warning

8. **JSON Output:**
   ```bash
   odoo create res.partner --fields name="Test" --json
   ```
   - ✅ Verify valid JSON output
   - ✅ Verify `success` and `id` fields present

**Acceptance Criteria:**
- ✅ All 8 test scenarios pass
- ✅ Commands work on real Odoo instance
- ✅ Error messages are helpful
- ✅ Performance acceptable (<500ms per operation)

---

## Phase 6: Batch Operations (Day 3-4)

### T013: Implement CREATE-BULK Command
**File:** `odoo_cli/commands/create_bulk.py`
**Priority:** HIGH
**Dependencies:** T003
**Est:** 4 hours

**Tasks:**
- [ ] Create `create_bulk.py` with Click command decorator
- [ ] Add `MODEL` argument
- [ ] Add `--file` option (JSON file path)
- [ ] Add `--batch-size` option (default: 100)
- [ ] Add `--json` flag for JSON output
- [ ] Load records from JSON file (validate format)
- [ ] Process records in batches
- [ ] Add progress bar with `rich.progress`
- [ ] Call `client.execute(model, 'create', batch)` per batch
- [ ] Collect all created IDs
- [ ] Add error handling (file not found, invalid JSON, etc.)
- [ ] Add rich console output with summary

**Command Syntax:**
```bash
odoo create-bulk MODEL --file FILE [--batch-size N] [--json]
```

**File Format (JSON array):**
```json
[
  {"name": "Partner 1", "email": "p1@test.com"},
  {"name": "Partner 2", "email": "p2@test.com"}
]
```

**Examples:**
```bash
odoo create-bulk res.partner --file partners.json
odoo create-bulk res.partner -f data.json --batch-size 50
```

**Acceptance Criteria:**
- ✅ Command creates multiple records
- ✅ Progress bar shows during processing
- ✅ Batching works correctly
- ✅ Returns all created IDs
- ✅ JSON mode outputs valid JSON

---

### T014: Unit Tests for CREATE-BULK Command
**File:** `tests/unit/test_commands_create_bulk.py`
**Priority:** HIGH
**Dependencies:** T013
**Est:** 2 hours

**Tasks:**
- [ ] Test successful bulk creation (100 records)
- [ ] Test batching logic (verify batch sizes)
- [ ] Test progress bar rendering
- [ ] Test `--json` output format
- [ ] Test error handling (invalid file, malformed JSON)
- [ ] Mock file I/O and `client.execute()`
- [ ] Achieve 85% coverage

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ 85% code coverage
- ✅ Batching logic verified

---

### T015: Implement UPDATE-BULK Command
**File:** `odoo_cli/commands/update_bulk.py`
**Priority:** MEDIUM
**Dependencies:** T006
**Est:** 4 hours

**Tasks:**
- [ ] Create `update_bulk.py` with Click command decorator
- [ ] Add `MODEL` argument
- [ ] Add `--file` option (JSON file path)
- [ ] Add `--batch-size` option (default: 100)
- [ ] Add `--json` flag for JSON output
- [ ] Load updates from JSON file (validate format)
- [ ] Create `group_by_fields()` utility for optimization
- [ ] Group updates by common field sets
- [ ] Process groups in batches
- [ ] Add progress bar
- [ ] Call `client.execute(model, 'write', ids, fields)` per group
- [ ] Add error handling
- [ ] Add rich console output with summary

**Command Syntax:**
```bash
odoo update-bulk MODEL --file FILE [--batch-size N] [--json]
```

**File Format (JSON object):**
```json
{
  "123": {"name": "Updated Name 1"},
  "124": {"name": "Updated Name 2"}
}
```

**Examples:**
```bash
odoo update-bulk res.partner --file updates.json
odoo update-bulk sale.order -f changes.json --batch-size 50
```

**Acceptance Criteria:**
- ✅ Command updates multiple records
- ✅ Progress bar shows during processing
- ✅ Optimization groups common updates
- ✅ Returns count of updated records
- ✅ JSON mode outputs valid JSON

---

### T016: Unit Tests for UPDATE-BULK Command
**File:** `tests/unit/test_commands_update_bulk.py`
**Priority:** MEDIUM
**Dependencies:** T015
**Est:** 2 hours

**Tasks:**
- [ ] Test successful bulk update (100 records)
- [ ] Test field grouping optimization
- [ ] Test batching logic
- [ ] Test progress bar rendering
- [ ] Test `--json` output format
- [ ] Test error handling (invalid file, malformed JSON)
- [ ] Mock file I/O and `client.execute()`
- [ ] Achieve 85% coverage

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ 85% code coverage
- ✅ Grouping optimization verified

---

### T017: Register Batch Commands
**File:** `odoo_cli/cli.py`
**Priority:** HIGH
**Dependencies:** T013, T015
**Est:** 15 minutes

**Tasks:**
- [ ] Import `create_bulk` and `update_bulk` commands
- [ ] Add command registrations
- [ ] Verify commands appear in `odoo --help`
- [ ] Test command execution

**Acceptance Criteria:**
- ✅ `odoo create-bulk` command available
- ✅ `odoo update-bulk` command available
- ✅ Help text displays correctly

---

### T018: Performance Testing - Batch Operations
**Priority:** HIGH
**Dependencies:** T017
**Est:** 2 hours

**Test Scenarios:**

1. **Create 100 Partners:**
   ```bash
   # Generate test file
   python3 -c "import json; print(json.dumps([{'name': f'Partner {i}', 'email': f'p{i}@test.com'} for i in range(100)]))" > /tmp/partners.json

   # Bulk create
   time odoo create-bulk res.partner --file /tmp/partners.json
   ```
   - ✅ Verify all 100 partners created
   - ✅ Verify time < 10 seconds
   - ✅ Verify progress bar displayed

2. **Create 1000 Partners:**
   ```bash
   # Generate larger test file
   python3 -c "import json; print(json.dumps([{'name': f'Partner {i}', 'email': f'p{i}@test.com'} for i in range(1000)]))" > /tmp/partners_1000.json

   # Bulk create with custom batch size
   time odoo create-bulk res.partner --file /tmp/partners_1000.json --batch-size 50
   ```
   - ✅ Verify all 1000 partners created
   - ✅ Verify time < 60 seconds
   - ✅ Verify batching works (50 per batch)

3. **Update 100 Partners:**
   ```bash
   # Get IDs of created partners
   odoo search res.partner '[["name", "ilike", "Partner %"]]' --json > /tmp/ids.json

   # Generate update file
   python3 -c "import json; ids = json.load(open('/tmp/ids.json')); print(json.dumps({str(id): {'active': False} for id in ids[:100]}))" > /tmp/updates.json

   # Bulk update
   time odoo update-bulk res.partner --file /tmp/updates.json
   ```
   - ✅ Verify all 100 partners updated
   - ✅ Verify time < 10 seconds

**Acceptance Criteria:**
- ✅ 100 records: <10 seconds
- ✅ 1000 records: <60 seconds
- ✅ Progress bars functional
- ✅ No memory issues

---

## Phase 7: Aggregation Helper (Day 5)

### T019: Implement AGGREGATE Command
**File:** `odoo_cli/commands/aggregate.py`
**Priority:** MEDIUM
**Dependencies:** T001
**Est:** 5 hours

**Tasks:**
- [ ] Create `aggregate.py` with Click command decorator
- [ ] Add `MODEL` and `DOMAIN` arguments
- [ ] Add `--sum` option (multiple fields)
- [ ] Add `--avg` option (multiple fields)
- [ ] Add `--count` flag
- [ ] Add `--group-by` option (single field)
- [ ] Add `--batch-size` option (default: 1000)
- [ ] Add `--json` flag for JSON output
- [ ] Parse domain from string
- [ ] Search for matching record IDs
- [ ] Read records in batches with progress bar
- [ ] Implement aggregation logic:
  - Count records per group
  - Sum specified fields per group
  - Calculate averages per group
- [ ] Format results as Rich table (non-JSON mode)
- [ ] Output JSON (JSON mode)
- [ ] Add error handling

**Command Syntax:**
```bash
odoo aggregate MODEL DOMAIN [--sum FIELD] [--avg FIELD] [--count] [--group-by FIELD] [--batch-size N] [--json]
```

**Examples:**
```bash
# Sum October 2025 sales
odoo aggregate sale.order '[["date_order",">=","2025-10-01"]]' --sum amount_total

# Count orders by state
odoo aggregate sale.order '[]' --count --group-by state

# Average order value by partner
odoo aggregate sale.order '[]' --avg amount_total --group-by partner_id
```

**Acceptance Criteria:**
- ✅ Command aggregates data correctly
- ✅ SUM calculation accurate
- ✅ AVG calculation accurate
- ✅ COUNT accurate
- ✅ GROUP BY works correctly
- ✅ Progress bar shows during processing
- ✅ Rich table output formatted well
- ✅ JSON mode outputs valid JSON

---

### T020: Unit Tests for AGGREGATE Command
**File:** `tests/unit/test_commands_aggregate.py`
**Priority:** MEDIUM
**Dependencies:** T019
**Est:** 2 hours

**Tasks:**
- [ ] Test SUM aggregation (single field)
- [ ] Test AVG aggregation (single field)
- [ ] Test COUNT aggregation
- [ ] Test GROUP BY logic (single group field)
- [ ] Test combined SUM + AVG + COUNT
- [ ] Test batching logic
- [ ] Test progress bar rendering
- [ ] Test `--json` output format
- [ ] Test error handling (invalid domain, no records found)
- [ ] Mock `client.search()` and `client.read()`
- [ ] Achieve 80% coverage

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ 80% code coverage
- ✅ Aggregation logic verified

---

### T021: Register AGGREGATE Command
**File:** `odoo_cli/cli.py`
**Priority:** MEDIUM
**Dependencies:** T019
**Est:** 15 minutes

**Tasks:**
- [ ] Import `aggregate` command
- [ ] Add command registration
- [ ] Verify command appears in `odoo --help`
- [ ] Test command execution

**Acceptance Criteria:**
- ✅ `odoo aggregate` command available
- ✅ Help text displays correctly

---

### T022: Verify October 2025 Sales Query
**Priority:** HIGH
**Dependencies:** T021
**Est:** 1 hour

**Test Scenario:**
```bash
# Verify same result as Python script from previous phase
odoo aggregate sale.order '[["date_order",">=","2025-10-01"],["date_order","<","2025-11-01"],["state","=","sale"]]' --sum amount_total --count
```

**Acceptance Criteria:**
- ✅ Result matches previous Python script: €6,681,527.19
- ✅ Count matches: 5,991 orders
- ✅ Command completes in <30 seconds
- ✅ Progress bar functional

---

## Phase 8: Documentation (Day 6)

### T023: Update README.md
**File:** `README.md`
**Priority:** MEDIUM
**Dependencies:** All previous tasks
**Est:** 2 hours

**Tasks:**
- [ ] Add "CRUD Commands" section with examples
- [ ] Add "Batch Operations" section with examples
- [ ] Add "Aggregation" section with examples
- [ ] Update "Quick Start" with new commands
- [ ] Update "Features" list
- [ ] Add performance benchmarks
- [ ] Update command list in table of contents

**New Sections:**
```markdown
## CRUD Commands

### Creating Records
Simple field=value syntax eliminates JSON requirement:

```bash
odoo create res.partner --fields name="Test Partner" email="test@test.com"
```

### Updating Records
Update single or multiple records:

```bash
odoo update sale.order 123 --fields state="done"
odoo update res.partner 1,2,3 --fields active=false
```

### Deleting Records
Safe deletion with confirmation:

```bash
odoo delete res.partner 456
odoo delete res.partner 456,457,458 --force
```

## Batch Operations

### Bulk Create
Create hundreds of records from JSON file:

```bash
odoo create-bulk res.partner --file partners.json
```

### Bulk Update
Update multiple records at once:

```bash
odoo update-bulk sale.order --file updates.json
```

## Data Aggregation

Calculate SUM, AVG, COUNT directly from CLI:

```bash
# Sum October 2025 sales
odoo aggregate sale.order '[["date_order",">=","2025-10-01"]]' --sum amount_total

# Count orders by state
odoo aggregate sale.order '[]' --count --group-by state
```
```

**Acceptance Criteria:**
- ✅ All new commands documented
- ✅ Examples clear and runnable
- ✅ README updated

---

### T024: Update LLM Development Guide
**File:** `docs/guides/LLM-DEVELOPMENT.md`
**Priority:** MEDIUM
**Dependencies:** T023
**Est:** 1.5 hours

**Tasks:**
- [ ] Update decision tree to include CRUD commands
- [ ] Add examples for `create/update/delete`
- [ ] Add batch operations guidance
- [ ] Update aggregation section with `aggregate` command
- [ ] Update "When to use Python vs CLI" section
- [ ] Add troubleshooting for new commands

**New Decision Tree:**
```markdown
## Updated Decision Tree

### Simple CRUD Operations (< 10 records)
**Recommendation:** Use CLI CRUD commands
```bash
odoo create res.partner --fields name="Test" email="test@test.com"
odoo update sale.order 123 --fields state="done"
```

### Bulk Operations (10-1000 records)
**Recommendation:** Use CLI batch commands
```bash
odoo create-bulk res.partner --file partners.json
odoo update-bulk sale.order --file updates.json
```

### Aggregations (any size)
**Recommendation:** Use CLI aggregate command
```bash
odoo aggregate sale.order '[]' --sum amount_total --group-by state
```

### Complex Logic (multiple steps, conditionals)
**Recommendation:** Use Python script
```

**Acceptance Criteria:**
- ✅ Decision tree updated
- ✅ All new commands documented
- ✅ Examples added

---

### T025: Create CRUD Operations Cookbook
**File:** `docs/examples/crud_operations.md`
**Priority:** MEDIUM
**Dependencies:** T023
**Est:** 2 hours

**Tasks:**
- [ ] Create new cookbook file
- [ ] Add 10+ real-world CRUD examples:
  - Create partner with all fields
  - Update order status workflow
  - Bulk create products
  - Bulk update prices
  - Delete draft records
  - Aggregate sales by period
  - Calculate customer lifetime value
  - Count records by category
  - Update based on search results
  - Chain operations (create → update → read)
- [ ] Add troubleshooting section
- [ ] Add performance tips

**Acceptance Criteria:**
- ✅ 10+ examples documented
- ✅ Examples tested and verified
- ✅ Clear explanations

---

### T026: Update help.py LLM Help
**File:** `odoo_cli/help.py`
**Priority:** MEDIUM
**Dependencies:** All previous tasks
**Est:** 1 hour

**Tasks:**
- [ ] Update `commands` array with new CRUD commands
- [ ] Add `create`, `update`, `delete` command definitions
- [ ] Add `create-bulk`, `update-bulk` command definitions
- [ ] Add `aggregate` command definition
- [ ] Update decision tree with CRUD guidance
- [ ] Update recommendations section
- [ ] Update quick reference
- [ ] Bump CLI version to 1.1.0

**Acceptance Criteria:**
- ✅ `odoo --llm-help` includes all new commands
- ✅ Decision tree updated
- ✅ JSON valid

---

### T027: Update CHANGELOG.md
**File:** `CHANGELOG.md`
**Priority:** MEDIUM
**Dependencies:** All previous tasks
**Est:** 30 minutes

**Tasks:**
- [ ] Add v1.1.0 section
- [ ] Document all new features:
  - User-friendly CRUD commands
  - Batch operations
  - Aggregation helper
  - Input validation
- [ ] Document breaking changes (if any)
- [ ] Document performance improvements
- [ ] Add migration guide

**Acceptance Criteria:**
- ✅ Changelog complete
- ✅ Version bumped to 1.1.0

---

## Phase 9: Final Testing & Release (Day 7)

### T028: Full Integration Testing
**Priority:** HIGH
**Dependencies:** All previous tasks
**Est:** 4 hours

**Test Matrix:**

| Operation | Command | Expected Result | Status |
|-----------|---------|-----------------|--------|
| Create Partner | `odoo create res.partner --fields name="Test"` | Record created | ⬜ |
| Update Partner | `odoo update res.partner X --fields name="New"` | Record updated | ⬜ |
| Delete Partner | `odoo delete res.partner X` | Record deleted | ⬜ |
| Bulk Create 100 | `odoo create-bulk res.partner --file data.json` | 100 created | ⬜ |
| Bulk Update 100 | `odoo update-bulk res.partner --file updates.json` | 100 updated | ⬜ |
| Aggregate Sum | `odoo aggregate sale.order '[]' --sum amount_total` | Correct sum | ⬜ |
| Aggregate Group | `odoo aggregate sale.order '[]' --count --group-by state` | Grouped counts | ⬜ |
| Field Validation | `odoo create res.partner --fields invalid_field="X"` | Error caught | ⬜ |
| Type Validation | Field type mismatch | Error caught | ⬜ |
| JSON Output | All commands with `--json` | Valid JSON | ⬜ |

**Acceptance Criteria:**
- ✅ All 10 test scenarios pass
- ✅ No regressions in existing commands
- ✅ Performance benchmarks met

---

### T029: Update All Unit Tests
**Priority:** HIGH
**Dependencies:** T028
**Est:** 2 hours

**Tasks:**
- [ ] Run all unit tests: `pytest tests/`
- [ ] Fix any failures
- [ ] Ensure no regressions
- [ ] Update test fixtures if needed
- [ ] Run coverage report: `pytest --cov=odoo_cli`
- [ ] Verify 85%+ overall coverage

**Acceptance Criteria:**
- ✅ All tests passing (existing + new)
- ✅ 85%+ code coverage
- ✅ No test warnings

---

### T030: Version Bump & Release Prep
**Files:** `pyproject.toml`, `setup.py`, `odoo_cli/__init__.py`
**Priority:** HIGH
**Dependencies:** T029
**Est:** 1 hour

**Tasks:**
- [ ] Update version to `1.1.0` in `pyproject.toml`
- [ ] Update version in `setup.py`
- [ ] Update version in `odoo_cli/__init__.py`
- [ ] Update version in `odoo_cli/help.py` (--llm-help output)
- [ ] Verify version consistency
- [ ] Create git tag: `git tag v1.1.0`
- [ ] Push tag: `git push origin v1.1.0`

**Acceptance Criteria:**
- ✅ Version updated in all files
- ✅ Git tag created
- ✅ Tag pushed

---

### T031: Create GitHub Release
**Priority:** MEDIUM
**Dependencies:** T030
**Est:** 1 hour

**Tasks:**
- [ ] Draft GitHub release notes
- [ ] Include feature summary
- [ ] Include breaking changes (if any)
- [ ] Include migration guide
- [ ] Add performance benchmarks
- [ ] Add example usage
- [ ] Publish release

**Release Notes Template:**
```markdown
# v1.1.0 - User-Friendly CRUD Commands & Batch Operations

## 🎉 New Features

### CRUD Commands
- **create** - Create records with simple field=value syntax
- **update** - Update single or multiple records
- **delete** - Delete records with confirmation prompt

### Batch Operations
- **create-bulk** - Create hundreds of records from JSON file
- **update-bulk** - Update multiple records at once

### Aggregation
- **aggregate** - Calculate SUM, AVG, COUNT with GROUP BY support

## 📈 Performance
- CREATE: <500ms per record
- BULK CREATE: <10s per 100 records
- AGGREGATE: <30s for 5000 records

## 🔧 Improvements
- Input validation with helpful error messages
- Field type inference (no quotes needed for strings)
- Progress bars for long operations
- Rich console output with colors

## 📚 Documentation
- Updated README.md with examples
- New CRUD operations cookbook
- Updated LLM development guide
- Updated --llm-help output

## 🔄 Migration
No breaking changes. All new commands are additive.

Existing `execute` command continues to work.

## 📦 Installation
```bash
pip install --upgrade odoo-xml-cli
```

## 💡 Examples
```bash
# Create partner
odoo create res.partner --fields name="Test" email="test@test.com"

# Update order
odoo update sale.order 123 --fields state="done"

# Bulk create
odoo create-bulk res.partner --file partners.json

# Aggregate sales
odoo aggregate sale.order '[]' --sum amount_total --group-by state
```
```

**Acceptance Criteria:**
- ✅ Release published on GitHub
- ✅ Release notes complete
- ✅ Download links working

---

## Summary

**Total Tasks:** 31
**Estimated Duration:** 7 days
**Priority Breakdown:**
- HIGH: 22 tasks
- MEDIUM: 9 tasks

**Phase Breakdown:**
- Phase 1: Foundation (Day 1) - 2 tasks
- Phase 2: CREATE (Day 1-2) - 3 tasks
- Phase 3: UPDATE (Day 2) - 3 tasks
- Phase 4: DELETE (Day 2) - 3 tasks
- Phase 5: Integration (Day 3) - 1 task
- Phase 6: Batch Ops (Day 3-4) - 6 tasks
- Phase 7: Aggregation (Day 5) - 4 tasks
- Phase 8: Docs (Day 6) - 5 tasks
- Phase 9: Release (Day 7) - 4 tasks

**Success Criteria:**
- ✅ All 31 tasks complete
- ✅ 85%+ code coverage
- ✅ All tests passing
- ✅ Performance benchmarks met
- ✅ Documentation complete
- ✅ v1.1.0 released
