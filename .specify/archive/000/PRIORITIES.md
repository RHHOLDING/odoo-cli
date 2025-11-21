# Implementation Priorities & Roadmap

**Last Updated:** 2025-11-21
**CLI Version:** v1.4.0 (in progress)
**Branch:** 005-quick-wins-bundle

This document provides a prioritized roadmap for implementing features from IDEA-01 through IDEA-08, considering development complexity, refactoring impact, and dependencies.

## ✅ COMPLETED FEATURES

### v1.3.0 - Context Management (DONE)
- ✅ Client context support in `_execute()` and all helper methods
- ✅ `--context` flag on all 10 CLI commands
- ✅ Context parser with type inference
- ✅ Documentation (README, CHANGELOG)

### v1.4.0 - Quick Wins Bundle (DONE)
- ✅ **search-count** command - Fast counting without data transfer
- ✅ **name-get** command - ID to name conversion in 1 call
- ✅ **name-search** command - Fuzzy name search for autocomplete
- ✅ **fields_get attributes** - Filter field metadata to reduce payload

---

---

## 🔥 CRITICAL - ~~Implement Immediately~~ COMPLETED ✅

### 1. ✅ Context Management (IDEA-04) - COMPLETED v1.3.0
**File:** `specs/000/IDEA-04_session-context-management.md` (Section 2)

**Why Critical:**
- **We send NO context to Odoo currently!**
- Missing: `lang`, `tz`, `active_test`, `allowed_company_ids`
- Impact: Translations broken, archived records invisible, multi-company fails
- **Affects all existing commands** - they all need context support

**Implementation:**
```python
# Phase 1: Add context parameter to client._execute()
def _execute(self, model, method, *args, context=None, **kwargs):
    if context:
        kwargs['context'] = context
    # ... existing code

# Phase 2: CLI flag support
odoo search product.product '[]' --context active_test=false
odoo create res.partner --fields name="Test" --context default_type=company

# Phase 3: Global config
odoo config set-context lang=de_DE tz=Europe/Berlin
```

**Effort:** Medium (2-3 days)
**Refactoring Impact:** 🟡 Medium - All commands need `--context` flag support
**Dependencies:** None
**Blocks:** Multi-company features, translations, archived record access

---

## 🚀 QUICK WINS - ~~High Value, Low Effort~~ COMPLETED ✅

### 2. ✅ search-count Command (IDEA-05) - COMPLETED v1.4.0
**File:** `specs/000/IDEA-05_odoo-api-best-practices.md` (Section 3)

**Why Quick Win:**
- **Already implemented in client.py (Line 349)!**
- Just needs CLI command wrapper
- Immediate performance benefit (no ID transfer)

**Implementation:**
```python
# odoo_cli/commands/search_count.py (NEW FILE)
@click.command('search-count')
@click.argument('model')
@click.argument('domain', default='[]')
@click.option('--json', 'json_mode', is_flag=True)
def search_count_cmd(model, domain, json_mode):
    client = get_odoo_client()
    count = client.search_count(model, parse_domain(domain))
    if json_mode:
        console.print_json({"count": count})
    else:
        console.print(count)
```

**Effort:** 5-10 minutes
**Refactoring Impact:** 🟢 None
**Dependencies:** None
**Value:** High - Fast counting for large datasets

---

### 3. ✅ name-get / name-search Commands (IDEA-05) - COMPLETED v1.4.0
**File:** `specs/000/IDEA-05_odoo-api-best-practices.md` (Sections 1-2)

**Why Quick Win:**
- Simple wrappers around existing RPC methods
- High value for LLMs (ID → Name lookups)
- Replaces search + read pattern (2 calls → 1 call)

**Implementation:**
```python
# Add to client.py
def name_get(self, model: str, ids: List[int]) -> List[Tuple[int, str]]:
    return self._execute(model, 'name_get', ids)

def name_search(self, model: str, name: str = '', domain: List = None,
                operator: str = 'ilike', limit: int = 100):
    domain = domain or []
    return self._execute(model, 'name_search', name, domain,
                        operator=operator, limit=limit)

# CLI commands (2 new files)
odoo name-get res.partner 1,2,3
odoo name-search res.partner "azure" --limit 10
```

