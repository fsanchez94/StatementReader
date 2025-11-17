#!/usr/bin/env python3
"""
Show transactions that match a specific pattern.
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


def show_pattern_matches(pattern_text, limit=50):
    """Show transactions that would match a pattern."""

    print("="*100)
    print(f"Transactions matching pattern: '{pattern_text}'")
    print("="*100)
    print()

    # Get all transactions
    all_transactions = Transaction.objects.all()

    # Find matches using 'contains' logic (lowercase)
    matches = []
    for txn in all_transactions:
        if pattern_text.lower() in txn.description.lower():
            matches.append(txn)

    print(f"Found {len(matches)} transactions matching '{pattern_text}'")
    print()

    if matches:
        print(f"Showing first {min(limit, len(matches))} matches:")
        print("-"*100)
        print(f"{'Date':<12} {'Description':<70} {'Category':<20}")
        print("-"*100)

        for txn in matches[:limit]:
            desc = txn.description[:68] if len(txn.description) > 68 else txn.description
            category = txn.category.name if txn.category else "Uncategorized"
            print(f"{str(txn.date):<12} {desc:<70} {category:<20}")

        print("-"*100)
        print()

        # Show unique description patterns
        print("Unique description patterns (first 30):")
        print("-"*100)

        unique_descs = {}
        for txn in matches:
            desc_lower = txn.description.lower()[:60]
            if desc_lower not in unique_descs:
                unique_descs[desc_lower] = {
                    'full': txn.description,
                    'count': 0,
                    'category': txn.category.name if txn.category else None
                }
            unique_descs[desc_lower]['count'] += 1

        sorted_descs = sorted(unique_descs.items(), key=lambda x: x[1]['count'], reverse=True)

        for i, (pattern, info) in enumerate(sorted_descs[:30]):
            print(f"{i+1:2d}. [{info['count']:3d}x] {info['full'][:70]}")
            print(f"     Category: {info['category'] or 'Uncategorized'}")

    print()
    print("="*100)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Show transactions matching a pattern')
    parser.add_argument('pattern', type=str, help='Pattern to search for')
    parser.add_argument('--limit', type=int, default=50, help='Max number of matches to show')

    args = parser.parse_args()

    show_pattern_matches(args.pattern, args.limit)
