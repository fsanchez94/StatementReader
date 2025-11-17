#!/usr/bin/env python3
"""
Create user-specified transaction patterns and categories.
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


def create_categories_and_patterns():
    """Create categories and patterns based on user specifications."""

    print("="*80)
    print("Creating Categories and Patterns")
    print("="*80)

    # Define categories to create
    categories_data = [
        {'name': 'Supermarket', 'color': '#4CAF50'},
        {'name': 'Insurance Fee', 'color': '#FF9800'},
        {'name': 'Restaurants', 'color': '#F44336'}
    ]

    # Create or get categories
    categories = {}
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'color': cat_data['color']}
        )
        categories[cat_data['name']] = category
        status = "Created" if created else "Found existing"
        print(f"[+] {status} category: {category.name}")

    print("\n" + "-"*80)
    print("Creating Transaction Patterns")
    print("-"*80)

    # Define patterns to create
    patterns_data = [
        {
            'pattern': 'la torre',
            'category': 'Supermarket',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'La Torre supermarket'
        },
        {
            'pattern': 'seguro fraude',
            'category': 'Insurance Fee',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Fraud insurance fee'
        },
        {
            'pattern': 'el josper de don emi',
            'category': 'Restaurants',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'El Josper restaurant'
        },
        {
            'pattern': 'le cafe etu plaza',
            'category': 'Restaurants',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Le Cafe ETU Plaza'
        },
        {
            'pattern': 'la terminal',
            'category': 'Restaurants',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'La Terminal restaurant'
        },
        {
            'pattern': 'abarroteria manantial',
            'category': 'Supermarket',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Abarroteria Manantial'
        }
    ]

    # Create or update patterns
    created_count = 0
    updated_count = 0

    for pattern_data in patterns_data:
        category = categories[pattern_data['category']]

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
            print(f"[+] Created pattern: '{pattern_obj.pattern}' -> {category.name}")
            print(f"    ({pattern_data['description']})")
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

    print("\n" + "="*80)
    print("Summary:")
    print("="*80)
    print(f"  Categories ready: {len(categories)}")
    print(f"  Patterns created: {created_count}")
    print(f"  Patterns updated: {updated_count}")
    print(f"  Total active patterns: {TransactionPattern.objects.filter(is_active=True).count()}")
    print("="*80)
    print("\nNext steps:")
    print("1. Run: python scripts/recategorize_transactions.py")
    print("2. Check results: python scripts/analyze_transaction_patterns.py overview")


if __name__ == '__main__':
    create_categories_and_patterns()