**Effort:** 15-20 minutes
**Refactoring Impact:** 🟢 None
**Dependencies:** None
**Value:** High - Better UX for LLMs

---

### 4. ✅ fields_get Attribute Filtering (IDEA-05) - COMPLETED v1.4.0
**File:** `specs/000/IDEA-05_odoo-api-best-practices.md` (Section 4)

**Why Quick Win:**
- Minor enhancement to existing method
- Reduces payload size significantly
- Already 80% implemented (has `allfields` parameter)

**Implementation:**
```python
# Modify client.py fields_get() - add 1 parameter
def fields_get(self, model: str, allfields: Optional[List[str]] = None,
               attributes: Optional[List[str]] = None):  # ← NEW
    kwargs = {}
    if allfields:
        kwargs['allfields'] = allfields
    if attributes:
        kwargs['attributes'] = attributes  # ← NEW
    return self._execute(model, 'fields_get', **kwargs)

# CLI usage
odoo get-fields res.partner --attributes type,required,readonly
```

**Effort:** 10 minutes
**Refactoring Impact:** 🟢 None
**Dependencies:** None
**Value:** Medium - Performance optimization

---

## ⚡ HIGH VALUE - Important, Medium Effort

### 5. Session Management (IDEA-04)
**File:** `specs/000/IDEA-04_session-context-management.md` (Section 1)

**Why High Value:**
- Eliminates repeated authentication
- Easy environment switching (prod/staging/dev)
- Better UX for developers

**Implementation:**
```python
# New file: odoo_cli/session.py
class SessionManager:
    def save(name, url, db, username, password):
        # Store in ~/.odoo-cli/sessions.json (encrypted)
    def load(name):
        # Return config dict
    def list():
        # Return session names
    def remove(name):
        # Delete session

# CLI commands
odoo session save prod --url https://prod.odoo.com --db prod
odoo session load prod
odoo session list
odoo session remove old-env
```

**Effort:** Medium (1-2 days)
**Refactoring Impact:** 🟡 Medium - Need credential encryption, config priority changes
**Dependencies:** None (independent feature)
**Blocks:** Nothing
**Value:** High - Developer productivity

**⚠️ Security Consideration:** Use `keyring` library for credential storage, not plain JSON!

---

### 6. copy Command (IDEA-05)
**File:** `specs/000/IDEA-05_odoo-api-best-practices.md` (Section 5)

**Why High Value:**
- Common operation (duplicate products, quotes, etc.)
- Simple RPC method call

**Implementation:**
```python
# Add to client.py
def copy(self, model: str, record_id: int,
         defaults: Optional[Dict] = None) -> int:
    args = [record_id]
    kwargs = {}
    if defaults:
        kwargs['default'] = defaults
    return self._execute(model, 'copy', *args, **kwargs)

# CLI command
odoo copy res.partner 42 --override name="Copy of Partner"
```

**Effort:** 20-30 minutes
**Refactoring Impact:** 🟢 None
**Dependencies:** None
**Value:** Medium-High - Common use case

---

### 7. Read-Only Mode (IDEA-02)
**File:** `specs/000/IDEA-02_read-only-mode.md`

**Why High Value:**
- Safe production access
- Simple environment variable check

**Implementation:**
```python
# Modify cli.py - check ODOO_READ_ONLY env var
ODOO_READ_ONLY = os.getenv('ODOO_READ_ONLY', 'false').lower() == 'true'

# In each write command (create, update, delete, etc.)
if ODOO_READ_ONLY:
    console.print("[red]Error: Read-only mode enabled[/red]")
    sys.exit(3)

# CLI usage
export ODOO_READ_ONLY=true
odoo read res.partner 1  # ✅ Works
odoo update res.partner 1 --fields name="Test"  # ❌ Blocked
```

**Effort:** 1 hour
**Refactoring Impact:** 🟡 Low-Medium - Add check to all write commands
**Dependencies:** None
**Value:** High - Production safety

---

## 💡 MEDIUM PRIORITY - Useful, But Not Urgent

