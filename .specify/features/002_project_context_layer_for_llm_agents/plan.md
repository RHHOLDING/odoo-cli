# Implementation Plan: Project Context Layer for LLM Agents

**Feature ID:** 002
**Branch:** `feature/002-project_context_layer_for_llm_agents`
**Status:** Planning Complete
**Version:** v1.5.0

---

## Executive Summary

This implementation plan details the phased development of the Project Context Layer feature, which enables LLM agents to automatically understand Odoo project structure without repeated API calls. The system will discover and cache models, fields, modules, and companies in a local `.odoo-context.json` file.

**Key Deliverables:**
1. `odoo-cli context` command group (init, refresh, show, status, clear)
2. Context discovery and caching system
3. Optional record count tracking (`--include-counts`)
4. Security measures for public repository safety

**Estimated Effort:** 2-3 days (~24 hours)

---

## Phase 0: Research & Foundation (2 hours)

### Objectives
- Understand existing odoo-cli architecture
- Review Odoo External API capabilities for metadata discovery
- Analyze file storage patterns (similar to `.env` handling)

### Tasks

#### Task 0.1: Codebase Analysis
**Description:** Review existing odoo-cli structure
**Effort:** 30 min
**Deliverables:**
- Document existing command structure in `odoo_cli/commands/`
- Identify client API patterns in `odoo_cli/client.py`
- Review existing JSON handling and error patterns

**Acceptance Criteria:**
- [ ] Understand how commands are registered in `cli.py`
- [ ] Know how to use existing Odoo client for API calls
- [ ] Understand existing error handling patterns

#### Task 0.2: Odoo API Research
**Description:** Research Odoo External API for metadata discovery
**Effort:** 45 min
**Deliverables:**
- Document API calls needed:
  - `models.execute_kw('ir.model', 'search_read')` for models
  - `models.execute_kw('ir.model.fields', 'search_read')` for fields
  - `models.execute_kw('ir.module.module', 'search_read')` for modules
  - `models.execute_kw('res.company', 'search_read')` for companies

**Acceptance Criteria:**
- [ ] Test API calls against dev Odoo instance
- [ ] Confirm all required metadata is accessible
- [ ] Understand performance characteristics (timing)

#### Task 0.3: Security Requirements Analysis
**Description:** Detail public repository safety measures
**Effort:** 45 min
**Deliverables:**
- Document gitignore strategy
- Design `.odoo-context.json.example` structure
- Plan CLI warnings for missing gitignore

**Acceptance Criteria:**
- [ ] Clear distinction between safe/unsafe data
- [ ] Example file uses only placeholder data
- [ ] Warning strategy documented

**Deliverable:** `research.md` with findings and API documentation

---

## Phase 1: Core Implementation (12 hours)

### Milestone: Context Discovery & Storage Working

#### Task 1.1: Data Structures & Models
**Description:** Implement `ProjectContext` dataclass and serialization
**Effort:** 2 hours
**Files:**
- `odoo_cli/context.py` (NEW)

**Implementation:**
```python
@dataclass
class ProjectContext:
    version: str
    generated_at: datetime
    odoo_version: str
    database: str
    companies: List[Dict]
    models: Dict[str, Dict]  # model_name -> {custom_fields, key_fields, module, record_count?}
    modules: Dict[str, Dict]  # module_name -> {type, state, version}

    @classmethod
    def load(cls, path: str = ".odoo-context.json") -> Optional['ProjectContext']

    def save(self, path: str = ".odoo-context.json")

    def is_stale(self, days: int = 7) -> bool

    def get_model_fields(self, model: str) -> List[str]
```

**Acceptance Criteria:**
- [ ] Context class can serialize/deserialize JSON
- [ ] `is_stale()` correctly calculates age
- [ ] `get_model_fields()` returns field list
- [ ] Unit tests for serialization pass

#### Task 1.2: Context Discovery Engine
**Description:** Implement core discovery logic
**Effort:** 3 hours
**Files:**
- `odoo_cli/context.py` (extend)

**Functions:**
```python
def discover_context(client: OdooClient, include_counts: bool = False) -> ProjectContext
def discover_models(client: OdooClient, include_counts: bool) -> Dict
def discover_fields(client: OdooClient, model_name: str) -> List[Dict]
def discover_modules(client: OdooClient) -> Dict
def discover_companies(client: OdooClient) -> List[Dict]
```

**Acceptance Criteria:**
- [ ] `discover_context()` calls all sub-discovery functions
- [ ] Handles API timeouts gracefully (partial saves)
- [ ] `--include-counts` flag adds `record_count` field
- [ ] Completes in <30s for typical project (1000 models)
- [ ] Unit tests with mocked API responses

