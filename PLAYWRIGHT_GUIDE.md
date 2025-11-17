# Playwright Quick Reference Guide

## Running Tests

### Frontend (JavaScript)
```bash
cd frontend

# Run all tests
npm run test:e2e

# Run with visible browser
npm run test:e2e:headed

# Run with Playwright UI (interactive, recommended for development)
npm run test:e2e:ui

# Run specific test file
npx playwright test e2e/home.spec.js

# Run in debug mode
npx playwright test --debug
```

### Backend (Python)
```bash
# Run all E2E tests
pytest tests/e2e/ -m e2e

# Run with visible browser
pytest tests/e2e/ -m e2e --headed

# Run specific test file
pytest tests/e2e/test_web_app.py -v

# Run specific test
pytest tests/e2e/test_web_app.py::TestWebApplication::test_home_page_loads -v

# Run with slow motion (1 second delay between actions)
pytest tests/e2e/ -m e2e --slowmo=1000

# Debug mode (step through test)
PWDEBUG=1 pytest tests/e2e/test_web_app.py::test_name -s
```

## Writing Tests

### Python Test Template
```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
def test_my_feature(page: Page, base_url: str):
    """Test description"""
    # Navigate
    page.goto(base_url)

    # Interact
    page.click('button:has-text("Click me")')

    # Assert
    expect(page.locator('.result')).to_be_visible()
```

### JavaScript Test Template
```javascript
const { test, expect } = require('@playwright/test');

test('my feature', async ({ page }) => {
  // Navigate
  await page.goto('http://localhost:3000');

  // Interact
  await page.click('button:has-text("Click me")');

  // Assert
  await expect(page.locator('.result')).toBeVisible();
});
```

## Common Selectors

```python
# By text
page.locator('text=Upload')
page.get_by_text('Upload')

# By role (accessibility - RECOMMENDED)
page.get_by_role('button', name='Upload')
page.get_by_role('textbox', name='Email')
page.get_by_role('link', name='Home')

# By test ID (BEST PRACTICE)
page.get_by_test_id('upload-button')
# Add to your React components: <button data-testid="upload-button">

# By CSS selector
page.locator('.class-name')
page.locator('#element-id')
page.locator('button.primary')

# By attribute
page.locator('[name="username"]')
page.locator('[type="file"]')

# Combined
page.locator('button:has-text("Submit")')
page.locator('.form >> button')
```

## Common Actions

```python
# Click
page.click('button')

# Fill text
page.fill('input[name="email"]', 'test@example.com')

# Select dropdown
page.select_option('select[name="type"]', 'value')
page.select_option('select[name="type"]', label='Option Label')

# Upload file
page.set_input_files('input[type="file"]', 'path/to/file.pdf')

# Check/uncheck
page.check('input[type="checkbox"]')
page.uncheck('input[type="checkbox"]')

# Hover
page.hover('.menu-item')

# Double click
page.dblclick('div')

# Right click
page.click('div', button='right')

# Press keyboard
page.press('input', 'Enter')
page.keyboard.press('Tab')
```

## Common Assertions

```python
from playwright.sync_api import expect

# Visibility
expect(page.locator('#element')).to_be_visible()
expect(page.locator('#element')).to_be_hidden()

# Text
expect(page.locator('h1')).to_have_text('Welcome')
expect(page.locator('.error')).to_contain_text('error')

# Count
expect(page.locator('.item')).to_have_count(5)

# URL
expect(page).to_have_url('http://localhost:3000/upload')
expect(page).to_have_url(re.compile(r'.*/upload'))

# Enabled/Disabled
expect(page.locator('button')).to_be_enabled()
expect(page.locator('button')).to_be_disabled()

# Value
expect(page.locator('input')).to_have_value('text')

# Attribute
expect(page.locator('button')).to_have_attribute('disabled', '')
```

## Waiting Strategies

