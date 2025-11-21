# Tasks: Project Context Layer for LLM Agents

**Feature ID:** 003
**Branch:** `feature/003-als_llm_agent_m_chte_ich_zugriff_auf_projektspezif`
**Status:** Ready for Implementation
**Version:** 1.0.0

---

## Overview

This document breaks down the implementation plan into granular, executable tasks. Tasks marked with **[P]** can be executed in parallel with other [P] tasks in the same phase.

**Total Tasks:** 23
**Estimated Effort:** 24 hours (3 working days)

---

## Task Execution Guide

### Sequential Execution
```bash
# Execute tasks in order (T001 → T002 → T003 → ...)
# Wait for each task to complete before starting the next
```

### Parallel Execution
```bash
# Tasks marked [P] can run in parallel within their phase
# Example: Phase 0 parallel tasks
Task agent T001 & Task agent T002 & Task agent T003  # Run in parallel
wait  # Wait for all to complete before proceeding to Phase 1
```

---

## Phase 0: Research & Foundation (4h)

**Objective:** Validate libraries, analyze patterns, define schemas, document data model

### T001: Research JSON5 Libraries [P]
**Effort:** 0.5h
**Dependencies:** None
**Files:** None (research task)

**Description:**
Evaluate `pyjson5` vs `json5` libraries for parsing JSON5 template file with inline comments. Choose based on PyPI maintenance status, Python 3.10+ compatibility, and parsing capabilities.

**Acceptance Criteria:**
- [ ] Library chosen (recommend `pyjson5`)
- [ ] Verified library can parse JSON5 with comments
- [ ] Dependency specification ready for `pyproject.toml`

**Deliverable:**
Research notes documenting library choice and rationale

**How to execute:**
1. Check PyPI for `pyjson5` and `json5` maintenance status
2. Review Python 3.10+ compatibility
3. Test parsing JSON5 with comments in Python REPL
4. Document recommendation

---

### T002: Analyze Existing CLI Command Patterns [P]
**Effort:** 1h
**Dependencies:** None
**Files to read:**
- `odoo_cli/commands/search.py`
- `odoo_cli/commands/create.py`
- `odoo_cli/utils.py`
- `odoo_cli/cli.py`

**Description:**
Review existing CLI commands to understand Click patterns, `@click.pass_obj` usage, `output_json()` and `output_error()` utilities, `--json` flag handling, and Rich formatting.

**Acceptance Criteria:**
- [ ] Understand `@click.pass_obj` usage pattern
- [ ] Understand `output_json()` and `output_error()` utilities
- [ ] Understand `--json` flag handling (command-level and global)
- [ ] Understand Rich formatting patterns

**Deliverable:**
Pattern documentation in `research.md` or notes

**How to execute:**
1. Read `odoo_cli/commands/search.py` for command structure
2. Read `odoo_cli/utils.py` for output utilities
3. Read `odoo_cli/cli.py` for command registration
4. Document patterns for reuse in context commands

---

### T003: Define JSON Schema [P]
**Effort:** 1.5h
**Dependencies:** None
**Files to create:**
- `odoo_cli/schemas/context_schema.json` (NEW)

**Description:**
Create formal JSON Schema for `.odoo-context.json` validation (used in strict mode). Schema defines: schema_version (required), project, companies, warehouses, workflows, modules, notes (all optional).

**Acceptance Criteria:**
- [ ] Schema validates example JSON structure
- [ ] All fields optional except `schema_version`
- [ ] Supports nested structures (e.g., company.warehouses references)
- [ ] Schema follows JSON Schema Draft 7 specification

**Deliverable:**
`odoo_cli/schemas/context_schema.json`

**How to execute:**
1. Create directory `odoo_cli/schemas/` if not exists
2. Create `context_schema.json` with JSON Schema Draft 7 format
3. Define required: `schema_version`
4. Define optional sections: project, companies, warehouses, workflows, modules, notes
5. Add descriptions and examples for each field

