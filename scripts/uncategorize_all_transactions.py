#!/usr/bin/env python3
"""
Uncategorize all transactions - reset all category assignments.
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


def uncategorize_all_transactions():
    """Remove all category assignments from transactions."""

    print("="*80)
    print("Uncategorizing All Transactions")
    print("="*80)

    # Get all transactions
    all_transactions = Transaction.objects.all()
    total_count = all_transactions.count()

    # Count currently categorized
    categorized_count = all_transactions.filter(category__isnull=False).count()
    manually_categorized_count = all_transactions.filter(manually_categorized=True).count()

    print(f"Total transactions: {total_count}")
    print(f"Currently categorized: {categorized_count}")
    print(f"Manually categorized: {manually_categorized_count}")
    print()

    # Ask for confirmation
    if categorized_count > 0:
        print(f"WARNING: This will remove category assignments from {categorized_count} transactions.")
        response = input("Are you sure you want to continue? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            print("\nOperation cancelled.")
            return

    print()
    print("Uncategorizing all transactions...")

    # Update all transactions
    updated_count = 0
    for transaction in all_transactions:
        if transaction.category is not None or transaction.category_confidence > 0:
            transaction.category = None
            transaction.category_confidence = 0.0
            transaction.manually_categorized = False
            transaction.save()
            updated_count += 1

            if updated_count % 100 == 0:
                print(f"  Processed {updated_count}/{categorized_count} transactions...")

    print()
    print("="*80)
    print("Uncategorization Complete")
    print("="*80)
    print(f"  Transactions uncategorized: {updated_count}")
    print(f"  Remaining categorized: {Transaction.objects.filter(category__isnull=False).count()}")
    print("="*80)
    print()
    print("Next steps:")
    print("1. Review your category patterns")
    print("2. Re-categorize when ready: python scripts/recategorize_transactions.py --force")
    print()


if __name__ == '__main__':
    uncategorize_all_transactions()
