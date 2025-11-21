# Implementation Tasks: Project Context Layer for LLM Agents

**Feature ID:** 002
**Branch:** `feature/002-project_context_layer_for_llm_agents`
**Status:** Ready for Implementation
**Version:** v1.5.0

---

## Task Status Legend
- ⏳ **Pending** - Not started
- 🔄 **In Progress** - Currently being worked on
- ✅ **Complete** - Finished and verified
- ⏸️ **Blocked** - Waiting on dependency

---

## Phase 0: Research & Foundation (2 hours)

### 0.1: Codebase Analysis ⏳
**Effort:** 30 min
**Description:** Review existing odoo-cli structure to understand command registration, client API patterns, and error handling.

**Tasks:**
- [ ] Review command registration in `odoo_cli/cli.py`
- [ ] Analyze client API patterns in `odoo_cli/client.py`
- [ ] Study existing JSON handling patterns
- [ ] Document error handling conventions

**Deliverable:** Understanding of odoo-cli architecture

---

### 0.2: Odoo API Research ⏳
**Effort:** 45 min
**Description:** Research and test Odoo External API calls needed for metadata discovery.

**Tasks:**
- [ ] Test `ir.model` search_read for model discovery
- [ ] Test `ir.model.fields` search_read for field metadata
- [ ] Test `ir.module.module` search_read for modules
- [ ] Test `res.company` search_read for companies
- [ ] Document API response structures
- [ ] Measure performance characteristics

**Deliverable:** API documentation with response examples

---

### 0.3: Security Requirements Analysis ⏳
**Effort:** 45 min
**Description:** Finalize public repository safety measures.

**Tasks:**
- [ ] Verify `.odoo-context.json` in `.gitignore` ✅ (already done)
- [ ] Verify `.odoo-context.json.example` exists ✅ (already done)
- [ ] Document CLI warning strategy for missing gitignore
- [ ] Design pre-commit hook (optional)

**Deliverable:** Security implementation checklist

---

## Phase 1: Core Implementation (12 hours)

### 1.1: Data Structures & Models ⏳
**Effort:** 2 hours
**Files:** `odoo_cli/context.py` (NEW)

**Tasks:**
- [ ] Create `ProjectContext` dataclass with fields:
  - version, generated_at, odoo_version, database
  - companies, models, modules
- [ ] Implement `ProjectContext.load()` classmethod
- [ ] Implement `ProjectContext.save()` method
- [ ] Implement `is_stale()` method (7-day threshold)
- [ ] Implement `get_model_fields()` method
- [ ] Write unit tests for serialization/deserialization
- [ ] Write unit tests for staleness detection

**Acceptance Criteria:**
- [ ] Context serializes to/from JSON correctly
- [ ] `is_stale()` calculates age accurately
- [ ] `get_model_fields()` returns correct field list
- [ ] Unit tests pass with 80%+ coverage

---

### 1.2: Context Discovery Engine ⏳
**Effort:** 3 hours
**Files:** `odoo_cli/context.py` (extend)

**Tasks:**
- [ ] Implement `discover_context(client, include_counts=False)`
- [ ] Implement `discover_models(client, include_counts)`
- [ ] Implement `discover_fields(client, model_name)`
- [ ] Implement `discover_modules(client)`
- [ ] Implement `discover_companies(client)`
- [ ] Add timeout handling for API calls
- [ ] Implement partial save on timeout (resume capability)
- [ ] Write unit tests with mocked API responses

**Acceptance Criteria:**
- [ ] `discover_context()` calls all sub-functions correctly
- [ ] Handles API timeouts gracefully
- [ ] `--include-counts` flag adds record_count field
- [ ] Completes in <30s for 1000 models
- [ ] Unit tests with mocks pass

---

### 1.3: CLI Command Group ⏳
**Effort:** 4 hours
**Files:**
- `odoo_cli/commands/context.py` (NEW)
- `odoo_cli/cli.py` (MODIFY)

**Tasks:**
- [ ] Create `context.py` command file
- [ ] Implement `context` command group
- [ ] Implement `context init` command with `--include-counts` flag
- [ ] Implement `context refresh` command with diff output
- [ ] Implement `context show` command with filters:
  - `--models` (list all models)
  - `--fields MODEL` (show model fields)
  - `--modules` (list modules)
