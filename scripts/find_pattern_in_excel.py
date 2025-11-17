#!/usr/bin/env python3
"""Find a pattern in the Excel file and show its row number."""

import pandas as pd
import sys

excel_file = r'D:\OneDrive\Desktop\CursorAI Projects\pdf_bank_parser\templatesbancos\RuleBook Description Categorize.xlsx'

if len(sys.argv) < 2:
    print("Usage: python find_pattern_in_excel.py <pattern>")
    sys.exit(1)

search_pattern = sys.argv[1].lower()

try:
    df = pd.read_excel(excel_file)

    print(f"Searching for pattern: '{search_pattern}'")
    print("="*100)

    found = False
    for idx, row in df.iterrows():
        desc = str(row['Description']).lower()
        if search_pattern in desc:
            print(f"\nRow {idx + 2} (Excel row including header):")
            print(f"  Description: {row['Description']}")
            print(f"  Match Type: {row['Match Type']}")
            print(f"  Category: {row['Category']}")
            found = True

    if not found:
        print(f"\nPattern '{search_pattern}' not found in Excel file.")

    print()

except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure the Excel file is closed.")
