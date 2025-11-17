#!/usr/bin/env python3
"""
Suggest which patterns should be 'exact' vs 'contains'.
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


def suggest_changes():
    """Suggest which patterns should change from exact to contains."""

    print("="*100)
    print("PATTERN MATCH TYPE RECOMMENDATIONS")
    print("="*100)
    print()

    # Keywords that indicate system messages (should stay EXACT)
    system_keywords = [
        'bimovil', 'seguro', 'debito', 'tarjeta', 'membresia',
        'recobro', 'fraude', 'cuota', 'protegida'
    ]

    exact_patterns = TransactionPattern.objects.filter(match_type='exact').order_by('category__name', 'pattern')

    keep_exact = []
    change_to_contains = []

    for p in exact_patterns:
        is_system = any(keyword in p.pattern.lower() for keyword in system_keywords)

        if is_system:
            keep_exact.append(p)
        else:
            change_to_contains.append(p)

    # Show patterns to keep as exact
    print("KEEP AS 'EXACT' (System messages that always appear the same):")
    print("-"*100)
    if keep_exact:
        for p in keep_exact:
            print(f"  [{p.category.name:<20}] {p.pattern}")
    else:
        print("  None")

    print()
    print(f"Total: {len(keep_exact)} patterns")
    print()
    print("="*100)
    print()

    # Show patterns to change to contains
    print("CHANGE TO 'CONTAINS' (Merchant names that appear in longer descriptions):")
    print("-"*100)

    if change_to_contains:
        # Group by category
        by_category = {}
        for p in change_to_contains:
            cat = p.category.name
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(p.pattern)

        for category in sorted(by_category.keys()):
            print(f"\n  {category}:")
            for pattern in sorted(by_category[category]):
                print(f"    - {pattern}")
    else:
        print("  None")

    print()
    print(f"Total: {len(change_to_contains)} patterns")
    print()
    print("="*100)
    print()
    print("SUMMARY:")
    print(f"  Keep as 'exact': {len(keep_exact)}")
    print(f"  Change to 'contains': {len(change_to_contains)}")
    print(f"  Total 'exact' patterns: {exact_patterns.count()}")
    print()


if __name__ == '__main__':
    suggest_changes()
