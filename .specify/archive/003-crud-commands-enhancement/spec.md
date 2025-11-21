# Specification: User-Friendly CRUD Commands & Batch Operations

**Spec ID:** 003-crud-commands-enhancement
**Status:** Planning
**Priority:** HIGH (Usability Critical)
**Created:** 2025-11-21
**Parent Spec:** 002-jsonrpc-migration

## Executive Summary

Enhance the Odoo CLI with **user-friendly CRUD commands** (`create`, `update`, `delete`) and **batch operations** to achieve **universal usability**. Current tool is expert-focused with low-level `execute` syntax. Goal: Make CLI accessible to all users with simple field=value syntax, eliminating JSON requirement for common operations.

**Current Maturity:** 70-75% (excellent READ, poor WRITE usability)
**Target Maturity:** 95% (universal tool for all operations)

## Problem Statement

### Current Issues

1. **Poor Write Operation UX:** Creating/updating data requires complex JSON syntax
   ```bash
   # Current (expert-only):
   odoo execute res.partner create --kwargs '{"name":"Test","email":"test@test.com"}'

   # Desired (user-friendly):
   odoo create res.partner --fields name="Test" email="test@test.com"
   ```

2. **No Batch Operations:** Single record at a time, no bulk create/update
   - Inefficient for data migrations
   - No import from JSON/CSV files
   - Manual loops required for multiple records

3. **Limited Aggregation:** No CLI-native GROUP BY, SUM, AVG helpers
   - Requires Python shell for aggregations
   - Not LLM-friendly for complex queries

4. **No Input Validation:** Silent failures on invalid JSON
   - Type mismatches caught too late (on server)
   - No pre-flight field validation
   - Poor error messages for syntax errors

5. **No Relationship Navigation:** Manual resolution of many2one/one2many
   - Verbose multi-step queries
   - No helper for related record access

### Business Impact

- **Reduced adoption** - Only experts can use write operations
- **Time waste** - Complex JSON syntax for simple tasks
- **Error-prone** - No validation before sending to Odoo
- **Limited automation** - Batch operations require external scripts

## Goals

### Primary Goals

1. ✅ Implement user-friendly `create` command with field=value syntax
2. ✅ Implement user-friendly `update` command with field=value syntax
3. ✅ Implement user-friendly `delete` command for single/multiple IDs
4. ✅ Add input validation for field types (pre-flight checks)
5. ✅ Add batch operations (`create-bulk`, `update-bulk`)
6. ✅ Add aggregation helper command (`aggregate`)
7. ✅ Update documentation with cookbook examples

### Success Metrics

- [ ] Create partner in <5 seconds with simple syntax
- [ ] Update 100 records in <10 seconds with batch command
- [ ] Field validation catches 90% of errors before Odoo call
- [ ] Aggregation command returns SUM/AVG/COUNT without shell
- [ ] 95% usability score (vs current 70%)
- [ ] All unit tests passing (new + existing)

## Technical Architecture

### Phase 1: User-Friendly CRUD Commands (High Priority)

#### 1.1 CREATE Command

**File:** `odoo_cli/commands/create.py`

```python
@click.command('create')
@click.argument('model')
@click.option('--fields', '-f', multiple=True, required=True,
              help='Field values as key=value pairs')
@click.option('--json', is_flag=True, help='Output result as JSON')
@click.pass_obj
def create(ctx, model, fields, json):
    """
    Create new record with simple field=value syntax.

    Examples:
        odoo create res.partner --fields name="Test Partner" email="test@test.com"
        odoo create sale.order --fields partner_id=123 date_order="2025-11-21"
        odoo create res.partner -f name="John" -f email="john@test.com" -f phone="+49123"
    """
    # Parse field=value pairs
    field_dict = parse_field_values(fields)

    # Validate field types (optional, with --no-validate flag to skip)
    if not ctx.no_validate:
        validate_fields(ctx.client, model, field_dict)

    # Create record
    record_id = ctx.client.execute(model, 'create', field_dict)

    # Output result
    if json:
        click.echo(json.dumps({'success': True, 'id': record_id}))
    else:
        ctx.console.print(f"[green]✓[/green] Created {model} with ID: {record_id}")
```

