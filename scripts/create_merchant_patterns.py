#!/usr/bin/env python3
"""
Create merchant normalization patterns.
Template script for bulk creating merchant patterns.
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


def create_merchant_patterns():
    """Create merchant normalization patterns."""

    print("="*80)
    print("Creating Merchant Normalization Patterns")
    print("="*80)

    # Define patterns to create
    # Format: {pattern, normalized_name, match_type, confidence, description}
    patterns_data = [
        # Supermarkets
        {
            'pattern': 'la torre',
            'normalized_name': 'La Torre',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'La Torre supermarket (all locations)'
        },
        {
            'pattern': 'supermercados la torre',
            'normalized_name': 'La Torre',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'La Torre supermarket (full name)'
        },
        {
            'pattern': 'abarroteria manantial',
            'normalized_name': 'Abarrotería Manantial',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Abarrotería Manantial'
        },

        # Restaurants
        {
            'pattern': 'el josper',
            'normalized_name': 'El Josper',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'El Josper restaurant'
        },
        {
            'pattern': 'le cafe etu',
            'normalized_name': 'Le Café ETU Plaza',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Le Café ETU Plaza'
        },
        {
            'pattern': 'la terminal',
            'normalized_name': 'La Terminal',
            'match_type': 'contains',
            'confidence': 0.90,
            'description': 'La Terminal restaurant'
        },
        {
            'pattern': 'mcdonalds',
            'normalized_name': "McDonald's",
            'match_type': 'contains',
            'confidence': 0.95,
            'description': "McDonald's"
        },

        # Tech & Services
        {
            'pattern': 'google *google one',
            'normalized_name': 'Google One',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Google One subscription'
        },
        {
            'pattern': 'uber *eats',
            'normalized_name': 'Uber Eats',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Uber Eats food delivery'
        },
        {
            'pattern': 'uber *trip',
            'normalized_name': 'Uber',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Uber ride'
        },
        {
            'pattern': 'www.getnomad.app',
            'normalized_name': 'Nomad',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Nomad app'
        },

        # Insurance & Banking
        {
            'pattern': 'seguro fraude',
            'normalized_name': 'Seguro Fraude BI',
            'match_type': 'contains',
            'confidence': 0.95,
            'description': 'Fraud insurance fee'
        },

        # Example regex pattern for Amazon variations
        # {
        #     'pattern': r'amzn?\.?(\s+mktp)?\s+(us|com)',
        #     'normalized_name': 'Amazon',
        #     'match_type': 'regex',
        #     'confidence': 0.95,
        #     'description': 'Amazon (all variations)'
        # },
    ]

    # Create or update patterns
    created_count = 0
    updated_count = 0

    for pattern_data in patterns_data:
        pattern_obj, created = MerchantPattern.objects.get_or_create(
            pattern=pattern_data['pattern'],
            defaults={
                'normalized_name': pattern_data['normalized_name'],
                'match_type': pattern_data['match_type'],
                'confidence': pattern_data['confidence'],
                'is_active': True
            }
        )

        if created:
            print(f"[+] Created pattern: '{pattern_obj.pattern}' -> '{pattern_obj.normalized_name}'")
            print(f"    ({pattern_data['description']})")
            created_count += 1
        else:
            # Update existing pattern
            pattern_obj.normalized_name = pattern_data['normalized_name']
            pattern_obj.match_type = pattern_data['match_type']
            pattern_obj.confidence = pattern_data['confidence']
            pattern_obj.is_active = True
            pattern_obj.save()
            print(f"[+] Updated pattern: '{pattern_obj.pattern}' -> '{pattern_obj.normalized_name}'")
            updated_count += 1

    print("\n" + "="*80)
    print("Summary:")
    print("="*80)
    print(f"  Patterns created: {created_count}")
    print(f"  Patterns updated: {updated_count}")
    print(f"  Total active patterns: {MerchantPattern.objects.filter(is_active=True).count()}")
    print("="*80)
    print("\nNext steps:")
    print("1. Run: python scripts/renormalize_transactions.py")
    print("2. Check results: python scripts/analyze_merchant_patterns.py overview")
    print("3. View merchants: python scripts/analyze_merchant_patterns.py common-merchants")


def create_patterns_from_csv(csv_file):
    """
    Create patterns from CSV file.
    CSV format: pattern,normalized_name,match_type,confidence
    """
    import csv

    print(f"Loading patterns from {csv_file}...")

    created_count = 0
    updated_count = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pattern_obj, created = MerchantPattern.objects.get_or_create(
                pattern=row['pattern'],
                defaults={
                    'normalized_name': row['normalized_name'],
                    'match_type': row.get('match_type', 'contains'),
                    'confidence': float(row.get('confidence', 0.95)),
                    'is_active': True
                }
            )

            if created:
                created_count += 1
                print(f"[+] Created: '{pattern_obj.pattern}' -> '{pattern_obj.normalized_name}'")
            else:
                pattern_obj.normalized_name = row['normalized_name']
                pattern_obj.match_type = row.get('match_type', 'contains')
                pattern_obj.confidence = float(row.get('confidence', 0.95))
                pattern_obj.is_active = True
                pattern_obj.save()
                updated_count += 1
                print(f"[+] Updated: '{pattern_obj.pattern}' -> '{pattern_obj.normalized_name}'")

    print(f"\nCreated: {created_count}, Updated: {updated_count}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create merchant normalization patterns')
    parser.add_argument('--csv', type=str, help='Load patterns from CSV file')

    args = parser.parse_args()

    if args.csv:
        create_patterns_from_csv(args.csv)
    else:
        create_merchant_patterns()
