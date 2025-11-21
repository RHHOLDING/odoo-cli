# Feature: Project Context Layer for LLM Agents

**ID:** 003
**Status:** Draft
**Version:** 1.0.0
**Priority:** High
**Effort:** Medium

---

## Problem Statement

**What problem does this solve?**

LLM agents using odoo-cli need access to project-specific business context (company roles, warehouse meanings, critical workflows, custom module purposes) to provide better recommendations. Currently, they must either analyze the Odoo system through API calls (slow, inefficient) or lack this context entirely (poor recommendations).

**Who is affected?**
- LLM agents (Claude, GPT) using odoo-cli in various projects
- Developers/consultants who want LLMs to understand their specific Odoo setup
- End users receiving LLM assistance for Odoo-related tasks

**Current pain points:**
- LLMs must query Odoo API to understand business context (e.g., "What does company ID 2 mean?")
- No standardized way to provide business knowledge to LLMs
- Context stored in repository files is not accessible during CLI runtime
- Risk of exposing sensitive business information in public repositories
- Each LLM session starts without business understanding

---

## Goals

### Primary Goals
1. Provide LLM-accessible business context through CLI commands
2. Enable manual curation of business knowledge without automatic discovery
3. Ensure security for public repositories (no sensitive data committed)
4. Create standardized format for business context across projects

### Success Criteria
- [ ] LLMs can retrieve business context via CLI commands (`context show`, `context guide`, `context validate`)
- [ ] `.odoo-context.json` file structure documented with template
- [ ] Template (`.odoo-context.json5.example`) provided for users with inline comments
- [ ] Security guide (Do's & Don'ts) prevents credential/data leaks
- [ ] Context commands documented in `--llm-help`
- [ ] `.odoo-context.json` added to `.gitignore`
- [ ] LLM can make better recommendations using context (manual validation)

---

## Solution Overview

**High-level approach:**

Introduce a manually-maintained `.odoo-context.json` file that contains business metadata about the Odoo instance. This file is local-only (like `.env`), with only a `.example` template committed to repositories. New CLI commands (`context show`, `context guide`, `context validate`) allow LLMs to query this context at runtime.

**Key components:**
1. **Context File (`.odoo-context.json`)** - JSON file with business metadata
2. **Context Manager** - Python module to load/validate context file
3. **CLI Commands** - Three new commands for context access
4. **Template & Documentation** - `.odoo-context.json5.example` (JSON5 with inline comments) + user guide
5. **LLM Help Integration** - Decision trees in `--llm-help`

---

## Clarifications

### Session 2025-11-21

- Q: How should the `context guide --task` command logic work? → A: Hardcoded mapping - predefined task names map to specific context sections via internal logic
- Q: How should inline comments be handled in the example file since JSON doesn't support comments? → A: Use JSON5 format (.json5 extension) which supports comments
- Q: Should context file search walk up directory tree or stay in current directory? → A: Search current directory only, no upward search
- Q: What additional checks should `context validate --strict` enforce? → A: All of the above - schema validation, fail on any warnings, require complete documentation
- Q: What specific patterns should trigger security warnings during validation? → A: Minimal - only literal "password" and "token" strings (case-insensitive) to avoid false positives

---

## Requirements

### Functional Requirements

#### FR-1: Context File Structure
**Description:** Define JSON schema for `.odoo-context.json` with sections for companies, warehouses, workflows, modules, and custom notes.
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] JSON schema documented with all supported fields
- [ ] Schema supports nested structures (e.g., company.warehouses)
- [ ] All fields are optional (partial context is valid)
- [ ] Schema version field for future compatibility

#### FR-2: CLI Command - context show
**Description:** Display all or filtered business context in JSON or human-readable format
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] `odoo-cli context show` displays full context
- [ ] `odoo-cli context show --section companies` filters by section
- [ ] `--json` flag returns structured JSON for LLM parsing
- [ ] Human-readable format uses Rich formatting
- [ ] Handles missing context file gracefully

#### FR-3: CLI Command - context guide
**Description:** Provide context-aware guidance for common tasks using hardcoded task-to-context mappings
**Priority:** Should Have
**Acceptance Criteria:**
- [ ] `odoo-cli context guide --task create-sales-order` returns relevant context using predefined mapping (e.g., sales-order tasks map to companies, warehouses sections)
- [ ] Predefined task names include: create-sales-order, manage-inventory, purchase-approval, production-workflow
- [ ] Suggests which company/warehouse to use based on context
- [ ] Returns empty guide if no relevant context exists or task name unrecognized
- [ ] Guides are LLM-parsable (JSON format)

