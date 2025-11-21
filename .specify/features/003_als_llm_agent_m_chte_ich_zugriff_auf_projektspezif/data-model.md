# Data Model: Project Context Layer

**Feature ID:** 003
**Version:** 1.0.0
**Status:** Foundation Phase Complete

---

## Overview

This document specifies the data structures and interface for the Project Context Layer feature. It defines how context files are loaded, stored, and validated.

---

## ContextManager Class

### Purpose
Manage loading and accessing `.odoo-context.json` files with validation capabilities.

### Location
`odoo_cli/context.py`

### Interface

```python
class ContextManager:
    """Manages loading and accessing .odoo-context.json files"""

    def __init__(self, context_file: Optional[Path] = None) -> None:
        """
        Initialize ContextManager

        Args:
            context_file: Path to context file (defaults to CWD/.odoo-context.json)
        """

    def load(self) -> Dict[str, Any]:
        """
        Load context from file

        Returns:
            - Full context dict if file exists and is valid JSON
            - Empty dict {} if file not found (no error)

        Raises:
            JSONDecodeError: If file exists but contains invalid JSON
        """

    def get_section(self, section: str) -> Any:
        """
        Get specific section from loaded context

        Args:
            section: Section name (companies, warehouses, workflows, modules, notes)

        Returns:
            - Section data if exists (array or object)
            - Empty list [] if section doesn't exist
        """

    def validate(self, strict: bool = False) -> Dict[str, Any]:
        """
        Validate context file

        Args:
            strict: Enforce strict validation (schema + completeness)

        Returns:
            {
                'valid': bool,
                'errors': List[str],    # Empty if valid
                'warnings': List[str]   # Empty if valid or strict mode
            }
        """
```

### Implementation Details

#### File Search Logic
- **Location:** Current working directory only
- **Path:** `Path.cwd() / ".odoo-context.json"`
- **No upward traversal:** Does not search parent directories
- **Missing file handling:** Returns empty dict, no error

#### Loading Process
1. Check if file exists at `Path.cwd() / ".odoo-context.json"`
2. If missing: return `{}`
3. If exists: read file as JSON
4. Parse and cache in `self.context`
5. Return parsed context

#### Error Handling
- **Missing file:** Not an error, return empty context
- **Invalid JSON:** Raise `JSONDecodeError` with file/line info
- **Permission denied:** Raise `PermissionError`

---

## Context File Structure

### Schema
File: `odoo_cli/schemas/context_schema.json`

### Top-Level Keys

```json
{
  "schema_version": "1.0.0",     // REQUIRED: version string (semantic versioning)
  "project": {...},               // OPTIONAL: project metadata
  "companies": [...],             // OPTIONAL: array of company objects
  "warehouses": [...],            // OPTIONAL: array of warehouse objects
  "workflows": [...],             // OPTIONAL: array of workflow objects
  "modules": [...],               // OPTIONAL: array of module objects
  "notes": {...}                  // OPTIONAL: freeform notes object
}
```

### Section Details

#### project (Object)
```python
{
    "name": str,           # Project name (e.g., "Azure Interior Production")
    "description": str,    # Project description
    "odoo_version": str    # Odoo version (e.g., "17.0")
}
```

#### companies (Array of Objects)
```python
{
    "id": int,             # Company ID (required)
    "name": str,           # Company name (required)
    "role": str,           # Business role (e.g., "Main manufacturing company")
    "context": str         # Operational context
}
```

#### warehouses (Array of Objects)
```python
{
    "id": int,             # Warehouse ID (required)
    "name": str,           # Warehouse name (required)
    "company_id": int,     # Associated company
    "role": str,           # Warehouse purpose
    "context": str         # Operational context
}
```

#### workflows (Array of Objects)
```python
{
    "name": str,           # Workflow name (required)
    "critical": bool,      # Is critical? (default: false)
    "context": str         # Rules and restrictions
}
```

#### modules (Array of Objects)
```python
{
    "name": str,           # Module name (required)
    "purpose": str,        # What it does
    "context": str         # Implementation details
}
```

#### notes (Object)
```python
{
    "common_tasks": [str], # Array of common task descriptions
    "pitfalls": [str]      # Array of gotcha/warning descriptions
}
```

---

## Validation Logic

### Normal Mode (`validate(strict=False)`)

Performs basic validation:

1. **File check:** Verify file exists
2. **JSON syntax:** Parse as JSON, catch syntax errors
3. **Security scan:**
   - Search for literal "password" (case-insensitive)
   - Search for literal "token" (case-insensitive)
   - Add warnings if found