**Example schema structure:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["schema_version"],
  "properties": {
    "schema_version": {"type": "string"},
    "project": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "odoo_version": {"type": "string"}
      }
    },
    "companies": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "name": {"type": "string"},
          "role": {"type": "string"},
          "context": {"type": "string"}
        }
      }
    }
  }
}
```

---

### T004: Document Data Model
**Effort:** 1h
**Dependencies:** T001, T002, T003
**Files to create:**
- `.specify/features/003_als_llm_agent_m_chte_ich_zugriff_auf_projektspezif/data-model.md` (NEW)

**Description:**
Create data-model.md specifying ContextManager class structure, data flow, file search logic (CWD only, no upward traversal), and validation logic flow.

**Acceptance Criteria:**
- [ ] Documents ContextManager interface (methods, properties)
- [ ] Documents context file structure and sections
- [ ] Documents validation logic flow (normal vs strict mode)
- [ ] Documents file search behavior (CWD only)

**Deliverable:**
`data-model.md` in feature directory

**How to execute:**
1. Create `data-model.md` in feature directory
2. Document ContextManager class interface
3. Document context file JSON structure
4. Document validation flow (normal mode: warnings; strict mode: schema + errors)
5. Document file search logic (Path.cwd() / ".odoo-context.json", no traversal)

---

## Phase 1: Core Implementation (10h)

**Objective:** Implement ContextManager class and 3 CLI commands

### T005: Implement ContextManager Class
**Effort:** 2h
**Dependencies:** T003, T004
**Files to create:**
- `odoo_cli/context.py` (NEW)

**Description:**
Create core ContextManager class for loading and accessing context files. Implements `load()`, `get_section()`, and placeholder for `validate()` (implemented in T008).

**Acceptance Criteria:**
- [ ] ContextManager loads valid JSON files
- [ ] Returns empty dict for missing files (no errors)
- [ ] `get_section()` returns empty list/dict for missing sections
- [ ] File search limited to CWD only (`Path.cwd() / ".odoo-context.json"`)

**Deliverable:**
`odoo_cli/context.py` with ContextManager class

**How to execute:**
1. Create `odoo_cli/context.py`
2. Import: `from typing import Dict, Optional, Any; from pathlib import Path; import json`
3. Implement `ContextManager.__init__(context_file: Optional[Path] = None)`
4. Implement `ContextManager.load() -> Dict[str, Any]`
5. Implement `ContextManager.get_section(section: str) -> Any`
6. Add placeholder `validate(strict: bool = False)` method (returns empty dict for now)

**Implementation reference:**
See plan.md Task 1.1 for full code

---

### T006: Implement `context show` Command
**Effort:** 2h
**Dependencies:** T005, T002
**Files to create:**
- `odoo_cli/commands/context.py` (NEW)

**Description:**
CLI command to display context (full or filtered by section). Supports `--section` filter and `--json` output mode.

**Acceptance Criteria:**
- [ ] `odoo-cli context show` displays full context
- [ ] `odoo-cli context show --section companies` filters correctly
- [ ] `--json` flag returns structured JSON for LLM parsing
- [ ] Rich formatting for human-readable output
- [ ] Handles missing context file gracefully (no errors, warning message)

**Deliverable:**
`odoo_cli/commands/context.py` with `context` group and `show` command

**How to execute:**
1. Create `odoo_cli/commands/context.py`
2. Import: `click`, `rich.console.Console`, `ContextManager`, `output_json`
3. Create `@click.group(name='context')` decorator for command group
4. Implement `show` command with `--section` and `--json` options
5. Use `ContextManager()` to load context
6. Handle missing file (return empty context message)
7. Filter by section if `--section` provided
8. Output JSON or Rich-formatted display

**Implementation reference:**
See plan.md Task 1.2 for full code

---

### T007: Implement `context guide` Command
**Effort:** 2.5h
**Dependencies:** T005, T002
**Files to modify:**
- `odoo_cli/commands/context.py` (MODIFY)

**Description:**
Provide task-specific guidance using hardcoded mappings. Maps 4 predefined tasks to relevant context sections.

**Acceptance Criteria:**
- [ ] Supports 4 predefined tasks: `create-sales-order`, `manage-inventory`, `purchase-approval`, `production-workflow`
- [ ] Returns relevant context sections based on hardcoded mapping
- [ ] Returns empty guide for missing context (no errors)
- [ ] JSON output is LLM-parsable
- [ ] Task selection via Click choice type

**Deliverable:**
`context guide` command in `odoo_cli/commands/context.py`

**How to execute:**
1. Open `odoo_cli/commands/context.py`
2. Define `TASK_MAPPINGS` dict with 4 task-to-section mappings:
   - `'create-sales-order': ['companies', 'warehouses']`
   - `'manage-inventory': ['warehouses', 'modules']`
   - `'purchase-approval': ['workflows', 'companies']`
   - `'production-workflow': ['modules', 'workflows']`
3. Implement `guide` command with `--task` option (Click.Choice)
4. Load context, filter by task mapping
5. Output JSON or Rich-formatted guide

**Implementation reference:**
See plan.md Task 1.3 for full code

---

### T008: Implement `context validate` Command
**Effort:** 3h
**Dependencies:** T005, T003, T002
**Files to modify:**
- `odoo_cli/context.py` (MODIFY - complete validate method)
- `odoo_cli/commands/context.py` (MODIFY - add validate command)

**Description:**
Validate context file with normal and strict modes. Normal mode: JSON syntax + security warnings. Strict mode: JSON schema validation + all sections required + warnings become errors.

**Acceptance Criteria:**
- [ ] Normal mode: checks JSON syntax, warns about literal "password"/"token" strings (case-insensitive)
- [ ] Strict mode: JSON schema validation, all sections (companies, warehouses, workflows, modules, notes) required non-empty, project.name required, warnings become errors
- [ ] Exit code 0 for valid, 3 for invalid
- [ ] Clear error messages with line numbers (for JSON syntax errors)
- [ ] Suggestions for missing sections

**Deliverable:**
Completed `ContextManager.validate()` method and `validate` CLI command

**How to execute:**
1. Open `odoo_cli/context.py`
2. Import: `jsonschema` (`from jsonschema import validate as schema_validate, ValidationError`)
3. Implement `ContextManager.validate(strict: bool = False) -> Dict[str, Any]`:
   - Return `{"valid": bool, "errors": List[str], "warnings": List[str]}`
   - Check file exists
   - Load JSON (catch JSONDecodeError)
   - Check for "password"/"token" in lowercase content (warnings)
   - If strict: load schema from `odoo_cli/schemas/context_schema.json`, validate, check required sections, convert warnings to errors
4. Open `odoo_cli/commands/context.py`
5. Implement `validate` command with `--strict` flag
6. Call `manager.validate(strict=strict)`
7. Output JSON or Rich-formatted results
8. Set exit code (`ctx.obj.exit_code = 0 or 3`)

**Implementation reference:**
See plan.md Task 1.4 for full code

---

### T009: Register Context Commands in CLI
**Effort:** 0.5h
**Dependencies:** T006, T007, T008
**Files to modify:**
- `odoo_cli/cli.py` (MODIFY)

**Description:**
Register `context` command group in main CLI so `odoo-cli context` is accessible.

**Acceptance Criteria:**
- [ ] `odoo-cli context --help` works
- [ ] All three subcommands (`show`, `guide`, `validate`) registered and accessible

**Deliverable:**
Updated `odoo_cli/cli.py`

**How to execute:**
1. Open `odoo_cli/cli.py`
2. Add import: `from odoo_cli.commands.context import context`
3. Add to CLI group: `cli.add_command(context)`
4. Test: `odoo-cli context --help`

---

## Phase 2: Testing & Documentation (6h)

**Objective:** Comprehensive tests and documentation updates

### T010: Unit Tests - ContextManager [P]
**Effort:** 1.5h
**Dependencies:** T005, T008
**Files to create:**
- `tests/unit/test_context.py` (NEW)

**Description:**
Unit tests for ContextManager class methods: `load()`, `get_section()`, `validate()`.

**Acceptance Criteria:**
- [ ] Test `load()` with valid file
- [ ] Test `load()` with missing file (returns empty dict)
- [ ] Test `load()` with invalid JSON (JSONDecodeError handling)
- [ ] Test `get_section()` for existing/missing sections
- [ ] Test `validate()` normal mode (detects "password", "token")
- [ ] Test `validate()` strict mode (schema enforcement, required sections)
- [ ] Tests use mock/temp files, not real data
- [ ] Coverage >90% for `odoo_cli/context.py`

**Deliverable:**
`tests/unit/test_context.py`

**How to execute:**
1. Create `tests/unit/test_context.py`
2. Import: `pytest`, `unittest.mock`, `tempfile`, `ContextManager`
3. Create test fixtures (valid/invalid JSON content)
4. Test each ContextManager method
5. Use `tmp_path` fixture for file tests
6. Run: `pytest tests/unit/test_context.py -v`

---

### T011: Unit Tests - Context Commands [P]
**Effort:** 1.5h
**Dependencies:** T006, T007, T008
**Files to create:**
- `tests/unit/test_commands_context.py` (NEW)

**Description:**
Unit tests for CLI commands: `context show`, `context guide`, `context validate`. Use Click's CliRunner for testing.

**Acceptance Criteria:**
- [ ] Test `show` with valid context file
- [ ] Test `show --section companies`
- [ ] Test `show --json` output format
- [ ] Test `guide --task create-sales-order`
- [ ] Test `validate` normal mode
- [ ] Test `validate --strict` mode
- [ ] Test missing context file handling (all commands)
- [ ] Mock ContextManager for isolated command testing

**Deliverable:**
`tests/unit/test_commands_context.py`

**How to execute:**
1. Create `tests/unit/test_commands_context.py`
2. Import: `pytest`, `click.testing.CliRunner`, `context` command group
3. Create fixtures for mock context data
4. Test each command with CliRunner
5. Verify output formats (JSON vs Rich)
6. Run: `pytest tests/unit/test_commands_context.py -v`

---

### T012: Integration Tests [P]
**Effort:** 1.5h
**Dependencies:** T009
**Files to create:**
- `tests/integration/test_context_integration.py` (NEW)
- `tests/fixtures/context-valid.json` (NEW)
- `tests/fixtures/context-invalid.json` (NEW)

**Description:**
Integration tests with actual context files and CLI execution in isolated temp directories.

**Acceptance Criteria:**
- [ ] Test full workflow: create context file → run `context show` → verify output
- [ ] Test `context guide --task create-sales-order` with fixture
- [ ] Test `context validate` with valid fixture (passes)
- [ ] Test `context validate` with invalid fixture (fails)
- [ ] Test missing context file (all commands handle gracefully)
- [ ] Tests run in isolated temp directories

**Deliverable:**
`tests/integration/test_context_integration.py` + fixtures

**How to execute:**
1. Create `tests/fixtures/context-valid.json` (valid context)
2. Create `tests/fixtures/context-invalid.json` (invalid JSON or schema violations)
3. Create `tests/integration/test_context_integration.py`
4. Use `tmp_path` to create isolated test environments
5. Copy fixtures to temp dir, run commands with CliRunner
6. Verify outputs match expectations
7. Run: `pytest tests/integration/test_context_integration.py -v`

---

### T013: Update README.md
**Effort:** 0.5h
**Dependencies:** T009
**Files to modify:**
- `README.md` (MODIFY)

**Description:**
Add "Business Context" section to README with examples, usage instructions, and security warnings.

**Acceptance Criteria:**
- [ ] New "Business Context" section added
- [ ] Examples use demo data (Azure Interior, Deco Addict)
- [ ] Command usage examples for `show`, `guide`, `validate`
- [ ] Security warnings about not committing `.odoo-context.json`
- [ ] Link to `.odoo-context.json5.example` template

**Deliverable:**
Updated `README.md`

**How to execute:**
1. Open `README.md`
2. Add section after existing commands documentation
3. Include:
   - Overview of context feature
   - Setup instructions (copy template)
   - Command examples with output
   - Security best practices
   - Link to template file

---

### T014: Update CLAUDE.md
**Effort:** 0.5h
**Dependencies:** T009
**Files to modify:**
- `CLAUDE.md` (MODIFY)

**Description:**
Add context file best practices and security guidelines for LLM developers.

**Acceptance Criteria:**
- [ ] Context feature documented in "Current Version" section
- [ ] Best practices for context file creation
- [ ] Security guidelines (no credentials, demo data only)
- [ ] Example LLM workflow (query context before recommendations)

**Deliverable:**
Updated `CLAUDE.md`

**How to execute:**
1. Open `CLAUDE.md`
2. Update "Current Version" section to v1.5.0
3. Add "Context Files" section under "Security & Privacy"
4. Document best practices for LLMs using context
5. Add security warnings and examples

---

### T015: Update CHANGELOG.md
**Effort:** 0.25h
**Dependencies:** T009
**Files to modify:**
- `CHANGELOG.md` (MODIFY)

**Description:**
Add v1.5.0 entry with context feature changelog.

**Acceptance Criteria:**
- [ ] v1.5.0 entry added at top
- [ ] Lists new commands: `context show`, `context guide`, `context validate`
- [ ] Lists new files: `.odoo-context.json5.example`, `context_schema.json`
- [ ] Documents breaking changes (none)
- [ ] Documents migration notes (optional feature)

**Deliverable:**
Updated `CHANGELOG.md`

**How to execute:**
1. Open `CHANGELOG.md`
2. Add v1.5.0 section at top
3. Format: `## [1.5.0] - YYYY-MM-DD`
4. Add subsections: Added, Changed (if any)
5. List new features and files