```python
# Wait for selector
page.wait_for_selector('.element')
page.wait_for_selector('.loading', state='hidden')

# Wait for URL
page.wait_for_url('**/upload')

# Wait for load state
page.wait_for_load_state('load')           # DOM loaded
page.wait_for_load_state('domcontentloaded')
page.wait_for_load_state('networkidle')     # No network activity

# Wait for function
page.wait_for_function('() => document.title !== ""')

# Wait for timeout (avoid if possible)
page.wait_for_timeout(1000)  # 1 second
```

## File Downloads

```python
# Expect and capture download
with page.expect_download() as download_info:
    page.click('a:has-text("Download")')

download = download_info.value

# Get filename
print(download.suggested_filename)

# Save file
download.save_as('path/to/save/file.csv')
```

## Screenshots

```python
# Full page screenshot
page.screenshot(path='screenshot.png')

# Element screenshot
page.locator('.element').screenshot(path='element.png')

# Screenshot on test failure (automatic in pytest)
# Just run tests normally, screenshots saved in test-results/
```

## Debugging

### Interactive Mode (UI)
```bash
# JavaScript
npx playwright test --ui

# Python - use PWDEBUG
PWDEBUG=1 pytest tests/e2e/test_name.py -s
```

### Pause Execution
```python
# Add to your test
page.pause()  # Opens Playwright Inspector
```

### Slow Motion
```bash
# Python
pytest tests/e2e/ --slowmo=1000  # 1 second delay

# JavaScript
npx playwright test --slowmo=1000
```

### Print Debug Info
```python
# Print page content
print(page.content())

# Print element text
print(page.locator('h1').inner_text())

# Print attributes
print(page.locator('button').get_attribute('class'))
```

## Best Practices

### 1. Use data-testid Attributes
```jsx
// In your React components
<button data-testid="upload-btn">Upload</button>

// In tests
page.get_by_test_id('upload-btn').click()
```

### 2. Wait for Network Idle
```python
page.goto(url)
page.wait_for_load_state('networkidle')  # Before assertions
```

### 3. Use Auto-waiting
```python
# Playwright auto-waits before actions
page.click('button')  # Waits for button to be visible and enabled

# No need for:
# page.wait_for_selector('button')
# page.click('button')
```

### 4. Use Fixtures
```python
# Define in conftest.py
@pytest.fixture
def logged_in_page(page: Page):
    page.goto('http://localhost:3000/login')
    page.fill('[name="username"]', 'testuser')
    page.fill('[name="password"]', 'testpass')
    page.click('button[type="submit"]')
    return page

# Use in tests
def test_dashboard(logged_in_page: Page):
    logged_in_page.goto('/dashboard')
    # ...
```

### 5. Mark Slow Tests
```python
@pytest.mark.slow
@pytest.mark.e2e
def test_long_process(page: Page):
    # ...
```

## Useful Commands

```bash
# Install/update browsers
python -m playwright install
npx playwright install

# Generate tests (record actions)
npx playwright codegen http://localhost:3000

# Show test report
npx playwright show-report
pytest tests/e2e/ --html=report.html

# List installed browsers
npx playwright list-browsers

# Clear browser cache
python -m playwright install --force
```

## Configuration Files

### Frontend: `frontend/playwright.config.js`
- Test directory: `./e2e`
- Base URL: `http://localhost:3000`
- Browsers: Chromium
- Auto-starts dev server

### Backend: `pytest.ini`
- Test marker: `@pytest.mark.e2e`
- Browser: Chromium
- Headed mode by default

## Examples

See these files for practical examples:
- `tests/e2e/test_example_usage.py` - Comprehensive Python examples
- `frontend/e2e/home.spec.js` - Basic JavaScript example
- `frontend/e2e/pdf-upload.spec.js` - File upload example

## Resources

- [Playwright Python Docs](https://playwright.dev/python/docs/intro)
- [Playwright JavaScript Docs](https://playwright.dev/docs/intro)
- [Pytest-Playwright Plugin](https://github.com/microsoft/playwright-pytest)
- [Best Practices](https://playwright.dev/docs/best-practices)