- [ ] Implement `context status` command (age, freshness warning)
- [ ] Implement `context clear` command with confirmation
- [ ] Register command group in `cli.py`
- [ ] Ensure JSON output for all commands
- [ ] Add error-only logging (NFR-3)

**Acceptance Criteria:**
- [ ] All 5 commands registered and callable
- [ ] `init` creates `.odoo-context.json`
- [ ] `refresh` shows diff of changes
- [ ] `show` returns JSON for LLM parsing
- [ ] `status` warns if >7 days old
- [ ] `clear` prompts for confirmation
- [ ] Minimal logging (errors only)

---

### 1.4: Security Measures ⏳
**Effort:** 2 hours
**Files:**
- `odoo_cli/commands/context.py` (extend)
- `README.md` (MODIFY)

**Tasks:**
- [ ] Implement gitignore detection in `context init`
- [ ] Add warning if `.odoo-context.json` not in `.gitignore`
- [ ] Add security warning section to README.md
- [ ] Document pre-commit hook suggestion (optional)
- [ ] Verify `.odoo-context.json.example` is safe

**Acceptance Criteria:**
- [ ] CLI detects missing gitignore entry
- [ ] Warning shown on `init` if not gitignored
- [ ] `.odoo-context.json.example` uses placeholder data only
- [ ] README.md has prominent security section

---

### 1.5: Integration with Existing Commands ⏳
**Effort:** 1 hour
**Files:** `odoo_cli/cli.py` (MODIFY)

**Tasks:**
- [ ] Add context loading hook at CLI startup
- [ ] Make context available via Click context (`ctx.obj['context']`)
- [ ] Add staleness warning on load
- [ ] Ensure no performance impact if file missing (<100ms)

**Acceptance Criteria:**
- [ ] Context auto-loads when present
- [ ] Commands can access via `ctx.obj['context']`
- [ ] Load time <100ms
- [ ] No errors if context file missing

---

## Phase 2: Testing & Documentation (6 hours)

### 2.1: Unit Tests ⏳
**Effort:** 2 hours
**Files:** `tests/unit/test_context.py` (NEW)

**Tasks:**
- [ ] Test context serialization/deserialization
- [ ] Test staleness detection logic
- [ ] Test model/field query methods
- [ ] Test discovery functions with mocked API
- [ ] Test CLI command execution
- [ ] Test error handling paths
- [ ] Achieve 80%+ code coverage

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] Coverage >80% for new code
- [ ] All Odoo API calls mocked
- [ ] Error paths tested

---

### 2.2: Integration Tests ⏳
**Effort:** 2 hours
**Files:** `tests/integration/test_context_integration.py` (NEW)

**Tasks:**
- [ ] Test full context init against demo Odoo instance
- [ ] Test context refresh detects module install
- [ ] Test context validation in commands
- [ ] Test large project performance (10k+ models simulation)
- [ ] Verify file size <5MB for typical project

**Acceptance Criteria:**
- [ ] Tests run against real Odoo demo instance
- [ ] Performance targets met (NFR-1)
- [ ] File size constraints verified (NFR-2 <5MB)

---

### 2.3: Documentation Updates ⏳
**Effort:** 2 hours
**Files:**
- `README.md` (MODIFY)
- `CLAUDE.md` (MODIFY)
- `GEMINI.md` (MODIFY)
- `CODEX.md` (MODIFY)
- `odoo_cli/help.py` (MODIFY)

**Tasks:**
- [ ] Add Context section to README.md with:
  - Command reference
  - Usage examples
  - Security warnings
  - Troubleshooting guide
- [ ] Update CLAUDE.md with usage patterns
- [ ] Update GEMINI.md with examples
- [ ] Update CODEX.md with workflow
- [ ] Update `--llm-help` with context commands
- [ ] Show examples with/without `--include-counts`

**Acceptance Criteria:**
- [ ] All docs updated consistently
- [ ] Security warning prominent in README
- [ ] `--llm-help` includes context commands
- [ ] Examples show both modes

---

## Phase 3: Polish & Release (4 hours)

### 3.1: Edge Case Handling ⏳
**Effort:** 2 hours

