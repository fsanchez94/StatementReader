# Transaction Pattern Statistics

Analyze transaction categorization patterns to improve the auto-categorization system.

## Description

This skill provides comprehensive analysis of your transaction categorization patterns, helping you:
- Identify the most effective patterns
- Find common uncategorized transactions
- Detect low-confidence categorizations
- Discover unused patterns
- Get suggestions for new patterns

## Usage

The skill accepts commands to analyze different aspects of your transaction data.

## Available Commands

1. **overview** - Display overall categorization health and statistics
2. **top-patterns** - Show the most effective transaction patterns
3. **uncategorized** - List most common uncategorized transaction descriptions
4. **low-confidence** - Find transactions with low categorization confidence
5. **unused-patterns** - Identify patterns that never match any transactions
6. **suggest-patterns** - Get AI-generated suggestions for new patterns
7. **test-pattern** - Test a pattern against existing transactions

## Instructions for Claude

When this skill is invoked, you should:

1. Parse the user's command and arguments
2. Run the analysis script located at `scripts/analyze_transaction_patterns.py`
3. Display the results in a clear, formatted way
4. Provide insights and recommendations based on the output

### Command Format

Use the Python script with the following syntax:

```bash
python scripts/analyze_transaction_patterns.py [command] [options]
```

### Command Options

- `--limit N` - Limit results to N items (default: 10)
- `--threshold X` - Set confidence threshold for low-confidence command (default: 0.6)
- `--pattern "text"` - Pattern text to test (required for test-pattern command)
- `--match-type TYPE` - Match type: exact, contains, starts_with, ends_with, regex

### Examples

**Get overview:**
```bash
python scripts/analyze_transaction_patterns.py overview
```

**Top 15 patterns:**
```bash
python scripts/analyze_transaction_patterns.py top-patterns --limit 15
```

**Find uncategorized:**
```bash
python scripts/analyze_transaction_patterns.py uncategorized --limit 20
```

**Low confidence (< 0.5):**
```bash
python scripts/analyze_transaction_patterns.py low-confidence --threshold 0.5 --limit 30
```

**Test a pattern:**
```bash
python scripts/analyze_transaction_patterns.py test-pattern --pattern "walmart" --match-type contains
```

## Response Format

After running the analysis:

1. **Show the output** - Display the formatted tables and statistics
2. **Provide insights** - Highlight key findings and patterns
3. **Suggest actions** - Recommend specific improvements:
   - Patterns to create
   - Patterns to modify
   - Patterns to deactivate
4. **Offer next steps** - Suggest what the user should analyze next

## Tips for Analysis

- Start with `overview` to understand overall categorization health
- Use `uncategorized` to find gaps in your pattern coverage
- Check `low-confidence` to identify weak pattern matches
- Use `test-pattern` before creating new patterns to avoid conflicts
- Review `unused-patterns` periodically to clean up your pattern database
- Use `suggest-patterns` when you need ideas for new categorization rules

## Creating New Patterns

After identifying needed patterns, you can create them via:

1. **Django Admin** - http://127.0.0.1:5000/admin/parser_api/transactionpattern/
2. **Django Shell** - Using management commands
3. **Bulk Import** - Using a script

Remember to:
- Test patterns first with `test-pattern` command
- Set appropriate confidence scores
- Use the most specific match_type possible
- Avoid overlapping patterns that might conflict
