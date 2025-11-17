#!/usr/bin/env python3
"""
Import transaction category patterns from Excel file.
Reads Excel file with columns: Description, Match Type, Category Name
"""

import os
import sys
import django
from pathlib import Path
import pandas as pd

# Setup Django
django_path = Path(__file__).parent.parent / 'backends' / 'django'
sys.path.insert(0, str(django_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_parser_project.settings')
django.setup()

from parser_api.models import Category, TransactionPattern


def import_from_excel(excel_file, confidence=0.8, auto_create_categories=True):
    """
    Import transaction category patterns from Excel file.

    Expected columns:
    - Description: Transaction description pattern to match
    - Match Type: exact, contains, starts_with, ends_with, regex
    - Category Name: Name of the category to assign
    """

    print("="*80)
    print("Importing Transaction Category Patterns from Excel")
    print("="*80)
    print(f"File: {excel_file}")
    print(f"Confidence level: {confidence}")
    print(f"Auto-create categories: {auto_create_categories}")
    print()

    # Validate file exists
    if not os.path.exists(excel_file):
        print(f"ERROR: File not found: {excel_file}")
        return

    # Read Excel file
    try:
        df = pd.read_excel(excel_file)
        print(f"Loaded {len(df)} rows from Excel")
    except Exception as e:
        print(f"ERROR reading Excel file: {e}")
        print("\nPlease make sure the Excel file is closed and try again.")
        return

    # Validate columns - support both 'Category Name' and 'Category'
    required_base_columns = ['Description', 'Match Type']
    category_column = None

    if 'Category Name' in df.columns:
        category_column = 'Category Name'
        required_columns = required_base_columns + ['Category Name']
    elif 'Category' in df.columns:
        category_column = 'Category'
        required_columns = required_base_columns + ['Category']
    else:
        print(f"ERROR: Missing category column. Expected 'Category Name' or 'Category'")
        print(f"Available columns: {list(df.columns)}")
        return

    missing_columns = [col for col in required_base_columns if col not in df.columns]

    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return

    print(f"Columns found: {list(df.columns)}")
    print(f"Using category column: '{category_column}'")
    print()

    # Valid match types
    valid_match_types = ['exact', 'contains', 'starts_with', 'ends_with', 'regex']

    # Track statistics
    categories_created = 0
    categories_found = 0
    patterns_created = 0
    patterns_updated = 0
    skipped_count = 0
    errors = []

    # Get existing categories for quick lookup
    existing_categories = {cat.name: cat for cat in Category.objects.all()}
    print(f"Found {len(existing_categories)} existing categories in database")
    print()

    # Process each row
    for idx, row in df.iterrows():
        try:
            # Extract data
            pattern = str(row['Description']).strip()
            match_type = str(row['Match Type']).strip().lower()
            category_name = str(row[category_column]).strip()

            # Skip empty rows
            if pd.isna(row['Description']) or pd.isna(row[category_column]):
                skipped_count += 1
                continue

            # Skip if pattern is empty
            if not pattern or pattern == 'nan':
                skipped_count += 1
                errors.append(f"Row {idx+2}: Empty pattern. Skipped.")
                continue

            # Validate match type
            if match_type not in valid_match_types:
                errors.append(f"Row {idx+2}: Invalid match type '{match_type}' for pattern '{pattern}'. Using 'contains' instead.")
                match_type = 'contains'

            # Get or create category
            if category_name in existing_categories:
                category = existing_categories[category_name]
                categories_found += 1
            else:
                if auto_create_categories:
                    # Auto-create new category
                    category = Category.objects.create(
                        name=category_name,
                        color='#808080'  # Default gray color
                    )
                    existing_categories[category_name] = category
                    categories_created += 1
                    print(f"[+] Created new category: '{category_name}'")
                else:
                    skipped_count += 1
                    errors.append(f"Row {idx+2}: Category '{category_name}' not found. Pattern '{pattern}' skipped.")
                    continue

            # Create or update pattern
            # Check if pattern already exists with same category
            existing_pattern = TransactionPattern.objects.filter(
                pattern=pattern,
                category=category
            ).first()

            if existing_pattern:
                # Update existing pattern
                existing_pattern.match_type = match_type
                existing_pattern.confidence = confidence
                existing_pattern.is_active = True
                existing_pattern.save()
                print(f"[*] Updated: '{pattern}' -> {category_name} ({match_type})")
                patterns_updated += 1
            else:
                # Check if pattern exists with different category
                other_pattern = TransactionPattern.objects.filter(pattern=pattern).first()
                if other_pattern:
                    # Update category
                    old_category = other_pattern.category.name
                    other_pattern.category = category
                    other_pattern.match_type = match_type
                    other_pattern.confidence = confidence
                    other_pattern.is_active = True
                    other_pattern.save()
                    print(f"[*] Updated: '{pattern}' -> {category_name} (was: {old_category}) ({match_type})")
                    patterns_updated += 1
                else:
                    # Create new pattern
                    TransactionPattern.objects.create(
                        pattern=pattern,
                        category=category,
                        match_type=match_type,
                        confidence=confidence,
                        is_active=True,
                        created_by_learning=False
                    )
                    print(f"[+] Created: '{pattern}' -> {category_name} ({match_type})")
                    patterns_created += 1

        except Exception as e:
            errors.append(f"Row {idx+2}: Error - {str(e)}")
            skipped_count += 1
            continue

    # Print summary
    print("\n" + "="*80)
    print("Import Summary")
    print("="*80)
    print(f"  Total rows in Excel:     {len(df)}")
    print(f"  Categories created:      {categories_created}")
    print(f"  Categories found:        {categories_found}")
    print(f"  Patterns created:        {patterns_created}")
    print(f"  Patterns updated:        {patterns_updated}")
    print(f"  Rows skipped:            {skipped_count}")
    print(f"  Total active patterns:   {TransactionPattern.objects.filter(is_active=True).count()}")
    print(f"  Total categories:        {Category.objects.count()}")
    print("="*80)

    # Print errors if any
    if errors:
        print("\nWarnings/Errors:")
        print("-"*80)
        for error in errors[:20]:  # Limit to first 20 errors
            print(f"  {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
        print("-"*80)

    # Show category breakdown
    print("\nCategories with Pattern Count:")
    print("-"*80)
    categories = Category.objects.all()
    for cat in categories:
        pattern_count = TransactionPattern.objects.filter(category=cat, is_active=True).count()
        if pattern_count > 0:
            print(f"  {cat.name}: {pattern_count} patterns")
    print("-"*80)

    # Next steps
    print("\nNext steps:")
    print("1. Recategorize transactions: python scripts/recategorize_transactions.py --force")
    print("2. Check results: python scripts/analyze_transaction_patterns.py overview")
    print("3. View top patterns: python scripts/analyze_transaction_patterns.py top-patterns")
    print()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Import transaction category patterns from Excel file')
    parser.add_argument(
        '--file',
        type=str,
        default=r'D:\OneDrive\Desktop\CursorAI Projects\pdf_bank_parser\templatesbancos\RuleBook Description Categorize.xlsx',
        help='Path to Excel file (default: templatesbancos/RuleBook Description Categorize.xlsx)'
    )
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.8,
        help='Confidence level for imported patterns (default: 0.8)'
    )
    parser.add_argument(
        '--no-auto-create',
        action='store_true',
        help='Disable auto-creation of categories (skip patterns with non-existent categories)'
    )

    args = parser.parse_args()

    import_from_excel(args.file, args.confidence, not args.no_auto_create)