### 8. default_get Command (IDEA-05)
**File:** `specs/000/IDEA-05_odoo-api-best-practices.md` (Section 6)

**Why Medium:**
- Helpful for LLMs to understand defaults
- Less frequently needed than other operations

**Implementation:**
```python
# Add to client.py
def default_get(self, model: str, fields: List[str]) -> Dict[str, Any]:
    return self._execute(model, 'default_get', fields)

# CLI
odoo default-get sale.order partner_id,date_order,warehouse_id
```

**Effort:** 15 minutes
**Refactoring Impact:** 🟢 None
**Dependencies:** None
**Value:** Medium - Niche use case

---

### 9. Access Control Checks (IDEA-04)
**File:** `specs/000/IDEA-04_session-context-management.md` (Section 5)

**Why Medium:**
- Better error messages
- Pre-flight validation
- Security best practice

**Implementation:**
```python
# Add to client.py
def check_access_rights(self, model: str, operation: str) -> bool:
    try:
        return self._execute(model, 'check_access_rights', operation,
                           raise_exception=True)
    except ValueError:
        return False

# CLI command
odoo check-access res.partner write
# Exit code: 0 = allowed, 1 = denied

# Optional: --strict flag in write commands
odoo update res.partner 1 --fields name="Test" --strict
# → First checks access, then updates
```

**Effort:** 1-2 hours
**Refactoring Impact:** 🟡 Low - Add optional `--strict` flag
**Dependencies:** None
**Value:** Medium - Better error messages

---

## 🔮 FUTURE - Larger Refactoring Required

### 10. JSON-RPC Batch Requests (IDEA-03)
**File:** `specs/000/IDEA-03_batch-requests-optimization.md` (Sections 1-2)

**Why Future:**
- **Requires significant refactoring of client._jsonrpc_call()**
- Changes request/response handling fundamentally
- Need buffering/queueing system
- High complexity, high testing burden

**Implementation Challenge:**
```python
# Current: Single request
payload = {"jsonrpc": "2.0", "method": "call", "params": {...}, "id": 1}
response = self.session.post(f"{self.url}/jsonrpc", json=payload)

# Future: Batch requests (array)
payloads = [
    {"jsonrpc": "2.0", "method": "call", "params": {...}, "id": 1},
    {"jsonrpc": "2.0", "method": "call", "params": {...}, "id": 2},
    {"jsonrpc": "2.0", "method": "call", "params": {...}, "id": 3},
]
response = self.session.post(f"{self.url}/jsonrpc", json=payloads)
# Response is also array → need to match by id
```

**Effort:** High (3-5 days)
**Refactoring Impact:** 🔴 HIGH - Affects all RPC calls, error handling, testing
**Dependencies:** Should implement AFTER context management (004)
**Blocks:** Async batching features
**Value:** Very High - 10x performance for bulk operations

**Decision Point:** Wait until we have solid context + session foundation

---

### 11. Async Batching (IDEA-04, Zenoo Pattern)
**File:** `specs/000/IDEA-04_session-context-management.md` (Section 4)

**Why Future:**
- **Requires async/await architecture** (breaking change!)
- Depends on IDEA-03 (Batch Requests)
- Need separate `async` CLI or compatibility layer

**Implementation Challenge:**
```python
# Would require rewriting entire client as async
class AsyncOdooClient:
    async def connect(self): ...
    async def execute(self, model, method, *args): ...

# CLI becomes async
async def main():
    async with AsyncOdooClient(...) as client:
        await client.execute(...)

# Compatibility nightmare with sync code
```

**Effort:** Very High (1-2 weeks)
**Refactoring Impact:** 🔴 CRITICAL - Complete rewrite
**Dependencies:** IDEA-03 (Batch Requests)
**Value:** Very High - But disruptive

**Decision:** Consider as separate project: `odoo-cli-async` or wait for strong demand

---

### 12. Cross-Platform Compatibility Testing (IDEA-01)
**File:** `specs/000/IDEA-01_cross-platform-compatibility.md`

**Why Future:**
- Validation/testing task, not new features
- Needs access to all platforms (macOS, Linux, Windows)
- Needs access to all Odoo types (Docker, odoo.sh, local)

