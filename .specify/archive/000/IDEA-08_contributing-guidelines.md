# Idea: Contributing Guidelines & Open Source Governance

## Problem
No clear guidelines for external contributors:
- How to submit features or bug fixes?
- What coding standards to follow?
- What's the review process?
- How to ensure quality?
- Who decides what gets merged?

**Result:** Inconsistent contributions, rejected PRs, frustrated contributors.

## Goal
Establish clear, welcoming **Contributing Guidelines** that enable external developers to contribute effectively while maintaining code quality and project vision.

Think of it as: **"The rulebook for collaborative development"**

---

## Core Philosophy

### Open Source Principles
1. **Welcoming:** Encourage contributions from everyone
2. **Transparent:** Clear processes, public discussions
3. **Respectful:** Code of Conduct for all interactions
4. **Quality-Focused:** High standards, but helpful reviews
5. **LLM-Friendly First:** Maintain design philosophy (Spec 007)

### Project Vision
**Primary Goal:** LLM-friendly CLI for Odoo via JSON-RPC
- NOT a user-friendly TUI/GUI tool
- NOT a replacement for Odoo web interface
- Focus: Structured, parsable output for AI assistants

**Key Constraint:** Maintain backward compatibility with existing LLM workflows

---

## 1. CONTRIBUTING.md File

**Location:** `/CONTRIBUTING.md` (repository root)

### Template Structure

```markdown
# Contributing to odoo-xml-cli

Thank you for your interest in contributing! This document explains how to contribute effectively.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Coding Standards](#coding-standards)
4. [Submitting Changes](#submitting-changes)
5. [Review Process](#review-process)
6. [Design Principles](#design-principles)

---

## Getting Started

### Before You Start
- Read the [README.md](README.md) to understand the project
- Check [existing issues](https://github.com/RHHOLDING/odoo-cli/issues) for similar work
- Review [PRIORITIES.md](specs/000/PRIORITIES.md) for planned features
- Join discussions in [GitHub Discussions](https://github.com/RHHOLDING/odoo-cli/discussions)

### Types of Contributions We Welcome
- ✅ Bug fixes
- ✅ New commands (aligned with LLM-friendly design)
- ✅ Performance improvements
- ✅ Documentation improvements
- ✅ Test coverage improvements
- ✅ Translation support
- ⚠️ Major architectural changes (requires discussion first!)

### NOT Accepting
- ❌ Interactive prompts/wizards (violates LLM-friendly principle)
- ❌ TUI/GUI components
- ❌ Features that break backward compatibility (without migration path)
- ❌ Dependencies on large libraries (keep CLI lightweight)

---

## Development Setup

### Prerequisites
- Python 3.10+
- Git
- Access to an Odoo instance (for testing)

### Setup Steps
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/odoo-xml-cli.git
cd odoo-xml-cli

# Add upstream remote
git remote add upstream https://github.com/RHHOLDING/odoo-cli.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests
pytest
```

### Environment Configuration
Create `.env` file:
```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
```

---

## Coding Standards

### Python Style
- **PEP 8** compliance (use `black` for formatting)
- **Type hints** for all function signatures
- **Docstrings** for all public functions (Google style)

**Example:**
```python
def search(
    self,
    model: str,
    domain: List = None,
    offset: int = 0,
    limit: Optional[int] = None,
    order: Optional[str] = None
) -> List[int]:
    """
    Search for record IDs matching a domain.

    Args:
        model: Model name (e.g., 'res.partner')
        domain: Search domain (default: [])
        offset: Number of records to skip
        limit: Maximum number of records
        order: Sort order (e.g., 'name ASC')

    Returns:
        List of matching record IDs

    Raises:
        ValueError: If model doesn't exist
        ConnectionError: If connection fails
    """
```

### Code Formatting
```bash
# Format code with black
black odoo_cli/

# Check with flake8
flake8 odoo_cli/ --max-line-length=100

# Sort imports with isort
isort odoo_cli/
```

### Naming Conventions
- **Functions/Methods:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private methods:** `_leading_underscore`

