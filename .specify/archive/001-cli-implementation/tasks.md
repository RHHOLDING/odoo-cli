# Tasks: Odoo XML-RPC CLI Tool

**Input**: Design documents from `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/specs/001-cli-implementation/`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓), quickstart.md (✓)

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Project root**: `/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli/`
- **Source**: `odoo_cli/` (Python package)
- **Tests**: `tests/` (pytest structure)

## Phase 3.1: Setup & Infrastructure
- [ ] T001 Create project structure: odoo_cli/, tests/, setup directories
- [ ] T002 Create pyproject.toml with Click 8.1.0+, Rich 13.0.0+, python-dotenv dependencies
- [ ] T003 [P] Extract and adapt XML-RPC client from /MCP/odoo/src/odoo_mcp/odoo_client.py to odoo_cli/client.py
- [ ] T004 [P] Create setup.py for editable install support if needed
- [ ] T005 [P] Create README.md with installation instructions and security warnings

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (from contracts/cli-commands.yaml)
- [ ] T006 [P] Contract test for 'execute' command in tests/contract/test_execute_command.py
- [ ] T007 [P] Contract test for 'search-employee' command in tests/contract/test_search_employee_command.py
- [ ] T008 [P] Contract test for 'search-holidays' command in tests/contract/test_search_holidays_command.py
- [ ] T009 [P] Contract test for 'get-models' command in tests/contract/test_get_models_command.py
- [ ] T010 [P] Contract test for 'get-fields' command in tests/contract/test_get_fields_command.py
- [ ] T011 [P] Contract test for 'search' command in tests/contract/test_search_command.py
- [ ] T012 [P] Contract test for 'read' command in tests/contract/test_read_command.py
- [ ] T013 [P] Contract test for 'shell' command in tests/contract/test_shell_command.py

### JSON Schema Tests (from contracts/json-schemas.json)
- [ ] T014 [P] JSON output schema test for success responses in tests/contract/test_json_success_schema.py
- [ ] T015 [P] JSON output schema test for error responses in tests/contract/test_json_error_schema.py

### Integration Tests (from quickstart.md scenarios)
- [ ] T016 [P] Integration test: Developer searches for employees in tests/integration/test_employee_search_flow.py
- [ ] T017 [P] Integration test: Admin upgrades a module in tests/integration/test_module_upgrade_flow.py
- [ ] T018 [P] Integration test: LLM parses JSON output in tests/integration/test_llm_json_parsing.py
- [ ] T019 [P] Integration test: Large dataset warning (500+ records) in tests/integration/test_large_dataset_handling.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models (from data-model.md)
- [ ] T020 [P] Implement OdooConfig dataclass in odoo_cli/models/config.py
- [ ] T021 [P] Implement CommandResult dataclass in odoo_cli/models/result.py
- [ ] T022 [P] Implement ShellSession class in odoo_cli/models/session.py
- [ ] T023 [P] Implement CliContext class in odoo_cli/models/context.py

### Utility Functions
- [ ] T024 [P] Create output formatting utilities (Rich tables, JSON mode) in odoo_cli/utils.py
- [ ] T025 [P] Create configuration loading logic (.env, environment vars) in odoo_cli/config.py
- [ ] T026 [P] Create error handling and exit code mapping in odoo_cli/errors.py

### CLI Commands Implementation
- [ ] T027 Create main CLI entry point with Click in odoo_cli/cli.py
- [ ] T028 Implement 'execute' command in odoo_cli/commands/execute.py
- [ ] T029 Implement 'search-employee' command in odoo_cli/commands/search_employee.py
- [ ] T030 Implement 'search-holidays' command in odoo_cli/commands/search_holidays.py
- [ ] T031 Implement 'get-models' command in odoo_cli/commands/get_models.py
- [ ] T032 Implement 'get-fields' command in odoo_cli/commands/get_fields.py
- [ ] T033 Implement 'search' command in odoo_cli/commands/search.py
- [ ] T034 Implement 'read' command in odoo_cli/commands/read.py
- [ ] T035 Implement 'shell' command with enhanced features in odoo_cli/commands/shell.py

### Client Integration
- [ ] T036 Adapt bundled XML-RPC client for standalone configuration in odoo_cli/client.py
- [ ] T037 Add connection pooling and retry logic to client in odoo_cli/client.py
- [ ] T038 Implement large dataset pagination in odoo_cli/client.py

