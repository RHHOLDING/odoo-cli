# Implementation Plan: Project Context Layer for LLM Agents

**Feature ID:** 003
**Branch:** `feature/003-als_llm_agent_m_chte_ich_zugriff_auf_projektspezif`
**Status:** Planning
**Version:** 1.0.0

---

## Executive Summary

This feature introduces a manually-maintained `.odoo-context.json` file that provides LLM agents with project-specific business context (company roles, warehouse meanings, critical workflows, custom module purposes). Three new CLI commands (`context show`, `context guide`, `context validate`) enable LLMs to query this context at runtime, improving recommendation quality without requiring API calls to analyze the Odoo system.

**Key Deliverables:**
1. ContextManager class for loading/validating context files
2. Three CLI commands: `context show`, `context guide`, `context validate`
3. JSON5 template file (`.odoo-context.json5.example`) with inline documentation
4. JSON Schema for validation and comprehensive documentation

**Estimated Effort:** 20-24 hours (2.5-3 working days)

---

## Phase 0: Research & Foundation (4h)

### Objectives
- Validate JSON5 library options for template parsing
- Explore existing CLI command patterns in odoo-cli
- Define JSON Schema structure for context validation
- Create data model and contract specifications

### Tasks

#### Task 0.1: Research JSON5 Libraries
**Description:** Evaluate `pyjson5` vs `json5` for parsing template file with inline comments
**Effort:** 0.5h
**Deliverables:**
- Library recommendation (prefer `pyjson5` for better maintenance)
- Dependency specification for `pyproject.toml`

**Acceptance Criteria:**
- [ ] Library chosen based on PyPI maintenance status and Python 3.10+ compatibility
- [ ] Verify library can parse JSON5 with comments

**Deliverable:** Library selection documented

#### Task 0.2: Analyze Existing Command Patterns
**Description:** Review existing CLI commands (search, create, etc.) to understand Click patterns, JSON output modes, and Rich formatting
**Effort:** 1h
**Deliverables:**
- Command structure pattern for context commands
- Error handling patterns to replicate

**Acceptance Criteria:**
- [ ] Understand `@click.pass_obj` usage
- [ ] Understand `output_json()` and `output_error()` utilities
- [ ] Understand `--json` flag handling

**Deliverable:** Pattern documentation in research.md

#### Task 0.3: Define JSON Schema
**Description:** Create formal JSON Schema for `.odoo-context.json` validation (strict mode)
**Effort:** 1.5h
**Deliverables:**
- `odoo_cli/schemas/context_schema.json`
- Schema defines: schema_version, project, companies, warehouses, workflows, modules, notes

**Acceptance Criteria:**
- [ ] Schema validates example JSON structure
- [ ] All fields optional except schema_version
- [ ] Supports nested structures (company.warehouses references)

**Deliverable:** `odoo_cli/schemas/context_schema.json`

#### Task 0.4: Document Data Model
**Description:** Create data-model.md specifying ContextManager class structure and data flow
**Effort:** 1h
**Deliverables:**
- Data model document in specs_dir
- Class diagram for ContextManager
- File search logic (CWD only, no upward traversal)

**Acceptance Criteria:**
- [ ] Documents ContextManager interface
- [ ] Documents context file structure
- [ ] Documents validation logic flow

**Deliverable:** `data-model.md` in feature directory

---

## Phase 1: Core Implementation (10h)

### Milestone: Functional CLI Commands

#### Task 1.1: Implement ContextManager Class
**Description:** Create core ContextManager class for loading and accessing context files
**Effort:** 2h
**Files:**
- `odoo_cli/context.py` (NEW)

**Implementation:**
```python
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

class ContextManager:
    """Manages loading and accessing .odoo-context.json"""

    def __init__(self, context_file: Optional[Path] = None):
        self.context_file = context_file or Path.cwd() / ".odoo-context.json"
        self.context: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """Load context from file, returns empty dict if not found"""
        if not self.context_file.exists():
            return {}

        with open(self.context_file, 'r') as f:
            self.context = json.load(f)
        return self.context

    def get_section(self, section: str) -> Any:
        """Get specific section (companies, warehouses, etc.)"""
        if self.context is None:
            self.load()
        return self.context.get(section, [])

    def validate(self, strict: bool = False) -> Dict[str, Any]:
        """Validate context file, return validation result"""
        # Implementation in Task 1.4
        pass
```

**Acceptance Criteria:**
- [ ] ContextManager loads valid JSON files
- [ ] Returns empty dict for missing files (no errors)
- [ ] get_section() returns empty list for missing sections
- [ ] File search limited to CWD only

