"""
Practical examples of using Playwright with the PDF Bank Parser application.

Run with: pytest tests/e2e/test_example_usage.py -v --headed
"""

import pytest
from playwright.sync_api import Page, expect
import re
from pathlib import Path


@pytest.mark.e2e
class TestPlaywrightExamples:
    """Examples showing common Playwright patterns"""

    def test_basic_navigation(self, page: Page, base_url: str):
        """Example: Basic navigation and element checks"""
        # Navigate to the app
        page.goto(base_url)

        # Wait for page to be fully loaded
        page.wait_for_load_state('networkidle')

        # Check the URL
        expect(page).to_have_url(base_url + '/')

        # Find and verify elements exist
        heading = page.locator('h1, h2, h3').first
        if heading.count() > 0:
            expect(heading).to_be_visible()

    def test_form_interaction_example(self, page: Page, base_url: str):
        """Example: Interacting with forms"""
        page.goto(base_url)

        # Look for select dropdowns (common in your upload flow)
        selects = page.locator('select')

        if selects.count() > 0:
            # Select an option
            selects.first.select_option(index=0)

            # Or select by value
            # selects.first.select_option(value='industrial_checking')

            # Or select by label
            # selects.first.select_option(label='Banco Industrial Checking')

    def test_file_upload_example(self, page: Page, base_url: str, sample_pdf_path):
        """Example: How to upload files"""
        page.goto(base_url)

        # Find file input (usually hidden in dropzone)
        file_input = page.locator('input[type="file"]')

        if file_input.count() > 0:
            # Upload single file
            file_input.set_input_files(str(sample_pdf_path))

            # To upload multiple files:
            # file_input.set_input_files([
            #     str(sample_pdf_path),
            #     str(another_pdf_path)
            # ])

            # To clear the file input:
            # file_input.set_input_files([])

    def test_waiting_for_elements(self, page: Page, base_url: str):
        """Example: Different ways to wait for elements"""
        page.goto(base_url)

        # Wait for specific selector
        page.wait_for_selector('nav', timeout=5000)

        # Wait for element to be visible
        button = page.locator('button').first
        if button.count() > 0:
            button.wait_for(state='visible', timeout=5000)

        # Wait for network to be idle (useful after form submission)
        page.wait_for_load_state('networkidle')

    def test_checking_multiple_elements(self, page: Page, base_url: str):
        """Example: Working with multiple elements"""
        page.goto(base_url)
        page.wait_for_load_state('networkidle')

        # Get all buttons
        buttons = page.locator('button')
        count = buttons.count()
        print(f"Found {count} buttons")

        # Iterate over elements
        for i in range(count):
            button = buttons.nth(i)
            text = button.inner_text()
            print(f"Button {i}: {text}")

    def test_conditional_logic(self, page: Page, base_url: str):
        """Example: Conditional actions based on element presence"""
        page.goto(base_url)

        # Check if element exists before interacting
        upload_link = page.locator('a:has-text("Upload")')

        if upload_link.count() > 0:
            upload_link.click()
            print("Clicked upload link")
        else:
            print("Upload link not found, might already be on upload page")

    @pytest.mark.skip(reason="Example only - requires running backend")
    def test_api_request_example(self, playwright):
        """Example: Making API requests directly"""
        # Create API request context
        request_context = playwright.request.new_context(
            base_url='http://localhost:5000'
        )

        # Make GET request
        response = request_context.get('/api/parser-types/')

        # Check response
        assert response.ok
        data = response.json()
        print(f"Parser types: {data}")

        # Cleanup
        request_context.dispose()

    @pytest.mark.skip(reason="Example only - requires running app")
    def test_screenshot_example(self, page: Page, base_url: str):
        """Example: Taking screenshots"""
        page.goto(base_url)

        # Full page screenshot
        page.screenshot(path='tests/e2e/screenshots/full_page.png')

        # Element screenshot
        element = page.locator('nav').first
        if element.count() > 0:
            element.screenshot(path='tests/e2e/screenshots/nav.png')

    def test_keyboard_and_mouse(self, page: Page, base_url: str):
        """Example: Keyboard and mouse actions"""
        page.goto(base_url)

        # Keyboard
        page.keyboard.press('Tab')
        page.keyboard.type('Hello')
        page.keyboard.press('Enter')

        # Mouse
        # page.mouse.click(100, 200)
        # page.mouse.dblclick(100, 200)

    def test_debugging_tips(self, page: Page, base_url: str):
        """Example: Debugging techniques"""
        page.goto(base_url)

        # Pause execution (useful with --headed)
        # page.pause()

        # Print page content
        # print(page.content())

        # Print element text
        heading = page.locator('h1').first
        if heading.count() > 0:
            print(f"Heading text: {heading.inner_text()}")

        # Get element attributes
        buttons = page.locator('button')
        if buttons.count() > 0:
            first_button = buttons.first
            print(f"Button class: {first_button.get_attribute('class')}")


@pytest.mark.e2e
@pytest.mark.skip(reason="Example - requires running frontend and backend")
class TestCompletePDFWorkflow:
    """Complete workflow example for PDF upload and processing"""

    def test_full_pdf_upload_workflow(
        self,
        page: Page,
        base_url: str,
        sample_pdf_path
    ):
        """
        Complete example of uploading and processing a PDF.

        Prerequisites:
        - Frontend running on http://localhost:3000
        - Backend running on http://localhost:5000
        - Sample PDF available
        """

        # Step 1: Navigate to app
        print("Step 1: Navigating to app...")
        page.goto(base_url)
        expect(page).to_have_url(base_url + '/')

        # Step 2: Go to upload page (adjust based on your routing)
        print("Step 2: Finding upload page...")
        upload_button = page.locator('a:has-text("Upload"), button:has-text("Upload")').first

        if upload_button.count() > 0:
            upload_button.click()
            page.wait_for_load_state('networkidle')

        # Step 3: Upload PDF file
        print("Step 3: Uploading PDF...")
        file_input = page.locator('input[type="file"]')
        expect(file_input).to_be_attached()
        file_input.set_input_files(str(sample_pdf_path))

        # Step 4: Select parser type
        print("Step 4: Selecting parser...")
        parser_select = page.locator('select[name="parser"], select[name="parserType"]').first
        if parser_select.count() > 0:
            parser_select.select_option('industrial_checking')

        # Step 5: Select account holder (if exists)
        print("Step 5: Selecting account holder...")
        account_select = page.locator('select[name="accountHolder"]').first
        if account_select.count() > 0:
            account_select.select_option('husband')

        # Step 6: Submit the form
        print("Step 6: Submitting form...")
        submit_button = page.locator(
            'button[type="submit"], button:has-text("Process"), button:has-text("Submit")'
        ).first
        submit_button.click()

        # Step 7: Wait for processing
        print("Step 7: Waiting for processing...")
        page.wait_for_selector(
            '[data-testid="success"], .success, :has-text("Success")',
            timeout=30000
        )

        # Step 8: Download results
        print("Step 8: Downloading results...")
        download_button = page.locator('a:has-text("Download"), button:has-text("Download")').first

        if download_button.count() > 0:
            with page.expect_download() as download_info:
                download_button.click()

            download = download_info.value
            print(f"Downloaded: {download.suggested_filename}")

            # Save the file
            save_path = Path('tests/e2e/downloads') / download.suggested_filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            download.save_as(str(save_path))
            print(f"Saved to: {save_path}")

        print("Workflow completed successfully!")