**Key Features:**
- Parse `key=value` syntax automatically
- Support multiple `--fields` options or comma-separated
- Type inference: `partner_id=123` → int, `name="Test"` → str, `active=true` → bool
- Optional field validation before sending
- Rich output with success/failure indicators

#### 1.2 UPDATE Command

**File:** `odoo_cli/commands/update.py`

```python
@click.command('update')
@click.argument('model')
@click.argument('ids')  # Comma-separated: "1,2,3"
@click.option('--fields', '-f', multiple=True, required=True,
              help='Field values to update as key=value pairs')
@click.option('--json', is_flag=True, help='Output result as JSON')
@click.pass_obj
def update(ctx, model, ids, fields, json):
    """
    Update existing records with simple field=value syntax.

    Examples:
        odoo update sale.order 123 --fields state="done" note="Completed"
        odoo update res.partner 1,2,3 --fields active=false
        odoo update sale.order 456 -f state="sale" -f date_order="2025-11-21"
    """
    # Parse IDs
    id_list = [int(x.strip()) for x in ids.split(',')]

    # Parse field=value pairs
    field_dict = parse_field_values(fields)

    # Validate field types (optional)
    if not ctx.no_validate:
        validate_fields(ctx.client, model, field_dict)

    # Update records
    success = ctx.client.execute(model, 'write', id_list, field_dict)

    # Output result
    if json:
        click.echo(json.dumps({'success': success, 'updated': len(id_list)}))
    else:
        ctx.console.print(f"[green]✓[/green] Updated {len(id_list)} {model} record(s)")
```

**Key Features:**
- Support single ID or comma-separated multiple IDs
- Same field=value syntax as `create`
- Batch update multiple records at once
- Validation before sending

#### 1.3 DELETE Command

**File:** `odoo_cli/commands/delete.py`

```python
@click.command('delete')
@click.argument('model')
@click.argument('ids')  # Comma-separated: "1,2,3"
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.option('--json', is_flag=True, help='Output result as JSON')
@click.pass_obj
def delete(ctx, model, ids, force, json):
    """
    Delete records by ID(s).

    Examples:
        odoo delete res.partner 456
        odoo delete res.partner 456,457,458
        odoo delete sale.order 123 --force  # Skip confirmation
    """
    # Parse IDs
    id_list = [int(x.strip()) for x in ids.split(',')]

    # Confirm deletion (unless --force)
    if not force and not json:
        if not click.confirm(f"Delete {len(id_list)} {model} record(s)?"):
            ctx.console.print("[yellow]Cancelled[/yellow]")
            return

    # Delete records
    success = ctx.client.execute(model, 'unlink', id_list)

    # Output result
    if json:
        click.echo(json.dumps({'success': success, 'deleted': len(id_list)}))
    else:
        ctx.console.print(f"[green]✓[/green] Deleted {len(id_list)} {model} record(s)")
```

**Key Features:**
- Confirmation prompt for safety (unless `--force`)
- Support multiple IDs
- Clear success/failure output

#### 1.4 Field Parsing Utility

**File:** `odoo_cli/utils/field_parser.py`

