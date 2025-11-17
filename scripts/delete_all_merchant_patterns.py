#!/usr/bin/env python3
"""
Delete all merchant normalization patterns.
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

from parser_api.models import MerchantPattern


def delete_all_patterns():
    """Delete all merchant patterns."""

    print("="*80)
    print("Deleting All Merchant Patterns")
    print("="*80)

    total_patterns = MerchantPattern.objects.count()
    active_patterns = MerchantPattern.objects.filter(is_active=True).count()

    print(f"Total patterns: {total_patterns}")
    print(f"Active patterns: {active_patterns}")
    print()

    if total_patterns == 0:
        print("No patterns to delete.")
        return

    # Ask for confirmation
    print(f"WARNING: This will permanently delete ALL {total_patterns} merchant patterns.")
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("\nOperation cancelled.")
        return

    print()
    print("Deleting all patterns...")

    # Delete all patterns
    deleted_count, _ = MerchantPattern.objects.all().delete()

    print()
    print("="*80)
    print("Deletion Complete")
    print("="*80)
    print(f"  Patterns deleted: {deleted_count}")
    print(f"  Remaining patterns: {MerchantPattern.objects.count()}")
    print("="*80)
    print()


if __name__ == '__main__':
    delete_all_patterns()
