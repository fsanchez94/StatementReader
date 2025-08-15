# PDF Testing Guide

This guide explains how to use real PDF examples for testing the bank statement parsers instead of generated mock data.

## Overview

The testing framework now supports both:
- **Mock testing**: Using generated transaction lines (existing functionality)
- **Real PDF testing**: Using actual bank statement PDFs (new functionality)

Real PDF testing provides more confidence in parser accuracy and catches real-world formatting issues that mock data might miss.

## Directory Structure

```
tests/
├── fixtures/
│   ├── sample_pdfs/           # Real PDF examples
│   │   ├── industrial/        # Banco Industrial PDFs
│   │   │   ├── checking/      # GTQ checking account PDFs
│   │   │   ├── usd_checking/  # USD checking account PDFs
│   │   │   ├── credit/        # Credit card PDFs
│   │   │   └── credit_usd/    # USD credit card PDFs
│   │   ├── bam/              # BAM bank PDFs
│   │   │   └── credit/       # BAM credit card PDFs
│   │   └── gyt/              # GyT bank PDFs
│   │       └── credit/       # GyT credit card PDFs
│   ├── expected_outputs/      # Expected CSV outputs
│   │   ├── industrial/
│   │   ├── bam/
│   │   └── gyt/
│   ├── test_data_loader.py    # Utilities for loading test data
│   └── pdf_sample_manager.py  # Management utilities
└── unit/
    ├── test_individual_parsers.py                # Enhanced with real PDF tests
    └── test_individual_parsers_with_real_pdfs.py # Comprehensive real PDF tests
```

## Adding Sample PDFs

### Step 1: Prepare PDF Files

⚠️ **SECURITY IMPORTANT**: Never use PDFs with real personal or financial information

1. **Obtain anonymized PDFs** with fictional data, or
2. **Redact real PDFs** by removing/replacing:
   - Account numbers
   - Personal names
   - Real addresses
   - Real transaction descriptions (replace with generic ones)

### Step 2: Place PDFs in Correct Directory

```bash
# Example: Adding Industrial checking account PDF
cp anonymized_statement.pdf tests/fixtures/sample_pdfs/industrial/checking/

# Use descriptive filenames
mv anonymized_statement.pdf industrial_checking_sample1.pdf
```

**File naming convention**: `{bank}_{account_type}_{description}.pdf`

Examples:
- `industrial_checking_sample1.pdf`
- `industrial_credit_multipage.pdf`
- `bam_credit_example.pdf`
- `gyt_credit_with_payments.pdf`

### Step 3: Generate Expected Output

Use the PDF sample manager to generate expected CSV outputs:

```bash
cd tests/fixtures
python pdf_sample_manager.py generate --bank industrial --account checking --pdf path/to/your.pdf
```

Or generate all at once:
```bash
python pdf_sample_manager.py generate
```

### Step 4: Verify Expected Output

1. **Review the generated CSV** in `tests/fixtures/expected_outputs/{bank}/`
2. **Manually verify** that the parsed data is correct
3. **Edit if necessary** to fix any parsing errors
4. **Commit both the PDF and expected CSV** to version control

### Step 5: Run Tests

```bash
# Run all tests (will include real PDF tests if PDFs are available)
pytest tests/

# Run only real PDF tests
pytest tests/unit/test_individual_parsers_with_real_pdfs.py

# Run integration tests with real PDFs
pytest tests/integration/test_end_to_end.py::TestRealPDFIntegration
```

## Management Commands

### Check PDF Status

```bash
cd tests/fixtures
python pdf_sample_manager.py report
```

This shows:
- Available PDFs by bank/account type
- Missing expected outputs
- Structure validation issues

### Validate PDF Processing

```bash
cd tests/fixtures
python pdf_sample_manager.py validate
```

This verifies that all PDFs still produce the expected outputs.

### Generate Missing Expected Outputs

```bash
cd tests/fixtures
python pdf_sample_manager.py generate
```

## Test Behavior

### When PDFs Are Available
- Real PDF tests run automatically
- Tests validate against expected outputs
- Performance benchmarks are measured

### When PDFs Are Missing
- Real PDF tests are automatically skipped
- Mock tests continue to run normally
- No test failures due to missing PDFs

### Test Types

