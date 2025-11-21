# Feature: Project Context Layer for LLM Agents

**ID:** 002
**Status:** idea
**Version:** v1.5.0
**Priority:** High
**Effort:** Medium (2-3 days)

---

## Problem Statement

**What problem does this solve?**

LLM agents currently need manual context about the Odoo project they're working with - available custom modules, company data, installed apps, custom fields, and model relationships. This leads to inefficient interactions where the LLM must repeatedly ask about project structure or make assumptions that may be incorrect.

**Who is affected?**
- LLM agents using odoo-cli for automation
- Developers using LLM assistants for Odoo development
- CI/CD pipelines that need project-aware operations

**Current pain points:**
- LLMs must query project structure repeatedly (what models exist? what fields? what modules?)
- No persistent project knowledge between sessions
- Manual context explanation required for each new conversation
- Inefficient API calls to discover project structure
- LLMs may suggest operations on non-existent models or fields

---

## Goals

### Primary Goals
1. Provide automatic project context discovery and caching for LLM agents
2. Enable project-aware command suggestions and validations
3. Reduce API calls and conversation overhead for project structure queries

### Success Criteria
- [ ] LLM can automatically discover available models, fields, and modules
- [ ] Context is cached locally and refreshed on-demand
- [ ] All commands can access project context without additional API calls
- [ ] Context file is human-readable and git-friendly (JSON format)
- [ ] Context initialization completes in < 30 seconds for typical projects

---

## Solution Overview

**High-level approach:**

Implement a `odoo-cli context` command group that discovers and caches project-specific metadata. The context is stored in a local `.odoo-context.json` file (gitignored) and automatically loaded by all commands. LLMs can query this context file to understand the project structure without making repeated API calls.

**Key components:**
1. **Context Discovery**: Scan Odoo instance for models, fields, modules, companies
2. **Context Storage**: Local JSON cache with project metadata
3. **Context Loading**: Automatic context injection into command execution
4. **Context Refresh**: On-demand updates when project structure changes

---

## Requirements

### Functional Requirements

#### FR-1: Context Initialization
**Description:** Command to discover and cache project context
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] `odoo-cli context init` discovers all installed models
- [ ] Captures custom fields for each model
- [ ] Lists installed modules (custom + standard)
- [ ] Stores company information
- [ ] Creates `.odoo-context.json` in project root
- [ ] Returns JSON summary of discovered context

#### FR-2: Context Refresh
**Description:** Update cached context when project changes
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] `odoo-cli context refresh` updates existing context
- [ ] Detects new models, fields, modules
- [ ] Preserves user annotations in context file
- [ ] Shows diff of changes (models added/removed, fields changed)

#### FR-3: Context Query
**Description:** Query cached context without API calls
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] `odoo-cli context show` displays cached context
- [ ] `odoo-cli context show --models` lists available models
- [ ] `odoo-cli context show --fields MODEL` shows model fields
- [ ] `odoo-cli context show --modules` lists installed modules
- [ ] Returns JSON for LLM parsing

#### FR-4: Automatic Context Loading
**Description:** All commands automatically access context
**Priority:** Should Have
**Acceptance Criteria:**
- [ ] Commands can validate model names against context
- [ ] Field suggestions based on context
- [ ] Warning when operating on models not in context
- [ ] Context available in `--llm-help` output

#### FR-5: Context File Management
**Description:** Manage context file lifecycle
**Priority:** Should Have
**Acceptance Criteria:**
- [ ] `odoo-cli context clear` removes cached context
- [ ] `odoo-cli context status` shows context age and freshness
- [ ] Auto-refresh prompt when context is >7 days old
- [ ] Context file is gitignored by default

#### FR-6: Safe Example File (Public Repo Security)
**Description:** Provide safe template without exposing real project data
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] `.odoo-context.json.example` created with generic placeholder data
- [ ] Example uses Odoo demo company names (Azure Interior, Deco Addict)
- [ ] Example shows structure without real custom module names
- [ ] `.odoo-context.json` added to `.gitignore`
- [ ] README warns: "DO NOT COMMIT .odoo-context.json"
- [ ] CLI detects if context file is not gitignored and warns user

### Non-Functional Requirements

#### NFR-1: Performance
**Description:** Context operations must be fast
**Metric:**
- Context init: < 30 seconds for typical project (1000 models)
- Context load: < 100ms per command
- Context query: < 50ms

#### NFR-2: File Size
**Description:** Context file should be reasonably sized
**Metric:**
- < 5MB for typical project
- Compressed if necessary
- Only essential metadata (no record data)

---

## User Stories