### Error Handling
```python
# Good: Specific exceptions, clear messages
try:
    result = client.execute(model, method, *args)
except ValueError as e:
    console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
    sys.exit(3)

# Bad: Generic exception, vague message
try:
    result = client.execute(model, method, *args)
except Exception:
    print("Something went wrong")
    sys.exit(1)
```

### LLM-Friendly Output
**CRITICAL:** All commands MUST support `--json` flag with structured output.

```python
# Good: Structured JSON output
if json_mode:
    output = {
        "success": True,
        "record_id": record_id,
        "model": model,
        "fields": field_dict
    }
    console.print_json(output)
else:
    console.print(f"✓ Created record: {record_id}")

# Bad: Only human-readable output
print(f"Record {record_id} created successfully!")
```

---

## Submitting Changes

### Branch Strategy
- **main/v16:** Production-ready code
- **develop:** Integration branch (if used)
- **feature/xxx:** New features
- **fix/xxx:** Bug fixes
- **docs/xxx:** Documentation only

### Branch Naming
```bash
# Features
git checkout -b feature/search-count-command

# Bug fixes
git checkout -b fix/context-validation-error

# Documentation
git checkout -b docs/update-readme-installation
```

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Add/update tests
- `chore`: Build process, dependencies

**Examples:**
```bash
feat(commands): Add search-count command with JSON output

Implements Spec 005 quick win - search_count CLI wrapper.
- Already exists in client.py (line 349)
- Added --json flag for LLM output
- 5 tests added, 100% coverage

Closes #42

---

fix(context): Validate context file before loading

Fixes crash when .odoo-context.yaml has invalid YAML syntax.
- Added YAML schema validation
- Clear error messages with line numbers
- Suggests corrections for common mistakes

Fixes #38

---

docs(readme): Add installation verification steps

Added SHA256 checksum verification for all platforms.
- macOS/Linux: shasum -a 256
- Windows: Get-FileHash
- Homebrew/PyPI: automatic verification

Related to Spec 006
```

### Pull Request Process

#### 1. Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass (`pytest`)
- [ ] New tests added for new features
- [ ] Documentation updated (README, docstrings)
- [ ] No breaking changes (or migration path documented)
- [ ] Commit messages follow conventions

#### 2. Submit PR
```bash
# Update your fork
git fetch upstream
git rebase upstream/main

# Push to your fork
git push origin feature/your-feature

# Create PR on GitHub
# - Clear title (follows conventional commit format)
# - Description explains WHY (not just WHAT)
# - Reference related issues/specs
# - Add screenshots for UI changes (if any)
```

#### 3. PR Template
```markdown
## Description
Brief summary of changes and motivation.

## Related Issue/Spec
Closes #42
Implements Spec 005 (Section 2)

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] Tested on real Odoo instance

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally (`pytest`)
- [ ] Conventional commit messages used

## Screenshots (if applicable)
```

---

## Review Process

### Review Timeline
- **Small PRs (<100 lines):** 1-3 days
- **Medium PRs (100-500 lines):** 3-7 days
- **Large PRs (>500 lines):** 1-2 weeks (consider splitting!)

### What Reviewers Look For
1. **Correctness:** Does it work as intended?
2. **Design:** Follows LLM-friendly principles?
3. **Code Quality:** Readable, maintainable, tested?
4. **Documentation:** Clear docstrings, updated README?
5. **Backward Compatibility:** Doesn't break existing workflows?

### Feedback Categories
- **Required Changes:** Must be fixed before merge
- **Suggestions:** Nice to have, but not blocking
- **Questions:** Clarifications needed

### Responding to Reviews
```markdown
# Good Response
> Suggestion: Use list comprehension instead of loop

Good catch! Changed in commit abc123. Also added type hint.

# Bad Response
Done.
```

### Approval Process
- ✅ **1 approval required** for small changes
- ✅ **2 approvals required** for major features/breaking changes
- ✅ **Maintainer final approval** for merging

---

## Design Principles