1. **Unit Tests** (`test_individual_parsers.py`):
   - Mock data tests (always run)
   - Basic real PDF tests (if PDFs available)

2. **Comprehensive Real PDF Tests** (`test_individual_parsers_with_real_pdfs.py`):
   - Parameterized tests across all available PDFs
   - Expected output validation
   - Performance benchmarking

3. **Integration Tests** (`test_end_to_end.py`):
   - Complete pipeline testing
   - Multi-bank processing
   - Error handling with real structure

## Expected CSV Format

Generated CSV files should have these columns:
- `Date`: Transaction date (YYYY-MM-DD format)
- `Description`: Cleaned transaction description
- `Original Description`: Original description from PDF
- `Amount`: Transaction amount (positive for credits, negative for debits)
- `Transaction Type`: 'credit' or 'debit'
- `Category`: Empty (for user categorization)
- `Account Name`: Account identifier (e.g., 'Industrial GTQ')

## Troubleshooting

### PDF Not Being Processed

1. **Check file placement**:
   ```bash
   ls tests/fixtures/sample_pdfs/industrial/checking/
   ```

2. **Verify PDF is readable**:
   ```bash
   python -c "
   from src.utils.pdf_processor import PDFProcessor
   processor = PDFProcessor()
   result = processor.process('path/to/your.pdf')
   print(f'Extracted {len(result)} characters')
   "
   ```

3. **Check parser compatibility**:
   ```bash
   python -c "
   from src.parsers.parser_factory import ParserFactory
   parser = ParserFactory.get_parser('industrial', 'checking', 'path/to/your.pdf')
   transactions = parser.extract_data()
   print(f'Found {len(transactions)} transactions')
   "
   ```

### Tests Failing

1. **Expected output mismatch**: Re-generate expected output
2. **Parser changes**: Update expected outputs after parser improvements
3. **PDF corruption**: Try with a different PDF file

### Performance Issues

1. **Large PDFs**: Consider splitting or using smaller samples
2. **OCR fallback**: Ensure Tesseract is properly installed
3. **Many PDFs**: Limit test runs to representative samples

## Best Practices

### PDF Selection
- **Variety**: Include PDFs with different transaction counts, date ranges, formatting
- **Edge cases**: PDFs with special characters, multiple pages, different layouts
- **Representative**: Cover common real-world scenarios

### Expected Outputs
- **Version control**: Always commit expected CSVs alongside PDFs
- **Documentation**: Add comments in CSV if special handling is needed
- **Validation**: Manually verify at least one transaction per PDF

### Test Maintenance
- **Regular validation**: Run `pdf_sample_manager.py validate` periodically
- **Parser updates**: Re-generate expected outputs when parsers are improved
- **Cleanup**: Remove outdated PDFs and outputs

## Security Considerations

- **Never commit real financial data**
- **Use fictional account numbers** (e.g., 1234567890)
- **Replace real names** with generic ones (e.g., "JUAN PEREZ")
- **Anonymize merchant names** 
- **Review PDFs** before committing to ensure no sensitive data

## Integration with CI/CD

The test framework automatically:
- Skips real PDF tests if no PDFs are available
- Runs all available tests in CI environments
- Provides clear skip messages for missing test data

For CI environments with PDFs:
1. Store encrypted PDFs in secure CI storage
2. Decrypt during test runs
3. Ensure cleanup after tests

## Example Workflow

```bash
# 1. Add new PDF
cp new_statement.pdf tests/fixtures/sample_pdfs/industrial/checking/industrial_checking_new.pdf

# 2. Generate expected output
cd tests/fixtures
python pdf_sample_manager.py generate --bank industrial --account checking --pdf ../sample_pdfs/industrial/checking/industrial_checking_new.pdf

# 3. Verify the output
cat expected_outputs/industrial/industrial_checking_new.csv

# 4. Run tests
pytest tests/unit/test_individual_parsers_with_real_pdfs.py -v

# 5. Commit both files
git add tests/fixtures/sample_pdfs/industrial/checking/industrial_checking_new.pdf
git add tests/fixtures/expected_outputs/industrial/industrial_checking_new.csv
git commit -m "Add new Industrial checking account test sample"
```

This approach ensures robust testing with real-world data while maintaining security and maintainability.