```python
def parse_field_values(fields: Tuple[str]) -> Dict[str, Any]:
    """
    Parse field=value pairs into dict with type inference.

    Args:
        fields: Tuple of "key=value" strings

    Returns:
        Dict with parsed values

    Examples:
        >>> parse_field_values(('name="Test"', 'partner_id=123', 'active=true'))
        {'name': 'Test', 'partner_id': 123, 'active': True}
    """
    result = {}

    for field_str in fields:
        if '=' not in field_str:
            raise ValueError(f"Invalid field format: {field_str}. Expected key=value")

        key, value = field_str.split('=', 1)
        key = key.strip()
        value = value.strip()

        # Type inference
        if value.lower() in ('true', 'false'):
            result[key] = value.lower() == 'true'
        elif value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1]  # Remove quotes
        elif value.startswith("'") and value.endswith("'"):
            result[key] = value[1:-1]  # Remove quotes
        elif value.isdigit():
            result[key] = int(value)
        elif is_float(value):
            result[key] = float(value)
        else:
            # Default to string (no quotes needed)
            result[key] = value

    return result


def validate_fields(client: OdooClient, model: str, fields: Dict[str, Any]) -> None:
    """
    Validate field names and types before sending to Odoo.

    Args:
        client: Authenticated OdooClient
        model: Model name
        fields: Field dict to validate

    Raises:
        ValueError: If field doesn't exist or type mismatch
    """
    # Get field definitions from cache
    field_defs = client.fields_get(model)

    for field_name, field_value in fields.items():
        # Check if field exists
        if field_name not in field_defs:
            raise ValueError(
                f"Field '{field_name}' does not exist on model '{model}'. "
                f"Run: odoo get-fields {model}"
            )

        # Check if field is readonly
        field_def = field_defs[field_name]
        if field_def.get('readonly', False):
            raise ValueError(
                f"Field '{field_name}' is readonly on model '{model}'"
            )

        # Type validation (basic)
        field_type = field_def.get('type')
        if field_type == 'integer' and not isinstance(field_value, int):
            raise ValueError(
                f"Field '{field_name}' expects integer, got {type(field_value).__name__}"
            )
        elif field_type == 'boolean' and not isinstance(field_value, bool):
            raise ValueError(
                f"Field '{field_name}' expects boolean, got {type(field_value).__name__}"
            )
```

### Phase 2: Batch Operations (High Priority)

#### 2.1 CREATE-BULK Command

**File:** `odoo_cli/commands/create_bulk.py`

```python
@click.command('create-bulk')
@click.argument('model')
@click.option('--file', '-f', type=click.File('r'), required=True,
              help='JSON file with array of record dicts')
@click.option('--batch-size', type=int, default=100,
              help='Records per batch (default: 100)')
@click.option('--json', is_flag=True, help='Output result as JSON')
@click.pass_obj
def create_bulk(ctx, model, file, batch_size, json):
    """
    Create multiple records from JSON file.

    File format (JSON array):
    [
        {"name": "Partner 1", "email": "p1@test.com"},
        {"name": "Partner 2", "email": "p2@test.com"}
    ]

    Examples:
        odoo create-bulk res.partner --file partners.json
        odoo create-bulk res.partner -f data.json --batch-size 50
    """
    # Load records from file
    records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("File must contain JSON array of records")

    # Process in batches
    created_ids = []
    total = len(records)

    with click.progressbar(length=total, label='Creating records') as bar:
        for i in range(0, total, batch_size):
            batch = records[i:i+batch_size]

            # Create batch (Odoo supports batch create)
            ids = ctx.client.execute(model, 'create', batch)
            created_ids.extend(ids if isinstance(ids, list) else [ids])

            bar.update(len(batch))

    # Output result
    if json:
        click.echo(json.dumps({
            'success': True,
            'created': len(created_ids),
            'ids': created_ids
        }))
    else:
        ctx.console.print(
            f"[green]✓[/green] Created {len(created_ids)} {model} records"
        )
```

#### 2.2 UPDATE-BULK Command

**File:** `odoo_cli/commands/update_bulk.py`