#### Task 1.3: CLI Command Group
**Description:** Implement `odoo-cli context` command group
**Effort:** 4 hours
**Files:**
- `odoo_cli/commands/context.py` (NEW)
- `odoo_cli/cli.py` (MODIFY - register command group)

**Commands to implement:**
```python
@click.group()
def context():
    """Manage project context for LLM agents"""

@context.command()
@click.option('--include-counts', is_flag=True)
def init(include_counts):
    """Initialize project context"""

@context.command()
def refresh():
    """Refresh existing context"""

@context.command()
@click.option('--models', is_flag=True)
@click.option('--fields', type=str)
@click.option('--modules', is_flag=True)
def show(models, fields, modules):
    """Query cached context"""

@context.command()
def status():
    """Show context status and freshness"""

@context.command()
def clear():
    """Remove cached context"""
```

**Acceptance Criteria:**
- [ ] All 5 commands registered and callable
- [ ] `init` creates `.odoo-context.json`
- [ ] `refresh` detects changes (diff output)
- [ ] `show` returns JSON for LLM parsing
- [ ] `status` shows age and warns if >7 days old
- [ ] `clear` removes file with confirmation
- [ ] Minimal logging (NFR-3): error messages only

#### Task 1.4: Security Measures
**Description:** Implement public repo safety features
**Effort:** 2 hours
**Files:**
- `.gitignore` (ALREADY DONE ✅)
- `.odoo-context.json.example` (ALREADY DONE ✅)
- `odoo_cli/commands/context.py` (extend)

**Implementation:**
- CLI warning if `.odoo-context.json` not in `.gitignore`
- README warning section
- Pre-commit hook suggestion (optional)

**Acceptance Criteria:**
- [ ] CLI detects missing gitignore entry
- [ ] Warning message shown on `init` if not gitignored
- [ ] `.odoo-context.json.example` committed to repo
- [ ] README.md updated with security section

#### Task 1.5: Integration with Existing Commands
**Description:** Auto-load context in command execution (optional FR-4)
**Effort:** 1 hour
**Files:**
- `odoo_cli/cli.py` (MODIFY - add context loading hook)

**Implementation:**
- Load context at CLI startup if file exists
- Make context available to all commands via Click context
- Warning if context stale

**Acceptance Criteria:**
- [ ] Context auto-loads when present
- [ ] Commands can access context via `ctx.obj['context']`
- [ ] No performance impact if context file missing (<100ms load time)

**Deliverable:** Working `odoo-cli context` commands

---

## Phase 2: Testing & Documentation (6 hours)

### Milestone: Production-Ready Feature

#### Task 2.1: Unit Tests
**Description:** Comprehensive unit test coverage
**Effort:** 2 hours
**Files:**
- `tests/unit/test_context.py` (NEW)

**Test Coverage:**
- Context serialization/deserialization
- Staleness detection
- Model/field queries
- Discovery functions (with mocked API)
- CLI command execution

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] Coverage >80% for new code
- [ ] Mock all Odoo API calls
- [ ] Test error handling paths

#### Task 2.2: Integration Tests
**Description:** End-to-end integration testing
**Effort:** 2 hours
**Files:**
- `tests/integration/test_context_integration.py` (NEW)

**Test Scenarios:**
- Full context init against demo Odoo instance
- Context refresh detects module install
- Context validation for commands
- Large project performance (10k+ models simulation)

**Acceptance Criteria:**
- [ ] Tests run against real Odoo demo instance
- [ ] Performance targets met (NFR-1)
- [ ] File size constraints verified (NFR-2 <5MB)

#### Task 2.3: Documentation Updates
**Description:** Update all LLM-facing documentation
**Effort:** 2 hours
**Files:**
- `README.md` (MODIFY - add Context section)
- `CLAUDE.md` (MODIFY - add usage patterns)
- `GEMINI.md` (MODIFY - add examples)
- `CODEX.md` (MODIFY - add workflow)
- `odoo_cli/help.py` (MODIFY - update --llm-help)

**Content to add:**
- Command reference
- Usage examples
- Security warnings
- Troubleshooting guide

**Acceptance Criteria:**
- [ ] All docs updated consistently
- [ ] Security warning prominent
- [ ] `--llm-help` includes context commands
- [ ] Examples show both with/without `--include-counts`

**Deliverable:** Tested and documented feature

---

## Phase 3: Polish & Release (4 hours)