**Effort:** Medium (1 week for comprehensive testing)
**Refactoring Impact:** 🟢 None (just testing)
**Dependencies:** None
**Value:** Medium - Quality assurance

**Recommendation:** Schedule as QA phase after implementing priority features

---

### 13. Advanced Domain Syntax (IDEA-05)
**File:** `specs/000/IDEA-05_odoo-api-best-practices.md` (Section "Odoo Domain Patterns")

**Why Future:**
- Complex parser needed
- Alternative syntax conflicts with Odoo standard
- Edge cases and escaping issues

**Example Challenge:**
```bash
# Odoo format (current - works but painful)
odoo search res.partner '["|",["name","=","A"],["name","=","B"]]'

# Proposed SQL-like syntax (needs complex parser)
odoo search res.partner --where "name=A OR name=B"
# How to parse nested AND/OR? Precedence rules?
```

**Effort:** High (2-3 days for robust parser)
**Refactoring Impact:** 🟡 Medium - New parser, maintain backward compatibility
**Dependencies:** None
**Value:** Medium - Nice to have, not critical

**Decision:** Low priority - current syntax works, just verbose

---

### 14. PyPI Package Publication (IDEA-06)
**File:** `specs/000/IDEA-06_package-distribution.md` (PyPI Section)

**Why High Priority:**
- Makes installation trivial: `pip install odoo-cli`
- Low effort, high impact
- Gateway to wider adoption

**Implementation:**
```bash
# Update pyproject.toml
[project]
name = "odoo-cli"
version = "1.2.0"
description = "LLM-friendly CLI tool for Odoo via JSON-RPC"
# ... metadata

# Build & publish
python -m build
twine upload dist/*

# GitHub Action (automated)
on:
  release:
    types: [published]
jobs:
  publish:
    - python -m build
    - twine upload dist/*
```

**Security:**
```bash
# SHA256 checksums auto-generated by PyPI
# Displayed on package page
# pip verifies automatically
```

**Effort:** Low (2-3 hours one-time setup, then automated)
**Refactoring Impact:** 🟢 None
**Dependencies:** None
**Value:** Very High - Essential for distribution

---

### 15. Homebrew Formula (IDEA-06)
**File:** `specs/000/IDEA-06_package-distribution.md` (Homebrew Section)

**Why High Value:**
- macOS/Linux users prefer Homebrew
- Professional distribution method
- Automatic SHA256 verification

**Implementation:**
```ruby
# Create homebrew-odoo-cli/Formula/odoo-cli.rb
class OdooCli < Formula
  desc "LLM-friendly CLI tool for Odoo via JSON-RPC"
  url "https://github.com/RHHOLDING/odoo-cli/archive/v1.2.0.tar.gz"
  sha256 "CHECKSUM_HERE"  # ← CRITICAL for security

  depends_on "python@3.10"

  def install
    virtualenv_install_with_resources
  end
end

# Users install
brew tap actec-andre/odoo-cli
brew install odoo-cli
```

**Effort:** Low (3-4 hours)
**Refactoring Impact:** 🟢 None
**Dependencies:** PyPI publication (for resource URLs)
**Value:** High - macOS/Linux users

---

### 16. Project Context Layer (IDEA-07)
**File:** `specs/000/IDEA-07_project-context-layer.md`

**Why High Value:**
- Dramatically improves LLM effectiveness
- Eliminates repeated "What's the ID?" questions
- Living documentation in version control

**Implementation:**
```yaml
# .odoo-context.yaml
companies:
  solarcraft:
    id: 1
    name: "SOLARCRAFT GmbH"
    purpose: "Solar products"

key_records:
  warehouses:
    main_eu:
      id: 1
      name: "Main Warehouse Europe"

custom_modules:
  actec_helpdesk_enh:
    models: [helpdesk.ticket]
    custom_fields:
      helpdesk.ticket:
        x_customer_priority: "VIP status"

# CLI integration
odoo context show      # Display loaded context
odoo context validate  # Check IDs exist in Odoo
odoo context init      # Generate template
```

**LLM Benefit:**
```
Without context: 5 questions to create order
With context: Creates order directly with correct IDs
```

