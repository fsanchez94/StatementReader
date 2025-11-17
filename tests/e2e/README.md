# E2E Tests with Playwright

This directory contains end-to-end tests using Playwright for Python.

## Prerequisites

1. Install Playwright:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   python -m playwright install chromium
   ```

3. Ensure both frontend and backend are running:
   - **Backend**: `python scripts/run_django.py` (runs on http://localhost:5000)
   - **Frontend**: `cd frontend && npm start` (runs on http://localhost:3000)

## Running Tests

### Run all E2E tests
```bash
pytest tests/e2e/ -m e2e
```

### Run tests in headless mode (no visible browser)
```bash
pytest tests/e2e/ -m e2e --headed=false
```

### Run tests in headed mode (visible browser - default)
```bash
pytest tests/e2e/ -m e2e --headed
```

### Run tests with slow motion (easier to see what's happening)
```bash
pytest tests/e2e/ -m e2e --slowmo=1000
```

### Run specific test file
```bash
pytest tests/e2e/test_web_app.py -v
```

### Run specific test
```bash
pytest tests/e2e/test_web_app.py::TestWebApplication::test_home_page_loads -v
```

### Run with different browsers
```bash
# Chromium (default)
pytest tests/e2e/ -m e2e --browser chromium

# Firefox
pytest tests/e2e/ -m e2e --browser firefox

# WebKit (Safari)
pytest tests/e2e/ -m e2e --browser webkit

# Run on all browsers
pytest tests/e2e/ -m e2e --browser chromium --browser firefox --browser webkit
```

### Generate HTML report
```bash
pytest tests/e2e/ -m e2e --html=tests/e2e/report.html --self-contained-html
```

## Test Structure

- **test_web_app.py**: Tests for the main web application UI
- **test_django_api.py**: Tests for Django REST API endpoints

## Writing New Tests

### Basic test structure
```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
def test_example(page: Page, base_url: str):
    page.goto(base_url)
    expect(page).to_have_title("Expected Title")
```

### Using fixtures
- `page`: Playwright page object
- `base_url`: Frontend URL (http://localhost:3000)
- `api_base_url`: Backend API URL (http://localhost:5000)
- `sample_pdf_path`: Path to sample PDF fixture

### Best Practices

1. **Use data-testid attributes** in your React components for stable selectors:
   ```jsx
   <button data-testid="upload-button">Upload</button>
   ```

2. **Wait for network idle** before assertions:
   ```python
   page.wait_for_load_state("networkidle")
   ```

3. **Use expect() for assertions**:
   ```python
   expect(page.locator("#element")).to_be_visible()
   ```

4. **Mark slow tests** appropriately:
   ```python
   @pytest.mark.slow
   @pytest.mark.e2e
   def test_long_running(page):
       # ...
   ```

5. **Skip tests that require specific setup**:
   ```python
   @pytest.mark.skip(reason="Requires running backend")
   def test_with_backend(page):
       # ...
   ```

## Debugging Tests

### Run with Playwright Inspector (step through tests)
```bash
PWDEBUG=1 pytest tests/e2e/test_web_app.py::test_name -s
```

### Take screenshots on failure
Screenshots are automatically saved in `test-results/` directory when tests fail.

### View trace files
```bash
pytest tests/e2e/ -m e2e --tracing=on
playwright show-trace trace.zip
```

## CI/CD Integration

These tests can be run in CI/CD pipelines. The configuration in `pytest.ini` includes:
- Automatic retry on failure (when `CI=true`)
- Single worker in CI mode
- Headless mode by default

Example GitHub Actions:
```yaml
- name: Run E2E tests
  run: |
    pytest tests/e2e/ -m e2e --headed=false
  env:
    CI: true
```

## Troubleshooting

### Browser not found
```bash
python -m playwright install chromium
```

### Tests timing out
Increase timeout in conftest.py or specific tests:
```python
page.set_default_timeout(60000)  # 60 seconds
```

### Frontend/Backend not running
Make sure both services are running before executing E2E tests:
```bash
# Terminal 1
python scripts/run_django.py

# Terminal 2
cd frontend && npm start

# Terminal 3
pytest tests/e2e/ -m e2e
```
