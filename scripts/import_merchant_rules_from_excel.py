#!/usr/bin/env python3
"""
Import merchant normalization patterns from Excel file.
Reads Excel file with columns: Action, Description, Match Type
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

from parser_api.models import MerchantPattern


def import_from_excel(excel_file, confidence=0.8):
    """
    Import merchant patterns from Excel file.

    Expected columns:
    - Action: "Rename to [Merchant Name]"
    - Description: Transaction description pattern
    - Match Type: exact, contains, starts_with, ends_with, regex
    """

    print("="*80)
    print("Importing Merchant Rules from Excel")
    print("="*80)
    print(f"File: {excel_file}")
    print(f"Confidence level: {confidence}")
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
        return

    # Validate columns
    required_columns = ['Action', 'Description', 'Match Type']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return

    print(f"Columns found: {list(df.columns)}")
    print()

    # Valid match types
    valid_match_types = ['exact', 'contains', 'starts_with', 'ends_with', 'regex']

    # Track statistics
    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    # Process each row
    for idx, row in df.iterrows():
        try:
            # Extract data
            action = str(row['Action']).strip()
            pattern = str(row['Description']).strip()
            match_type = str(row['Match Type']).strip().lower()

            # Skip empty rows
            if pd.isna(row['Action']) or pd.isna(row['Description']):
                skipped_count += 1
                continue

            # Extract normalized name from Action
            # Format: "Rename to [Merchant Name]"
            if action.lower().startswith('rename to '):
                normalized_name = action[10:].strip()  # Remove "Rename to " prefix
            else:
                normalized_name = action  # Use as-is if format is different

            # Validate match type
            if match_type not in valid_match_types:
                errors.append(f"Row {idx+2}: Invalid match type '{match_type}' for pattern '{pattern}'. Using 'contains' instead.")
                match_type = 'contains'

            # Skip if pattern or normalized name is empty
            if not pattern or not normalized_name:
                skipped_count += 1
                errors.append(f"Row {idx+2}: Empty pattern or normalized name. Skipped.")
                continue

            # Create or update pattern
            pattern_obj, created = MerchantPattern.objects.get_or_create(
                pattern=pattern,
                defaults={
                    'normalized_name': normalized_name,
                    'match_type': match_type,
                    'confidence': confidence,
                    'is_active': True
                }
            )

            if created:
                print(f"[+] Created: '{pattern}' -> '{normalized_name}' ({match_type})")
                created_count += 1
            else:
                # Update existing pattern
                old_name = pattern_obj.normalized_name
                pattern_obj.normalized_name = normalized_name
                pattern_obj.match_type = match_type
                pattern_obj.confidence = confidence
                pattern_obj.is_active = True
                pattern_obj.save()

                if old_name != normalized_name:
                    print(f"[*] Updated: '{pattern}' -> '{normalized_name}' (was: '{old_name}') ({match_type})")
                else:
                    print(f"[*] Updated: '{pattern}' -> '{normalized_name}' ({match_type})")
                updated_count += 1

        except Exception as e:
            errors.append(f"Row {idx+2}: Error - {str(e)}")
            skipped_count += 1
            continue

    # Print summary
    print("\n" + "="*80)
    print("Import Summary")
    print("="*80)
    print(f"  Total rows in Excel: {len(df)}")
    print(f"  Patterns created:    {created_count}")
    print(f"  Patterns updated:    {updated_count}")
    print(f"  Rows skipped:        {skipped_count}")
    print(f"  Total active patterns in DB: {MerchantPattern.objects.filter(is_active=True).count()}")
    print("="*80)

    # Print errors if any
    if errors:
        print("\nWarnings/Errors:")
        print("-"*80)
        for error in errors:
            print(f"  {error}")
        print("-"*80)

    # Next steps
    print("\nNext steps:")
    print("1. Renormalize transactions: python scripts/renormalize_transactions.py --force")
    print("2. Check results: python scripts/analyze_merchant_patterns.py overview")
    print("3. View top patterns: python scripts/analyze_merchant_patterns.py top-patterns")
    print()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Import merchant rules from Excel file')
    parser.add_argument(
        '--file',
        type=str,
        default=r'D:\OneDrive\Desktop\CursorAI Projects\pdf_bank_parser\templatesbancos\RuleBook Description Renames.xlsx',
        help='Path to Excel file (default: templatesbancos/RuleBook Description Renames.xlsx)'
    )
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.8,
        help='Confidence level for imported patterns (default: 0.8)'
    )

    args = parser.parse_args()

    import_from_excel(args.file, args.confidence)
