#!/usr/bin/env python3
"""
Update specific category patterns from 'exact' to 'contains'.
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


def update_patterns():
    """Update patterns to 'contains' for specific categories."""

    print("="*80)
    print("Updating Pattern Match Types")
    print("="*80)
    print()

    # Categories to update
    categories_to_update = [
        'Restaurantes',
        'Supermercado',
        'Medicinas',
        'Ropa'
    ]

    print(f"Updating patterns in these categories to 'contains':")
    for cat in categories_to_update:
        print(f"  - {cat}")
    print()

    updated_count = 0

    for category_name in categories_to_update:
        patterns = TransactionPattern.objects.filter(
            category__name=category_name,
            match_type='exact'
        )

        count = patterns.count()
        if count > 0:
            print(f"\n{category_name}: Updating {count} patterns")
            for pattern in patterns:
                print(f"  - {pattern.pattern}")
                pattern.match_type = 'contains'
                pattern.save()
                updated_count += 1

    print()
    print("="*80)
    print("Update Complete")
    print("="*80)
    print(f"  Total patterns updated: {updated_count}")
    print("="*80)
    print()


if __name__ == '__main__':
    update_patterns()
