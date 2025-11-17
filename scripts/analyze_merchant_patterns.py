#!/usr/bin/env python3
"""
Merchant Pattern Analysis Tool
Analyzes merchant normalization patterns and provides insights for improvement.
"""

import os
import sys
import django
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import re

# Setup Django
django_path = Path(__file__).parent.parent / 'backends' / 'django'
sys.path.insert(0, str(django_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_parser_project.settings')
django.setup()

from django.db.models import Count, Q
from parser_api.models import Transaction, MerchantPattern


class MerchantAnalyzer:
    """Analyzes merchant patterns and normalization effectiveness."""

    def __init__(self):
        self.total_transactions = Transaction.objects.count()
        self.normalized = Transaction.objects.filter(merchant_name__isnull=False).exclude(merchant_name='').count()
        self.unnormalized = self.total_transactions - self.normalized

    def print_header(self, title):
        """Print formatted header."""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)

    def print_table_row(self, *columns, widths=None):
        """Print formatted table row."""
        if widths is None:
            widths = [20, 15, 15, 30]

        row = ""
        for col, width in zip(columns, widths):
            row += str(col).ljust(width)
        print(row)

    def overview(self):
        """Display overall normalization statistics."""
        self.print_header("Merchant Normalization Overview")

        print(f"\nTotal Transactions: {self.total_transactions:,}")
        coverage_pct = (self.normalized / self.total_transactions * 100) if self.total_transactions > 0 else 0
        print(f"Normalized: {self.normalized:,} ({coverage_pct:.1f}%)")
        print(f"Not Normalized: {self.unnormalized:,} ({100 - coverage_pct:.1f}%)")

        # Active patterns
        active_patterns = MerchantPattern.objects.filter(is_active=True).count()
        total_patterns = MerchantPattern.objects.count()
        print(f"\nActive Patterns: {active_patterns} / {total_patterns}")

        # Unique merchants
        unique_merchants = Transaction.objects.filter(
            merchant_name__isnull=False
        ).exclude(merchant_name='').values('merchant_name').distinct().count()
        print(f"Unique Normalized Merchants: {unique_merchants}")

        # By bank type
        print("\n" + "-" * 80)
        print("Normalization by Bank Type:")
        print("-" * 80)

        bank_stats = Transaction.objects.values('bank_type').annotate(
            total=Count('id'),
            normalized=Count('id', filter=Q(merchant_name__isnull=False) & ~Q(merchant_name=''))
        ).order_by('-total')

        self.print_table_row("Bank Type", "Total", "Normalized", "Coverage %",
                            widths=[20, 15, 15, 15])
        print("-" * 65)

        for stat in bank_stats:
            bank = stat['bank_type'] or 'Unknown'
            total = stat['total']
            norm = stat['normalized']
            coverage = (norm / total * 100) if total > 0 else 0
            self.print_table_row(bank, total, norm, f"{coverage:.1f}%",
                               widths=[20, 15, 15, 15])

    def top_patterns(self, limit=10):
        """Display most effective merchant patterns."""
        self.print_header(f"Top {limit} Most Effective Patterns")

        patterns = MerchantPattern.objects.filter(is_active=True)
        pattern_stats = []

        for pattern in patterns:
            # Count transactions with this normalized name
            match_count = Transaction.objects.filter(merchant_name=pattern.normalized_name).count()

            if match_count > 0:
                pattern_stats.append({
                    'pattern': pattern.pattern,
                    'normalized_name': pattern.normalized_name,
                    'match_type': pattern.match_type,
                    'count': match_count,
                    'confidence': pattern.confidence
                })

        # Sort by count
        pattern_stats.sort(key=lambda x: x['count'], reverse=True)

        print(f"\n{'Pattern'.ljust(25)} {'Normalized Name'.ljust(20)} {'Type'.ljust(12)} {'Matches'.ljust(10)} Confidence")
        print("-" * 90)

        for stat in pattern_stats[:limit]:
            print(f"{stat['pattern'][:24].ljust(25)} "
                  f"{stat['normalized_name'][:19].ljust(20)} "
                  f"{stat['match_type'][:11].ljust(12)} "
                  f"{stat['count']:>7}    "
                  f"{stat['confidence']:.2f}")

        if not pattern_stats:
            print("No patterns are currently matching any transactions.")

    def common_merchants(self, limit=20):
        """Display most common normalized merchant names."""
        self.print_header(f"Top {limit} Most Common Normalized Merchants")

        merchant_counts = Transaction.objects.filter(
            merchant_name__isnull=False
        ).exclude(merchant_name='').values('merchant_name').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]

        if not merchant_counts:
            print("\nNo normalized merchants found!")
            return

        print(f"\n{'Count'.ljust(8)} {'Normalized Merchant Name'.ljust(50)}")
        print("-" * 60)

        for item in merchant_counts:
            print(f"{item['count']:>5}    {item['merchant_name'][:49]}")

    def unnormalized_analysis(self, limit=20):
        """Analyze most common unnormalized transaction descriptions."""
        self.print_header(f"Top {limit} Most Common Unnormalized Descriptions")

        unnormalized_txns = Transaction.objects.filter(
            Q(merchant_name__isnull=True) | Q(merchant_name='')
        )

        if unnormalized_txns.count() == 0:
            print("\nAll transactions are normalized!")
            return

        # Group by description
        description_counts = Counter()
        description_samples = {}

        for txn in unnormalized_txns:
            desc = txn.description.strip()
            description_counts[desc] += 1
            if desc not in description_samples:
                description_samples[desc] = {
                    'amount': txn.amount,
                    'date': txn.date,
                    'type': txn.transaction_type
                }

        print(f"\n{'Count'.ljust(8)} {'Description'.ljust(60)} {'Sample Amount'.ljust(15)}")
        print("-" * 85)

        for desc, count in description_counts.most_common(limit):
            sample = description_samples[desc]
            amount_str = f"Q{sample['amount']:,.2f}"
            print(f"{count:>5}    {desc[:59].ljust(60)} {amount_str}")

        # Print suggestions
        print("\n" + "-" * 80)
        print("Pattern Suggestions:")
        print("-" * 80)
        self._suggest_patterns_from_descriptions(
            [desc for desc, _ in description_counts.most_common(limit)]
        )

    def merchant_variations(self, limit=15):
        """Find and display merchant name variations that could be normalized."""
        self.print_header(f"Merchant Name Variations (Top {limit})")

        unnormalized_txns = Transaction.objects.filter(
            Q(merchant_name__isnull=True) | Q(merchant_name='')
        )

        # Extract potential merchant names
        merchant_groups = defaultdict(list)

        for txn in unnormalized_txns:
            desc = txn.description.strip()
            # Extract first few words as potential merchant name
            words = desc.split()[:3]
            if words:
                key = ' '.join(words).lower()
                merchant_groups[key].append(desc)

        # Find groups with multiple variations
        variations = []
        for key, descs in merchant_groups.items():
            unique_descs = set(descs)
            if len(unique_descs) > 1:
                variations.append({
                    'key': key,
                    'count': len(descs),
                    'variations': len(unique_descs),
                    'examples': list(unique_descs)[:5]
                })

        # Sort by count
        variations.sort(key=lambda x: x['count'], reverse=True)

        if not variations:
            print("\nNo merchant variations found!")
            return

        print(f"\n{'Base Name'.ljust(30)} {'Total'.ljust(8)} {'Variations'.ljust(12)} Example Descriptions")
        print("-" * 100)

        for var in variations[:limit]:
            print(f"{var['key'][:29].ljust(30)} {var['count']:>5}    {var['variations']:>10}     {var['examples'][0][:50]}")
            for example in var['examples'][1:3]:
                print(f"{''.ljust(53)} {example[:50]}")
            if len(var['examples']) > 3:
                print(f"{''.ljust(53)} ... and {len(var['examples']) - 3} more")
            print()

    def unused_patterns(self):
        """Display patterns that never match any transactions."""
        self.print_header("Unused Patterns")

        patterns = MerchantPattern.objects.filter(is_active=True)
        unused = []

        for pattern in patterns:
            # Check if any transaction has this normalized name
            match_count = Transaction.objects.filter(merchant_name=pattern.normalized_name).count()

            if match_count == 0:
                unused.append(pattern)

        if not unused:
            print("\nAll active patterns are matching at least one transaction!")
            return

        print(f"\n{'Pattern'.ljust(30)} {'Normalized Name'.ljust(30)} {'Match Type'.ljust(15)} Created")
        print("-" * 90)

        for pattern in unused:
            created = pattern.created_at.strftime('%Y-%m-%d')
            print(f"{pattern.pattern[:29].ljust(30)} "
                  f"{pattern.normalized_name[:29].ljust(30)} "
                  f"{pattern.match_type.ljust(15)} "
                  f"{created}")

        print(f"\nFound {len(unused)} unused patterns")

    def test_pattern(self, pattern_text, match_type='contains', show_limit=20):
        """Test a pattern against existing transactions."""
        self.print_header(f"Testing Pattern: '{pattern_text}' ({match_type})")

        matching_txns = []

        for txn in Transaction.objects.all():
            desc_lower = txn.description.lower()
            pattern_lower = pattern_text.lower()
            matched = False

            if match_type == 'exact':
                matched = desc_lower == pattern_lower
            elif match_type == 'contains':
                matched = pattern_lower in desc_lower
            elif match_type == 'starts_with':
                matched = desc_lower.startswith(pattern_lower)
            elif match_type == 'ends_with':
                matched = desc_lower.endswith(pattern_lower)
            elif match_type == 'regex':
                try:
                    matched = bool(re.search(pattern_text, txn.description, re.IGNORECASE))
                except:
                    pass

            if matched:
                matching_txns.append(txn)

        print(f"\nFound {len(matching_txns)} matching transactions:\n")

        if matching_txns:
            print(f"{'Description'.ljust(50)} {'Current Merchant'.ljust(25)} {'Amount'.ljust(12)} Date")
            print("-" * 100)

            for txn in matching_txns[:show_limit]:
                merchant = txn.merchant_name if txn.merchant_name else 'None'
                amount_str = f"Q{txn.amount:,.2f}"
                print(f"{txn.description[:49].ljust(50)} "
                      f"{merchant[:24].ljust(25)} "
                      f"{amount_str.ljust(12)} "
                      f"{txn.date}")

            if len(matching_txns) > show_limit:
                print(f"\n... and {len(matching_txns) - show_limit} more")

            # Show variations
            unique_descriptions = set(txn.description for txn in matching_txns)
            if len(unique_descriptions) > 1:
                print(f"\nUnique description variations: {len(unique_descriptions)}")

    def _suggest_patterns_from_descriptions(self, descriptions):
        """Suggest patterns based on common description elements."""
        suggestions = []

        for desc in descriptions[:10]:
            # Extract merchant-like keywords
            # Remove common banking terms
            desc_clean = re.sub(r'\b(pago|compra|retiro|deposito|transferencia|cargo|abono|applepay|ach)\b',
                               '', desc, flags=re.IGNORECASE).strip()

            # Extract potential merchant name (first 2-3 words)
            words = desc_clean.split()[:3]
            if words:
                main_word = ' '.join(words)
                suggested_name = self._clean_merchant_name(main_word)
                if suggested_name:
                    suggestions.append({
                        'pattern': main_word.lower(),
                        'normalized_name': suggested_name,
                        'description': desc
                    })

        for i, sugg in enumerate(suggestions, 1):
            print(f"{i}. Pattern: '{sugg['pattern']}' → '{sugg['normalized_name']}'")
            print(f"   Example: {sugg['description'][:70]}")
            print()

    def _clean_merchant_name(self, text):
        """Clean and format merchant name."""
        # Remove extra whitespace
        text = ' '.join(text.split())

        # Title case
        text = text.title()

        # Remove trailing backslash and location info
        text = text.split('\\')[0].strip()

        return text if len(text) > 2 else None


