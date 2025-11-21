# CLAUDE.md

## Project Status

**This is a PUBLIC open-source project**
- Repository: https://github.com/RHHOLDING/odoo-cli
- Visibility: PUBLIC
- License: MIT License
- Maintainer: Andre Kremer ([@actec-andre](https://github.com/actec-andre))

**IMPORTANT: Public Repository Guidelines**
- ❌ Never commit real credentials, API keys, or passwords
- ❌ Never include real customer/company data in examples
- ❌ Never reference internal systems or private infrastructure
- ✅ Use example/demo data from Odoo's standard demo database
- ✅ Use generic company names (e.g., "Azure Interior", "Deco Addict")
- ✅ Mask sensitive URLs and database names in documentation

## Language Policy

**All development in this repository must be in English:**
- Code, comments, and docstrings
- Documentation (README, SPEC, etc.)
- Commit messages and PR descriptions
- Variable and function names

## Project Overview

This is a standalone CLI tool (`odoo-cli`) that provides an LLM-friendly Odoo JSON-RPC interface.

**Key References:**
- `README.md` - User-facing documentation
- `.specify/` - BMAD-style feature specifications
- `CODEX.md` - OpenAI/Codex/ChatGPT assistant guide (keep aligned with this file)
- Parent context: Originally developed as part of ODOO-MAIN workspace

**Technology Stack:**
- Python 3.10+
- Click (CLI framework)
- Rich (terminal output)
- Pure JSON-RPC implementation (no Odoo dependencies)

## Design Principle: LLM-Friendly First

**IMPORTANT:** This tool is designed to be **LLM-friendly**, not user-friendly. This is a critical distinction:

**LLM-Friendly means:**
- ✅ Structured, parsable outputs (JSON-first)
- ✅ Predictable command structures
- ✅ Machine-readable error messages with error_type fields
- ✅ Consistent exit codes (0=success, 1=connection, 2=auth, 3=operation)
- ✅ Comprehensive `--llm-help` output with decision trees
- ✅ Field validation with actionable suggestions
- ✅ Automatic type inference (minimal typing required)

**NOT user-friendly in traditional sense:**
- ❌ No interactive prompts or wizards
- ❌ No TUI/GUI components
- ❌ Minimal pretty-printing (use Rich for console output, but JSON is primary)

**Why LLM-friendly?**
This tool is primarily used by AI assistants (Claude, GPT) to interact with Odoo on behalf of users. LLMs need:
- Clear, structured data they can parse
- Predictable error patterns they can handle
- Decision trees to choose the right command
- Validation feedback they can act on

**Example: Error handling**
```json
{
  "success": false,
  "error": "Field 'nam' does not exist on model 'res.partner'",
  "error_type": "field_validation",
  "suggestion": "Did you mean: name, email? Run: odoo get-fields res.partner"
}
```

This structure allows LLMs to:
1. Parse the error programmatically
2. Understand the error category (field_validation)
3. Take corrective action (suggest alternatives, run get-fields)

## Security & Privacy

**Public Repository Security:**
- `.env` files are gitignored and NEVER committed
- All credentials use environment variables or config files
- Example data uses Odoo demo database references only
- No real customer data in documentation or tests

**Credential Management:**
- Environment variables: `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`
- Config file: `~/.odoo-cli.yaml` (user's home directory, not in repo)
- Never hardcode credentials in code or tests

## Current Version

**v1.4.0 - Quick Wins Bundle**
- ✅ Core CLI + JSON-RPC client
- ✅ CRUD commands (create, read, update, delete + bulk)
- ✅ Field parser & aggregation
- ✅ Context management (multi-company, translations, archived)
- ✅ Quick wins: search-count, name-get, name-search, fields_get optimization

**Next: v1.5.0 - Environment Profiles**
- Specification ready in `.specify/features/001_environment_profiles/`
- Easy switching between prod/staging/dev environments
- Per-profile configurations

## Development Workflow

### BMAD Specify Workflow
```bash
# Create new feature spec
/specify:specify "Feature description"

# Generate implementation plan
/specify:plan

# Generate task breakdown
/specify:tasks

# Implement feature
/specify:implement
```

### Feature Structure
```
.specify/
├── features/
│   └── 001_environment_profiles/
│       ├── spec.md      # Feature specification
│       ├── plan.md      # Implementation plan (generated)
│       └── tasks.md     # Task breakdown (generated)
└── archive/             # Completed/archived specs
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=odoo_cli

# Run specific test
pytest tests/unit/test_client.py
```

**Test Guidelines:**
- Use mock data, never real production data
- Mock Odoo responses in unit tests
- Integration tests use demo database only
- No credentials in test files

## Documentation

**User-Facing:**
- `README.md` - Main documentation (keep examples generic!)
- `CHANGELOG.md` - Version history
- `docs/` - Detailed guides and examples

**Developer:**
- `CLAUDE.md` - This file (project guidelines)
- `.specify/` - Feature specifications
- Code comments in English

**Example Data Guidelines:**
When writing examples, use Odoo's standard demo data:
- Companies: "Azure Interior", "Deco Addict", "Gemini Furniture"
- Products: "Office Chair", "Conference Table", "Desk Lamp"
- Partners: Generic names like "John Doe", "Jane Smith"
- URLs: Generic like "https://your-instance.odoo.com"

## Common Tasks

### Add New Command
1. Create file in `odoo_cli/commands/your_command.py`
2. Use `@click.command()` decorator
3. Add `@click.pass_obj` for context
4. Handle JSON mode: `json_mode = json_mode or ctx.json_mode`
5. Use `output_json()` and `output_error()` from utils
6. Register in `odoo_cli/cli.py`
7. Update `--llm-help` in `odoo_cli/help.py`
8. Add tests in `tests/unit/test_commands_your_command.py`
9. Document in README.md

### Update LLM Help
File: `odoo_cli/help.py`
- Add new commands to `commands` array
- Add decision tree entries for new use cases
- Update version number
- Keep JSON structure LLM-parsable

### Release New Version
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Update `--llm-help` version
4. Create git tag: `git tag v1.x.x`
5. Push: `git push origin v1.x.x`
6. GitHub will auto-create release

## Code Style

- **Format:** Black (line length 120)
- **Imports:** isort
- **Docstrings:** Google style
- **Type hints:** Use where beneficial
- **Comments:** Explain "why", not "what"

## Git Workflow

**Branches:**
- `main` - Stable, production-ready
- `dev` - Development branch (if needed)
- `feature/XXX-name` - Feature branches

**Commit Messages:**
```
feat: Add environment profile switching
fix: Handle missing credentials gracefully
docs: Update README with new examples
test: Add unit tests for profile manager
```

**Before Committing:**
- Run tests: `pytest`
- Check no secrets: `git diff | grep -i "password\|secret\|key"`
- Format code: `black odoo_cli tests`
- Update docs if needed

## License

This project is licensed under the **MIT License** - see the LICENSE file for details.

**Why MIT?**
- Maximum adoption - anyone can use it (including commercial use)
- Business-friendly - no copyleft requirements
- Standard for CLI tools - simple and permissive
- Encourages wider integration with LLM toolchains

## Contributing

This is an open-source project. External contributors welcome!

**Contribution Guidelines:**
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

**Review Process:**
- Maintainer: Andre Kremer ([@actec-andre](https://github.com/actec-andre))
- CODEOWNERS file enforces review requirements
- All PRs require passing tests

## Support

- **Issues:** https://github.com/RHHOLDING/odoo-cli/issues
- **Discussions:** GitHub Discussions (if enabled)
- **Documentation:** README.md and docs/ folder

---

**Remember:** This is a PUBLIC repository. Always think twice before committing!