```python
@click.command('update-bulk')
@click.argument('model')
@click.option('--file', '-f', type=click.File('r'), required=True,
              help='JSON file with {id: {...fields...}} mapping')
@click.option('--batch-size', type=int, default=100,
              help='Records per batch (default: 100)')
@click.option('--json', is_flag=True, help='Output result as JSON')
@click.pass_obj
def update_bulk(ctx, model, file, batch_size, json):
    """
    Update multiple records from JSON file.

    File format (JSON object):
    {
        "123": {"name": "Updated Name 1"},
        "124": {"name": "Updated Name 2"}
    }

    Examples:
        odoo update-bulk res.partner --file updates.json
        odoo update-bulk sale.order -f changes.json --batch-size 50
    """
    # Load updates from file
    updates = json.load(file)

    if not isinstance(updates, dict):
        raise ValueError("File must contain JSON object with {id: fields} mapping")

    # Group updates by common fields (for optimization)
    # If all records have same fields, can do single write call
    field_groups = group_by_fields(updates)

    total_updated = 0

    for field_set, records in field_groups.items():
        ids = [int(id_str) for id_str in records.keys()]
        fields = records[list(records.keys())[0]]  # All have same fields

        # Update batch
        ctx.client.execute(model, 'write', ids, fields)
        total_updated += len(ids)

    # Output result
    if json:
        click.echo(json.dumps({'success': True, 'updated': total_updated}))
    else:
        ctx.console.print(
            f"[green]✓[/green] Updated {total_updated} {model} records"
        )
```

### Phase 3: Aggregation Helper (Medium Priority)

#### 3.1 AGGREGATE Command

**File:** `odoo_cli/commands/aggregate.py`

```python
@click.command('aggregate')
@click.argument('model')
@click.argument('domain')
@click.option('--sum', multiple=True, help='Fields to sum')
@click.option('--avg', multiple=True, help='Fields to average')
@click.option('--count', is_flag=True, help='Count records')
@click.option('--group-by', help='Field to group by')
@click.option('--batch-size', type=int, default=1000,
              help='Records per batch (default: 1000)')
@click.option('--json', is_flag=True, help='Output result as JSON')
@click.pass_obj
def aggregate(ctx, model, domain, sum, avg, count, group_by, batch_size, json):
    """
    Aggregate data with SUM, AVG, COUNT operations.

    Performs client-side aggregation with batching for reliability.

    Examples:
        # Sum total sales for October 2025
        odoo aggregate sale.order '[["date_order",">=","2025-10-01"]]' --sum amount_total

        # Average order value by partner
        odoo aggregate sale.order '[]' --avg amount_total --group-by partner_id

        # Count orders by state
        odoo aggregate sale.order '[]' --count --group-by state
    """
    import ast
    from collections import defaultdict

    # Parse domain
    domain = ast.literal_eval(domain)

    # Get all record IDs
    all_ids = ctx.client.search(model, domain)

    if not all_ids:
        result = {'count': 0, 'sum': {}, 'avg': {}}
        if json:
            click.echo(json.dumps(result))
        else:
            ctx.console.print("[yellow]No records found[/yellow]")
        return

    # Determine fields to retrieve
    fields_to_read = list(sum) + list(avg)
    if group_by:
        fields_to_read.append(group_by)

    # Read in batches
    aggregations = defaultdict(lambda: {'count': 0, 'sum': {}, 'values': {}})

    with click.progressbar(length=len(all_ids), label='Processing records') as bar:
        for i in range(0, len(all_ids), batch_size):
            batch_ids = all_ids[i:i+batch_size]
            records = ctx.client.read(model, batch_ids, fields_to_read)

            for record in records:
                # Determine group key
                if group_by:
                    group_key = record.get(group_by)
                    if isinstance(group_key, (list, tuple)):
                        group_key = group_key[0]  # many2one
                else:
                    group_key = 'all'

                # Aggregate
                aggregations[group_key]['count'] += 1

                for field in sum:
                    value = record.get(field, 0)
                    aggregations[group_key]['sum'][field] = \
                        aggregations[group_key]['sum'].get(field, 0) + value

                for field in avg:
                    if field not in aggregations[group_key]['values']:
                        aggregations[group_key]['values'][field] = []
                    aggregations[group_key]['values'][field].append(
                        record.get(field, 0)
                    )

            bar.update(len(batch_ids))

    # Calculate averages
    for group_key in aggregations:
        aggregations[group_key]['avg'] = {}
        for field in avg:
            values = aggregations[group_key]['values'][field]
            aggregations[group_key]['avg'][field] = \
                sum(values) / len(values) if values else 0
        # Remove raw values from output
        del aggregations[group_key]['values']

    # Output result
    if json:
        click.echo(json.dumps(dict(aggregations), indent=2))
    else:
        from rich.table import Table

        table = Table(title=f"Aggregation Results: {model}")

        if group_by:
            table.add_column(f"Group ({group_by})", style="cyan")
        table.add_column("Count", style="green")

        for field in sum:
            table.add_column(f"Sum({field})", style="yellow")

        for field in avg:
            table.add_column(f"Avg({field})", style="magenta")

        for group_key, data in aggregations.items():
            row = []
            if group_by:
                row.append(str(group_key))
            row.append(str(data['count']))

            for field in sum:
                row.append(f"{data['sum'][field]:,.2f}")

            for field in avg:
                row.append(f"{data['avg'][field]:,.2f}")

            table.add_row(*row)

        ctx.console.print(table)
```

