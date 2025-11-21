# Project Constitution: odoo-cli

**Version:** 1.0
**Last Updated:** 2025-01-21

---

## Core Principles

### 1. LLM-First Design
- Machine-readable output is primary (JSON by default)
- Structured errors with actionable suggestions
- Predictable exit codes (0=success, 1=connection, 2=auth, 3=operation)
- Comprehensive `--llm-help` for AI agents

### 2. Zero Dependencies Philosophy
- Standalone Python 3.10+ tool
- No Odoo server dependencies
- Minimal external packages
- Self-contained functionality

### 3. Public Repository Safety
- **NEVER** commit credentials or customer data
- Use placeholder data in examples (Azure Interior, Deco Addict, Gemini Furniture)
- `.env` files gitignored
- Security warnings in all documentation

### 4. Code Quality Standards
- **Black** formatter (line length 120)
- **isort** for imports
- Google-style docstrings
- Type hints where useful
- Comment for "why", not "what"

### 5. Testing Requirements
- Unit tests with mocked Odoo responses
- Integration tests against demo instances
- No real customer data in tests
- `pytest` with coverage reporting

---

## Development Workflow

### Feature Development
1. Create feature branch from `main`
2. Write specification in `.specify/features/{ID}_{name}/spec.md`
3. Run clarifications (`/specify:clarify`) to resolve ambiguities
4. Generate implementation plan (`/specify:plan`)
5. Implement with tests
6. Update documentation
7. PR to `main` with conventional commits

### Commit Message Format
```
type: summary

Examples:
feat: Add environment profile switching
fix: Handle SSL errors in connection
docs: Update LLM documentation for v1.4.1
test: Add unit tests for context discovery
```

### Branch Naming
```
feature/{ID}-{short-description}
fix/{issue-id}-{short-description}
```

---

## Architecture Constraints

### CLI Framework
- **Click** for command-line interface
- **Rich** for human-readable output (optional)
- JSON output always available via `--json` or `ODOO_CLI_JSON=1`

### Odoo Integration
- JSON-RPC via `odoo_cli/client.py`
- No direct XML-RPC dependencies
- Connection config via environment variables or `~/.odoo-cli.yaml`

### File Structure
```
odoo-cli/
├── odoo_cli/
│   ├── commands/       # CLI command implementations
│   ├── client.py       # Odoo JSON-RPC client
│   ├── help.py         # LLM help system
│   └── cli.py          # Main CLI entry point
├── tests/
│   ├── unit/           # Unit tests with mocks
│   └── integration/    # Integration tests
├── .specify/           # Feature specifications
└── docs/               # User documentation
```

---

## Documentation Requirements

### User-Facing Docs
- `README.md` - Main user documentation
- `CHANGELOG.md` - Version history with migration notes
- `docs/` - Deeper guides and tutorials

### LLM-Facing Docs
- `CLAUDE.md` - Canonical development guidelines
- `CODEX.md` - OpenAI/Codex specific guide
- `GEMINI.md` - Google Gemini guide
- Keep all three in sync

### In-Code Documentation
- Docstrings for all public functions/classes
- Inline comments for non-obvious logic
- Type hints for function signatures
- `--llm-help` for command decision trees

---

## Security & Privacy

### Credentials Management
- Environment variables (`ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`)
- Config file (`~/.odoo-cli.yaml`) - gitignored
- `.env` files - gitignored
- **NEVER** hardcode credentials

### Data Safety
- Use demo data in tests and examples
- No real customer names, emails, or business data
- Sanitize output in error messages
- Clear warnings about production use

### Context Files
- `.odoo-context.json` - gitignored (contains project-specific data)
- `.odoo-context.json.example` - safe template (committed)
- CLI warns if context file not gitignored

---

## Performance Targets

### CLI Responsiveness
- Command startup: <500ms
- Simple operations (read single record): <2s
- Batch operations: Progress indicators for >5s
- Context loading: <100ms

### API Efficiency
- Batch API calls where possible
- Minimize round-trips
- Use `fields` parameter to limit data transfer
- Cache metadata when appropriate

---

## Error Handling

### Exit Codes
- `0` - Success
- `1` - Connection error
- `2` - Authentication error
- `3` - Operation error (user input, Odoo API error)

### Error Message Format (JSON)
```json
{
  "success": false,
  "error": "Description of what went wrong",
  "error_type": "connection|auth|operation",
  "suggestion": "Actionable next step"
}
```

### Error Message Format (Human)
- Clear description of problem
- Actionable suggestion (what to do next)
- Reference to `--help` or documentation if relevant

---

## Release Process

### Version Numbering
- Semantic versioning: `vMAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backwards compatible)
- Patch: Bug fixes

### Release Checklist
- [ ] Update `pyproject.toml` version
- [ ] Update `CHANGELOG.md` with changes
- [ ] Update `--llm-help` version reference
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Tag release: `vX.Y.Z`
- [ ] Publish to PyPI (when ready)

---

## Contributing Guidelines

### Pull Request Requirements
- Feature branch from `main`
- Tests for new functionality
- Documentation updates
- No breaking changes without discussion
- Code formatted (Black + isort)
- Conventional commit messages

### Code Review Criteria
- Follows code quality standards
- Adequate test coverage
- Documentation updated
- No credentials or customer data
- Performance acceptable
- Error handling appropriate

---

## Future Considerations

### Roadmap Priorities
1. ✅ Core CLI + CRUD operations (v1.0-1.4)
2. 🚧 Project Context Layer (v1.5)
3. 📋 Environment Profiles (v1.6)
4. 📋 Context-aware autocomplete (v2.0)
5. 📋 Interactive shell enhancements (v2.x)

### Deprecation Policy
- Announce deprecations one minor version ahead
- Maintain backwards compatibility for one major version
- Clear migration guides in CHANGELOG.md

---

**This constitution guides all development decisions. When in doubt, prioritize LLM usability, security, and code quality.**
