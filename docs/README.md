# Odoo CLI Documentation Hub
**Complete Guide to Using, Testing, and Extending the Odoo JSON-RPC CLI Tool**

---

## 📚 Documentation Index

### 🚀 Installation & Setup
- **[installation/README.md](installation/README.md)** - Installation guide overview
  - Platform-specific instructions (macOS, Linux, Windows)
  - Quick start (all platforms)
  - Configuration and credentials
  - Troubleshooting

- **[installation/INSTALL-MAC.md](installation/INSTALL-MAC.md)** - macOS Installation
  - Homebrew, Python, Virtual Environment
  - Credential configuration
  - macOS-specific troubleshooting

### 🎯 Usage & Development
- **[guides/LLM-DEVELOPMENT.md](guides/LLM-DEVELOPMENT.md)** - How LLMs should use the CLI
  - When to use Python scripts vs CLI commands
  - Aggregation patterns and best practices
  - Template scripts for common tasks
  - Error handling for scripting

### 📖 Reference & Quality
- **[IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md)** - What was built (overview)
  - Complete feature list
  - Real-world usage examples
  - Quick reference guide

- **[ERROR-HANDLING.md](ERROR-HANDLING.md)** - Comprehensive error guide
  - Error categories and solutions
  - Debugging workflow
  - Common mistakes and patterns
  - JSON error format for LLM integration

- **[AUDIT-REPORT.md](AUDIT-REPORT.md)** - Code audit and quality analysis
  - Issues found and fixed
  - Code patterns established
  - Testing summary
  - Recommendations for future development

### 📚 Main CLI Documentation
- **[../README.md](../README.md)** - Main CLI repository README
  - Features overview
  - Basic command examples
  - Security best practices

### Examples
Located in `examples/` directory:
- `aggregation_script.py` - Summing/averaging large datasets
- `batch_processing.py` - Processing records in batches
- `error_handling.py` - Robust error handling patterns
- `complex_query.py` - Multi-step queries with logic

---

## 🎯 Common Tasks

### Task: "Sum sales for October 2025"
→ Use Python script template from [LLM-DEVELOPMENT.md](guides/LLM-DEVELOPMENT.md)
→ Expected result: €6,681,527.19 (5,991 orders)

### Task: "Find all partners with email"
→ CLI command: `odoo search res.partner '[["email", "!=", false]]'`

### Task: "Get field definitions"
→ CLI command: `odoo get-fields sale.order --field amount_untaxed`

### Task: "Debug domain format error"
→ See [ERROR-HANDLING.md](ERROR-HANDLING.md) → Domain Errors section

### Task: "Create reusable aggregation script"
→ See [LLM-DEVELOPMENT.md](guides/LLM-DEVELOPMENT.md) → Python Script Template section

---

## 🔧 For Developers

### Understanding the Architecture

```
odoo-xml-cli/
├── odoo_cli/
│   ├── client.py           # JSON-RPC client (core)
│   ├── cache.py            # 24h response caching
│   ├── error_handler.py    # Enhanced error handling
│   ├── commands/           # CLI commands
│   │   ├── execute.py      # Direct method execution
│   │   ├── search.py       # Domain-based search
│   │   ├── read.py         # Record retrieval
│   │   └── ...
│   └── utils.py            # Shared utilities
├── tests/
│   └── unit/               # Unit tests
│       ├── test_cache.py   # Cache tests
│       ├── test_client_core.py  # Client tests
│       ├── test_commands_*.py    # Command tests
│       └── ...
└── docs/                   # This documentation
    ├── guides/
    │   └── LLM-DEVELOPMENT.md
    ├── examples/
    ├── ERROR-HANDLING.md
    ├── AUDIT-REPORT.md
    └── README.md (you are here)
```

### Key Patterns

**Method Execution Pattern:**
```python
# ✅ Correct way to call a method
result = client._execute(model, method, *args, **kwargs)

# ✅ Avoid double-wrapping domains
domain = [["field", "=", "value"]]  # Already a list
result = client.search(model, domain)  # Don't wrap again
```