## Phase 3.4: JSON Mode & LLM Optimization
- [ ] T039 Add --json flag support to all commands (modify odoo_cli/cli.py)
- [ ] T040 Implement stdout/stderr separation for JSON mode in odoo_cli/utils.py
- [ ] T041 Add structured error JSON output in odoo_cli/errors.py
- [ ] T042 Implement 500+ record warning with confirmation in odoo_cli/client.py

## Phase 3.5: Shell Enhancements
- [ ] T043 Add readline history support (~/.odoo_cli_history) in odoo_cli/commands/shell.py
- [ ] T044 Create startup banner with examples in odoo_cli/commands/shell.py
- [ ] T045 Pre-import utilities (json, pprint, datetime) in shell namespace
- [ ] T046 Add tab completion for client methods in odoo_cli/commands/shell.py

## Phase 3.6: Polish & Documentation
- [ ] T047 [P] Add unit tests for config validation in tests/unit/test_config.py
- [ ] T048 [P] Add unit tests for utils and formatting in tests/unit/test_utils.py
- [ ] T049 [P] Add unit tests for error handling in tests/unit/test_errors.py
- [ ] T050 [P] Create comprehensive docstrings for all commands
- [ ] T051 [P] Add type hints throughout the codebase
- [ ] T052 Update README.md with full command reference and examples
- [ ] T053 Add security documentation for .env files (chmod 600)
- [ ] T054 Create CHANGELOG.md for version tracking
- [ ] T055 Run quickstart.md scenarios for validation

## Dependencies
- Setup (T001-T005) must complete first
- All tests (T006-T019) before implementation (T020-T046)
- Data models (T020-T023) before commands (T027-T035)
- Client adaptation (T036-T038) before command implementation
- Core implementation before JSON mode (T039-T042)
- Core implementation before shell enhancements (T043-T046)
- Everything before polish (T047-T055)

## Parallel Execution Examples

### Launch all contract tests together (T006-T013):
```bash
# Run in parallel - different test files
Task: "Contract test for 'execute' command in tests/contract/test_execute_command.py"
Task: "Contract test for 'search-employee' command in tests/contract/test_search_employee_command.py"
Task: "Contract test for 'search-holidays' command in tests/contract/test_search_holidays_command.py"
Task: "Contract test for 'get-models' command in tests/contract/test_get_models_command.py"
Task: "Contract test for 'get-fields' command in tests/contract/test_get_fields_command.py"
Task: "Contract test for 'search' command in tests/contract/test_search_command.py"
Task: "Contract test for 'read' command in tests/contract/test_read_command.py"
Task: "Contract test for 'shell' command in tests/contract/test_shell_command.py"
```

### Launch all data models together (T020-T023):
```bash
# Run in parallel - different model files
Task: "Implement OdooConfig dataclass in odoo_cli/models/config.py"
Task: "Implement CommandResult dataclass in odoo_cli/models/result.py"
Task: "Implement ShellSession class in odoo_cli/models/session.py"
Task: "Implement CliContext class in odoo_cli/models/context.py"
```

### Launch utility implementations together (T024-T026):
```bash
# Run in parallel - different utility files
Task: "Create output formatting utilities (Rich tables, JSON mode) in odoo_cli/utils.py"
Task: "Create configuration loading logic (.env, environment vars) in odoo_cli/config.py"
Task: "Create error handling and exit code mapping in odoo_cli/errors.py"
```

## Notes
- XML-RPC client extraction (T003) is critical - all commands depend on it
- Contract tests must be written to fail initially (TDD approach)
- Commands T028-T035 may need sequential implementation due to shared cli.py imports
- JSON mode (T039-T042) modifies existing command files - cannot run in parallel with command implementation
- Shell enhancements (T043-T046) all modify same file - must be sequential
- Validate against quickstart.md scenarios (T055) as final check

## Validation Checklist
- ✅ All 8 CLI commands from contracts have tests and implementation tasks
- ✅ All 4 entities from data-model.md have creation tasks
- ✅ All tests (T006-T019) come before implementation (T020+)
- ✅ Parallel tasks ([P]) work on different files
- ✅ Each task specifies exact file path
- ✅ No [P] task modifies same file as another [P] task
- ✅ JSON schemas from contracts have test coverage
- ✅ Quickstart scenarios have integration tests

**Total Tasks**: 55
**Parallel Groups**: 7 groups with 35 parallel tasks
**Critical Path**: Setup → Tests → Client → Models → Commands → JSON/Shell → Polish