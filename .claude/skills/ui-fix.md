# UI Verification and Fix

Verify UI issues using Playwright before making fixes to ensure accurate understanding of the problem.

## Description

This skill uses Playwright to capture screenshots and verify the actual rendered UI before making any changes. This ensures that fixes are based on the real user experience rather than assumptions from code analysis.

## When to Use

Invoke this skill when the user asks to:
- Fix UI issues or bugs
- Modify UI appearance or behavior
- Debug visual problems
- Verify UI changes
- Check responsive design issues

## Instructions for Claude

When this skill is invoked, you MUST follow these steps in order:

### Step 1: Verify Servers are Running

Check that both servers are running:
- Django backend: http://localhost:5000
- React frontend: http://localhost:3000

If not running, inform the user to start them:
```bash
# Terminal 1
python scripts/run_django.py

# Terminal 2
cd frontend && npm start
```

### Step 2: Capture UI Screenshot

Use Playwright to take a screenshot of the relevant page. Create a temporary test file:

```python
# Create temp file: temp_ui_verify.py
from playwright.sync_api import sync_playwright
import sys

def capture_ui(url_path='/', selector=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to page
        page.goto(f'http://localhost:3000{url_path}')

        # Wait for network to be idle
        page.wait_for_load_state('networkidle')

        # Take screenshot
        if selector:
            page.locator(selector).screenshot(path='temp_ui_screenshot.png')
            print(f"Screenshot of '{selector}' saved to temp_ui_screenshot.png")
        else:
            page.screenshot(path='temp_ui_screenshot.png', full_page=True)
            print("Full page screenshot saved to temp_ui_screenshot.png")

        # Get page HTML for additional context
        html = page.content()
        with open('temp_ui_html.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML saved to temp_ui_html.html")

        browser.close()

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else '/'
    selector = sys.argv[2] if len(sys.argv) > 2 else None
    capture_ui(url, selector)
```

Run it:
```bash
# Full page screenshot of home
python temp_ui_verify.py /

# Screenshot of transactions page
python temp_ui_verify.py /transactions

# Screenshot of account holders page
python temp_ui_verify.py /account-holders

# Screenshot of specific element
python temp_ui_verify.py / ".MuiAppBar-root"
```

### Step 3: Analyze the Screenshot

Read the screenshot using the Read tool to see the actual rendered UI:
```
Read temp_ui_screenshot.png
```

Analyze:
- What the user is referring to
- The actual current state of the UI
- What needs to be changed
- What components are involved

### Step 4: Create Todo List

Use TodoWrite to create a plan with specific tasks:
```
1. Verify the issue in the screenshot
2. Identify the component(s) to modify
3. Make the necessary code changes
4. Test the changes with another screenshot
5. Clean up temporary files
```

### Step 5: Make Changes

Based on the screenshot analysis:
1. Identify the exact React component(s) to modify
2. Read the component files
3. Make precise changes
4. Explain what was changed and why

### Step 6: Verify the Fix

After making changes:
1. Take another screenshot using the same script
2. Read the new screenshot
3. Confirm the issue is fixed
4. Mark todos as complete

### Step 7: Clean Up

Remove temporary files:
```bash
rm temp_ui_verify.py temp_ui_screenshot.png temp_ui_html.html
```

## Common UI Pages

- `/` - Home page (file upload)
- `/transactions` - Transactions list with chart
- `/account-holders` - Account holder management

## Common Selectors

- `.MuiAppBar-root` - Navigation bar
- `.MuiButton-root` - Buttons
- `.MuiPaper-root` - Paper containers
- `[data-testid="..."]` - Test ID selectors (best practice)
- `.MuiTableContainer-root` - Tables
- `.recharts-wrapper` - Charts

## Tips

1. **Always verify first** - Never skip the screenshot step
2. **Use specific selectors** - Target exact elements when possible
3. **Full page vs element** - Use full page for layout issues, element screenshots for specific components
4. **Multiple pages** - If the issue spans multiple pages, capture all relevant pages
5. **Before/after** - Always take before and after screenshots
6. **Mobile view** - Can modify script to test responsive designs

## Example Workflow

User says: "The upload button looks weird on the home page"

1. Take screenshot: `python temp_ui_verify.py /`
2. Read screenshot and identify the upload button issue
3. Find it's in FileUpload.js component
4. Make CSS/styling changes
5. Take new screenshot to verify
6. Clean up temp files

## Advanced: Interactive Debugging

For complex issues, use Playwright codegen:
```bash
cd frontend
npx playwright codegen http://localhost:3000
```

This opens a browser where you can interact with the UI and Playwright will generate code showing the selectors and actions.

## Notes

- Screenshots are visual representations that Claude can analyze
- HTML dumps provide additional context for debugging
- Always verify servers are running before attempting screenshots
- Playwright must be installed: `python -m playwright install chromium`