### 1. LLM-Friendly First (CRITICAL!)
**Why:** This tool is primarily used BY AI assistants, not directly by humans.

**Means:**
- ✅ Structured JSON output (parsable)
- ✅ Predictable command structure
- ✅ Machine-readable errors with `error_type`
- ✅ Consistent exit codes (0=success, 1=connection, 2=auth, 3=operation)
- ❌ NO interactive prompts/wizards
- ❌ NO TUI/GUI components

**Example:**
```python
# Good: LLM can parse
{
  "success": false,
  "error": "Field 'nam' does not exist",
  "error_type": "field_validation",
  "suggestion": "Did you mean: name, email?"
}

# Bad: LLM cannot parse
Error: Field nam does not exist. Did you mean: name, email?
```

### 2. Backward Compatibility
**Breaking changes require:**
- Major version bump (1.x.x → 2.0.0)
- Migration guide
- Deprecation warnings for 1 minor version
- Discussion in GitHub Issues

### 3. Keep It Simple
- Avoid over-engineering
- One command = one responsibility
- Minimal dependencies (currently: click, rich, requests, dotenv)
- No frameworks unless absolutely necessary

### 4. Test Everything
- Unit tests for all functions
- Integration tests for commands
- Real Odoo testing encouraged (but not in CI)
- Target: 80%+ coverage

### 5. Document Well
- Docstrings for all public functions
- README updated for new commands
- help.py updated for LLM guidance
- CHANGELOG.md for all changes

---

## Testing Guidelines

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_commands_search.py

# With coverage
pytest --cov=odoo_cli --cov-report=html

# Verbose
pytest -v
```

### Writing Tests
```python
# tests/unit/test_commands_example.py
import pytest
from click.testing import CliRunner
from odoo_cli.commands.example import example_cmd

