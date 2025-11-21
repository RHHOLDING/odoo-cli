# Error Handling & Debugging Guide
**Making Errors Your Friend: JSON-RPC Error Excellence**

---

## Why JSON-RPC Error Messages Are Better

JSON-RPC provides **structured, detailed error messages** that make debugging easier than ever:

### Example: Clear Error Messages

```
Command: odoo execute sale.order search --args '[["date_order", ">=", "2025-10-01"]]'

❌ Error: Odoo error: Odoo Server Error: Domains to normalize must have a 'domain' form:
          a list or tuple of domain components

✓ What's wrong: Domain format error
✓ Why it happened: Missing outer list wrapper
✓ Fix: Use [["date_order", ">=", "2025-10-01"]] (note the extra brackets)
```

---

## Error Categories & Solutions

### 1. Domain Errors (Most Common)

#### Error: "unhashable type: 'list'"
```
Cause: Domain wrapped too many times
Wrong: _execute(model, 'search', [domain])
Right: _execute(model, 'search', domain)
Fix:   Remove extra brackets when calling _execute()
```

#### Error: "tuple index out of range"
```
Cause: Domain condition incomplete (missing operator or value)
Wrong: [["field"]]  or [["field", "="]]
Right: [["field", "=", "value"]]
Fix:   Each condition needs 3 parts: field, operator, value
```

#### Error: "Domains to normalize must have a 'domain' form"
```
Cause: Domain is string instead of list
Wrong: '"some_string"'
Right: '[["field", "=", "some_string"]]'
Fix:   Always use lists for domains, never bare strings
```

**Solution Flowchart:**
```
Domain Error?
├─ Check outer brackets: [...]
├─ Check each condition: ["field", "op", "value"]
├─ Check no strings instead of lists
├─ Verify operator is valid: =, !=, <, >, <=, >=, ilike, in, not in
└─ Try with simpler domain first: []
```

---

### 2. Field Errors

#### Error: "Invalid field 'field_name' on model 'model_name'"
```
Cause: Field doesn't exist or typo
Fix:   odoo get-fields model_name --field field_name
      (Lists all available fields with descriptions)
```

#### Error: "has no attribute 'field'"
```
Cause: Model doesn't support this field
Fix:   Check if field is company-specific or requires a module
      Use: odoo get-fields model_name
```

**Quick Fix:**
```bash
# See all fields:
odoo get-fields sale.order

# Find specific field:
odoo get-fields sale.order --field amount

# Get field definition:
odoo get-fields sale.order --field amount_untaxed --json
```

---

### 3. Model Errors

#### Error: "Model 'model_name' does not exist"
```
Cause: Model name typo or doesn't exist in this instance
Fix:   odoo get-models --filter "pattern"
      (Search for similar models)
```

#### Error: "Access denied for model 'model_name'"
```
Cause: User lacks read permission
Fix:   Check user roles or use admin account
      In .env: ODOO_USERNAME=admin@example.com
```

**Find the right model:**
```bash
# List all models:
odoo get-models

# Search for specific models:
odoo get-models --filter "sale"
odoo get-models --filter "partner"
odoo get-models --filter "invoice"
```

---

### 4. Authentication & Connection

#### Error: "Authentication failed: Invalid username or password"
```
Cause: Wrong credentials
Fix:   Check .env file or environment variables:
       - ODOO_USERNAME (correct format: email or username)
       - ODOO_PASSWORD (correct password)
       - ODOO_URL (with https://)
       - ODOO_DB (correct database name)
```

#### Error: "Failed to connect to Odoo server"
```
Cause: Network unreachable, URL wrong, or server down
Fix:   1. Ping server: curl https://your-url.odoo.com
       2. Check .env: ODOO_URL=https://your-url.odoo.com
       3. Check network: ping your-url.odoo.com
       4. Try with explicit timeout: odoo get-models --timeout 60
```

#### Error: "Connection timeout after 30 seconds"
```
Cause: Server slow or network latency
Fix:   Increase timeout: odoo get-models --timeout 60
      Or: export ODOO_TIMEOUT=60
      Or: Use smaller queries (reduce data size)
```

**Verify connection:**
```bash
# Test basic connection:
odoo get-models

# Test with longer timeout:
odoo get-models --timeout 60

# Show debug info:
ODOO_DEBUG=1 odoo get-models
```

---

### 5. Permission Errors

#### Error: "Access denied for operation"
```
Cause: User lacks permission for this operation
Fix:   1. Use admin account
       2. Check user roles in Settings > Users
       3. Create a read-only API user for automation
       4. Use sudo: odoo execute --sudo (if available)
```

#### Error: "You are not allowed to modify this field"
```
Cause: Field is read-only or computed
Fix:   Check field properties: odoo get-fields model --field field_name
      Look for "readonly": true in output
```

---

## Error Output Formats

### CLI Mode (Human Readable)
```
✗ Error: Model not found
  Search failed for model "sale_order"
  → Use 'odoo get-models' to list available models
```

