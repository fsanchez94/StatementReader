# Test Suite for PDF Bank Statement Parser

This directory contains comprehensive tests for the PDF bank statement parser application.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_base_parser.py     # BaseParser abstract class tests
│   ├── test_pdf_processor.py   # PDFProcessor utility tests
│   ├── test_parser_factory.py  # ParserFactory pattern tests
│   └── test_individual_parsers.py # Individual bank parser tests
├── integration/             # Integration and end-to-end tests
│   └── test_end_to_end.py      # Full pipeline testing
├── fixtures/                # Test data and expected outputs
│   ├── sample_industrial_checking_data.txt
│   ├── expected_industrial_checking_output.csv
│   ├── sample_credit_card_data.txt
│   └── test_data_loader.py     # Utility for loading test data
├── conftest.py             # Pytest configuration and fixtures
└── README.md               # This file
```

## Running Tests

### Install Test Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Unit Tests Only
```bash
pytest tests/unit/
```

### Run Integration Tests Only
```bash
pytest tests/integration/
```

### Run with Coverage Report
```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test Categories
```bash
# Run tests marked as 'unit'
pytest -m unit

# Run tests marked as 'integration'  
pytest -m integration

# Run tests that work with PDFs
pytest -m pdf
```

## Test Categories

### Unit Tests
- **BaseParser**: Tests abstract base class functionality, date conversion, CSV export
- **PDFProcessor**: Tests PDF text extraction, OCR fallback, validation logic
- **ParserFactory**: Tests factory pattern for creating appropriate parsers
- **Individual Parsers**: Tests parsing logic for each bank/account type combination

### Integration Tests
- **End-to-End Processing**: Tests complete pipeline from PDF input to CSV output
- **Multi-Parser Support**: Tests all supported bank and account type combinations
- **Error Handling**: Tests system behavior with invalid inputs and edge cases
- **Batch Processing**: Tests processing multiple PDFs in folders

## Test Data

### Fixtures
- Sample bank statement text data for different banks
- Expected CSV output files for validation
- Mock PDF content generators
- Test data loader utilities

### Supported Test Scenarios
- Valid transaction parsing
- Invalid/malformed data handling
- Date format validation
- Amount parsing with commas
- Balance calculation logic
- Spouse account differentiation
- Multi-page PDF processing
- OCR fallback scenarios

## Coverage Goals

The test suite aims for >85% code coverage across all modules:
- Parser implementations: >90%
- Utility functions: >95%
- Error handling paths: >80%
- Integration scenarios: >85%

## Writing New Tests

When adding new functionality:

1. **Add unit tests** for new parser logic in `tests/unit/`
2. **Add integration tests** if the change affects the complete pipeline
3. **Update fixtures** with new sample data if supporting new banks
4. **Use appropriate markers** (`@pytest.mark.unit`, `@pytest.mark.integration`)
5. **Mock external dependencies** (PDFplumber, Tesseract) in unit tests

## Common Test Patterns

```python
# Unit test with mocking
@patch('parsers.banco_industrial_checking_parser.pdfplumber.open')
def test_parser_functionality(self, mock_pdfplumber):
    # Setup mock
    mock_page = Mock()
    mock_page.extract_text.return_value = "test data"
    # ... rest of test

# Integration test with temp files
def test_end_to_end_processing(self, temp_output_dir):
    # Use temp directory for outputs
    output_path = temp_output_dir / "test_output.csv"
    # ... test processing
```