---

### T016: Update LLM Help System
**Effort:** 0.75h
**Dependencies:** T009
**Files to modify:**
- `odoo_cli/help.py` (MODIFY)

**Description:**
Add context commands to `--llm-help` with decision trees for when to use each command.

**Acceptance Criteria:**
- [ ] `context show` added to commands list
- [ ] `context guide` added to commands list
- [ ] `context validate` added to commands list
- [ ] Decision tree entries for context use cases:
  - "Need business context" → use `context show`
  - "Task-specific guidance" → use `context guide --task`
  - "Validate context file" → use `context validate`
- [ ] Version number updated to 1.5.0

**Deliverable:**
Updated `odoo_cli/help.py`

**How to execute:**
1. Open `odoo_cli/help.py`
2. Add context commands to `commands` array with descriptions
3. Add decision tree entries under appropriate categories
4. Update version number
5. Test: `odoo-cli --llm-help`

---

## Phase 3: Polish & Release (4h)

**Objective:** Final polish, templates, edge cases, performance

### T017: Create JSON5 Template File [P]
**Effort:** 1.5h
**Dependencies:** T003
**Files to create:**
- `.odoo-context.json5.example` (NEW)

**Description:**
Create `.odoo-context.json5.example` with inline comments, comprehensive examples, and Do's & Don'ts section.

