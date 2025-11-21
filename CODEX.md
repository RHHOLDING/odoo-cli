# CODEX.md

Quick briefing for OpenAI/Codex/ChatGPT-style assistants working on this public repository. Keep this aligned with `CLAUDE.md`.

## Repository Safety
- PUBLIC repo: https://github.com/RHHOLDING/odoo-cli (no secrets, no customer data)
- Secrets live outside the repo: env vars `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`; config file at `~/.odoo-cli.yaml`
- Example/demo data only: Odoo demo names (Azure Interior, Deco Addict, Gemini Furniture), generic partners/products, masked URLs and DB names
- .env files are gitignored; do not add credentials or internal URLs to code, tests, or docs
- License: MIT License (LICENSE file and README aligned)

## Language & Style
- Everything in English: code, comments, docs, commit messages, specs
- Format with Black (line length 120) and isort; Google-style docstrings; add type hints where useful
- Comment for "why", not "what"; prefer clear names over heavy comments

## LLM-First CLI
- Standalone Python 3.10+ CLI (`odoo-cli`) for Odoo JSON-RPC; no Odoo dependencies
- Outputs are machine-first: JSON by default, structured errors with `error_type`, predictable exit codes (0=success, 1=connection, 2=auth, 3=operation)
- No interactive prompts/TUIs; Rich is fine for readability but JSON output is primary
- Keep `--llm-help` comprehensive and deterministic; avoid unstructured tracebacks in normal flow

## Key Files & References
- `README.md` main docs; `CHANGELOG.md` version history; `docs/` deeper guides
- `CLAUDE.md` canonical guidelines; keep this file in sync
- `.specify/` feature specs; current next feature: environment profiles (`.specify/features/001_environment_profiles/`)
- `odoo_cli/help.py` drives `--llm-help` and decision trees; `odoo_cli/commands/` holds CLI commands

## Common Tasks
- New command: add under `odoo_cli/commands/`, register in `odoo_cli/cli.py`, update `odoo_cli/help.py`, add tests in `tests/unit/`, document in `README.md`
- Error handling: return structured JSON with actionable suggestions; avoid plain tracebacks
- Testing: `pytest` or `pytest --cov=odoo_cli`; mock Odoo responses, use demo data for integration-style tests
- Releases: bump version in `pyproject.toml`, update `CHANGELOG.md`, align `--llm-help` version; tag as `vX.Y.Z`

## Roadmap Snapshot
- v1.4.0 shipped: core CLI + CRUD/bulk ops, field parser/aggregation, search-count/name-get/name-search, context management
- Next v1.5.0: environment profiles for prod/stage/dev switching (spec ready)

## Contribution Etiquette
- Branch off feature branches; scoped PRs with tests and docs
- Commit messages in `type: summary` format (e.g., `feat: Add environment profile switching`)
- Run formatters/linters/tests before submitting; check diffs for secrets/internal URLs

If unsure, mirror `CLAUDE.md` and prefer deterministic, LLM-friendly behaviors over human-facing conveniences.