**Deliverable:** Working ContextManager class

#### Task 1.2: Implement `context show` Command
**Description:** CLI command to display context (full or filtered by section)
**Effort:** 2h
**Files:**
- `odoo_cli/commands/context.py` (NEW)

**Implementation:**
```python
import click
from rich.console import Console
from rich.table import Table
from odoo_cli.context import ContextManager
from odoo_cli.utils import output_json, output_error

@click.group(name='context')
def context():
    """Manage project-specific business context"""
    pass

@context.command()
@click.option('--section', type=str, help='Filter by section (companies, warehouses, workflows, modules, notes)')
@click.option('--json', 'json_mode', is_flag=True, help='Output as JSON')
@click.pass_obj
def show(ctx, section, json_mode):
    """Display business context for LLM agents"""
    json_mode = json_mode or ctx.json_mode

    manager = ContextManager()
    context_data = manager.load()

    if not context_data:
        if json_mode:
            output_json({"context": {}, "message": "No context file found"})
        else:
            console = Console()
            console.print("[yellow]No .odoo-context.json file found in current directory[/yellow]")
        return

    if section:
        context_data = {section: manager.get_section(section)}

    if json_mode:
        output_json({"context": context_data})
    else:
        # Rich formatting
        console = Console()
        # Format and display context
```

**Acceptance Criteria:**
- [ ] `odoo-cli context show` displays full context
- [ ] `--section companies` filters correctly
- [ ] `--json` flag returns structured JSON
- [ ] Rich formatting for human-readable output
- [ ] Handles missing file gracefully

**Deliverable:** Working `context show` command

#### Task 1.3: Implement `context guide` Command
**Description:** Provide task-specific guidance using hardcoded mappings
**Effort:** 2.5h
**Files:**
- `odoo_cli/commands/context.py` (MODIFY)

**Implementation:**
```python
# Hardcoded task-to-section mappings
TASK_MAPPINGS = {
    'create-sales-order': ['companies', 'warehouses'],
    'manage-inventory': ['warehouses', 'modules'],
    'purchase-approval': ['workflows', 'companies'],
    'production-workflow': ['modules', 'workflows']
}

@context.command()
@click.option('--task', required=True, type=click.Choice(list(TASK_MAPPINGS.keys())),
              help='Task name for context-aware guidance')
@click.option('--json', 'json_mode', is_flag=True, help='Output as JSON')
@click.pass_obj
def guide(ctx, task, json_mode):
    """Get context-aware guidance for common tasks"""
    json_mode = json_mode or ctx.json_mode

    manager = ContextManager()
    context_data = manager.load()

    if not context_data:
        if json_mode:
            output_json({"guide": {}, "message": "No context available"})
        else:
            console = Console()
            console.print("[yellow]No context file found[/yellow]")
        return

    # Get relevant sections for task
    relevant_sections = TASK_MAPPINGS[task]
    guide_data = {section: manager.get_section(section) for section in relevant_sections}

    if json_mode:
        output_json({"task": task, "guide": guide_data})
    else:
        # Rich formatting with task-specific suggestions
```

**Acceptance Criteria:**
- [ ] Supports 4 predefined tasks (create-sales-order, manage-inventory, purchase-approval, production-workflow)
- [ ] Returns relevant context sections based on hardcoded mapping
- [ ] Returns empty guide for missing context
- [ ] JSON output is LLM-parsable

**Deliverable:** Working `context guide` command

#### Task 1.4: Implement `context validate` Command
**Description:** Validate context file with normal and strict modes
**Effort:** 3h
**Files:**
- `odoo_cli/commands/context.py` (MODIFY)
- `odoo_cli/context.py` (MODIFY - add validate method)