### Milestone: Ready for Merge

#### Task 3.1: Edge Case Handling
**Description:** Implement all 5 edge cases from spec
**Effort:** 2 hours

**Edge Cases:**
1. Corrupted JSON → Graceful error, suggest re-init
2. API timeout → Partial save, resume capability
3. Very large projects → Pagination, compression
4. Multiple environments → Shared file (RESOLVED in clarifications)
5. Module uninstall → Refresh detects removed models

**Acceptance Criteria:**
- [ ] All edge cases tested
- [ ] Error messages actionable (NFR-3)
- [ ] No data loss on API timeout

#### Task 3.2: Performance Optimization
**Description:** Ensure performance targets met
**Effort:** 1 hour

**Targets (NFR-1):**
- Context init: <30s for 1000 models
- Context load: <100ms per command
- Context query: <50ms

**Optimizations:**
- Batch API calls where possible
- Lazy loading of field details
- JSON compression if file >5MB

**Acceptance Criteria:**
- [ ] All NFR-1 targets met
- [ ] Profiling shows no bottlenecks

#### Task 3.3: Final Review & PR Preparation
**Description:** Code review, changelog, PR description
**Effort:** 1 hour

**Checklist:**
- [ ] All acceptance criteria met (FRs 1-6, NFRs 1-3)
- [ ] All tests passing
- [ ] No linting errors
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow convention
- [ ] PR description references spec and clarifications

**Deliverable:** Ready-to-merge PR

---

## Dependencies & Prerequisites

### External Dependencies
- None (uses existing `odoo_cli/client.py`)

### Internal Dependencies
- Existing Odoo client implementation
- Click CLI framework
- Python dataclasses
- JSON serialization (stdlib)

### Required Access
- Odoo instance for testing (dev environment: `rhholding-ac-mail-deploy-25766690.dev.odoo.com`)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| API timeout during init | Medium | Medium | Implement partial save + resume |
| Large project performance | Medium | High | Pagination + optional filtering |
| Context file accidentally committed | Low | Critical | CLI warnings + gitignore check |
| Context out of sync | Medium | Low | Staleness detection + easy refresh |

---

## Success Criteria Checklist

### Functional Requirements
- [ ] FR-1: Context init discovers all models, fields, modules, companies
- [ ] FR-1: Optional `--include-counts` flag works
- [ ] FR-2: Context refresh detects changes and shows diff
- [ ] FR-3: Context query commands return JSON
- [ ] FR-4: Auto-loading context in commands (optional)
- [ ] FR-5: Context file management (status, clear)
- [ ] FR-6: Safe example file created, gitignore configured

### Non-Functional Requirements
- [ ] NFR-1: Performance targets met (<30s init, <100ms load, <50ms query)
- [ ] NFR-2: File size <5MB for typical project
- [ ] NFR-3: Minimal logging (errors only, actionable messages)

### User Stories
- [ ] Story 1: LLM can read context and understand project
- [ ] Story 2: Developer can initialize context with single command
- [ ] Story 3: LLM can validate operations against context

### Testing
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass against real Odoo instance
- [ ] Manual testing completed
- [ ] Edge cases handled

### Documentation
- [ ] README.md updated
- [ ] CLAUDE.md/GEMINI.md/CODEX.md updated
- [ ] `--llm-help` updated
- [ ] Security warnings prominent

---

## Timeline Estimate

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 0: Research | 2h | None |
| Phase 1: Core Implementation | 12h | Phase 0 |
| Phase 2: Testing & Docs | 6h | Phase 1 |
| Phase 3: Polish & Release | 4h | Phase 2 |
| **Total** | **24h** | |

**Target Completion:** 3 working days

---

## Clarifications Applied

From Session 2025-01-21:

1. **Record counts:** Optional via `--include-counts` flag
   - Implementation: Add flag to `init` command
   - Data model: Optional `record_count` field in model metadata

2. **Environment strategy:** Shared single file across environments
   - Implementation: Single `.odoo-context.json` in project root
   - User manages re-init when switching environments

3. **Observability:** Minimal logging (errors only)
   - Implementation: No verbose output, no progress bars
   - Error messages to stderr with actionable suggestions

---

## Next Steps

1. **Commit this plan:** `git add plan.md && git commit -m "docs: Add implementation plan for Project Context Layer"`
2. **Start Phase 0:** Research existing codebase patterns
3. **Create task tracking:** Convert plan tasks to GitHub issues or checklist
4. **Begin implementation:** Start with Task 1.1 (Data Structures)

**Ready to proceed with implementation!** 🚀
