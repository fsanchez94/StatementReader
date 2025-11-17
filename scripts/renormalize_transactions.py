#!/usr/bin/env python3
"""
Re-normalize existing transactions using current merchant patterns.
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

from parser_api.models import Transaction, MerchantPattern
from django.db.models import Q
import re


def auto_normalize_merchant(transaction):
    """
    Auto-normalize a merchant name based on patterns.
    Matches the logic in backends/django/parser_api/views.py
    """
    description = transaction.description.lower()

    # Get patterns ordered by confidence (highest first)
    patterns = MerchantPattern.objects.filter(is_active=True).order_by('-confidence')

    for pattern in patterns:
        pattern_text = pattern.pattern.lower()
        matched = False

        if pattern.match_type == 'exact':
            matched = description == pattern_text
        elif pattern.match_type == 'contains':
            matched = pattern_text in description
        elif pattern.match_type == 'starts_with':
            matched = description.startswith(pattern_text)
        elif pattern.match_type == 'ends_with':
            matched = description.endswith(pattern_text)
        elif pattern.match_type == 'regex':
            try:
                matched = bool(re.search(pattern.pattern, transaction.description, re.IGNORECASE))
            except:
                matched = False

        if matched:
            transaction.merchant_name = pattern.normalized_name
            transaction.save()
            return True

    return False


def renormalize_all_transactions(force=False):
    """Re-normalize all unnormalized transactions (or all if force=True)."""

    if force:
        transactions = Transaction.objects.all()
        print(f"Re-normalizing ALL {transactions.count()} transactions...")
    else:
        transactions = Transaction.objects.filter(
            Q(merchant_name__isnull=True) | Q(merchant_name='')
        )
        print(f"Normalizing {transactions.count()} unnormalized transactions...")

    normalized_count = 0
    failed_count = 0

    for i, txn in enumerate(transactions, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{transactions.count()} transactions...")

        # Clear existing normalization if force
        if force:
            txn.merchant_name = None

        if auto_normalize_merchant(txn):
            normalized_count += 1
        else:
            failed_count += 1

    print(f"\n{'='*60}")
    print(f"Re-normalization Complete")
    print(f"{'='*60}")
    print(f"  Successfully normalized: {normalized_count}")
    print(f"  Still unnormalized: {failed_count}")
    print(f"  Total processed: {transactions.count()}")
    print(f"{'='*60}")

    # Show breakdown by merchant
    from django.db.models import Count
    merchants = Transaction.objects.filter(
        merchant_name__isnull=False
    ).exclude(merchant_name='').values('merchant_name').annotate(
        count=Count('id')
    ).order_by('-count')[:20]

    if merchants:
        print(f"\nTop 20 Normalized Merchants:")
        for merchant in merchants:
            print(f"  {merchant['merchant_name']}: {merchant['count']}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Re-normalize merchant names in transactions')
    parser.add_argument('--force', action='store_true',
                       help='Re-normalize ALL transactions, not just unnormalized')

    args = parser.parse_args()
    renormalize_all_transactions(force=args.force)