**Acceptance Criteria:**
- [ ] All schema sections covered (project, companies, warehouses, workflows, modules, notes)
- [ ] Uses Odoo demo data (Azure Interior, Deco Addict, generic names)
- [ ] Inline comments explain each section
- [ ] Do's & Don'ts clearly stated at top
- [ ] No real credentials or customer data
- [ ] Valid JSON5 syntax

**Deliverable:**
`.odoo-context.json5.example` in repository root

**How to execute:**
1. Create `.odoo-context.json5.example` in repo root
2. Add header comments with Do's & Don'ts
3. Add all schema sections with inline comments
4. Use demo data from Odoo (Azure Interior, Marketplace Hub, etc.)
5. Verify JSON5 syntax (test with `pyjson5` if needed)

**Example structure:**
See plan.md Task 3.1 for full template

---

### T018: Update .gitignore [P]
**Effort:** 0.25h
**Dependencies:** None
**Files to modify:**
- `.gitignore` (MODIFY)

**Description:**
Ensure `.odoo-context.json` is gitignored to prevent accidental commit of sensitive data.

**Acceptance Criteria:**
- [ ] `.odoo-context.json` added to `.gitignore`
- [ ] `.odoo-context.json5.example` is NOT gitignored (should be committed)

**Deliverable:**
Updated `.gitignore`

