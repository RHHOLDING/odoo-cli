# Agent Experience Improvement Plan

**Version:** 1.6.0+
**Status:** Draft
**Problem Owner:** Andre Kremer

---

## Executive Summary

The odoo-cli is designed to be "LLM-friendly" but currently fails at the **first contact** experience. When an LLM agent encounters this tool for the first time, it must:

1. Figure out how to call it (`cd` into directory, `uv run`, etc.)
2. Run `--help` and parse unstructured text
3. Run `--llm-help` and parse a large JSON blob
4. Make trial-and-error queries

**Compare to GitHub CLI:**
```bash
gh --help                    # Immediately clear what to do
gh issue list               # Self-explaining
gh pr create                # Works anywhere
```

**Current odoo-cli:**
```bash
cd /path/to/odoo-cli        # Must navigate to project
uv run odoo-cli --help      # Complex invocation
uv run odoo-cli --llm-help  # 500+ lines of JSON
# Agent still confused
```

---

## Three Core Problems

### Problem 1: No Self-Discovery
When an agent first encounters odoo-cli, there's no quick way to understand:
- What can this tool do?
- How should I structure my queries?
- What's the workflow?

**Current:** `--llm-help` dumps 500+ lines of JSON
**Needed:** Quick "getting started" response

### Problem 2: No Batch/Script Mode
Agents make many sequential small queries:
```bash
odoo-cli search res.partner '[]' --limit 1   # Check connection
odoo-cli get-fields res.partner              # Get field info
odoo-cli search res.partner '[["name","ilike","Azure"]]'  # Search
odoo-cli read res.partner 123                # Read details
```

**Needed:** Single structured request with multiple operations

### Problem 3: Environment Coupling
The tool only works reliably from its project directory because:
- `.env` file is in project root
- No system-wide installation
- Agent must always `cd` first

---

## Proposed Solutions

### Solution 1: Agent Bootstrap Command

New command: `odoo-cli agent-info`

```bash
$ odoo-cli agent-info

{
  "tool": "odoo-cli",
  "version": "1.6.0",
  "status": "connected",
  "profile": "staging",
  "capabilities": {
    "read": ["search", "read", "get-fields", "get-models"],
    "write": ["create", "update", "delete"],
    "batch": ["create-bulk", "update-bulk", "script"],
    "meta": ["context", "profiles", "agent-info"]
  },
  "quick_start": {
    "list_models": "odoo-cli get-models",
    "search_partners": "odoo-cli search res.partner '[]' --limit 10",
    "read_record": "odoo-cli read res.partner 1",
    "create_record": "odoo-cli create res.partner -f name=\"Test\""
  },
  "next_steps": [
    "Run 'odoo-cli get-models' to see available models",
    "Run 'odoo-cli context show' for project context",
    "Use --json flag for structured output"
  ]
}
```

**Key features:**
- Single command to understand the tool
- Shows connection status
- Shows active profile/environment
- Provides next steps
- JSON output by default (LLM-first)

### Solution 2: Script/Batch Mode

New command: `odoo-cli script <file.yaml|file.json>`

```yaml
# operations.yaml
version: 1
operations:
  - id: find_partner
    action: search
    model: res.partner
    domain: [["name", "ilike", "Azure"]]
    fields: [id, name, email]
    limit: 5

  - id: get_orders
    action: search
    model: sale.order
    domain: [["partner_id", "in", "$find_partner.ids"]]
    fields: [id, name, state, amount_total]

  - id: update_status
    action: update
    model: sale.order
    ids: "$get_orders.ids"
    values:
      note: "Processed by automation"
```

```bash
$ odoo-cli script operations.yaml

{
  "success": true,
  "results": {
    "find_partner": {
      "success": true,
      "ids": [123, 456],
      "count": 2
    },
    "get_orders": {
      "success": true,
      "ids": [789, 790, 791],
      "count": 3
    },
    "update_status": {
      "success": true,
      "updated": 3
    }
  },
  "execution_time_ms": 234
}
```

**Key features:**
- Multiple operations in single file
- Variable substitution (`$operation_id.field`)
- Dependency ordering (operations run in sequence)
- Rollback on failure (optional)
- JSON and YAML support

**Why this helps agents:**
- Agent builds a "plan" as YAML
- Single execution, single response
- No back-and-forth
- Error handling in one place

### Solution 3: Global Installation + Config Discovery

**Goal:** `odoo-cli` works from anywhere, not just project directory.

#### 3a. Installation Options

```bash
# Option 1: pipx (recommended for CLI tools)
pipx install odoo-cli

# Option 2: pip global
pip install --user odoo-cli

# Option 3: Homebrew (future)
brew install odoo-cli
```

#### 3b. Config Discovery (like Git)

Search order:
1. `--config /path/to/config.yaml`
2. `ODOO_CONFIG=/path/to/config.yaml`
3. `./.odoo-cli.yaml` (current directory)
4. `../.odoo-cli.yaml` (parent search, up to 5 levels)
5. `~/.config/odoo-cli/config.yaml` (XDG standard)
6. `~/.odoo-cli.yaml` (legacy)

```bash
# Works from anywhere
$ pwd
/some/random/directory

$ odoo-cli search res.partner '[]'
# Finds ~/.config/odoo-cli/config.yaml automatically
```

#### 3c. Environment Variable Consolidation

| Variable | Purpose |
|----------|---------|
| `ODOO_URL` | Server URL |
| `ODOO_DB` | Database name |
| `ODOO_USERNAME` | Login |
| `ODOO_PASSWORD` | Password |
| `ODOO_PROFILE` | Active profile name |
| `ODOO_CONFIG` | Config file path |
| `ODOO_CLI_JSON` | JSON output mode |

