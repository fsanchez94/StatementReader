#!/usr/bin/env python3
"""
Re-categorize existing transactions using current patterns.
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

from parser_api.models import Transaction, TransactionPattern
import re


def auto_categorize_transaction(transaction):
    """
    Auto-categorize a transaction based on patterns.
    Matches the logic in backends/django/parser_api/views.py
    """
    if transaction.manually_categorized:
        return False  # Don't override manual categorizations

    patterns = TransactionPattern.objects.filter(is_active=True).order_by('-confidence')
    description_lower = transaction.description.lower()

    for pattern in patterns:
        matched = False

        if pattern.match_type == 'exact':
            matched = description_lower == pattern.pattern.lower()
        elif pattern.match_type == 'contains':
            matched = pattern.pattern.lower() in description_lower
        elif pattern.match_type == 'starts_with':
            matched = description_lower.startswith(pattern.pattern.lower())
        elif pattern.match_type == 'ends_with':
            matched = description_lower.endswith(pattern.pattern.lower())
        elif pattern.match_type == 'regex':
            try:
                matched = bool(re.search(pattern.pattern, transaction.description, re.IGNORECASE))
            except:
                matched = False

        if matched:
            transaction.category = pattern.category
            transaction.category_confidence = pattern.confidence
            transaction.save()
            return True

    return False


def recategorize_all_transactions(force=False):
    """Re-categorize all uncategorized transactions (or all if force=True)."""

    if force:
        transactions = Transaction.objects.filter(manually_categorized=False)
        print(f"Re-categorizing ALL {transactions.count()} auto-categorized transactions...")
    else:
        transactions = Transaction.objects.filter(category__isnull=True)
        print(f"Categorizing {transactions.count()} uncategorized transactions...")

    categorized_count = 0
    failed_count = 0

    for i, txn in enumerate(transactions, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{transactions.count()} transactions...")

        # Clear existing auto-categorization if force
        if force:
            txn.category = None
            txn.category_confidence = 0.0

        if auto_categorize_transaction(txn):
            categorized_count += 1
        else:
            failed_count += 1

    print(f"\n{'='*60}")
    print(f"Re-categorization Complete")
    print(f"{'='*60}")
    print(f"  Successfully categorized: {categorized_count}")
    print(f"  Still uncategorized: {failed_count}")
    print(f"  Total processed: {transactions.count()}")
    print(f"{'='*60}")

    # Show breakdown by category
    from django.db.models import Count
    categories = Transaction.objects.filter(
        category__isnull=False
    ).values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')

    if categories:
        print(f"\nCategory Breakdown:")
        for cat in categories:
            print(f"  {cat['category__name']}: {cat['count']}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Re-categorize transactions')
    parser.add_argument('--force', action='store_true',
                       help='Re-categorize ALL transactions, not just uncategorized')

    args = parser.parse_args()
    recategorize_all_transactions(force=args.force)
