#!/usr/bin/env python3
"""
Show sample transactions with their descriptions and merchant names.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
django_path = Path(__file__).parent.parent / 'backends' / 'django'
sys.path.insert(0, str(django_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_parser_project.settings')
django.setup()

from parser_api.models import Transaction
from collections import defaultdict


def show_samples():
    """Show sample transactions."""

    print("="*80)
    print("Transaction Samples")
    print("="*80)
    print()

    # Get all transactions
    all_transactions = Transaction.objects.all().order_by('-date')[:100]

    print(f"Showing first 50 recent transactions:\n")
    print(f"{'Date':<12} {'Description':<60} {'Merchant':<30} {'Amount':<10}")
    print("-"*120)

    for txn in all_transactions[:50]:
        merchant = txn.merchant_name if txn.merchant_name else ""
        desc = txn.description[:58] if len(txn.description) > 58 else txn.description
        print(f"{str(txn.date):<12} {desc:<60} {merchant:<30} Q{txn.amount:<10.2f}")

    print("\n" + "="*80)
    print()

    # Group by merchant name
    print("Transactions grouped by Merchant Name:")
    print("-"*80)

    merchant_groups = defaultdict(list)
    for txn in Transaction.objects.all():
        if txn.merchant_name:
            merchant_groups[txn.merchant_name].append(txn)

    for merchant, txns in sorted(merchant_groups.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
        print(f"\n{merchant}: {len(txns)} transactions")
        # Show first example
        if txns:
            print(f"  Example: {txns[0].description[:70]}")

    print("\n" + "="*80)
    print()

    # Show most common description patterns
    print("Most Common Description Patterns:")
    print("-"*80)

    desc_patterns = defaultdict(int)
    desc_examples = {}

    for txn in Transaction.objects.all():
        # Get first 40 chars as pattern
        pattern = txn.description.lower()[:40]
        desc_patterns[pattern] += 1
        if pattern not in desc_examples:
            desc_examples[pattern] = txn.description

    for pattern, count in sorted(desc_patterns.items(), key=lambda x: x[1], reverse=True)[:30]:
        full_desc = desc_examples[pattern]
        print(f"\n{count:4d}x: {full_desc[:70]}")

    print("\n" + "="*80)


if __name__ == '__main__':
    show_samples()