**Implementation:**
```python
import re
from jsonschema import validate as schema_validate, ValidationError

# In ContextManager class
def validate(self, strict: bool = False) -> Dict[str, Any]:
    """Validate context file, return validation result"""
    warnings = []
    errors = []

    if not self.context_file.exists():
        return {"valid": False, "errors": ["Context file not found"], "warnings": []}

    try:
        with open(self.context_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "warnings": []}

    # Check for security issues (minimal: literal "password" or "token")
    content_str = json.dumps(data, indent=2).lower()
    if "password" in content_str:
        warnings.append("Found literal 'password' in context file")
    if "token" in content_str:
        warnings.append("Found literal 'token' in context file")

    # Strict mode: schema validation
    if strict:
        # Load schema
        schema_path = Path(__file__).parent / "schemas" / "context_schema.json"
        with open(schema_path) as f:
            schema = json.load(f)

        try:
            schema_validate(instance=data, schema=schema)
        except ValidationError as e:
            errors.append(f"Schema validation failed: {e.message}")

        # Strict: require all major sections non-empty
        required_sections = ['companies', 'warehouses', 'workflows', 'modules', 'notes']
        for section in required_sections:
            if section not in data or not data[section]:
                errors.append(f"Section '{section}' is missing or empty (required in strict mode)")

        # Strict: require project metadata
        if 'project' not in data or not data['project'].get('name'):
            errors.append("Project name is required in strict mode")

        # Strict: warnings become errors
        if warnings:
            errors.extend([f"Warning (strict): {w}" for w in warnings])
            warnings = []

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

# CLI command
@context.command()
@click.option('--strict', is_flag=True, help='Enforce strict validation (schema + completeness)')
@click.option('--json', 'json_mode', is_flag=True, help='Output as JSON')
@click.pass_obj
def validate(ctx, strict, json_mode):
    """Validate context file"""
    json_mode = json_mode or ctx.json_mode

    manager = ContextManager()
    result = manager.validate(strict=strict)

    exit_code = 0 if result['valid'] else 3

    if json_mode:
        output_json(result)
    else:
        console = Console()
        if result['valid']:
            console.print("[green]✓ Context file is valid[/green]")
        else:
            console.print("[red]✗ Context file validation failed[/red]")
            for error in result['errors']:
                console.print(f"  [red]ERROR:[/red] {error}")

        for warning in result['warnings']:
            console.print(f"  [yellow]WARNING:[/yellow] {warning}")

    ctx.obj.exit_code = exit_code
```

**Acceptance Criteria:**
- [ ] Normal mode: checks JSON syntax, warns about "password"/"token" strings
- [ ] Strict mode: JSON schema validation, all sections required, warnings become errors
- [ ] Exit code 0 for valid, 3 for invalid
- [ ] Clear error messages with suggestions

**Deliverable:** Working `context validate` command

#### Task 1.5: Register Context Commands
**Description:** Register context command group in main CLI
**Effort:** 0.5h
**Files:**
- `odoo_cli/cli.py` (MODIFY)

**Implementation:**
```python
from odoo_cli.commands.context import context

# Add to main CLI group
cli.add_command(context)
```

**Acceptance Criteria:**
- [ ] `odoo-cli context --help` works
- [ ] All three subcommands registered

**Deliverable:** Context commands accessible via CLI

---

## Phase 2: Testing & Documentation (6h)

### Milestone: Tested and Documented Feature

#### Task 2.1: Unit Tests
**Description:** Comprehensive unit tests for ContextManager and commands
**Effort:** 3h
**Files:**
- `tests/unit/test_context.py` (NEW)
- `tests/unit/test_commands_context.py` (NEW)

**Test Coverage:**
- ContextManager.load() with valid file
- ContextManager.load() with missing file (returns empty dict)
- ContextManager.load() with invalid JSON (graceful error)
- ContextManager.get_section() for each section type
- ContextManager.validate() normal mode (detects "password", "token")
- ContextManager.validate() strict mode (schema enforcement, required sections)
- CLI command invocations (mocked Click context)
- JSON output format validation

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] Coverage >90% for new code
- [ ] Tests use mock context files, not real data

**Deliverable:** Comprehensive unit test suite

#### Task 2.2: Integration Tests
**Description:** Integration tests with actual context files
**Effort:** 1.5h
**Files:**
- `tests/integration/test_context_integration.py` (NEW)
- `tests/fixtures/context-valid.json` (NEW)
- `tests/fixtures/context-invalid.json` (NEW)

**Test Scenarios:**
- Create temp context file, run `context show`, verify output
- Run `context guide --task create-sales-order` with fixture
- Run `context validate` with valid/invalid fixtures
- Test missing context file (all commands handle gracefully)

**Acceptance Criteria:**
- [ ] Tests run in isolated temp directories
- [ ] All integration tests pass

**Deliverable:** Integration test suite

#### Task 2.3: Documentation Updates
**Description:** Update all user-facing and developer documentation
**Effort:** 1.5h
**Files:**
- `README.md` (MODIFY)
- `CLAUDE.md` (MODIFY)
- `CHANGELOG.md` (MODIFY)
- `odoo_cli/help.py` (MODIFY)

