#!/usr/bin/env python3
"""
Delete all transaction category patterns.
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

from parser_api.models import TransactionPattern


def delete_all_patterns():
    """Delete all transaction category patterns."""

    print("="*80)
    print("Deleting All Transaction Category Patterns")
    print("="*80)

    # Count patterns
    total_patterns = TransactionPattern.objects.count()
    active_patterns = TransactionPattern.objects.filter(is_active=True).count()

    print(f"Total patterns: {total_patterns}")
    print(f"Active patterns: {active_patterns}")
    print()

    if total_patterns == 0:
        print("No patterns to delete.")
        return

    # Show pattern breakdown by category
    print("Patterns by Category:")
    print("-"*80)
    from django.db.models import Count
    patterns_by_category = TransactionPattern.objects.values(
        'category__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    for item in patterns_by_category:
        print(f"  {item['category__name']}: {item['count']} patterns")
    print("-"*80)
    print()

    # Ask for confirmation
    print(f"WARNING: This will permanently delete ALL {total_patterns} transaction patterns.")
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("\nOperation cancelled.")
        return

    print()
    print("Deleting all patterns...")

    # Delete all patterns
    deleted_count, _ = TransactionPattern.objects.all().delete()

    print()
    print("="*80)
    print("Deletion Complete")
    print("="*80)
    print(f"  Patterns deleted: {deleted_count}")
    print(f"  Remaining patterns: {TransactionPattern.objects.count()}")
    print("="*80)
    print()


if __name__ == '__main__':
    delete_all_patterns()