**Priority:** CLI flags > env vars > config file > defaults

---

## Implementation Phases

### Phase 1: Agent Bootstrap (v1.6.0)
**Effort:** 2-3 hours

1. Create `odoo-cli agent-info` command
2. Show connection status, profile, capabilities
3. Provide quick-start examples
4. JSON output by default

**Files:**
- `odoo_cli/commands/agent_info.py` (new)
- `odoo_cli/cli.py` (register command)
- `odoo_cli/help.py` (update decision tree)

### Phase 2: Script Mode (v1.7.0)
**Effort:** 6-8 hours

1. Define script YAML/JSON schema
2. Create script parser
3. Implement operation executor with variable substitution
4. Add error handling and rollback
5. Create `odoo-cli script` command

**Files:**
- `odoo_cli/commands/script.py` (new)
- `odoo_cli/script/parser.py` (new)
- `odoo_cli/script/executor.py` (new)
- `odoo_cli/schemas/script_schema.json` (new)

### Phase 3: Global Installation (v1.8.0)
**Effort:** 4-5 hours

1. Update config.py for XDG paths
2. Add config discovery (parent search)
3. Test pipx installation
4. Update install.sh for global install
5. Document new installation methods

**Files:**
- `odoo_cli/config.py` (major update)
- `install.sh` (update)
- `README.md` (update)
- `pyproject.toml` (ensure entry point works)

### Phase 4: Environment Profiles (already specified)
**Effort:** 4-6 hours

See: `.specify/features/001_environment_profiles/spec.md`

---

## Comparison: Before vs After

### Before (Current)
```bash
# Agent's workflow today
cd /path/to/odoo-cli
uv run odoo-cli --llm-help          # 500 lines of JSON
uv run odoo-cli search res.partner '[]' --limit 1
uv run odoo-cli get-fields res.partner
uv run odoo-cli search res.partner '[["name","=","Azure"]]'
uv run odoo-cli read res.partner 123
# 5 commands, multiple round trips, must stay in directory
```

### After (Proposed)
```bash
# Agent's workflow after improvements
odoo-cli agent-info                  # Quick orientation
odoo-cli script <<EOF
version: 1
operations:
  - action: search
    model: res.partner
    domain: [["name", "=", "Azure"]]
    fields: [id, name, email, phone]
EOF
# 2 commands, works from anywhere
```

---

## Script Mode: Detailed Design

### Schema (v1)

```yaml
version: 1                     # Schema version
context:                       # Optional: apply to all operations
  lang: en_US
  company_id: 1

operations:
  - id: unique_name            # Required for variable reference
    action: search|read|create|update|delete|execute
    model: model.name

    # For search:
    domain: [[field, op, value], ...]
    fields: [field1, field2]   # Optional
    limit: 100                 # Optional
    offset: 0                  # Optional
    order: "name asc"          # Optional

    # For read:
    ids: [1, 2, 3] | "$prev.ids"
    fields: [field1, field2]

    # For create:
    values:
      field: value
      field2: "$prev.some_field"

    # For update:
    ids: [1, 2, 3] | "$prev.ids"
    values:
      field: new_value

    # For delete:
    ids: [1, 2, 3] | "$prev.ids"

    # For execute (custom method):
    method: action_confirm
    args: []
    kwargs: {}

# Error handling
on_error: stop|continue|rollback   # Default: stop
```

### Variable Substitution

```yaml
# Reference previous operation results
domain: [["id", "in", "$find_partner.ids"]]

# Nested access
values:
  partner_id: "$partners.records[0].id"

# Computed values
limit: "$config.batch_size"
```

### Execution Flow

```
1. Parse script file
2. Validate schema
3. Resolve static values
4. For each operation:
   a. Resolve variable references from previous results
   b. Execute operation
   c. Store result for future reference
   d. On error: stop/continue/rollback based on config
5. Return consolidated results
```

---

## Questions for User

1. **Script format preference?**
   - YAML only (simpler, human-readable)
   - JSON only (LLM-native)
   - Both (more complexity)

2. **Script complexity level?**
   - Simple (linear operations only)
   - Medium (variable substitution)
   - Advanced (conditionals, loops)

3. **Priority order?**
   - Agent Bootstrap first (quick win)
   - Script Mode first (biggest impact)
   - Global Install first (foundation)

4. **Profile integration?**
   - Include profiles in v1.6.0?
   - Or keep as separate v1.5.x release?

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Commands to understand tool | 3-5 | 1 |
| Commands for typical workflow | 5-10 | 2-3 |
| Directory dependency | Yes | No |
| Agent confusion incidents | High | Low |
| Time to first successful query | ~5 min | ~30 sec |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Script mode too complex | Medium | High | Start with v1 schema, iterate |
| Breaking existing workflows | Low | High | Backward compatibility tests |
| Security issues in scripts | Medium | High | No shell execution, sandboxed |
| Over-engineering | High | Medium | MVP first, features later |

---

## Next Steps

1. **Review this plan** with user
2. **Clarify questions** about priorities and preferences
3. **Create detailed spec** for Phase 1 (Agent Bootstrap)
4. **Implement Phase 1** as quick win
5. **Iterate** based on real-world agent feedback

---

## Appendix: Existing Work

### Already Specified
- Environment Profiles (001): Ready for implementation
- Project Context Layer (implemented in v1.5.0)

### Related IDEAs
- IDEA-03: Batch Requests Optimization
- IDEA-09: Python SDK Library
- IDEA-07: Project Context Layer (done)

### Files to Review
- `odoo_cli/help.py` - Current LLM help
- `odoo_cli/config.py` - Current config loading
- `odoo_cli/commands/context.py` - Context pattern to follow
