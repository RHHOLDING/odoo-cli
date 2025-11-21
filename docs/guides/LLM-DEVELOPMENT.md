# LLM Development Guide for Odoo CLI
**Making the CLI LLM-Friendly and Production-Ready**

---

## Quick Decision Tree: CLI vs Python Scripts

```
User asks for data?
├─ Simple query (< 100 records)?
│  └─ Use CLI command directly ✅
├─ Complex aggregation (sum, avg, group)?
│  └─ Generate temporary Python script 🐍
├─ Large dataset (> 1,000 records)?
│  └─ Use Python script with batching 🐍
└─ One-off analysis?
   └─ Use interactive shell or Python script 🐍
```

---

## When to Generate Python Scripts

The CLI is powerful, but for **aggregation, batching, and complex logic**, generate temporary Python scripts.

### ✅ Generate Python Scripts When:

1. **Aggregating Large Datasets**
   - Summing, averaging, grouping across 1,000+ records
   - Native Odoo `read_group` returns per-record data, not summaries
   - **Example:** October 2025 sales sum (5,991 orders)

2. **Processing in Batches**
   - Reading more than 500 records at once
   - Server might timeout or return incomplete data
   - **Safe batch size:** 500-2,000 records per read

3. **Complex Business Logic**
   - Multiple queries with conditional logic
   - Transforming/enriching data before output
   - **Example:** Match invoices to orders by date range

4. **Analyzing Error Patterns**
   - Testing multiple domain filters to isolate issues
   - Debugging failed operations
   - **Example:** Finding why a specific domain filter fails

### ❌ Don't Generate Scripts For:

- Getting 1-2 pieces of information quickly
- One-off CLI commands
- Data that fits in a table (< 50 rows)
- Simple filters without aggregation

---

## Python Script Template for Aggregation

When an LLM needs to aggregate data, use this template:

```python
#!/usr/bin/env python3
"""
Temporary aggregation script for [TASK DESCRIPTION]
Auto-generated on [DATE]
Delete after use: rm /tmp/[FILENAME].py
"""
import os
import sys
from pathlib import Path

# Add CLI to path (adjust if needed)
sys.path.insert(0, str(Path(__file__).parent.parent / 'odoo-xml-cli'))

from odoo_cli.client import OdooClient

# Initialize client (credentials from environment or .env)
client = OdooClient(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USERNAME'),
    password=os.getenv('ODOO_PASSWORD')
)
client.connect()

print("\n" + "=" * 70)
print("[TASK DESCRIPTION]")
print("=" * 70)

# Step 1: Search for matching records
print("\n[1/3] Searching for records...")
domain = [
    # YOUR DOMAIN HERE
]

record_ids = client.search('YOUR_MODEL', domain=domain)
print(f"✓ Found {len(record_ids)} matching records")

if not record_ids:
    print("⚠ No records found, exiting")
    exit(0)

# Step 2: Read in batches
print(f"\n[2/3] Reading {len(record_ids)} records in batches...")
batch_size = 1000
aggregated_data = []

for i in range(0, len(record_ids), batch_size):
    batch_ids = record_ids[i:i+batch_size]
    records = client.read(
        'YOUR_MODEL',
        ids=batch_ids,
        fields=['field1', 'field2', 'amount_untaxed']
    )
    aggregated_data.extend(records)

    progress = min(i + batch_size, len(record_ids))
    print(f"  Progress: {progress:,} / {len(record_ids):,}")

print(f"✓ Read {len(aggregated_data)} records")

# Step 3: Aggregate/process
print("\n[3/3] Aggregating data...")

# Example: Sum amounts
total = sum(r['amount_untaxed'] for r in aggregated_data)
count = len(aggregated_data)
average = total / count if count > 0 else 0

print(f"\n{'=' * 70}")
print(f"RESULTS:")
print(f"{'=' * 70}")
print(f"Total records:     {count:,}")
print(f"Total amount:      €{total:,.2f}")
print(f"Average amount:    €{average:,.2f}")
print(f"{'=' * 70}\n")

# Optional: Save results
# with open('/tmp/results.csv', 'w') as f:
#     f.write('id,field1,amount\n')
#     for r in aggregated_data:
#         f.write(f"{r['id']},{r['field1']},{r['amount_untaxed']}\n")
```

---

## JSON-RPC Aggregation Options

### Option 1: Client-Side Aggregation (✅ Recommended for most cases)

```python
# Search → Read in batches → Sum in Python
order_ids = client.search('sale.order', domain=domain)
total = 0
for batch in batches(order_ids, 1000):
    orders = client.read('sale.order', batch)
    total += sum(o['amount_untaxed'] for o in orders)
```

**Pros:**
- ✅ Always works (no domain parsing issues)
- ✅ Easy to debug in Python
- ✅ Can handle complex logic
- ✅ Control over batch size

**Cons:**
- ⚠ Network overhead (multiple reads)
- ⚠ Slower for very large datasets

### Option 2: Server-Side Aggregation (read_group)

```python
# Use Odoo's native read_group
result = client.execute('sale.order', 'read_group', domain, [], ['amount_untaxed'])
# Returns: [
#   {'amount_untaxed': 100, '__count': 5, ...},
#   {'amount_untaxed': 200, '__count': 3, ...},
#   ...
# ]
total = sum(r['amount_untaxed'] * r['__count'] for r in result)
```

**Pros:**
- ✅ Server does grouping (faster)
- ✅ Fewer API calls