### Phase 4: Input Validation (Medium Priority)

Already covered in Phase 1 with `validate_fields()` function.

**Additional improvements:**
- Add `--no-validate` flag to skip validation (for speed)
- Cache field definitions for validation
- Provide helpful error messages with suggestions
- Support required field detection

## Implementation Plan

### Task Breakdown

#### Phase 1: CRUD Commands (Days 1-2)
- T001: Create `odoo_cli/utils/field_parser.py` with parsing logic
- T002: Create `odoo_cli/commands/create.py` command
- T003: Create `odoo_cli/commands/update.py` command
- T004: Create `odoo_cli/commands/delete.py` command
- T005: Register new commands in `cli.py`
- T006: Add unit tests for field parsing
- T007: Add unit tests for CRUD commands
- T008: Manual testing on real Odoo instance

#### Phase 2: Batch Operations (Days 3-4)
- T009: Create `odoo_cli/commands/create_bulk.py` command
- T010: Create `odoo_cli/commands/update_bulk.py` command
- T011: Add utility function `group_by_fields()` for optimization
- T012: Register bulk commands in `cli.py`
- T013: Add unit tests for bulk operations
- T014: Performance testing (1000+ records)

#### Phase 3: Aggregation Helper (Day 5)
- T015: Create `odoo_cli/commands/aggregate.py` command
- T016: Add progress bars for long-running aggregations
- T017: Register aggregate command in `cli.py`
- T018: Add unit tests for aggregation logic
- T019: Test with October 2025 sales query

#### Phase 4: Documentation (Day 6)
- T020: Update README.md with CRUD examples
- T021: Update docs/guides/LLM-DEVELOPMENT.md
- T022: Create docs/examples/crud_operations.md cookbook
- T023: Update docs/examples/batch_operations.py
- T024: Update CHANGELOG.md
- T025: Update --llm-help JSON structure

#### Phase 5: Testing & Release (Day 7)
- T026: Full integration testing
- T027: Update all unit tests
- T028: CI/CD pipeline testing
- T029: Create GitHub release notes
- T030: Version bump to v1.1.0

## Testing Strategy

### Unit Tests

**New test files:**
- `tests/unit/test_field_parser.py` - Field parsing logic
- `tests/unit/test_commands_create.py` - CREATE command
- `tests/unit/test_commands_update.py` - UPDATE command
- `tests/unit/test_commands_delete.py` - DELETE command
- `tests/unit/test_commands_create_bulk.py` - Bulk create
- `tests/unit/test_commands_update_bulk.py` - Bulk update
- `tests/unit/test_commands_aggregate.py` - Aggregation

**Test coverage goals:**
- Field parser: 100%
- CRUD commands: 90%
- Batch operations: 85%
- Aggregation: 80%

### Integration Tests

**Test scenarios:**
1. Create partner with various field types
2. Update multiple orders at once
3. Delete records with confirmation
4. Bulk create 100+ partners
5. Aggregate October 2025 sales
6. Validation catches invalid fields

### Performance Tests

**Benchmarks:**
- CREATE: <500ms per record
- UPDATE: <500ms per record
- CREATE-BULK: <10s for 100 records
- AGGREGATE: <30s for 5000 records

## Documentation Updates

### Files to Update

