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

### JSON Output Modes

**Two ways to get JSON output:**

```bash
# 1. Command-level flag
odoo-cli exec -c "result = client.search_read('res.partner', [], limit=5)" --json

# 2. Environment variable (RECOMMENDED for automation)
export ODOO_CLI_JSON=1
odoo-cli exec -c "result = client.search_read('res.partner', [], limit=5)"
```

**For LLM automation:**
- Set `ODOO_CLI_JSON=1` in your environment once
- All commands return structured JSON automatically
- Perfect for scripting and automation workflows

**Example: Python automation**
```python
import os
import subprocess
import json

os.environ['ODOO_CLI_JSON'] = '1'

result = subprocess.run([
    'odoo-cli', 'exec', '-c',
    "result = client.search_read('res.partner', [], limit=5)"
], capture_output=True, text=True)
data = json.loads(result.stdout)
```

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

**v2.0.0 - exec-only Architecture**

All Odoo operations now go through the `exec` command. This is a major breaking change.

**Commands in v2.0:**
```
exec            Execute Python code (PRIMARY - all Odoo operations)
config          Manage connection profiles (alias: profiles)
context         Project business context
agent-info      Complete API reference for LLM agents
```

**Why exec-only?**
- LLM agents write Python - they don't need specialized CLI commands
- One interface to learn - `exec` with the `client` object handles everything
- More flexible - complex operations, loops, conditionals all work naturally
- Easier maintenance - 4 commands instead of 20+

**Removed commands (with migration guidance):**
`search`, `read`, `create`, `update`, `delete`, `create-bulk`, `update-bulk`, `aggregate`, `search-count`, `name-get`, `name-search`, `get-models`, `get-fields`, `execute`, `search-employee`, `search-holidays`, `shell`

When deprecated commands are used, the CLI returns helpful JSON with migration instructions.

## Context File Configuration (v1.5.1+)

**v1.5.1 adds flexible context file path resolution:**

Context files (`.odoo-context.json`) can be located anywhere. Resolution order (highest priority first):

1. **Command-line flag** (explicit path):
   ```bash
   odoo-cli context show --context-file /path/to/.odoo-context.json
   odoo-cli context guide --task create-sales-order --context-file /path/to/.odoo-context.json
   ```

2. **`ODOO_CONTEXT_FILE` environment variable** (recommended for automation):
   ```bash
   export ODOO_CONTEXT_FILE=/path/to/.odoo-context.json
   odoo-cli context show  # Uses env var
   odoo-cli context validate --strict  # Uses env var
   ```

3. **Parent directory search** (like Git's `.git/` lookup):
   - Searches current directory and up to 5 parent directories
   - No configuration needed; just works from subdirectories

4. **Default location**:
   - `./.odoo-context.json` in current working directory

**For LLM agents:**
- Use `ODOO_CONTEXT_FILE` environment variable for reliable discovery
- Set once, works across all context commands
- Perfect for multi-directory projects

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

### v2.0 Architecture Note
In v2.0, all Odoo operations go through `exec`. New functionality is added via:
- Client methods in `odoo_cli/client.py`
- Patterns documented in `agent-info` and `--llm-help`

**No new CLI commands should be added** - the exec-only architecture is intentional.

### Update LLM Help
File: `odoo_cli/help.py`
- Add new patterns to the `patterns` section
- Update client API reference
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