**Batch Processing Pattern:**
```python
batch_size = 1000
for i in range(0, len(ids), batch_size):
    batch = ids[i:i+batch_size]
    records = client.read(model, batch)
    # Process batch
```

**Error Handling Pattern:**
```python
try:
    result = client.search(model, domain)
except ValueError as e:
    error_type, message, suggestion = ErrorAnalyzer.analyze(str(e))
    # Act on error_type: 'domain', 'model', 'field', etc.
```

---

## ✅ Quality Assurance

### Code Quality Checks
- ✅ Type hints on all public methods
- ✅ Docstrings on all classes and functions
- ✅ 31+ unit tests (100% passing)
- ✅ 94% coverage for cache module
- ✅ 59% coverage for client module

### Error Handling
- ✅ Categorized error types (domain, model, field, auth, etc.)
- ✅ Intelligent error suggestions
- ✅ JSON error output for LLM integration

### Performance
- ✅ 75% higher throughput than XML-RPC (175 req/s)
- ✅ 43% faster response times (~285ms average)
- ✅ Connection pooling for persistent sessions
- ✅ 24-hour caching for model definitions

### Testing
- ✅ Unit tests for all core functionality
- ✅ Command tests for CLI integration
- ✅ Error handling tests
- ✅ Real Odoo instance validation

---

## 🚀 Getting Started with Documentation

### If you want to...

**Use the CLI tool:**
→ Start with [../README.md](../README.md)

**Debug an error:**
→ Go to [ERROR-HANDLING.md](ERROR-HANDLING.md)

**Write a Python script for aggregation:**
→ See [LLM-DEVELOPMENT.md](guides/LLM-DEVELOPMENT.md)

**Understand code changes:**
→ Read [AUDIT-REPORT.md](AUDIT-REPORT.md)

**Extend the CLI:**
→ Check architecture in this README, then look at `test_commands_*.py`

**Improve error messages:**
→ Edit `error_handler.py`, add patterns to `ERROR_PATTERNS` dict

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Commands available | 8 (execute, search, read, get-models, get-fields, search-employee, search-holidays, shell) |
| Response time | ~285ms (vs 500ms XML-RPC) |
| Throughput | 175 req/s (vs 100 req/s XML-RPC) |
| Test coverage | 94% (cache), 59% (client) |
| Error categories | 8 types with intelligent suggestions |
| Odoo version support | v14, v15, v16, v17 |

---

## 🔄 Workflow Examples

### Workflow 1: Find & List Partners
```bash
# Step 1: Search
odoo search res.partner '[["is_company", "=", true]]' --limit 10

# Step 2: If domain fails, check available fields
odoo get-fields res.partner --field is_company

# Step 3: Retry with correct field
odoo search res.partner '[["is_company", "=", true]]' --limit 10
```

### Workflow 2: Aggregate Sales Data
```bash
# Step 1: Estimate size
odoo execute sale.order search_count --args '[[["date_order", ">=", "2025-10-01"]]]'

# Step 2: If > 1000, use Python script (see LLM-DEVELOPMENT.md)
python3 /tmp/aggregate_sales.py

# Step 3: Results printed with progress
```

### Workflow 3: Debug Connection
```bash
# Step 1: Test connection
odoo get-models --timeout 60

# Step 2: If fails, check .env
cat .env

# Step 3: Validate each credential
odoo --url https://test.odoo.com --db test_db --username admin get-models
```

---

## 📝 Contributing

When improving the CLI:

1. **Read the AUDIT-REPORT.md** to understand current code patterns
2. **Write tests first** in `tests/unit/test_*.py`
3. **Follow error handling** patterns from `error_handler.py`
4. **Update docs** when adding features
5. **Run existing tests** to ensure no regressions

---

## 🔗 Related Documentation

- **Parent Repository:** `/Users/andre/Documents/dev/ODOO-MAIN/`
- **Main CLI README:** `../README.md`
- **Changelog:** `../CHANGELOG.md`
- **Python Package:** `../pyproject.toml`

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0 (JSON-RPC)
**Status:** Production Ready ✅