**Content to add:**
- README: New "Business Context" section with examples
- CLAUDE.md: Context file best practices, security guidelines
- CHANGELOG: v1.5.0 entry with context feature
- `--llm-help`: Decision tree for when to use context commands

**Acceptance Criteria:**
- [ ] All docs updated consistently
- [ ] Examples use demo data (Azure Interior, Deco Addict)
- [ ] Security warnings prominent

**Deliverable:** Tested and documented feature

---

## Phase 3: Polish & Release (4h)

### Milestone: Ready for Merge

#### Task 3.1: Create JSON5 Template File
**Description:** Create `.odoo-context.json5.example` with inline comments and Do's & Don'ts
**Effort:** 1.5h
**Files:**
- `.odoo-context.json5.example` (NEW)

**Content:**
```json5
// .odoo-context.json5.example
//
// This is a template for project-specific business context.
// Copy this file to .odoo-context.json (standard JSON, no comments) and customize.
//
// DO's:
// - Use business-friendly descriptions (not just technical IDs)
// - Document critical workflows and their rules
// - Keep file updated as your Odoo instance evolves
//
// DON'Ts:
// - NEVER include passwords, API keys, or tokens
// - NEVER include real customer data or emails
// - NEVER commit .odoo-context.json to version control

{
  "schema_version": "1.0.0",

  // Project metadata
  "project": {
    "name": "Azure Interior Production",
    "description": "Main ERP instance for furniture manufacturing",
    "odoo_version": "17.0"
  },

  // Company definitions with business roles
  "companies": [
    {
      "id": 1,
      "name": "Azure Interior",
      "role": "Main manufacturing company",
      "context": "Handles all production and B2B sales"
    },
    {
      "id": 2,
      "name": "Marketplace Hub",
      "role": "E-commerce operations",
      "context": "Highest volume, B2C sales, uses automated workflows"
    }
  ],

  // Warehouse context
  "warehouses": [
    {
      "id": 1,
      "name": "Main Warehouse",
      "company_id": 1,
      "role": "Production storage",
      "context": "Raw materials and finished goods"
    }
  ],

  // Critical workflows
  "workflows": [
    {
      "name": "Purchase Approval",
      "critical": true,
      "context": "Requires dual approval for purchases > 10k EUR"
    }
  ],

  // Custom modules and their purposes
  "modules": [
    {
      "name": "custom_mrp_workflow",
      "purpose": "Custom manufacturing workflow for furniture",
      "context": "Handles multi-step production with quality checks"
    }
  ],

  // Freeform notes
  "notes": {
    "common_tasks": [
      "Most sales orders go through company_id=2 (Marketplace Hub)",
      "Never modify archived products without checking with inventory team"
    ],
    "pitfalls": [
      "Warehouse transfers between company 1 and 2 require manual approval"
    ]
  }
}
```

**Acceptance Criteria:**
- [ ] All schema sections covered with examples
- [ ] Uses Odoo demo data (Azure Interior, Deco Addict)
- [ ] Inline comments explain each section
- [ ] Do's & Don'ts clearly stated

**Deliverable:** `.odoo-context.json5.example`

#### Task 3.2: Update .gitignore
**Description:** Ensure `.odoo-context.json` is gitignored
**Effort:** 0.25h
**Files:**
- `.gitignore` (MODIFY)

**Acceptance Criteria:**
- [ ] `.odoo-context.json` added to `.gitignore`
- [ ] `.odoo-context.json5.example` is NOT gitignored (should be committed)

**Deliverable:** Updated .gitignore

#### Task 3.3: Edge Case Handling
**Description:** Test and handle all edge cases from spec
**Effort:** 1h

**Edge Cases:**
1. Missing context file → Return empty context, no errors
2. Invalid JSON syntax → Clear error with line number
3. Partial context (some sections missing) → Accept gracefully, return empty for missing
4. Very large file (>1MB) → Warn during validation
5. Context file not in CWD → Clear error message (no upward search)

**Acceptance Criteria:**
- [ ] All edge cases tested
- [ ] Clear error messages for each case
- [ ] No crashes or unclear errors

**Deliverable:** Edge cases handled

#### Task 3.4: Performance Validation
**Description:** Validate performance targets
**Effort:** 0.5h

**Targets:**
- Context file load time <100ms (for files up to 1MB)
- Command startup remains <500ms

**Acceptance Criteria:**
- [ ] Performance targets met
- [ ] No noticeable CLI slowdown

**Deliverable:** Performance validated