**Effort:** Medium (2-3 days)
**Refactoring Impact:** 🟡 Low - Add to llm-help output
**Dependencies:** Context Management (IDEA-04)
**Value:** Very High - Massive LLM productivity boost

---

### 17. Contributing Guidelines (IDEA-08)
**File:** `specs/000/IDEA-08_contributing-guidelines.md`

**Why Important:**
- Enables external contributions
- Maintains code quality
- Scales project development

**Implementation:**
```markdown
# CONTRIBUTING.md (complete template)
1. Getting Started
2. Development Setup
3. Coding Standards (PEP 8, type hints, docstrings)
4. Submitting Changes (branches, commits, PRs)
5. Review Process
6. Design Principles (LLM-friendly FIRST!)
7. Testing Guidelines (80%+ coverage)

# GitHub Templates
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/feature_request.yml
.github/PULL_REQUEST_TEMPLATE.md

# CODE_OF_CONDUCT.md
Welcoming, inclusive, zero harassment
```

**Key Principles:**
- **LLM-Friendly First** (non-negotiable)
- Backward Compatibility
- Test Everything (80%+ coverage)
- Keep It Simple

**Effort:** Medium (2-3 days)
**Refactoring Impact:** 🟢 None
**Dependencies:** None (but best after features stable)
**Value:** High - Essential for open source project

---

## 📊 Implementation Roadmap

### ✅ Phase 1: Foundation (Week 1) - COMPLETED
**Goal:** Fix critical issues, add quick wins

1. ✅ **Context Management** (CRITICAL) - 2-3 days - **DONE v1.3.0**
   - ✅ Global context config
   - ✅ `--context` flag for all commands
   - ✅ Update `_execute()` in client.py

2. ✅ **Quick Wins Bundle** - 1 day - **DONE v1.4.0**
   - ✅ `search-count` command
   - ✅ `name-get` / `name-search` commands
   - ✅ `fields_get` attributes parameter

**Deliverable:** ✅ v1.3.0 - Context Support (RELEASED)
**Deliverable:** ✅ v1.4.0 - Quick Wins Bundle (IN PROGRESS)

---

### Phase 2: Developer Experience (Week 2-3) - NEXT
**Goal:** Improve workflow, reduce friction

3. ⏳ **Session Management** - 2 days
   - Save/load/list sessions
   - Credential encryption
   - Session switching

4. ⏳ **Read-Only Mode** - 1 hour
   - Environment variable check
   - Block write operations

5. ⏳ **copy Command** - 30 minutes
   - Record duplication

**Deliverable:** v1.5.0 - Sessions + Safety Features

---

### Phase 3: Enhancement (Week 4)
**Goal:** Polish, quality improvements

6. ✅ **Access Control Checks** - 1-2 hours
   - `check-access` command
   - Optional `--strict` flag

7. ✅ **default_get Command** - 15 minutes
   - Form defaults helper

8. ✅ **Project Context Layer** (IDEA-07) - 2-3 days
   - .odoo-context.yaml file support
   - Auto-discovery and loading
   - LLM-help integration
   - Context validation

**Deliverable:** v1.5.0 - Enhanced API Coverage + Project Context

---

### Phase 4: Distribution & Community (Week 5-6)
**Goal:** Make project accessible and open for contributions

9. ✅ **PyPI Publication** (IDEA-06) - 3 hours
   - Update pyproject.toml metadata
   - Create PyPI account + API token
   - GitHub Action for auto-publish
   - SHA256 checksums

10. ✅ **Homebrew Tap** (IDEA-06) - 4 hours
   - Create homebrew-odoo-cli repository
   - Write Formula with checksums
   - Test on macOS & Linux

11. ✅ **Contributing Guidelines** (IDEA-08) - 2-3 days
   - CONTRIBUTING.md
   - CODE_OF_CONDUCT.md
   - Issue/PR templates
   - Enable GitHub Discussions

**Deliverable:** v1.5.0 - Public Release Ready

---

### Phase 5: Future (TBD)
**Goal:** Major refactoring if demand exists