**Cons:**
- ⚠ Groups by EACH field value (not true aggregation)
- ⚠ More complex to parse results
- ⚠ May not work for all field types

**Verdict:** Client-side aggregation is simpler and more reliable.

---

## Error Messages & Debugging

### Quality of JSON-RPC Errors

The JSON-RPC implementation provides **excellent error messages**:

```
Odoo error: Odoo Server Error: Domains to normalize must have a 'domain' form:
a list or tuple of domain components
```

✅ **What makes this good:**
- Clear what went wrong (domain format issue)
- Explains what Odoo expects ("list or tuple")
- Specific enough to fix (know to use `[...]` not `"string"`)

### Common Errors & Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| `unhashable type: 'list'` | Domain wrapped twice | Remove extra `[...]` wrapper |
| `multiple values for argument` | Kwargs passed as positional | Use `**kwargs` to unpack |
| `has no attribute` | Method doesn't exist | Check `client.execute()` signature |
| `Access denied` | User lacks permissions | Use admin user or check roles |
| `tuple index out of range` | Domain format error | Ensure `[['field', 'op', 'value']]` format |

---

## Best Practices for LLM Scripts

### 1. Always Batch Large Reads

```python
# ❌ WRONG - Will fail on large datasets
all_records = client.read('sale.order', record_ids)

# ✅ CORRECT - Batch in 1000-2000 record chunks
batch_size = 1000
for i in range(0, len(record_ids), batch_size):
    batch = record_ids[i:i+batch_size]
    records = client.read('sale.order', batch)
```

### 2. Use search() + read() Not search_read()

```python
# ❌ LESS FLEXIBLE
results = client.search_read('sale.order', domain, limit=100)

# ✅ MORE FLEXIBLE - Can batch, can process
ids = client.search('sale.order', domain)
for batch in batches(ids, 1000):
    records = client.read('sale.order', batch)
```

### 3. Always Show Progress for Large Operations

```python
for i in range(0, len(ids), batch_size):
    batch = ids[i:i+batch_size]
    process_batch(batch)
    progress = min(i + batch_size, len(ids))
    print(f"Progress: {progress:,} / {len(ids):,}", end='\r')
```

### 4. Validate Domains Before Large Queries

```python
# Test with count first
try:
    count = client.search_count('sale.order', domain)
    if count > 10000:
        print(f"⚠ Warning: {count:,} records will take time")
except Exception as e:
    print(f"✗ Domain error: {e}")
    exit(1)
```

### 5. Clean Up Temp Files

```python
import atexit
import os

temp_file = '/tmp/odoo_script.py'

def cleanup():
    if os.path.exists(temp_file):
        os.remove(temp_file)

atexit.register(cleanup)
```

---

## Example: Real Aggregation Problem

### User Request
"What was the total net sales for October 2025?"

### LLM Decision Tree
1. **Data size?** → 5,991 orders (too large for one read)
2. **Aggregation?** → Need to sum `amount_untaxed`
3. **Solution?** → Generate Python script with batching

### Generated Script

```python
#!/usr/bin/env python3
"""Aggregate October 2025 sales data"""
import os, sys
sys.path.insert(0, '/Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli')
from odoo_cli.client import OdooClient

client = OdooClient(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USERNAME'),
    password=os.getenv('ODOO_PASSWORD')
)
client.connect()

domain = [
    ["date_order", ">=", "2025-10-01"],
    ["date_order", "<", "2025-11-01"]
]

print("Fetching October 2025 orders...")
ids = client.search('sale.order', domain=domain)
print(f"Found {len(ids)} orders")

total_net = 0
for i in range(0, len(ids), 1000):
    batch = ids[i:i+1000]
    orders = client.read('sale.order', ids=batch, fields=['amount_untaxed', 'amount_total'])
    for order in orders:
        total_net += order['amount_untaxed']
    print(f"  Progress: {min(i+1000, len(ids)):,} / {len(ids):,}")

print(f"\n✓ October 2025 Net Total: €{total_net:,.2f}")
```

### Output
```
Fetching October 2025 orders...
Found 5991 orders
  Progress: 1,000 / 5,991
  Progress: 2,000 / 5,991
  Progress: 3,000 / 5,991
  Progress: 4,000 / 5,991
  Progress: 5,000 / 5,991
  Progress: 5,991 / 5,991

✓ October 2025 Net Total: €6,681,527.19
```

---

## Summary: When to Use What

| Task | Tool | Script | Reason |
|------|------|--------|--------|
| Get 1 value | CLI | ❌ | `odoo execute ...` |
| List 10 records | CLI | ❌ | `odoo search ...` |
| **Sum 1,000+ records** | **Python** | **✅** | **Batching needed** |
| **Complex logic** | **Python** | **✅** | **Easier to debug** |
| Quick filter | CLI | ❌ | `odoo search ...` |
| Repeating task | CLI | ❌ | Set up once, reuse |

---

## Checklist for LLM-Generated Scripts

- [ ] Credentials loaded from environment (not hardcoded)
- [ ] Batching implemented (batch_size = 500-2000)
- [ ] Progress shown for large operations
- [ ] Error handling with try/except
- [ ] Domain validated with search_count first
- [ ] Comments explaining the purpose
- [ ] Temp file cleanup on exit
- [ ] CSV/JSON output option for results
- [ ] Proper indentation and formatting
- [ ] Self-deleting instructions in docstring

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0