### Story 1: LLM Discovers Project Structure
**As a** LLM agent
**I want** to automatically understand what models and fields exist in the project
**So that** I can make accurate suggestions without querying the API repeatedly

**Acceptance Criteria:**
- [ ] LLM can read `.odoo-context.json` to understand project
- [ ] Context includes model names, field types, and relationships
- [ ] Context shows which modules are custom vs standard

### Story 2: Developer Initializes Context
**As a** developer
**I want** to initialize project context once after setup
**So that** LLM agents have persistent project knowledge

**Acceptance Criteria:**
- [ ] Single command initializes context: `odoo-cli context init`
- [ ] Context file is created in project root
- [ ] Clear output shows what was discovered

### Story 3: LLM Validates Operations
**As a** LLM agent
**I want** to validate that models and fields exist before suggesting operations
**So that** I don't suggest invalid commands

**Acceptance Criteria:**
- [ ] LLM checks model name against context before suggesting commands
- [ ] LLM only suggests fields that exist in context
- [ ] LLM warns if context is stale

---

## Design

### CLI Interface

```bash
# Initialize context (first time)
odoo-cli context init
# Output: Discovered 1247 models, 8432 fields, 156 modules

# Refresh context (after installing modules)
odoo-cli context refresh
# Output: +3 models, +47 fields, +2 modules

# Query context
odoo-cli context show --models
odoo-cli context show --fields res.partner
odoo-cli context show --modules --filter custom

# Context status
odoo-cli context status
# Output: Context age: 3 days, Last refresh: 2024-01-15

# Clear context
odoo-cli context clear
```

### Configuration

**Real context file (`.odoo-context.json`) - NEVER COMMIT:**

```json
{
  "version": "1.0",
  "generated_at": "2024-01-18T10:30:00Z",
  "odoo_version": "16.0",
  "database": "production-db",
  "companies": [
    {"id": 1, "name": "SOLARCRAFT GmbH"},
    {"id": 2, "name": "AC TEC GmbH"}
  ],
  "models": {
    "res.partner": {
      "custom_fields": ["x_studio_field_1"],
      "key_fields": ["name", "email", "phone"],
      "module": "base"
    },
    "helpdesk.ticket": {
      "custom_fields": ["x_priority_score"],
      "key_fields": ["name", "partner_id", "stage_id"],
      "module": "actec_helpdesk_enh"
    }
  },
  "modules": {
    "actec_helpdesk_enh": {
      "type": "custom",
      "state": "installed",
      "version": "16.0.1.0"
    }
  }
}
```

**Example template (`.odoo-context.json.example`) - SAFE TO COMMIT:**

```json
{
  "version": "1.0",
  "generated_at": "2024-01-18T10:30:00Z",
  "odoo_version": "16.0",
  "database": "your-database-name",
  "companies": [
    {"id": 1, "name": "Azure Interior"},
    {"id": 2, "name": "Deco Addict"}
  ],
  "models": {
    "res.partner": {
      "custom_fields": ["x_custom_field"],
      "key_fields": ["name", "email", "phone"],
      "module": "base"
    },
    "sale.order": {
      "custom_fields": ["x_custom_status"],
      "key_fields": ["name", "partner_id", "amount_total"],
      "module": "sale"
    }
  },
  "modules": {
    "your_custom_module": {
      "type": "custom",
      "state": "installed",
      "version": "16.0.1.0"
    }
  }
}
```

### Data Structures

```python
# odoo_cli/context.py

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class ProjectContext:
    version: str
    generated_at: datetime
    odoo_version: str
    database: str
    companies: List[Dict]
    models: Dict[str, Dict]
    modules: Dict[str, Dict]

    @classmethod
    def load(cls, path: str = ".odoo-context.json") -> Optional['ProjectContext']:
        """Load context from file"""
        pass

    def save(self, path: str = ".odoo-context.json"):
        """Save context to file"""
        pass

    def is_stale(self, days: int = 7) -> bool:
        """Check if context needs refresh"""
        pass

    def get_model_fields(self, model: str) -> List[str]:
        """Get fields for a model"""
        pass
```

---

## Implementation Notes

### Files to Modify
- `odoo_cli/cli.py` - Add context command group
- `odoo_cli/help.py` - Update LLM help with context info
- `.gitignore` - Add `.odoo-context.json`

### New Files
- `odoo_cli/commands/context.py` - Context command implementation
- `odoo_cli/context.py` - Context data structures and loading
- `tests/unit/test_context.py` - Context unit tests
- `.odoo-context.json.example` - Safe template file (committed to repo)
- `.odoo-context.json` - Real context file (gitignored, never committed)