**Tasks:**
- [ ] Handle corrupted JSON → Error message + suggest re-init
- [ ] Handle API timeout → Partial save + resume capability
- [ ] Handle large projects → Pagination + compression
- [ ] Handle module uninstall → Refresh detects removed models
- [ ] Test all edge cases
- [ ] Ensure actionable error messages (NFR-3)

**Acceptance Criteria:**
- [ ] All 5 edge cases from spec tested
- [ ] No data loss on API timeout
- [ ] Error messages actionable

---

### 3.2: Performance Optimization ⏳
**Effort:** 1 hour

**Tasks:**
- [ ] Profile context init performance
- [ ] Optimize batch API calls
- [ ] Implement lazy loading for field details
- [ ] Add JSON compression if file >5MB
- [ ] Verify NFR-1 targets met:
  - Context init: <30s for 1000 models
  - Context load: <100ms per command
  - Context query: <50ms

**Acceptance Criteria:**
- [ ] All NFR-1 performance targets met
- [ ] Profiling shows no bottlenecks

---

### 3.3: Final Review & PR Preparation ⏳
**Effort:** 1 hour

**Tasks:**
- [ ] Review all acceptance criteria (FR-1 to FR-6, NFR-1 to NFR-3)
- [ ] Run all tests (unit + integration)
- [ ] Check linting (Black + isort)
- [ ] Update CHANGELOG.md with:
  - New feature: Project Context Layer
  - Breaking changes (if any)
  - Migration notes
- [ ] Review commit messages (conventional format)
- [ ] Write PR description referencing spec and clarifications
- [ ] Run final manual test on demo instance

**Acceptance Criteria:**
- [ ] All FRs and NFRs met
- [ ] All tests passing
- [ ] No linting errors
- [ ] CHANGELOG.md updated
- [ ] Conventional commit messages
- [ ] PR ready for review

---

## Dependencies

### External Dependencies
- None (uses existing `odoo_cli/client.py`)

### Internal Dependencies
- Existing Odoo client implementation
- Click CLI framework
- Python dataclasses
- JSON serialization (stdlib)

### Required Access
- Odoo demo instance for testing: `rhholding-ac-mail-deploy-25766690.dev.odoo.com`

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation | Status |
|------|------------|--------|------------|--------|
| API timeout during init | Medium | Medium | Partial save + resume | ⏳ Not implemented |
| Large project performance | Medium | High | Pagination + filtering | ⏳ Not implemented |
| Context accidentally committed | Low | Critical | CLI warnings + gitignore | ✅ Gitignore done |
| Context out of sync | Medium | Low | Staleness detection | ⏳ Not implemented |

---

## Progress Tracking

**Overall Progress:** 0% (0/15 tasks complete)

### By Phase:
- **Phase 0:** 0/3 tasks (0%)
- **Phase 1:** 0/5 tasks (0%)
- **Phase 2:** 0/3 tasks (0%)
- **Phase 3:** 0/3 tasks (0%)

**Next Task:** 0.1 - Codebase Analysis

---

## Success Criteria Checklist

### Functional Requirements
- [ ] FR-1: Context init discovers all models, fields, modules, companies
- [ ] FR-1: Optional `--include-counts` flag works
- [ ] FR-2: Context refresh detects changes and shows diff
- [ ] FR-3: Context query commands return JSON
- [ ] FR-4: Auto-loading context in commands (optional)
- [ ] FR-5: Context file management (status, clear)
- [ ] FR-6: Safe example file created, gitignore configured ✅ (partially done)

### Non-Functional Requirements
- [ ] NFR-1: Performance targets met (<30s init, <100ms load, <50ms query)
- [ ] NFR-2: File size <5MB for typical project
- [ ] NFR-3: Minimal logging (errors only, actionable messages)

### User Stories
- [ ] Story 1: LLM can read context and understand project
- [ ] Story 2: Developer can initialize context with single command
- [ ] Story 3: LLM can validate operations against context

---

## Notes

- Tasks marked ✅ in the risk table indicate prerequisite work already completed (gitignore, example file)
- Focus on Phase 0 first to understand architecture before implementing
- All clarifications from Session 2025-01-21 incorporated into tasks
- Security is highest priority - no customer data must leak to public repo