**How to execute:**
1. Open `.gitignore`
2. Add line: `.odoo-context.json`
3. Verify `.odoo-context.json5.example` is not listed (should be committed)
4. Test: create `.odoo-context.json`, verify `git status` ignores it

---

### T019: Add Dependencies to pyproject.toml [P]
**Effort:** 0.25h
**Dependencies:** T001
**Files to modify:**
- `pyproject.toml` (MODIFY)

**Description:**
Add `jsonschema` and `pyjson5` dependencies to project.

**Acceptance Criteria:**
- [ ] `jsonschema` added to dependencies
- [ ] `pyjson5` added to dev dependencies (optional, for template parsing)
- [ ] Version constraints specified (e.g., `jsonschema>=4.0.0`)

**Deliverable:**
Updated `pyproject.toml`

**How to execute:**
1. Open `pyproject.toml`
2. Add to `[project.dependencies]`: `jsonschema>=4.0.0`
3. Add to `[project.optional-dependencies]` dev section: `pyjson5>=0.9.0`
4. Run: `pip install -e .` to verify

---

### T020: Edge Case Testing
**Effort:** 1h
**Dependencies:** T010, T011, T012
**Files to modify:**
- `tests/unit/test_context.py` (MODIFY)
- `tests/integration/test_context_integration.py` (MODIFY)

