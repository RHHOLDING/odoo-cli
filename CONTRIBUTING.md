# Contributing to odoo-cli

Thank you for your interest in contributing to odoo-cli! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of Odoo and JSON-RPC

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/odoo-cli.git
   cd odoo-cli
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Odoo test instance credentials
   ```

5. **Run Tests**
   ```bash
   pytest
   pytest --cov=odoo_cli  # With coverage
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or fixes

### 2. Make Your Changes

Follow our coding standards (see below).

### 3. Write Tests

- Add unit tests for new functionality
- Ensure all tests pass: `pytest`
- Aim for high coverage: `pytest --cov=odoo_cli`

### 4. Update Documentation

- Update README.md if adding new commands
- Update CHANGELOG.md with your changes
- Add docstrings to new functions/classes
- Update `odoo_cli/help.py` if modifying CLI behavior

### 5. Commit Your Changes

Follow conventional commit format:

```bash
git commit -m "feat: Add environment profile switching"
git commit -m "fix: Handle missing credentials gracefully"
git commit -m "docs: Update README with new examples"
git commit -m "test: Add unit tests for profile manager"
```

**Commit types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Reference to related issues (if any)
- Screenshots/examples (if applicable)

## Coding Standards

### Python Style

- **Formatter**: Black (line length 120)
  ```bash
  black odoo_cli tests
  ```

- **Import sorting**: isort
  ```bash
  isort odoo_cli tests
  ```

- **Linting**: flake8 (optional but recommended)
  ```bash
  flake8 odoo_cli tests
  ```

### Code Conventions

- **Docstrings**: Google style
  ```python
  def my_function(param1: str, param2: int) -> bool:
      """Short description.

      Longer description if needed.

      Args:
          param1: Description of param1
          param2: Description of param2

      Returns:
          Description of return value

      Raises:
          ValueError: When invalid input
      """
      pass
  ```

- **Type Hints**: Use where beneficial
  ```python
  def process_data(data: dict[str, Any]) -> list[str]:
      ...
  ```

- **Comments**: Explain "why", not "what"
  ```python
  # Good: Retry on transient network errors (Odoo.sh rate limiting)
  # Bad: This retries the connection
  ```

### LLM-Friendly Design Principles

This tool is designed for LLM consumption:

1. **Structured Output**
   - JSON-first with `--json` flag
   - Predictable error structures with `error_type`
   - Consistent exit codes (0=success, 1=connection, 2=auth, 3=operation)

2. **No Interactive Prompts**
   - Avoid TUIs or interactive wizards
   - Use flags like `--force` instead of confirmations in JSON mode

3. **Actionable Error Messages**
   ```python
   # Good
   {"error": "Field 'nam' not found", "error_type": "field_validation",
    "suggestion": "Did you mean: name? Run: odoo get-fields res.partner"}

   # Bad
   {"error": "KeyError: 'nam'"}
   ```

4. **Comprehensive Help**
   - Update `odoo_cli/help.py` with decision trees
   - Keep `--llm-help` output deterministic

## Adding New Commands

### Step-by-Step Guide

1. **Create Command File**
   ```bash
   # odoo_cli/commands/your_command.py
   import click
   from odoo_cli.utils.output import output_json, output_error

   @click.command()
   @click.argument('model')
   @click.option('--json', 'json_mode', is_flag=True)
   @click.pass_obj
   def your_command(ctx, model, json_mode):
       """Your command description."""
       json_mode = json_mode or ctx.json_mode

       try:
           # Implementation
           result = ctx.client.your_method(model)
           output_json({"success": True, "data": result}, json_mode)
       except Exception as e:
           output_error(str(e), json_mode, error_type="operation")
   ```

2. **Register Command**
   ```python
   # odoo_cli/cli.py
   from odoo_cli.commands.your_command import your_command

   cli.add_command(your_command)
   ```

3. **Update LLM Help**
   ```python
   # odoo_cli/help.py
   {
       "command": "your-command",
       "description": "...",
       "usage": "odoo your-command MODEL [OPTIONS]",
       "when_to_use": "..."
   }
   ```

4. **Add Tests**
   ```python
   # tests/unit/test_commands_your_command.py
   def test_your_command_success(mock_client):
       # Test implementation
       pass
   ```

5. **Document**
   - Add to README.md command table
   - Add usage examples
   - Update CHANGELOG.md

## Testing Guidelines

### Unit Tests

- Mock Odoo responses using `unittest.mock`
- Test both success and error cases
- Test JSON and non-JSON output modes
- Use fixtures from `tests/conftest.py`

```python
from unittest.mock import Mock, patch

def test_create_command(mock_client):
    mock_client.create.return_value = 123
    # Test logic
```

### Test Data

- Use demo data (Azure Interior, Deco Addict, Gemini Furniture)
- Never use real customer data
- Mock credentials (use "password" for test passwords)

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/unit/test_client.py

# With coverage
pytest --cov=odoo_cli

# Verbose
pytest -v
```

## Security Guidelines

**Before committing:**

1. **Check for Secrets**
   ```bash
   git diff | grep -i "password\|secret\|key\|token"
   ```

2. **Verify .env is Ignored**
   ```bash
   git status  # .env should not appear
   ```

3. **Use Placeholder Data**
   - No real URLs: `https://your-instance.odoo.com`
   - No real databases: `your-database-name`
   - No real credentials: `your-username`

4. **Review Changes**
   ```bash
   git diff  # Review before commit
   ```

## Pull Request Process

1. **Ensure CI Passes**
   - All tests pass
   - Code coverage maintained
   - No linting errors

2. **Update Documentation**
   - README.md (if adding features)
   - CHANGELOG.md (always)
   - Docstrings (for new code)

3. **Request Review**
   - Tag maintainer: @actec-andre
   - Respond to feedback promptly
   - Make requested changes

4. **Squash Commits** (if requested)
   ```bash
   git rebase -i HEAD~N  # N = number of commits
   ```

## Release Process

**For Maintainers:**

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Update `--llm-help` version in `odoo_cli/help.py`
4. Create git tag: `git tag v1.x.x`
5. Push: `git push origin v1.x.x`
6. GitHub Actions creates release automatically

## Questions or Need Help?

- **Issues**: [GitHub Issues](https://github.com/RHHOLDING/odoo-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RHHOLDING/odoo-cli/discussions)
- **Security**: See [SECURITY.md](SECURITY.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to odoo-cli! 🎉
