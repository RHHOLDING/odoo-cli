#!/usr/bin/env python3
"""
Example: Aggregating Large Datasets with the Odoo CLI

This script demonstrates best practices for:
- Handling large datasets (5,991+ records)
- Batch processing for performance
- Progress tracking
- Error handling
- Clean code patterns

Usage:
    python3 aggregation_script.py

Requirements:
    - .env file with ODOO_* credentials in parent directory
    - Odoo instance with sales data
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add CLI package to path
cli_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(cli_path))

from odoo_cli.client import OdooClient
from odoo_cli.error_handler import ErrorAnalyzer


def load_credentials() -> Dict[str, str]:
    """Load Odoo credentials from environment or .env file"""
    # Check environment variables first
    url = os.getenv('ODOO_URL')
    db = os.getenv('ODOO_DB')
    username = os.getenv('ODOO_USERNAME')
    password = os.getenv('ODOO_PASSWORD')

    if all([url, db, username, password]):
        return {'url': url, 'db': db, 'username': username, 'password': password}

    # Try loading from .env file
    env_file = Path(__file__).parent.parent.parent.parent / '.env'
    if env_file.exists():
        import sys
        from pathlib import Path
        # Simple .env parser
        for line in env_file.read_text().split('\n'):
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

        return load_credentials()  # Retry

    raise ValueError(
        "Missing ODOO credentials. Please set environment variables:\n"
        "  ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD\n"
        "Or create a .env file in the parent directory"
    )


def create_client() -> OdooClient:
    """Create and connect Odoo client with error handling"""
    creds = load_credentials()

    try:
        client = OdooClient(
            url=creds['url'],
            db=creds['db'],
            username=creds['username'],
            password=creds['password'],
            timeout=60  # Longer timeout for large datasets
        )
        client.connect()
        return client
    except Exception as e:
        error_type, message, suggestion = ErrorAnalyzer.analyze(str(e))
        print(f"\n❌ Connection Error ({error_type}):")
        print(f"   {message}")
        if suggestion:
            print(f"   → {suggestion}")
        sys.exit(1)


def search_records(
    client: OdooClient,
    model: str,
    domain: List,
    show_count: bool = True
) -> List[int]:
    """Search for records with domain and show count"""
    try:
        count = client.search_count(model, domain=domain)

        if show_count:
            print(f"\n📊 Found {count:,} records matching domain")

        if count == 0:
            print("   ⚠ No records found")
            return []

        if count > 10000:
            print("   ⚠ Large dataset - this may take a moment")

        return client.search(model, domain=domain)

    except Exception as e:
        error_type, message, suggestion = ErrorAnalyzer.analyze(str(e))
        print(f"\n❌ Search Error ({error_type}):")
        print(f"   {message}")
        if suggestion:
            print(f"   → {suggestion}")
        sys.exit(1)


def read_in_batches(
    client: OdooClient,
    model: str,
    record_ids: List[int],
    fields: List[str],
    batch_size: int = 1000
) -> List[Dict[str, Any]]:
    """Read records in batches with progress tracking"""
    print(f"\n📖 Reading {len(record_ids):,} records in batches of {batch_size}...")

    all_records = []
    batch_count = (len(record_ids) + batch_size - 1) // batch_size

    for batch_num, i in enumerate(range(0, len(record_ids), batch_size)):
        batch_ids = record_ids[i:i+batch_size]

        try:
            records = client.read(model, ids=batch_ids, fields=fields)
            all_records.extend(records)

            # Show progress
            processed = min(i + batch_size, len(record_ids))
            progress_pct = (processed / len(record_ids)) * 100
            bar_length = 30
            filled = int(bar_length * processed / len(record_ids))
            bar = '█' * filled + '░' * (bar_length - filled)

            print(f"   [{bar}] {progress_pct:5.1f}% ({processed:,}/{len(record_ids):,})", end='\r')

        except Exception as e:
            print(f"\n❌ Error reading batch {batch_num + 1}/{batch_count}:")
            print(f"   {str(e)}")
            sys.exit(1)

    print()  # New line after progress bar
    return all_records


def aggregate_amount_data(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate amount data from records"""
    total_net = 0
    total_gross = 0
    min_net = float('inf')
    max_net = float('-inf')

    for record in records:
        net = record.get('amount_untaxed', 0)
        gross = record.get('amount_total', 0)

        total_net += net
        total_gross += gross
        min_net = min(min_net, net)
        max_net = max(max_net, net)

    count = len(records)
    average_net = total_net / count if count > 0 else 0

    return {
        'total_net': total_net,
        'total_gross': total_gross,
        'total_tax': total_gross - total_net,
        'count': count,
        'average_net': average_net,
        'min_net': min_net if min_net != float('inf') else 0,
        'max_net': max_net if max_net != float('-inf') else 0,
    }


def print_results(results: Dict[str, Any], title: str = "Results"):
    """Print aggregated results in a formatted table"""
    print(f"\n{'=' * 70}")
    print(f"✅ {title}")
    print(f"{'=' * 70}")
    print(f"   Total Records:       {results['count']:,}")
    print(f"   Net Total:           €{results['total_net']:>15,.2f}")
    print(f"   Gross Total:         €{results['total_gross']:>15,.2f}")
    print(f"   Total Tax:           €{results['total_tax']:>15,.2f}")
    print(f"   Average per Record:  €{results['average_net']:>15,.2f}")
    print(f"   Min Amount:          €{results['min_net']:>15,.2f}")
    print(f"   Max Amount:          €{results['max_net']:>15,.2f}")
    print(f"{'=' * 70}\n")


def save_results_to_json(records: List[Dict[str, Any]], filename: str = "/tmp/results.json"):
    """Save records to JSON file for further analysis"""
    with open(filename, 'w') as f:
        json.dump(records, f, indent=2, default=str)
    print(f"📁 Results saved to: {filename}")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("📊 ODOO AGGREGATION SCRIPT - October 2025 Sales Analysis")
    print("=" * 70)

    # Step 1: Connect to Odoo
    print("\n[1/4] Connecting to Odoo...")
    client = create_client()
    print("   ✓ Connected")

    # Step 2: Search for matching records
    print("\n[2/4] Searching for October 2025 sales orders...")
    domain = [
        ["date_order", ">=", "2025-10-01"],
        ["date_order", "<", "2025-11-01"],
    ]
    order_ids = search_records(client, 'sale.order', domain)

    if not order_ids:
        print("No records found, exiting.")
        return

    # Step 3: Read records in batches
    print("\n[3/4] Fetching order details...")
    fields = ['name', 'date_order', 'amount_untaxed', 'amount_total', 'partner_id']
    orders = read_in_batches(client, 'sale.order', order_ids, fields)

    # Step 4: Aggregate and display results
    print("\n[4/4] Aggregating results...")
    results = aggregate_amount_data(orders)
    print_results(results, "October 2025 Sales Summary")

    # Optional: Save to file
    # save_results_to_json(orders)

    print("✨ Done!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
