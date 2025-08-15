# Test Suite

This directory contains the comprehensive test suite for the PDF Bank Statement Parser, including both traditional mock-based tests and new real PDF testing capabilities.

## Test Structure

```
tests/
├── api/                    # Django API tests
├── integration/           # End-to-end integration tests
│   └── test_end_to_end.py # Mock and real PDF integration tests
├── unit/                  # Unit tests for individual components
│   ├── test_base_parser.py              # BaseParser abstract class tests
│   ├── test_pdf_processor.py            # PDFProcessor utility tests
│   ├── test_parser_factory.py           # ParserFactory pattern tests
│   ├── test_individual_parsers.py       # Mock + basic real PDF tests
│   └── test_individual_parsers_with_real_pdfs.py # Comprehensive real PDF tests
├── fixtures/              # Test data and utilities
│   ├── sample_pdfs/       # Real PDF examples organized by bank/account type
│   │   ├── industrial/    # Banco Industrial samples
│   │   ├── bam/          # BAM bank samples
│   │   └── gyt/          # GyT bank samples
│   ├── expected_outputs/  # Expected CSV outputs for real PDFs
│   ├── sample_*.txt       # Mock text data files
│   ├── test_data_loader.py # Utilities for loading test data
│   └── pdf_sample_manager.py # PDF sample management utilities
├── conftest.py           # Pytest configuration and fixtures
└── README.md             # This file
```

## Running Tests

### Install Test Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest tests/
```

### Run by Category
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only  
pytest tests/integration/

# API tests only
pytest tests/api/
```

### Real PDF Tests
```bash
# Comprehensive real PDF testing
pytest tests/unit/test_individual_parsers_with_real_pdfs.py

# Integration tests with real PDFs
pytest tests/integration/test_end_to_end.py::TestRealPDFIntegration
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

## Test Types

### 1. Unit Tests (`tests/unit/`)

**Mock-based tests** (always run):
- `test_individual_parsers.py`: Tests parsers with generated mock data
- `test_parser_factory.py`: Tests parser factory pattern
- `test_base_parser.py`: Tests base parser functionality
- `test_pdf_processor.py`: Tests PDF processing utilities

**Real PDF tests** (run when sample PDFs are available):
- `test_individual_parsers_with_real_pdfs.py`: Comprehensive testing with real PDFs

### 2. Integration Tests (`tests/integration/`)

**Mock-based integration** (always run):
- Complete pipeline tests with mocked PDF content
- Error handling and edge cases
- Performance benchmarks with mock data

**Real PDF integration** (run when sample PDFs are available):
- End-to-end processing with real PDF files
- Cross-bank compatibility testing
- Performance benchmarks with real data

### 3. API Tests (`tests/api/`)

- Django REST API endpoint testing
- File upload and processing workflows
- Session management and cleanup

## Test Data

### Mock Data
Located in `tests/fixtures/`:
- `sample_industrial_checking_data.txt`: Sample text data
- `sample_credit_card_data.txt`: Sample credit card data
- `test_data_loader.py`: Utilities for loading mock data

### Real PDF Data
Located in `tests/fixtures/sample_pdfs/`:
- Organized by bank type and account type
- Used for realistic testing scenarios
- Requires manual addition (see PDF Testing Guide)

## PDF Testing

The test suite supports both mock and real PDF testing:

- **Mock testing**: Uses generated transaction lines, always available
- **Real PDF testing**: Uses actual anonymized bank statements, optional

### Adding Real PDFs

See `docs/PDF_TESTING_GUIDE.md` for detailed instructions.

Quick start:
1. Add anonymized PDF to appropriate directory in `tests/fixtures/sample_pdfs/`
2. Generate expected output: `python tests/fixtures/pdf_sample_manager.py generate`
3. Run tests: `pytest tests/`

### Test Behavior

- **PDFs available**: Both mock and real PDF tests run
- **No PDFs**: Only mock tests run, real PDF tests are skipped
- **Missing expected outputs**: Tests are skipped with clear messages

## Coverage Goals

The test suite aims for >85% code coverage across all modules:
- Parser implementations: >90%
- Utility functions: >95%
- Error handling paths: >80%
- Integration scenarios: >85%

## Test Utilities

### `test_data_loader.py`
- Loading sample PDFs by type
- Expected output management
- Test data validation
- Directory structure validation

### `pdf_sample_manager.py`
- Generate expected outputs
- Validate PDF processing
- Status reporting
- Batch operations

## Performance Testing

### Benchmarks Included
- PDF processing time per file
- Parser execution time
- Memory usage during processing
- Batch processing performance

### Performance Expectations
- PDF processing: < 30 seconds per file
- Average processing: < 10 seconds per file
- Memory: Reasonable usage for file sizes

## Contributing

When adding new tests:
1. Follow existing patterns and naming conventions
2. Add both mock and real PDF tests when applicable
3. Include appropriate skip conditions
4. Document any special requirements
5. Ensure tests are isolated and repeatable

For questions or issues with testing, see:
- `docs/PDF_TESTING_GUIDE.md` for PDF testing specifics
- Project README for general setup
- Test files for examples of test patterns