### Dependencies
- No new external dependencies required
- Uses existing odoo_cli/client.py for API calls

---

## Testing Strategy

### Unit Tests
- [ ] Test context initialization from API responses
- [ ] Test context loading from file
- [ ] Test context staleness detection
- [ ] Test context queries (models, fields, modules)
- [ ] Test context file serialization/deserialization

### Integration Tests
- [ ] Test full context init against demo Odoo instance
- [ ] Test context refresh detects changes
- [ ] Test context validation for commands

### Manual Testing
- [ ] Initialize context on real project
- [ ] Verify context file is human-readable
- [ ] Test LLM can parse and use context
- [ ] Verify context refresh after module install

---

## Edge Cases

1. **Context file corrupted or invalid JSON**
   Handling: Graceful error message, prompt to re-initialize with `context init`

2. **API timeout during context initialization**
   Handling: Partial context save, resume on next init, show progress indicator

3. **Very large projects (10,000+ models)**
   Handling: Paginated discovery, compressed storage, optional filtering

4. **Multiple Odoo environments (prod/staging/dev)**
   Handling: Context file includes environment identifier, warn on mismatch

5. **Context file out of sync after module uninstall**
   Handling: `context refresh` detects removed models, prompts for cleanup

---

## Security Considerations

⚠️ **CRITICAL: Public Repository Safety**

This is a PUBLIC open-source repository. Context files may contain project-specific information that should NEVER be committed.

**Required Safety Measures:**

1. **`.odoo-context.json` MUST be gitignored**
   - Add to `.gitignore` immediately
   - Never commit real project context
   - Contains company names, custom module names, field names

2. **`.odoo-context.json.example` for documentation**
   - Template file that IS committed to repo
   - Uses generic placeholder data (Azure Interior, Deco Addict, etc.)
   - Shows structure without revealing real project info
   - Similar pattern to `.env.example`

3. **Context file warnings**
   - CLI warns if context file is not in `.gitignore`
   - Error if trying to commit `.odoo-context.json`
   - Documentation clearly states: "DO NOT COMMIT CONTEXT FILES"

**Safe vs Unsafe Data:**

✅ **Safe for public repo (in .example):**
- File structure and schema
- Generic Odoo model names (res.partner, sale.order)
- Placeholder company names (Demo Company, Example Corp)
- Example field names (x_custom_field)

❌ **NEVER commit to public repo:**
- Real company names (SOLARCRAFT GmbH, AC TEC GmbH)
- Custom module names (actec_helpdesk_enh, samsa_*)
- Internal field names (x_priority_score, x_studio_*)
- Database names, instance URLs
- Any customer-identifiable information

**Implementation Requirements:**
- [ ] Add `.odoo-context.json` to `.gitignore`
- [ ] Create `.odoo-context.json.example` with safe placeholder data
- [ ] Add pre-commit check to prevent accidental commits
- [ ] Update README.md with security warnings
- [ ] CLI warns if context file exists but not in .gitignore

---

## Documentation Updates

- [ ] Update README.md with context commands
- [ ] Update CLAUDE.md with context usage patterns
- [ ] Update GEMINI.md with context examples
- [ ] Update CODEX.md with context workflow
- [ ] Update --llm-help with context decision tree

---

## Related Work

**Related Features:**
- Feature 001: Environment Profiles (context per environment)
- Future: Context-aware autocomplete
- Future: Context validation in all commands

**Dependencies:**
- Requires working odoo-cli connection (uses existing client)
- Compatible with all existing commands

**Conflicts:**
- None

---

## Open Questions

1. Should context include record counts per model? (helps LLMs estimate query performance)
2. Should context track field usage frequency? (helps LLMs suggest common fields)
3. Should context be per-environment or shared? (likely per-environment)
4. Should context include custom Python code paths for modules? (helps with debugging)
5. Should context cache example records for reference? (NO - too large, privacy concern)

---

## Timeline

**Estimated Effort:** 2-3 days
**Complexity:** Medium

**Breakdown:**
- Design: 4 hours
- Implementation: 12 hours (core context system)
- Testing: 4 hours
- Documentation: 4 hours

**Total:** ~24 hours

---

## Appendix

### References
- [Odoo External API](https://www.odoo.com/documentation/16.0/developer/misc/api/odoo.html)
- [odoo-cli existing commands](../../odoo_cli/commands/)
- Similar pattern: `terraform init` (discovers provider schema)

### Previous Discussions
- PRIORITIES.md IDEA-07: "Project Context Layer"
- User request: "Als LLM Agent möchte ich automatisch verstehen, in welchem Odoo-Projekt-Kontext ich mich befinde"