### JSON Mode (LLM Friendly)
```json
{
  "success": false,
  "error": "Model not found",
  "error_type": "model",
  "details": "sale_order does not exist",
  "suggestion": "Use 'odoo get-models' to list available models"
}
```

---

## Structured Error Categories

The CLI categorizes errors into types for better handling:

| Error Type | Examples | When It Happens |
|-----------|----------|-----------------|
| `connection` | Cannot reach server, timeout | Network issues, wrong URL |
| `auth` | Invalid credentials, login failed | Wrong username/password |
| `model` | Model not found, not accessible | Wrong model name, permissions |
| `field` | Invalid field, field not found | Wrong field name, permissions |
| `domain` | Domain format error, parsing fails | Malformed domain structure |
| `permission` | Access denied, not authorized | User lacks permissions |
| `data` | Invalid data, constraint violation | Bad data, unique constraint |
| `unknown` | Other errors | Unexpected issues |

---

## Debugging Workflow

### Step 1: Read the Error Type
```
The first line tells you what category of error occurred
"error_type": "domain"  → Domain problem
"error_type": "model"   → Model problem
"error_type": "auth"    → Authentication problem
```

### Step 2: Read the Suggestion
```json
{
  "error": "...",
  "suggestion": "Use 'odoo get-fields sale.order' to see available fields"
}
```

Suggestions often tell you exactly what to do next!

### Step 3: Apply Suggested Fix
```bash
# If suggestion says: "Use 'odoo get-fields sale.order'"
odoo get-fields sale.order

# Then find the right field and retry with correct name
```

### Step 4: Try with Simpler Input
```bash
# If complex query fails:
odoo execute sale.order search --args '[[["date", ">=", "2025-01-01"]]]'

# Try simpler version:
odoo execute sale.order search --args '[[]]'
# If this works, the domain format is the problem
```

---

## Common Mistake Patterns

### Pattern 1: Domain Wrapping
```python
# ❌ WRONG (double-wrapped domain):
self._execute(model, 'search', [domain], **kwargs)

# ✅ CORRECT (domain not wrapped):
self._execute(model, 'search', domain, **kwargs)

# ❌ User mistake:
odoo execute sale.order search --args '[domain]'  # Too many brackets

# ✅ Correct:
odoo execute sale.order search --args 'domain'
```

### Pattern 2: Field Doesn't Exist
```bash
# ❌ Typo or wrong field:
odoo search sale.order '[["date_oder", ">", "2025-01-01"]]'
# Error: Invalid field 'date_oder'

# ✅ Check available fields:
odoo get-fields sale.order --field date

# ✅ Use correct field:
odoo search sale.order '[["date_order", ">", "2025-01-01"]]'
```

### Pattern 3: Model Doesn't Exist
```bash
# ❌ Model name typo:
odoo search sale_order '[]'
# Error: Model sale_order does not exist

# ✅ Check available models:
odoo get-models --filter sale

# ✅ Use correct model:
odoo search sale.order '[]'
```

---

## Best Practices for Error Handling

### 1. Always Check Error Type First
```python
try:
    # Your command
except OdooError as e:
    print(f"Error Type: {e.error_type}")
    # Handle specific error type
```

### 2. Use Suggestions as Hints
```
Error message says: "Use 'odoo get-fields sale.order'"
→ Run that command immediately
→ Look for your field in the output
→ Retry with correct field name
```

### 3. Test with Simpler Queries First
```bash
# If this fails:
odoo search sale.order '[["date_order", ">=", "2025-10-01"], ["state", "=", "sale"]]'

# Try this first:
odoo search sale.order '[]'

# Then add one condition:
odoo search sale.order '[["date_order", ">=", "2025-10-01"]]'

# Then add another:
odoo search sale.order '[["date_order", ">=", "2025-10-01"], ["state", "=", "sale"]]'
```

### 4. Use JSON Mode for Scripting
```python
import json
import subprocess

result = subprocess.run(
    ['odoo', '--json', 'search', 'sale.order', '[]'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
if not data['success']:
    error_type = data['error_type']
    suggestion = data.get('suggestion')
    print(f"Error ({error_type}): {suggestion}")
```

---

## Error Messages for LLM Integration

When an LLM (Claude, GPT, etc.) uses the CLI, structured errors help:

```json
{
  "success": false,
  "error": "Domain format error",
  "error_type": "domain",
  "details": "Domains to normalize must have a list or tuple",
  "suggestion": "Use domain format: [['field', '=', 'value']]"
}
```

The LLM can:
1. **Identify the problem** - `error_type: "domain"`
2. **Understand why** - `details: "...must have a list or tuple"`
3. **Know how to fix it** - `suggestion: "Use domain format: ..."`

---

## Resources

- **Field Names:** `odoo get-fields MODEL_NAME`
- **Model Names:** `odoo get-models` or `odoo get-models --filter PATTERN`
- **Test Connection:** `odoo get-models --timeout 60`
- **Config Check:** `cat .env`

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0 (JSON-RPC)