1. **README.md** - Add CRUD command examples
2. **docs/guides/LLM-DEVELOPMENT.md** - Update decision tree
3. **docs/examples/** - Add CRUD cookbook
4. **CHANGELOG.md** - Document new features
5. **odoo_cli/help.py** - Update --llm-help JSON

### Example Documentation

```markdown
## Creating Records

Simple field=value syntax:

```bash
# Create partner
odoo create res.partner --fields name="Test Partner" email="test@test.com"

# Create sale order
odoo create sale.order --fields partner_id=123 date_order="2025-11-21"
```

## Updating Records

```bash
# Update single record
odoo update sale.order 123 --fields state="done"

# Update multiple records
odoo update res.partner 1,2,3 --fields active=false
```

## Batch Operations

```bash
# Create 100 partners from JSON
odoo create-bulk res.partner --file partners.json

# Update multiple orders
odoo update-bulk sale.order --file updates.json
```

## Aggregations

```bash
# Sum October 2025 sales
odoo aggregate sale.order '[["date_order",">=","2025-10-01"]]' --sum amount_total

# Count orders by state
odoo aggregate sale.order '[]' --count --group-by state
```
```

## Dependencies

**New Python packages:**
- No new dependencies (using existing `click`, `rich`, `requests`)

**Optional enhancements:**
- `tabulate` - Better table formatting for aggregations (optional)
- `tqdm` - Alternative progress bars (optional, `rich` already provides)

## Success Criteria

### Functional Requirements
- ✅ CREATE command works with field=value syntax
- ✅ UPDATE command works with single/multiple IDs
- ✅ DELETE command with confirmation prompt
- ✅ Bulk operations handle 100+ records
- ✅ Aggregation returns correct SUM/AVG/COUNT
- ✅ Field validation catches errors before Odoo

### Non-Functional Requirements
- ✅ Performance: CREATE <500ms, BULK <10s/100 records
- ✅ Usability: 95% user satisfaction (from 70%)
- ✅ Compatibility: Works on Odoo v14-17
- ✅ Documentation: Complete cookbook with examples
- ✅ Testing: 90% code coverage

### Release Criteria
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ Performance benchmarks met
- ✅ Documentation complete
- ✅ CHANGELOG updated
- ✅ Version bumped to v1.1.0

## Risks & Mitigations

### Risk 1: Type Inference Errors
**Mitigation:** Provide `--no-validate` flag to skip validation

### Risk 2: Bulk Operation Timeouts
**Mitigation:** Configurable batch size, progress tracking

### Risk 3: Breaking Changes
**Mitigation:** Existing `execute` command still works, new commands are additive

### Risk 4: Field Validation Performance
**Mitigation:** Cache field definitions, make validation optional

## Rollout Plan

### Phase 1: Alpha Release (Internal Testing)
- Deploy to dev environment
- Test with 10 common operations
- Gather feedback from team

### Phase 2: Beta Release (Selected Users)
- Release v1.1.0-beta
- Document in CHANGELOG
- Collect bug reports

### Phase 3: Stable Release
- Release v1.1.0 stable
- Update documentation
- Announce on GitHub

## Appendix

### Example Use Cases

**Use Case 1: Create 100 Partners**
```bash
# Generate JSON file
cat > partners.json << EOF
[
  {"name": "Partner 1", "email": "p1@test.com"},
  {"name": "Partner 2", "email": "p2@test.com"},
  ...
]
EOF

# Bulk create
odoo create-bulk res.partner --file partners.json
```

**Use Case 2: Update Order States**
```bash
# Update multiple orders to "done"
odoo update sale.order 123,124,125 --fields state="done"
```

**Use Case 3: Calculate Q4 Revenue**
```bash
# Sum all sales for Q4 2025
odoo aggregate sale.order '[["date_order",">=","2025-10-01"],["date_order","<","2026-01-01"]]' --sum amount_total
```

### Related Specifications

- **001-cli-implementation** - Original CLI implementation
- **002-jsonrpc-migration** - JSON-RPC performance improvements
- **004-relationship-navigation** (Future) - Helper for many2one/one2many traversal
