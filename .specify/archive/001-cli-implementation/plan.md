# Implementation Plan: Odoo XML-RPC CLI Tool

**Branch**: `001-cli-implementation` | **Date**: 2025-11-20 | **Spec**: `specs/001-cli-implementation/spec.md`
**Input**: Feature specification from `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/specs/001-cli-implementation/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
2. Fill Technical Context ✓
3. Fill the Constitution Check section ✓
4. Evaluate Constitution Check section ✓
5. Execute Phase 0 → research.md [IN PROGRESS]
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
7. Re-evaluate Constitution Check section
8. Plan Phase 2 → Describe task generation approach
9. STOP - Ready for /tasks command
```

## Summary
A standalone, LLM-optimized CLI tool for Odoo XML-RPC operations that packages all MCP server functionality into terminal commands. The tool extracts and bundles the XML-RPC client code to be fully independent, supporting 8 core commands with JSON output mode for AI assistant parsing and an enhanced interactive shell with command history and examples.

## Technical Context
**Language/Version**: Python 3.10+
**Primary Dependencies**: Click 8.1.0+, Rich 13.0.0+, python-dotenv 1.0.0+
**Storage**: Configuration via .env files, command history in ~/.odoo_cli_history
**Testing**: pytest with contract tests for XML-RPC operations
**Target Platform**: macOS, Linux, Windows (terminal/CLI)
**Project Type**: single (standalone CLI tool)
**Performance Goals**: Commands respond within 2-5 seconds (network dependent)
**Constraints**: <500 records without warning, pure JSON mode for LLM parsing
**Scale/Scope**: 8 commands, ~1000 LOC, standalone pip package

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Multi-Company Awareness
- ✅ **PASS**: Tool respects company_id in all operations via XML-RPC
- Configuration includes multi-company Odoo instances
- No direct database access, all through XML-RPC API

### II. Queue Job Architecture
- ✅ **PASS**: Not applicable - CLI tool doesn't implement async operations
- Tool can trigger queue jobs via `execute` command but doesn't manage them

### III. Security-First Development
- ✅ **PASS with notes**:
  - Credentials stored in .env with documented security warnings
  - No direct database access, all through authenticated XML-RPC
  - README must include chmod 600 recommendation for .env files

### IV. Performance Optimization
- ✅ **PASS**:
  - 500+ record warning threshold implemented
  - JSON streaming for large datasets
  - No unnecessary reconnections (client reuse)

### V. Production Error Monitoring
- ⚠️ **N/A**: CLI tool itself doesn't need Sentry
- Errors output to stderr in structured JSON format for external monitoring

**Gate Status**: ✅ PASS - No constitutional violations

## Project Structure

### Documentation (this feature)
```
specs/001-cli-implementation/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
odoo-xml-cli/
├── pyproject.toml      # Package configuration
├── setup.py            # Setup script (if needed)
├── README.md           # User documentation
├── LICENSE             # MIT License
├── CLAUDE.md           # AI assistant context
├── .gitignore          # Git ignore rules
├── odoo_cli/           # Main package
│   ├── __init__.py     # Package initialization
│   ├── cli.py          # Click CLI entry point
│   ├── client.py       # Bundled Odoo XML-RPC client
│   ├── utils.py        # Output formatting utilities
│   └── shell.py        # Interactive shell implementation
└── tests/
    ├── contract/       # API contract tests
    ├── integration/    # End-to-end command tests
    └── unit/          # Unit tests for utilities
```

**Structure Decision**: Single project structure - standalone CLI tool with bundled dependencies for maximum portability and LLM-friendly operation.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context**:
   - XML-RPC client extraction strategy from MCP server
   - Shell auto-completion implementation for Click
   - Command history persistence across sessions
   - JSON streaming for large datasets

2. **Generate and dispatch research tasks**:
   - Research: Best practices for bundling external code (MCP client extraction)
   - Research: Click framework patterns for LLM-optimized CLIs
   - Research: Rich library integration with JSON output modes
   - Research: Shell enhancement techniques (readline, history, autocomplete)

3. **Consolidate findings** in `research.md`

**Output**: research.md with implementation strategies resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - OdooConfig (url, database, username, password)
   - CommandResult (data, error, exit_code)
   - ShellSession (client, history, context)

2. **Generate API contracts** from functional requirements:
   - CLI command signatures for all 8 commands
   - JSON output schemas for each command
   - Error response formats

3. **Generate contract tests** from contracts:
   - Test each command with mock XML-RPC responses
   - Validate JSON output structure
   - Test error handling and exit codes

4. **Extract test scenarios** from user stories:
   - Developer searches for employees
   - Admin upgrades a module
   - LLM parses JSON output

5. **Update CLAUDE.md** for AI assistant context

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Extract XML-RPC client code from MCP server [P]
- Create project structure and pyproject.toml [P]
- Implement each CLI command (8 tasks)
- Add JSON output mode with --json flag
- Implement enhanced shell with examples
- Add configuration loading from .env
- Create comprehensive README with security warnings
- Write contract tests for all commands

**Ordering Strategy**:
- Infrastructure first (project setup, client extraction)
- Core functionality (commands)
- Enhancements (shell, JSON mode)
- Documentation and tests

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md)
**Phase 5**: Validation (test all commands, verify LLM compatibility)

## Complexity Tracking
*No violations - section not needed*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (via /clarify session)
- [x] Complexity deviations documented (none)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*