class TestExampleCommand:
    """Test suite for example command."""

    @pytest.fixture
    def runner(self):
        """Click CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_client(self, mocker):
        """Mock Odoo client."""
        return mocker.patch('odoo_cli.commands.example.get_odoo_client')

    def test_example_success(self, runner, mock_client):
        """Test successful execution."""
        mock_client.return_value.execute.return_value = [1, 2, 3]

        result = runner.invoke(example_cmd, ['res.partner', '[]'])

        assert result.exit_code == 0
        assert '3 records' in result.output

    def test_example_json_output(self, runner, mock_client):
        """Test JSON output mode."""
        mock_client.return_value.execute.return_value = [1, 2, 3]

        result = runner.invoke(example_cmd, ['res.partner', '[]', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['count'] == 3
        assert data['ids'] == [1, 2, 3]
```

### Test Coverage Requirements
- **New features:** 80%+ coverage required
- **Bug fixes:** Add regression test
- **Refactoring:** Maintain or improve coverage

---

## Documentation Standards

### README.md
- Keep installation instructions up-to-date
- Add new commands to usage section
- Include examples for complex features

### Docstrings (Google Style)
```python
def complex_function(arg1: str, arg2: int = 0) -> Dict[str, Any]:
    """
    Brief one-line description.

    Longer description if needed, explaining purpose, behavior,
    and any important details.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2 (default: 0)

    Returns:
        Dictionary with keys:
            - key1 (str): Description
            - key2 (int): Description

    Raises:
        ValueError: When arg1 is empty
        ConnectionError: When connection fails

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['key1'])
        'test'
    """
```

### help.py Updates
When adding commands, update `help.py`:
```python
# Add to commands list
{
    "name": "search-count",
    "description": "Count records matching a domain (no IDs transferred)",
    "usage": "odoo search-count <model> <domain>",
    "example": "odoo search-count res.partner '[[\"customer_rank\",\">\",0]]'",
    "flags": {
        "--json": "Output as JSON"
    }
}

# Add to decision_tree if needed
```

---

## Communication Channels

### GitHub Issues
**For:**
- Bug reports
- Feature requests
- Questions about implementation

**Template:**
```markdown
## Description
Clear description of issue/feature

## Steps to Reproduce (for bugs)
1. Run command: `odoo read res.partner 1`
2. See error: ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- odoo-xml-cli version: 1.2.0
- Python version: 3.10.5
- OS: macOS 14.1
- Odoo version: 16.0

## Additional Context
Screenshots, logs, etc.
```

### GitHub Discussions
**For:**
- General questions
- Design discussions
- Feature brainstorming
- Community help

### Pull Requests
**For:**
- Code changes
- Documentation updates
- Bug fixes

---

## Code of Conduct

### Our Pledge
We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity
- Gender identity and expression
- Level of experience, education
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive Behavior:**
- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints
- ✅ Gracefully accepting constructive criticism
- ✅ Focusing on what's best for the community
- ✅ Showing empathy towards others

**Unacceptable Behavior:**
- ❌ Harassment, trolling, insulting/derogatory comments
- ❌ Personal or political attacks
- ❌ Public or private harassment
- ❌ Publishing others' private information
- ❌ Other unethical or unprofessional conduct

### Enforcement
- Violations reported to: andre@ananda.gmbh
- Maintainers review and investigate all complaints
- Appropriate action taken (warning, temp ban, permanent ban)

---

## Release Process (Maintainers)

### Version Numbering (Semantic Versioning)
```
MAJOR.MINOR.PATCH
  |     |     |
  |     |     +-- Bug fixes (backward compatible)
  |     +-------- New features (backward compatible)
  +-------------- Breaking changes
```

**Examples:**
- `1.2.0 → 1.2.1` - Bug fix
- `1.2.1 → 1.3.0` - New feature (backward compatible)
- `1.3.0 → 2.0.0` - Breaking change

### Release Checklist
- [ ] All tests pass
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Version bumped in `odoo_cli/help.py`
- [ ] Documentation updated
- [ ] Tag created: `git tag v1.3.0`
- [ ] Pushed to GitHub: `git push --tags`
- [ ] GitHub Release created
- [ ] PyPI package published
- [ ] Homebrew Formula updated

---

## Quick Reference

### First-Time Contributors
1. Fork repository
2. Clone your fork
3. Create feature branch
4. Make changes
5. Run tests
6. Commit with conventional messages
7. Push to your fork
8. Create Pull Request

### Maintainers
1. Review PRs
2. Provide constructive feedback
3. Approve when ready
4. Merge with squash (keep clean history)
5. Update CHANGELOG.md
6. Create release when appropriate

---

## FAQ

**Q: How do I pick an issue to work on?**
A: Look for issues labeled `good first issue` or `help wanted`

**Q: Can I work on something not in issues?**
A: Yes, but open an issue first to discuss! Avoid wasting effort on rejected PRs.

**Q: How long until my PR is reviewed?**
A: Small PRs: 1-3 days. Large PRs: 1-2 weeks. Be patient!

**Q: My PR was rejected. Why?**
A: Common reasons:
- Doesn't align with LLM-friendly design
- Breaks backward compatibility
- Insufficient tests/documentation
- Too large/complex (split it up!)

**Q: Can I add a new dependency?**
A: Only if absolutely necessary. Discuss in issue first.

**Q: Do I need to sign a CLA?**
A: No, but contributions are licensed under MIT (same as project).

---

## License
By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to odoo-xml-cli! 🚀
```

---

## 2. Issue Templates

**Location:** `.github/ISSUE_TEMPLATE/`

### Bug Report Template
```yaml
name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to report a bug!

  - type: textarea
    id: description
    attributes:
      label: Description
      description: Clear description of the bug
      placeholder: What happened?
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: How can we reproduce this?
      placeholder: |
        1. Run command: `odoo read res.partner 1`
        2. See error: ...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What should happen?
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happens?
    validations:
      required: true

  - type: input
    id: version
    attributes:
      label: odoo-xml-cli Version
      placeholder: "1.2.0"
    validations:
      required: true

  - type: input
    id: python
    attributes:
      label: Python Version
      placeholder: "3.10.5"
    validations:
      required: true

  - type: input
    id: odoo
    attributes:
      label: Odoo Version
      placeholder: "16.0"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: Operating System
      options:
        - macOS
        - Linux (Ubuntu)
        - Linux (Debian)
        - Linux (Other)
        - Windows
        - Docker
    validations:
      required: true

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Logs, screenshots, etc.
```

### Feature Request Template
```yaml
name: Feature Request
description: Suggest a new feature
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for suggesting a feature!

  - type: textarea
    id: problem
    attributes:
      label: Problem Statement
      description: What problem does this solve?
      placeholder: I'm frustrated when...
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: How should this work?
      placeholder: I'd like to be able to...
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: What other solutions did you consider?

  - type: checkboxes
    id: design-principles
    attributes:
      label: Design Principles
      description: Does this align with project principles?
      options:
        - label: LLM-friendly (structured output, no interactive prompts)
        - label: Backward compatible (or has migration path)
        - label: Keeps CLI lightweight (minimal dependencies)
    validations:
      required: true

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Examples, mockups, etc.
```

---

## 3. Pull Request Template

**Location:** `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Description
<!-- Brief summary of changes and motivation -->

## Related Issue/Spec
<!-- Closes #42, Implements Spec 005 -->

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to break)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Test improvements

## Testing
- [ ] Unit tests added/updated
- [ ] All tests pass (`pytest`)
- [ ] Manual testing completed on real Odoo instance
- [ ] Tested on multiple platforms (if applicable)

## Design Principles Checklist
- [ ] LLM-friendly: Supports `--json` flag with structured output
- [ ] No interactive prompts/wizards
- [ ] Backward compatible (or migration path documented)
- [ ] Minimal dependencies (no new heavy libraries)
- [ ] Exit codes: 0=success, 1=connection, 2=auth, 3=operation

## Code Quality Checklist
- [ ] Code follows PEP 8 style guidelines
- [ ] Type hints added for all function signatures
- [ ] Docstrings added (Google style)
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No new warnings generated

## Documentation Checklist
- [ ] README.md updated (if adding new command)
- [ ] help.py updated for LLM guidance
- [ ] CHANGELOG.md updated
- [ ] Docstrings complete and accurate

## Commit Messages
- [ ] Follow Conventional Commits format
- [ ] Clear and descriptive

## Screenshots (if applicable)
<!-- Add screenshots for visual changes -->

## Additional Notes
<!-- Any other information for reviewers -->
```

---

## Priority

**Impact:** Very High - Enables community contributions
**Effort:** Medium (2-3 days to create all templates + guidelines)
**Complexity:** Low
**Dependencies:** None

**Recommendation:** P2 - High Priority
- Create after basic features are stable (Phase 2-3)
- Before promoting project widely
- Essential for scaling project

---

## Implementation Checklist

- [ ] Create `CONTRIBUTING.md` in repository root
- [ ] Create `CODE_OF_CONDUCT.md`
- [ ] Create `.github/ISSUE_TEMPLATE/bug_report.yml`
- [ ] Create `.github/ISSUE_TEMPLATE/feature_request.yml`
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] Add "Contributing" section to README.md
- [ ] Enable GitHub Discussions
- [ ] Add labels: `good first issue`, `help wanted`, `bug`, `enhancement`, `documentation`
- [ ] Create first "good first issue" for new contributors
- [ ] Document maintainer workflow

---

## Open Questions

1. **Code Review:**
   - Require 1 or 2 approvals?
   - Auto-merge for maintainers?

2. **CI/CD:**
   - Run tests on all PRs?
   - Auto-format with black?
   - Require coverage threshold?

3. **License:**
   - MIT (most permissive)?
   - Apache 2.0 (patent protection)?
   - GPL (copyleft)?

4. **CLA (Contributor License Agreement):**
   - Required or not?
   - Most small projects skip this

5. **Governance:**
   - Single maintainer?
   - Core team?
   - Community voting?

---

**Status:** Contributing guidelines & open source governance
**Related:** Spec 006 (Distribution) - makes project accessible, this makes it contributable
**Next Action:** Create CONTRIBUTING.md, issue/PR templates, enable Discussions