12. ✅ **Docker Image** (IDEA-06) - 3 hours
   - Dockerfile + auto-build
   - Docker Hub publishing

13. ✅ **Binary Distribution** (IDEA-06) - 1 day
   - PyInstaller for all platforms
   - SHA256SUMS.txt generation

14. ❓ **Batch Requests** (IDEA-03) - IF needed
15. ❓ **Async Support** (IDEA-04) - IF needed
16. ✅ **Cross-Platform Testing** (IDEA-01) - QA task
17. ❓ **Advanced Domains** (IDEA-05) - IF requested

---

## 🎯 Priority Matrix

| Feature | Spec | Impact | Effort | Refactoring | Priority | Status |
|---------|------|--------|--------|-------------|----------|--------|
| **Context Management** | 004 | 🔥 Critical | Medium | Medium | P0 | ✅ v1.3.0 |
| **search-count** | 005 | High | Low | None | P1 | ✅ v1.4.0 |
| **name-get/search** | 005 | High | Low | None | P1 | ✅ v1.4.0 |
| **fields_get attributes** | 005 | Medium | Low | None | P1 | ✅ v1.4.0 |
| **Session Management** | 004 | High | Medium | Medium | P2 | 2 |
| **Read-Only Mode** | 002 | High | Low | Low | P2 | 2 |
| **copy Command** | 005 | Medium | Low | None | P2 | 2 |
| **Access Control** | 004 | Medium | Low | Low | P3 | 3 |
| **default_get** | 005 | Medium | Low | None | P3 | 3 |
| **Project Context Layer** | 007 | High | Medium | Low | P2 | 3 |
| **PyPI Publication** | 006 | High | Low | None | P1 | 4 |
| **Homebrew Tap** | 006 | High | Low | None | P2 | 4 |
| **Contributing Guidelines** | 008 | Medium | Medium | None | P2 | 4 |
| **Docker Image** | 006 | Medium | Low | None | P3 | 5 |
| **Binary Distribution** | 006 | Medium | Medium | None | P3 | 5 |
| **Batch Requests** | 003 | Very High | High | High | P4 | Future |
| **Async Support** | 004 | Very High | Very High | Critical | P5 | Future |
| **Cross-Platform Test** | 001 | Medium | Medium | None | P3 | Future |
| **Advanced Domains** | 005 | Medium | High | Medium | P5 | Future |

---

## 🚦 Decision Guidelines

**Implement Now if:**
- ✅ Critical bug or missing core functionality
- ✅ Quick win (< 1 hour, high value)
- ✅ Blocks other features
- ✅ Low refactoring impact

**Defer to Future if:**
- ❌ Requires major refactoring (> 3 days)
- ❌ Breaking changes to API
- ❌ Uncertain demand
- ❌ Blocks nothing else

**Re-evaluate if:**
- 🔄 User feedback indicates different priorities
- 🔄 New Odoo version changes APIs
- 🔄 Performance issues emerge in production

---

## 📝 Notes

- **Context is CRITICAL** - Without it, multi-company, translations, and archived records don't work
- **Quick wins first** - Build momentum with visible progress
- **Avoid premature optimization** - Don't implement batch/async until proven necessary
- **Maintain LLM-friendly design** - All features must preserve structured JSON output

---

---

## 📦 Complete Specs Overview

| Spec | Title | Category | Lines | Priority |
|------|-------|----------|-------|----------|
| 001 | Cross-Platform Compatibility | Testing | ~150 | P3 |
| 002 | Read-Only Mode | Safety | ~120 | P2 |
| 003 | Batch Requests Optimization | Performance | ~131 | P4 |
| 004 | Session & Context Management | **Core** | ~655 | **P0** |
| 005 | API Best Practices & Quick Wins | Enhancement | ~655 | P1 |
| 006 | Package Distribution + Security | Distribution | ~956 | P1 |
| 007 | Project Context Layer for LLMs | LLM Enhancement | ~760 | P2 |
| 008 | Contributing Guidelines | Governance | ~1,006 | P2 |

**Total Documentation:** ~4,433 lines across 8 comprehensive specs

---

**Next Action:** Implement Phase 1 (Context + Quick Wins) → Target: v1.3.0
