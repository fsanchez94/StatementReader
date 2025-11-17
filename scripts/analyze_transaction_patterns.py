#!/usr/bin/env python3
"""
Transaction Pattern Analysis Tool
Analyzes transaction categorization patterns and provides insights for improvement.
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

from django.db.models import Count, Avg, Q
from parser_api.models import Transaction, TransactionPattern, Category


class PatternAnalyzer:
    """Analyzes transaction patterns and categorization effectiveness."""

    def __init__(self):
        self.total_transactions = Transaction.objects.count()
        self.categorized = Transaction.objects.filter(category__isnull=False).count()
        self.uncategorized = Transaction.objects.filter(category__isnull=True).count()

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
        """Display overall categorization statistics."""
        self.print_header("Transaction Categorization Overview")

        print(f"\nTotal Transactions: {self.total_transactions:,}")
        print(f"Categorized: {self.categorized:,} ({self.categorized/self.total_transactions*100:.1f}%)" if self.total_transactions > 0 else "Categorized: 0")
        print(f"Uncategorized: {self.uncategorized:,} ({self.uncategorized/self.total_transactions*100:.1f}%)" if self.total_transactions > 0 else "Uncategorized: 0")

        # Auto vs Manual categorization
        auto_categorized = Transaction.objects.filter(
            category__isnull=False,
            manually_categorized=False
        ).count()
        manually_categorized = Transaction.objects.filter(
            manually_categorized=True
        ).count()

        print(f"\nAuto-categorized: {auto_categorized:,}")
        print(f"Manually categorized: {manually_categorized:,}")

        # Average confidence
        avg_confidence = Transaction.objects.filter(
            category__isnull=False
        ).aggregate(Avg('category_confidence'))['category_confidence__avg']

        if avg_confidence:
            print(f"Average Confidence: {avg_confidence:.2f}")

        # Active patterns
        active_patterns = TransactionPattern.objects.filter(is_active=True).count()
        total_patterns = TransactionPattern.objects.count()
        print(f"\nActive Patterns: {active_patterns} / {total_patterns}")

        # By bank type
        print("\n" + "-" * 80)
        print("Categorization by Bank Type:")
        print("-" * 80)

        bank_stats = Transaction.objects.values('bank_type').annotate(
            total=Count('id'),
            categorized=Count('id', filter=Q(category__isnull=False))
        ).order_by('-total')

        self.print_table_row("Bank Type", "Total", "Categorized", "Coverage %",
                            widths=[20, 15, 15, 15])
        print("-" * 65)

        for stat in bank_stats:
            bank = stat['bank_type'] or 'Unknown'
            total = stat['total']
            cat = stat['categorized']
            coverage = (cat / total * 100) if total > 0 else 0
            self.print_table_row(bank, total, cat, f"{coverage:.1f}%",
                               widths=[20, 15, 15, 15])

    def top_patterns(self, limit=10):
        """Display most effective transaction patterns."""
        self.print_header(f"Top {limit} Most Effective Patterns")

        patterns = TransactionPattern.objects.filter(is_active=True)
        pattern_stats = []

        for pattern in patterns:
            # Count transactions matched by this pattern
            match_count = 0
            transactions = Transaction.objects.filter(category=pattern.category)

            for txn in transactions:
                if self._matches_pattern(txn.description.lower(), pattern):
                    match_count += 1

            if match_count > 0:
                pattern_stats.append({
                    'pattern': pattern.pattern,
                    'category': pattern.category.name if pattern.category else 'None',
                    'match_type': pattern.match_type,
                    'count': match_count,
                    'confidence': pattern.confidence
                })

        # Sort by count
        pattern_stats.sort(key=lambda x: x['count'], reverse=True)

        print(f"\n{'Pattern'.ljust(25)} {'Category'.ljust(20)} {'Type'.ljust(12)} {'Matches'.ljust(10)} Confidence")
        print("-" * 90)

        for stat in pattern_stats[:limit]:
            print(f"{stat['pattern'][:24].ljust(25)} "
                  f"{stat['category'][:19].ljust(20)} "
                  f"{stat['match_type'][:11].ljust(12)} "
                  f"{stat['count']:>7}    "
                  f"{stat['confidence']:.2f}")

        if not pattern_stats:
            print("No patterns are currently matching any transactions.")

    def uncategorized_analysis(self, limit=10):
        """Analyze most common uncategorized transaction descriptions."""
        self.print_header(f"Top {limit} Most Common Uncategorized Descriptions")

        uncategorized_txns = Transaction.objects.filter(category__isnull=True)

        if uncategorized_txns.count() == 0:
            print("\nNo uncategorized transactions found!")
            return

        # Group by description
        description_counts = Counter()
        description_samples = {}

        for txn in uncategorized_txns:
            desc = txn.description.strip()
            description_counts[desc] += 1
            if desc not in description_samples:
                description_samples[desc] = {
                    'amount': txn.amount,
                    'date': txn.date,
                    'type': txn.transaction_type
                }

        print(f"\n{'Count'.ljust(8)} {'Description'.ljust(50)} {'Sample Amount'.ljust(15)} Type")
        print("-" * 90)

        for desc, count in description_counts.most_common(limit):
            sample = description_samples[desc]
            amount_str = f"Q{sample['amount']:,.2f}"
            print(f"{count:>5}    {desc[:49].ljust(50)} {amount_str.ljust(15)} {sample['type']}")

        # Print suggestions
        print("\n" + "-" * 80)
        print("Pattern Suggestions:")
        print("-" * 80)
        self._suggest_patterns_from_descriptions(
            [desc for desc, _ in description_counts.most_common(limit)]
        )

    def low_confidence_transactions(self, threshold=0.6, limit=20):
        """Display transactions with low categorization confidence."""
        self.print_header(f"Low Confidence Transactions (< {threshold})")

        low_conf_txns = Transaction.objects.filter(
            category__isnull=False,
            category_confidence__lt=threshold
        ).order_by('category_confidence')[:limit]

        if not low_conf_txns.exists():
            print(f"\nNo transactions with confidence below {threshold}!")
            return

        print(f"\n{'Conf'.ljust(6)} {'Description'.ljust(40)} {'Category'.ljust(20)} {'Amount'.ljust(12)} Date")
        print("-" * 90)

        for txn in low_conf_txns:
            cat_name = txn.category.name if txn.category else 'None'
            amount_str = f"Q{txn.amount:,.2f}"
            print(f"{txn.category_confidence:.2f}   "
                  f"{txn.description[:39].ljust(40)} "
                  f"{cat_name[:19].ljust(20)} "
                  f"{amount_str.ljust(12)} "
                  f"{txn.date}")

        print(f"\nShowing {low_conf_txns.count()} transactions")

    def unused_patterns(self):
        """Display patterns that never match any transactions."""
        self.print_header("Unused Patterns")

        patterns = TransactionPattern.objects.filter(is_active=True)
        unused = []

        for pattern in patterns:
            # Check if any transaction matches this pattern
            match_found = False
            transactions = Transaction.objects.all()[:1000]  # Sample for performance

            for txn in transactions:
                if self._matches_pattern(txn.description.lower(), pattern):
                    match_found = True
                    break

            if not match_found:
                unused.append(pattern)

        if not unused:
            print("\nAll active patterns are matching at least one transaction!")
            return

        print(f"\n{'Pattern'.ljust(30)} {'Category'.ljust(25)} {'Match Type'.ljust(15)} Created")
        print("-" * 90)

        for pattern in unused:
            cat_name = pattern.category.name if pattern.category else 'None'
            created = pattern.created_at.strftime('%Y-%m-%d') if hasattr(pattern, 'created_at') else 'Unknown'
            print(f"{pattern.pattern[:29].ljust(30)} "
                  f"{cat_name[:24].ljust(25)} "
                  f"{pattern.match_type.ljust(15)} "
                  f"{created}")

        print(f"\nFound {len(unused)} unused patterns")

    def suggest_patterns(self, limit=10):
        """Suggest new patterns based on uncategorized transactions."""
        self.print_header("Suggested New Patterns")

        uncategorized_txns = Transaction.objects.filter(category__isnull=True)

        if uncategorized_txns.count() == 0:
            print("\nNo uncategorized transactions to analyze!")
            return

        # Extract common words from descriptions
        word_counts = Counter()

        for txn in uncategorized_txns:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', txn.description.lower())
            word_counts.update(words)

        # Get most common words
        common_words = word_counts.most_common(limit)

        print("\nBased on uncategorized transaction analysis:\n")
        print(f"{'Suggested Pattern'.ljust(25)} {'Match Type'.ljust(15)} {'Frequency'.ljust(12)} Suggested Category")
        print("-" * 90)

        for word, count in common_words:
            # Skip common words
            if word in ['pago', 'compra', 'retiro', 'deposito', 'transferencia', 'cargo', 'abono']:
                continue

            match_type = 'contains'
            suggested_category = self._suggest_category_for_word(word)

            print(f"{word.ljust(25)} {match_type.ljust(15)} {str(count).ljust(12)} {suggested_category}")

    def test_pattern(self, pattern_text, match_type='contains'):
        """Test a pattern against existing transactions."""
        self.print_header(f"Testing Pattern: '{pattern_text}' ({match_type})")

        matching_txns = []

        for txn in Transaction.objects.all():
            test_pattern = type('TestPattern', (), {
                'pattern': pattern_text,
                'match_type': match_type
            })()

            if self._matches_pattern(txn.description.lower(), test_pattern):
                matching_txns.append(txn)

        print(f"\nFound {len(matching_txns)} matching transactions:\n")

        if matching_txns:
            print(f"{'Description'.ljust(45)} {'Current Category'.ljust(25)} {'Amount'.ljust(12)} Date")
            print("-" * 95)

            for txn in matching_txns[:20]:
                cat_name = txn.category.name if txn.category else 'Uncategorized'
                amount_str = f"Q{txn.amount:,.2f}"
                print(f"{txn.description[:44].ljust(45)} "
                      f"{cat_name[:24].ljust(25)} "
                      f"{amount_str.ljust(12)} "
                      f"{txn.date}")

            if len(matching_txns) > 20:
                print(f"\n... and {len(matching_txns) - 20} more")

            # Category distribution
            cat_counts = Counter()
            for txn in matching_txns:
                cat_name = txn.category.name if txn.category else 'Uncategorized'
                cat_counts[cat_name] += 1

            print("\nCategory Distribution:")
            for cat, count in cat_counts.most_common():
                print(f"  {cat}: {count}")

    def _matches_pattern(self, description, pattern):
        """Check if a description matches a pattern."""
        desc_lower = description.lower()
        pattern_lower = pattern.pattern.lower()

        if pattern.match_type == 'exact':
            return desc_lower == pattern_lower
        elif pattern.match_type == 'contains':
            return pattern_lower in desc_lower
        elif pattern.match_type == 'starts_with':
            return desc_lower.startswith(pattern_lower)
        elif pattern.match_type == 'ends_with':
            return desc_lower.endswith(pattern_lower)
        elif pattern.match_type == 'regex':
            try:
                return bool(re.search(pattern.pattern, description, re.IGNORECASE))
            except:
                return False
        return False

    def _suggest_patterns_from_descriptions(self, descriptions):
        """Suggest patterns based on common description elements."""
        suggestions = []

        for desc in descriptions[:5]:
            # Extract potential keywords
            words = re.findall(r'\b[a-zA-Z]{4,}\b', desc.lower())

            if words:
                main_word = max(words, key=len) if len(words) > 0 else words[0]
                suggested_cat = self._suggest_category_for_word(main_word)
                suggestions.append({
                    'pattern': main_word,
                    'type': 'contains',
                    'category': suggested_cat,
                    'description': desc
                })

        for i, sugg in enumerate(suggestions, 1):
            print(f"{i}. Pattern: '{sugg['pattern']}' -> {sugg['category']}")
            print(f"   Example: {sugg['description'][:70]}")
            print()

    def _suggest_category_for_word(self, word):
        """Suggest a category based on keyword."""
        # Common category mappings
        food_keywords = ['restaurant', 'cafe', 'pizza', 'burger', 'comida', 'food', 'super', 'market']
        transport_keywords = ['gasolina', 'uber', 'taxi', 'bus', 'transport', 'shell', 'puma']
        shopping_keywords = ['tienda', 'store', 'shop', 'mall', 'plaza', 'boutique']
        health_keywords = ['farmacia', 'hospital', 'clinica', 'medico', 'doctor', 'pharmacy']
        utilities_keywords = ['eegsa', 'agua', 'luz', 'internet', 'telefono', 'claro', 'tigo']

        word_lower = word.lower()

        if any(kw in word_lower for kw in food_keywords):
            return "Food & Dining"
        elif any(kw in word_lower for kw in transport_keywords):
            return "Transportation"
        elif any(kw in word_lower for kw in shopping_keywords):
            return "Shopping"
        elif any(kw in word_lower for kw in health_keywords):
            return "Health & Medical"
        elif any(kw in word_lower for kw in utilities_keywords):
            return "Utilities"
        else:
            return "Uncategorized"


def main():
    """Main entry point for the analysis tool."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze transaction categorization patterns')
    parser.add_argument('command', nargs='?', default='overview',
                       choices=['overview', 'top-patterns', 'uncategorized', 'low-confidence',
                               'unused-patterns', 'suggest-patterns', 'test-pattern'],
                       help='Analysis command to run')
    parser.add_argument('--limit', type=int, default=10, help='Number of results to show')
    parser.add_argument('--threshold', type=float, default=0.6, help='Confidence threshold')
    parser.add_argument('--pattern', type=str, help='Pattern to test')
    parser.add_argument('--match-type', type=str, default='contains',
                       choices=['exact', 'contains', 'starts_with', 'ends_with', 'regex'],
                       help='Pattern match type')

    args = parser.parse_args()

    analyzer = PatternAnalyzer()

    if args.command == 'overview':
        analyzer.overview()
    elif args.command == 'top-patterns':
        analyzer.top_patterns(limit=args.limit)
    elif args.command == 'uncategorized':
        analyzer.uncategorized_analysis(limit=args.limit)
    elif args.command == 'low-confidence':
        analyzer.low_confidence_transactions(threshold=args.threshold, limit=args.limit)
    elif args.command == 'unused-patterns':
        analyzer.unused_patterns()
    elif args.command == 'suggest-patterns':
        analyzer.suggest_patterns(limit=args.limit)
    elif args.command == 'test-pattern':
        if not args.pattern:
            print("Error: --pattern required for test-pattern command")
            sys.exit(1)
        analyzer.test_pattern(args.pattern, args.match_type)

    print("\n")


if __name__ == '__main__':
    main()
