# Contributing to PDF Bank Parser

Thank you for your interest in contributing to the PDF Bank Statement Parser project!

## Development Setup

### Prerequisites

- Python 3.12+ (specified in `.python-version`)
- Node.js 20.18+ (specified in `.nvmrc`)
- Tesseract OCR installed
  - Windows: Install at `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - Linux/Ubuntu: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/fsanchez94/StatementReader.git
   cd pdf_bank_parser
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development tools
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## Code Quality Standards

This project uses automated CI/CD checks to maintain code quality. All pull requests must pass these checks before merging.

### Python Code Quality

**Linting with flake8:**
```bash
flake8 src/ tests/ backends/django/ scripts/
```

**Code formatting with Black:**
```bash
# Check formatting
black --check src/ tests/ backends/django/ scripts/

# Auto-format code
black src/ tests/ backends/django/ scripts/
```

**Import sorting with isort:**
```bash
# Check import order
isort --check-only src/ tests/ backends/django/ scripts/

# Auto-sort imports
isort src/ tests/ backends/django/ scripts/
```

**Configuration files:**
- `.flake8` - Linting rules
- `pyproject.toml` - Black and isort configuration

### Frontend Code Quality

**ESLint:**
```bash
cd frontend
npm run lint        # Check for issues
npm run lint:fix    # Auto-fix issues
```

**Prettier:**
```bash
cd frontend
npm run format:check  # Check formatting
npm run format        # Auto-format code
```

**Configuration files:**
- `frontend/.eslintrc.json` - ESLint rules
- `frontend/.prettierrc` - Prettier configuration

### Testing

**Python tests:**
```bash
# Run all tests with coverage
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run only unit tests
python -m pytest tests/unit/ -v

# Run only integration tests
python -m pytest tests/integration/ -v

# Using the custom test runner
python run_tests.py --unit --coverage
```

**Coverage requirement:** 85% minimum

**Frontend tests:**
```bash
cd frontend
npm test
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration. Workflows run automatically on pull requests to the `main` branch.

### Workflows

1. **Python Backend CI** (`.github/workflows/python-ci.yml`)
   - Linting (flake8, black, isort)
   - Unit and integration tests
   - Coverage reporting (85% minimum)
   - Uploads coverage reports to Codecov

2. **Frontend CI** (`.github/workflows/frontend-ci.yml`)
   - ESLint checking
   - Prettier formatting check
   - Build verification
   - Test execution (when available)

3. **Security Scanning** (`.github/workflows/security.yml`)
   - Python: Bandit (security linter) + Safety (dependency scanner)
   - Frontend: npm audit
   - Runs weekly on Sundays + on pull requests

### Manual Workflow Triggers

You can manually trigger any workflow from the GitHub Actions tab in the repository.

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and ensure they follow code quality standards:
   ```bash
   # Python
   black src/ tests/ backends/django/ scripts/
   isort src/ tests/ backends/django/ scripts/
   flake8 src/ tests/ backends/django/ scripts/

   # Frontend
   cd frontend
   npm run format
   npm run lint:fix
   ```

3. **Run tests locally:**
   ```bash
   python -m pytest tests/ --cov=src --cov-fail-under=85
   cd frontend && npm test
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Adding or updating tests
   - `refactor:` - Code refactoring
   - `chore:` - Maintenance tasks

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** to the `main` branch

7. **Wait for CI checks** to pass. The PR cannot be merged until:
   - All linting checks pass
   - All tests pass
   - Code coverage meets 85% threshold
   - No security vulnerabilities detected

8. **Address review feedback** if any

## Development Tips

### Pre-commit Checks (Optional)

To catch issues before pushing, you can run:

```bash
# Quick pre-commit check script
python -m pytest tests/unit/ -v && \
black --check src/ && \
flake8 src/ && \
cd frontend && npm run lint && npm run format:check
```

### Running the Application Locally

**Django Backend:**
```bash
python scripts/run_django.py
# Server runs at http://127.0.0.1:5000
```

**React Frontend:**
```bash
cd frontend
npm start
# Application opens at http://localhost:3000
```

### Adding New Bank Parsers

See `src/parsers/README.md` (if exists) or follow the pattern in `src/parsers/base_parser.py`:

1. Create a new parser class inheriting from `BaseParser`
2. Implement `extract_data()` method
3. Add parser to `parser_factory.py`
4. Write unit tests in `tests/unit/`
5. Add sample PDF fixture for integration tests

## Security

- Never commit sensitive data (API keys, passwords, real bank statements)
- Use `.env` files for local configuration (not tracked in git)
- Report security vulnerabilities privately to the maintainers

## Questions?

- Check the [README.md](README.md) for project overview
- Review existing code and tests for examples
- Open an issue for questions or clarifications

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