**Description:**
Test and handle all edge cases from spec: missing file, invalid JSON, partial context, large file, file not in CWD.

**Acceptance Criteria:**
- [ ] Test missing context file → returns empty context, no errors
- [ ] Test invalid JSON syntax → clear error with line number
- [ ] Test partial context (some sections missing) → accepts gracefully, returns empty for missing
- [ ] Test very large file (>1MB) → warns during validation
- [ ] Test context file not in CWD → clear error message (no upward search)
- [ ] All edge cases have clear error messages
- [ ] No crashes or unclear errors

**Deliverable:**
Updated test files with edge case coverage

**How to execute:**
1. Add edge case tests to `test_context.py` and `test_context_integration.py`
2. Test each scenario
3. Verify error messages are clear and actionable
4. Run: `pytest tests/ -v --cov=odoo_cli/context.py`

---

### T021: Performance Validation
**Effort:** 0.5h
**Dependencies:** T009
**Files:** None (testing task)

**Description:**
Validate performance targets: context file load <100ms (files up to 1MB), command startup <500ms.

**Acceptance Criteria:**
- [ ] Context file load time <100ms for files up to 1MB
- [ ] Command startup remains <500ms (test with `time odoo-cli context show`)
- [ ] No noticeable CLI slowdown vs existing commands

**Deliverable:**
Performance validation results documented

**How to execute:**
1. Create test context file of varying sizes (10KB, 100KB, 1MB)
2. Use `time` or Python's `timeit` to measure load times
3. Test: `time odoo-cli context show`
4. Verify targets met (<100ms load, <500ms startup)
5. Document results

---

### T022: Final Code Review & Linting
**Effort:** 0.5h
**Dependencies:** T005-T021
**Files:** All modified files

**Description:**
Final code review: run Black formatter, isort, check for linting errors, verify no credentials or sensitive data.

**Acceptance Criteria:**
- [ ] All code formatted with Black (line length 120)
- [ ] Imports sorted with isort
- [ ] No linting errors (flake8, mypy if used)
- [ ] No credentials or sensitive data in any files
- [ ] Example file uses only demo data
- [ ] All tests passing

**Deliverable:**
Formatted, linted, reviewed code

**How to execute:**
1. Run: `black odoo_cli tests --line-length 120`
2. Run: `isort odoo_cli tests`
3. Run: `flake8 odoo_cli tests` (if configured)
4. Search for secrets: `git diff | grep -i "password\|secret\|key\|token"`
5. Verify all tests pass: `pytest tests/ -v`

---