#### Task 3.5: Final Review & PR Preparation
**Description:** Final checks before merge
**Effort:** 0.75h

**Checklist:**
- [ ] All acceptance criteria met (FR-1 through FR-6, NFR-1 through NFR-3)
- [ ] All tests passing
- [ ] No linting errors (Black, isort)
- [ ] CHANGELOG.md updated
- [ ] All three LLM docs updated (CLAUDE.md, CODEX.md, GEMINI.md)
- [ ] No credentials or sensitive data in any files
- [ ] Example file uses only demo data

**Deliverable:** Ready-to-merge PR

---

## Dependencies & Prerequisites

### External Dependencies
- `jsonschema` - For JSON Schema validation in strict mode
- `pyjson5` - For parsing JSON5 template file (development/testing only)

### Internal Dependencies
- Existing CLI framework (Click)
- Existing output utilities (`output_json`, `output_error`)
- Rich formatting library

### Required Access
- None (all local development)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| JSON5 library incompatibility | Low | Medium | Evaluate both `pyjson5` and `json5` in Phase 0; choose most stable |
| Schema validation performance on large files | Medium | Low | Test with 1MB file; add size check in validation |
| Users commit sensitive data despite warnings | Medium | High | Multiple safeguards: gitignore, validate warnings, prominent docs |
| Hardcoded task mappings too limiting | Medium | Low | Document as extensible in future; start with 4 core tasks |

---

## Success Criteria Checklist

### Functional Requirements
- [ ] FR-1: Context file structure defined with JSON schema
- [ ] FR-2: `context show` command implemented (full + filtered)
- [ ] FR-3: `context guide` command with hardcoded task mappings
- [ ] FR-4: `context validate` command (normal + strict modes)
- [ ] FR-5: `.odoo-context.json5.example` template created
- [ ] FR-6: Security by default (.gitignore, validate warnings)

### Non-Functional Requirements
- [ ] NFR-1: Context loading <100ms for files up to 1MB
- [ ] NFR-2: JSON mode available for all context commands
- [ ] NFR-3: CLI functions normally without context file

### User Stories
- [ ] Story 1: LLM retrieves company context via `context show --section companies --json`
- [ ] Story 2: Developer creates context file from template, validates successfully
- [ ] Story 3: LLM checks workflow criticality via `context show --section workflows --json`

### Testing
- [ ] Unit tests pass (>90% coverage for new code)
- [ ] Integration tests pass
- [ ] Edge cases tested

### Documentation
- [ ] README.md updated with Business Context section
- [ ] CLAUDE.md updated with context best practices
- [ ] CHANGELOG.md updated for v1.5.0
- [ ] `--llm-help` includes context command decision trees

---

## Timeline Estimate

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 0: Research | 4h | None |
| Phase 1: Implementation | 10h | Phase 0 |
| Phase 2: Testing | 6h | Phase 1 |
| Phase 3: Polish | 4h | Phase 2 |
| **Total** | **24h** | |

**Target Completion:** 3 working days

---

## Clarifications Applied

From Session 2025-11-21:

1. **Task guide logic:** Hardcoded mapping with predefined task names
   - Implementation: `TASK_MAPPINGS` dict in `context.py` with 4 tasks (create-sales-order, manage-inventory, purchase-approval, production-workflow)

2. **Template file format:** JSON5 (.json5.example) with inline comments
   - Implementation: Use `pyjson5` for parsing template (dev only); actual context file remains standard JSON

3. **File search scope:** Current directory only, no upward search
   - Implementation: `ContextManager.__init__` uses `Path.cwd() / ".odoo-context.json"` with no directory traversal

4. **Strict validation enforcement:** Schema validation + fail on warnings + require complete docs
   - Implementation: `validate(strict=True)` enforces JSON schema, requires all sections non-empty, converts warnings to errors

5. **Security pattern matching:** Minimal (literal "password"/"token" only)
   - Implementation: Simple case-insensitive string search in JSON content; avoid false positives

---

## Progress Tracking

- [x] Phase 0: Research & Foundation
- [ ] Phase 1: Core Implementation
- [ ] Phase 2: Testing & Documentation
- [ ] Phase 3: Polish & Release

---

## Next Steps

1. **Review this plan:** Ensure alignment with spec and clarifications
2. **Start Phase 0:** Begin with Task 0.1 (Research JSON5 Libraries)
3. **Generate tasks.md:** Run `/specify:tasks` to create granular task breakdown
4. **Begin implementation:** Execute Phase 1 tasks sequentially

**Ready to proceed with implementation!** 🚀
