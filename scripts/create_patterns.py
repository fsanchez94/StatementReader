#!/usr/bin/env python3
"""
Create transaction patterns and categories.
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

from parser_api.models import Category, TransactionPattern


def create_uncategorized_patterns():
    """Create patterns for uncategorized banking transactions."""

    # Get or create the "Uncategorized" category
    category, created = Category.objects.get_or_create(
        name="Uncategorized",
        defaults={
            'color': '#CCCCCC'
        }
    )

    if created:
        print(f"[+] Created category: {category.name}")
    else:
        print(f"[+] Found existing category: {category.name}")

    # Define patterns to create
    patterns_to_create = [
        {
            'pattern': 'banca movil',
            'match_type': 'contains',
            'confidence': 0.9,
            'description': 'Mobile banking transactions'
        },
        {
            'pattern': 'pago por internet ach',
            'match_type': 'contains',
            'confidence': 0.9,
            'description': 'ACH internet payments'
        }
    ]

    # Create or update patterns
    created_count = 0
    updated_count = 0

    for pattern_data in patterns_to_create:
        pattern_obj, created = TransactionPattern.objects.get_or_create(
            pattern=pattern_data['pattern'],
            defaults={
                'category': category,
                'match_type': pattern_data['match_type'],
                'confidence': pattern_data['confidence'],
                'is_active': True
            }
        )

        if created:
            print(f"[+] Created pattern: '{pattern_obj.pattern}' -> {category.name} ({pattern_data['description']})")
            created_count += 1
        else:
            # Update existing pattern
            pattern_obj.category = category
            pattern_obj.match_type = pattern_data['match_type']
            pattern_obj.confidence = pattern_data['confidence']
            pattern_obj.is_active = True
            pattern_obj.save()
            print(f"[+] Updated pattern: '{pattern_obj.pattern}' -> {category.name}")
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Category: {category.name}")
    print(f"  Patterns created: {created_count}")
    print(f"  Patterns updated: {updated_count}")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"1. Re-process existing transactions to apply new patterns")
    print(f"2. Run: python scripts/analyze_transaction_patterns.py overview")
    print(f"3. Check categorization coverage improvement")


if __name__ == '__main__':
    create_uncategorized_patterns()