### T023: PR Preparation
**Effort:** 0.75h
**Dependencies:** T022
**Files:** Multiple

**Description:**
Final checklist before creating pull request: verify all acceptance criteria met, update version, prepare PR description.

**Acceptance Criteria:**
- [ ] All functional requirements (FR-1 through FR-6) met
- [ ] All non-functional requirements (NFR-1 through NFR-3) met
- [ ] All user stories (Story 1-3) satisfied
- [ ] All tests passing (unit + integration)
- [ ] Documentation complete (README, CLAUDE.md, CHANGELOG, --llm-help)
- [ ] Version updated in relevant files
- [ ] No credentials or sensitive data
- [ ] Example file uses demo data only

**Deliverable:**
Ready-to-merge PR

**How to execute:**
1. Review spec.md Success Criteria checklist
2. Run full test suite: `pytest tests/ -v --cov`
3. Verify all documentation updated
4. Create PR description from spec + plan
5. Tag reviewers (if any)

---

## Parallel Execution Examples

### Phase 0 - Research (All parallel)
```bash
# All Phase 0 tasks can run in parallel
Task agent T001 &  # Research JSON5 libraries
Task agent T002 &  # Analyze CLI patterns
Task agent T003 &  # Define JSON schema
wait
# T004 depends on T001-T003, run sequentially
Task agent T004    # Document data model
```

### Phase 1 - Core Implementation (Sequential due to file dependencies)
```bash
# Phase 1 tasks modify same files, must run sequentially
Task agent T005    # ContextManager class (creates context.py)
Task agent T006    # context show command (creates commands/context.py)
Task agent T007    # context guide command (modifies commands/context.py)
Task agent T008    # context validate command (modifies both files)
Task agent T009    # Register commands (modifies cli.py)
```

### Phase 2 - Testing & Documentation (Parallel groups)
```bash
# Tests can run in parallel
Task agent T010 &  # Unit tests - ContextManager
Task agent T011 &  # Unit tests - Commands
Task agent T012 &  # Integration tests
wait

# Documentation updates can run in parallel
Task agent T013 &  # README.md
Task agent T014 &  # CLAUDE.md
Task agent T015 &  # CHANGELOG.md
Task agent T016 &  # LLM Help
wait
```

### Phase 3 - Polish & Release (Parallel where possible)
```bash
# Independent file creation/modification
Task agent T017 &  # JSON5 template
Task agent T018 &  # .gitignore
Task agent T019 &  # pyproject.toml
wait

# Testing tasks (sequential, depend on implementation)
Task agent T020    # Edge case testing
Task agent T021    # Performance validation

# Final review (sequential)
Task agent T022    # Code review & linting
Task agent T023    # PR preparation
```

---

## Dependency Graph

```
Phase 0:
  [T001, T002, T003] → T004

Phase 1 (Sequential):
  T004 → T005 → T006 → T007 → T008 → T009

Phase 2:
  Group 1 (Tests): [T010, T011, T012] (depend on T009)
  Group 2 (Docs): [T013, T014, T015, T016] (depend on T009)

Phase 3:
  Group 1: [T017, T018, T019] (parallel, minimal dependencies)
  T020 → depends on T010, T011, T012
  T021 → depends on T009
  T022 → depends on all previous tasks
  T023 → depends on T022
```

---

## Progress Tracking

- [ ] **Phase 0:** Research & Foundation (T001-T004)
- [ ] **Phase 1:** Core Implementation (T005-T009)
- [ ] **Phase 2:** Testing & Documentation (T010-T016)
- [ ] **Phase 3:** Polish & Release (T017-T023)

**Mark tasks complete as you execute them. Update this document to track progress.**

---

## Next Steps

1. **Start Phase 0:** Execute T001, T002, T003 in parallel
2. **Complete T004:** Document data model after research tasks complete
3. **Begin Phase 1:** Implement core functionality (T005-T009)
4. **Execute tests:** Run Phase 2 tasks once implementation complete
5. **Polish & release:** Complete Phase 3 and prepare PR

**Ready to execute!** 🚀