4. **Return:** `{valid: True, errors: [], warnings: [...]}`

### Strict Mode (`validate(strict=True)`)

Enforces comprehensive validation:

1. **JSON syntax:** Same as normal mode
2. **Schema validation:** Validate against `context_schema.json` using `jsonschema`
3. **Required sections:** All major sections must exist and be non-empty:
   - `companies`
   - `warehouses`
   - `workflows`
   - `modules`
   - `notes`
4. **Project metadata:** `project.name` must be present
5. **Security:** Same as normal mode, but warnings become errors
6. **Return:** `{valid: bool, errors: [...], warnings: []}`

### Exit Codes
- `0`: Valid context file
- `3`: Invalid context file (JSON syntax, schema, or security issues)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  CLI Commands (show, guide, validate)                       │
└───────┬─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  ContextManager (odoo_cli/context.py)                       │
│  - load()                                                    │
│  - get_section()                                            │
│  - validate()                                               │
└───────┬─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  .odoo-context.json (Current Working Directory)            │
│                                                              │
│  {                                                           │
│    "schema_version": "1.0.0",                               │
│    "project": {...},                                        │
│    "companies": [...],                                      │
│    "warehouses": [...]                                      │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Validation (jsonschema library)                            │
│  - context_schema.json                                      │
│  - Security pattern matching                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Task-to-Context Mappings

### Hardcoded Mappings (in `context.py`)

Used by `context guide --task` command:

```python
TASK_MAPPINGS = {
    'create-sales-order': ['companies', 'warehouses'],
    'manage-inventory': ['warehouses', 'modules'],
    'purchase-approval': ['workflows', 'companies'],
    'production-workflow': ['modules', 'workflows']
}
```

### Mapping Logic
1. User requests guidance for a task
2. Look up task name in `TASK_MAPPINGS`
3. Get list of relevant sections
4. Return context for those sections only

---

## Type Definitions

```python
from typing import Dict, Any, List, Optional
from pathlib import Path

# Full context type
ContextData = Dict[str, Any]

# Validation result type
ValidationResult = Dict[str, Any]
# Example: {
#     'valid': bool,
#     'errors': List[str],
#     'warnings': List[str]
# }

# Section data types
CompanyData = Dict[str, Any]  # Has: id, name, role, context
WarehouseData = Dict[str, Any]  # Has: id, name, company_id, role, context
WorkflowData = Dict[str, Any]  # Has: name, critical, context
ModuleData = Dict[str, Any]  # Has: name, purpose, context
NoteData = Dict[str, Any]  # Has: common_tasks, pitfalls
```

---

## Edge Cases

| Case | Handling |
|------|----------|
| Missing context file | Return `{}`, no error |
| Invalid JSON syntax | Raise `JSONDecodeError` |
| Empty context file `{}` | Valid, returns empty |
| Partial sections | Valid, missing sections return `[]` or `{}` |
| Very large file (>1MB) | Warn during validation |
| File not in CWD | No upward search, clear error |
| Permission denied | Raise `PermissionError` |

---

## Security Considerations

### Pattern Matching
- Literal `"password"` (case-insensitive)
- Literal `"token"` (case-insensitive)
- Checks JSON stringified content

### Design Rationale
- Minimal patterns avoid false positives
- Users responsible for manual review
- Warnings in normal mode, errors in strict mode

---

## Performance

### Targets
- Load time < 100ms (for files up to 1MB)
- No caching needed (simple dict operation)
- Validation with schema < 50ms

### Optimization Notes
- Single-pass JSON parse
- Lazy section access (only load what's needed)
- Schema validation only in strict mode

---

## Dependencies

### Runtime
- `json` (stdlib)
- `pathlib` (stdlib)
- `typing` (stdlib)

### Optional (Strict Mode)
- `jsonschema>=4.0.0` (added to `pyproject.toml`)

### Dev Only
- `pyjson5>=0.9.0` (for parsing `.json5.example`)

---

## Version Compatibility

### Schema Version
- Current: `1.0.0`
- Format: Semantic versioning (`MAJOR.MINOR.PATCH`)
- Future: Support for schema upgrades

### Backward Compatibility
- All fields optional except `schema_version`
- Future versions can add new fields
- Old files work with new code

---

## References

- **Schema File:** `odoo_cli/schemas/context_schema.json`
- **Implementation:** `odoo_cli/context.py`
- **CLI Commands:** `odoo_cli/commands/context.py`
- **Tests:** `tests/unit/test_context.py`, `tests/unit/test_commands_context.py`