#### FR-4: CLI Command - context validate
**Description:** Validate context file against schema and check for common issues; strict mode enforces comprehensive validation
**Priority:** Should Have
**Acceptance Criteria:**
- [ ] Normal mode: Checks JSON syntax validity, validates against schema, warns about potential security issues (literal "password" or "token" strings, case-insensitive), suggests improvements (missing sections, empty fields)
- [ ] `--strict` mode enforces: (1) Formal JSON schema validation with no unknown fields, (2) All warnings become errors (fail validation), (3) All major schema sections (companies, warehouses, workflows, modules, notes) must be present and non-empty, (4) Project metadata (name, description) required
- [ ] Exit code 0 for valid, non-zero for invalid (different codes for syntax vs schema vs security issues)
- [ ] Clear error messages with line numbers and suggestions

#### FR-5: Template and Example File
**Description:** Provide `.odoo-context.json5.example` with comprehensive examples using JSON5 format (supports inline comments)
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] Example file uses JSON5 format with .json5 extension to support inline comments
- [ ] Example file covers all schema sections
- [ ] Uses generic Odoo demo data (Azure Interior, Deco Addict)
- [ ] Includes inline comments explaining each section
- [ ] Contains Do's & Don'ts section as comments
- [ ] Note: Actual user context file `.odoo-context.json` remains standard JSON (no comments needed)

#### FR-6: Security by Default
**Description:** Prevent accidental commit of sensitive data
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] `.odoo-context.json` added to `.gitignore`
- [ ] `context validate` warns if file contains literal "password" or "token" strings (case-insensitive)
- [ ] Documentation emphasizes security best practices and manual review
- [ ] Example file contains no real credentials/data

### Non-Functional Requirements

#### NFR-1: Performance
**Description:** Context loading should not impact CLI responsiveness
**Metric:** Context file load time < 100ms for files up to 1MB

#### NFR-2: LLM-Friendly Output
**Description:** All outputs must be easily parsable by LLMs
**Metric:** JSON mode available for all context commands

#### NFR-3: Backward Compatibility
**Description:** CLI functions normally without context file
**Metric:** All existing commands work if `.odoo-context.json` is missing

---

## User Stories

### Story 1: LLM Retrieves Company Context
**As a** LLM agent
**I want** to understand what company ID 2 represents
**So that** I can recommend the correct company for a sales order

**Acceptance Criteria:**
- [ ] LLM runs `odoo-cli context show --section companies --json`
- [ ] Receives structured JSON with company metadata
- [ ] Uses context to make informed recommendation

### Story 2: Developer Sets Up Context
**As a** Odoo developer
**I want** to create a context file for my project
**So that** LLMs can understand my business setup

**Acceptance Criteria:**
- [ ] Developer copies `.odoo-context.json5.example` and converts to `.odoo-context.json` (removes comments, converts to standard JSON)
- [ ] Customizes with project-specific metadata
- [ ] Validates with `odoo-cli context validate`
- [ ] File is automatically gitignored

### Story 3: LLM Validates Workflow
**As a** LLM agent
**I want** to check if a specific workflow is critical
**So that** I can warn the user before suggesting changes

**Acceptance Criteria:**
- [ ] LLM runs `odoo-cli context show --section workflows --json`
- [ ] Identifies "Purchase Approval" as critical workflow
- [ ] Provides appropriate warning in recommendation

---

## Design

### CLI Interface

```bash
# Show full context
odoo-cli context show
odoo-cli context show --json

# Show specific section
odoo-cli context show --section companies
odoo-cli context show --section warehouses --json

# Get context-aware guidance (using hardcoded task mappings)
odoo-cli context guide --task create-sales-order
odoo-cli context guide --task manage-inventory --json
odoo-cli context guide --task purchase-approval
odoo-cli context guide --task production-workflow

# Task mappings (hardcoded):
# create-sales-order → companies, warehouses
# manage-inventory → warehouses, modules
# purchase-approval → workflows, companies
# production-workflow → modules, workflows

# Validate context file
odoo-cli context validate
odoo-cli context validate --strict
```

### Configuration

```json
{
  "schema_version": "1.0.0",
  "project": {
    "name": "Azure Interior Production",
    "description": "Main ERP instance for furniture manufacturing",
    "odoo_version": "17.0"
  },
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
  "warehouses": [
    {
      "id": 1,
      "name": "Main Warehouse",
      "company_id": 1,
      "role": "Production storage",
      "context": "Raw materials and finished goods"
    }
  ],
  "workflows": [
    {
      "name": "Purchase Approval",
      "critical": true,
      "context": "Requires dual approval for purchases > 10k EUR"
    }
  ],
  "modules": [
    {
      "name": "custom_mrp_workflow",
      "purpose": "Custom manufacturing workflow for furniture",
      "context": "Handles multi-step production with quality checks"
    }
  ],
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

### Data Structures

```python
# odoo_cli/context.py

from typing import Dict, List, Optional, Any
from pathlib import Path
import json

class ContextManager:
    """Manages loading and accessing .odoo-context.json"""

    def __init__(self, context_file: Path = None):
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

    def validate(self, strict: bool = False) -> List[str]:
        """Validate context file, return list of warnings/errors"""
        warnings = []
        # Check for potential secrets
        # Validate schema
        # Check for empty sections
        return warnings