def main():
    """Main entry point for the analysis tool."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze merchant normalization patterns')
    parser.add_argument('command', nargs='?', default='overview',
                       choices=['overview', 'top-patterns', 'common-merchants',
                               'unnormalized', 'variations', 'unused-patterns',
                               'test-pattern'],
                       help='Analysis command to run')
    parser.add_argument('--limit', type=int, default=20, help='Number of results to show')
    parser.add_argument('--pattern', type=str, help='Pattern to test')
    parser.add_argument('--match-type', type=str, default='contains',
                       choices=['exact', 'contains', 'starts_with', 'ends_with', 'regex'],
                       help='Pattern match type')

    args = parser.parse_args()

    analyzer = MerchantAnalyzer()

    if args.command == 'overview':
        analyzer.overview()
    elif args.command == 'top-patterns':
        analyzer.top_patterns(limit=args.limit)
    elif args.command == 'common-merchants':
        analyzer.common_merchants(limit=args.limit)
    elif args.command == 'unnormalized':
        analyzer.unnormalized_analysis(limit=args.limit)
    elif args.command == 'variations':
        analyzer.merchant_variations(limit=args.limit)
    elif args.command == 'unused-patterns':
        analyzer.unused_patterns()
    elif args.command == 'test-pattern':
        if not args.pattern:
            print("Error: --pattern required for test-pattern command")
            sys.exit(1)
        analyzer.test_pattern(args.pattern, args.match_type, show_limit=args.limit)

    print("\n")


if __name__ == '__main__':
    main()