```

---

## Implementation Notes

### Files to Modify
- `.gitignore` - Add `.odoo-context.json`
- `odoo_cli/cli.py` - Register new `context` command group
- `odoo_cli/help.py` - Add context commands to `--llm-help`
- `README.md` - Document context feature
- `CLAUDE.md` - Update with context guidelines

### New Files
- `odoo_cli/context.py` - ContextManager class
- `odoo_cli/commands/context.py` - CLI commands (show, guide, validate)
- `odoo_cli/schemas/context_schema.json` - JSON Schema definition for validation (used in strict mode)
- `.odoo-context.json5.example` - Template file (JSON5 format with inline comments)
- `docs/context-guide.md` - Detailed user guide
- `tests/unit/test_context.py` - Unit tests for ContextManager
- `tests/unit/test_commands_context.py` - CLI command tests

### Dependencies
- `jsonschema` - For JSON Schema validation in strict mode
- `pyjson5` or `json5` - For parsing JSON5 template file (example only, not required for runtime)
- Uses existing: `click`, `rich`, `json` (stdlib for actual context file)

---

## Testing Strategy

### Unit Tests
- [ ] Test ContextManager.load() with valid file
- [ ] Test ContextManager.load() with missing file
- [ ] Test ContextManager.load() with invalid JSON
- [ ] Test ContextManager.get_section() for each section type
- [ ] Test ContextManager.validate() detects security issues
- [ ] Test validate() detects schema violations

### Integration Tests
- [ ] Test `context show` with example file
- [ ] Test `context show --section companies --json`
- [ ] Test `context validate` with valid/invalid files
- [ ] Test context commands without context file (graceful degradation)

### Manual Testing
- [ ] LLM retrieves context and makes recommendation
- [ ] Developer creates context file from template
- [ ] Validate command catches security issues (test with fake credentials)
- [ ] Context guide provides relevant suggestions

---

## Edge Cases

1. **Missing context file**
   Handling: Return empty context, CLI continues normally, no errors

2. **Invalid JSON syntax**
   Handling: Show clear error message with line number, suggest validation

3. **Partial context (only some sections filled)**
   Handling: Accept gracefully, return empty arrays/objects for missing sections

4. **Very large context file (>1MB)**
   Handling: Warn during validation, suggest splitting or simplifying

5. **Context file not in current directory**
   Handling: No upward search - file must be in current working directory (`.odoo-context.json` in CWD). Document this requirement clearly.

6. **Multiple context files (project + user level)**
   Handling: Future enhancement - for v1.0, only support single file in current directory

---

## Security Considerations

- **Never commit `.odoo-context.json`** - Added to `.gitignore` by default
- **Validate command scans for secrets** - Minimal pattern matching (literal "password" and "token" strings, case-insensitive) to avoid false positives; users responsible for manual review
- **Example file uses only demo data** - Azure Interior, Deco Addict, generic names
- **Documentation emphasizes security** - Clear Do's & Don'ts in template, recommend manual review before committing any context-related files
- **No automatic data collection** - User manually curates context
- **Public repo safe** - Only `.json5.example` file committed, contains no sensitive data

---

## Documentation Updates

- [ ] Update README.md - Add "Business Context" section
- [ ] Update SPEC.md - Document context file format
- [ ] Update CLAUDE.md - Add context best practices
- [ ] Update --llm-help - Add context command decision trees
- [ ] Create docs/context-guide.md - Comprehensive user guide
- [ ] Add inline help to context commands

---

## Related Work

**Related Features:**
- Feature 001 (Environment Profiles) - Context could be per-environment
- Feature 002 (Project Context Layer) - This IS feature 002 (based on plan.md in repo)

**Dependencies:**
- None - Standalone feature

**Conflicts:**
- None identified

---

## Open Questions

1. Should context file support includes/references to other files?
2. Should we support multiple context files (merged hierarchy: project > user > global)?
3. Should context validation be automatic on CLI startup (opt-in)?
4. Should we provide a `context init` command to create template?
5. Should context support environment-specific overrides (combine with Feature 001)?

---

## Timeline

**Estimated Effort:** 2-3 days
**Complexity:** Medium

**Breakdown:**
- Design & Schema: 4 hours
- ContextManager Implementation: 4 hours
- CLI Commands: 6 hours
- Template & Documentation: 4 hours
- Testing: 4 hours
- LLM Help Integration: 2 hours

---

## Appendix

### References
- CLAUDE.md - Project guidelines and LLM-friendly design principles
- Feature 001 (Environment Profiles) - Similar configuration pattern
- Odoo demo data: https://demo.odoo.com

### Previous Discussions
- User request: "LLMs need business context access via CLI"
- Design principle: Manual curation, no auto-discovery
- Security: Must be safe for public repositories
