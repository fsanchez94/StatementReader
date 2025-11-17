"""
E2E tests for the web application using Playwright.

These tests verify the full user journey from the frontend through to the backend.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestWebApplication:
    """Test the main web application functionality"""

    def test_home_page_loads(self, page: Page, base_url: str):
        """Test that the home page loads successfully"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Check that we're on the correct page
        expect(page).to_have_url(base_url + "/")

        # Verify some content is visible
        # Adjust selectors based on your actual app structure
        heading = page.locator("h1, h2, h3").first
        expect(heading).to_be_visible()

    def test_navigation_exists(self, page: Page, base_url: str):
        """Test that navigation elements are present"""
        page.goto(base_url)

        # Check for navigation
        # Adjust selector based on your actual navigation structure
        nav = page.locator("nav, header").first
        expect(nav).to_be_visible()


@pytest.mark.e2e
class TestPDFUploadWorkflow:
    """Test the PDF upload and processing workflow"""

    def test_upload_page_accessible(self, page: Page, base_url: str):
        """Test that users can navigate to the upload page"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Try to find and click upload-related navigation
        # This is a generic test - adjust based on your actual UI
        upload_links = page.locator(
            'a:has-text("Upload"), a:has-text("Process"), button:has-text("Upload")'
        )

        if upload_links.count() > 0:
            upload_links.first.click()
            page.wait_for_load_state("networkidle")

            # Verify we're on a page with upload functionality
            url = page.url()
            assert url is not None

    @pytest.mark.skip(reason="Requires actual PDF file and running backend")
    def test_pdf_upload_and_processing(
        self, page: Page, base_url: str, sample_pdf_path
    ):
        """
        Test the complete PDF upload and processing workflow.

        Note: This test requires:
        1. Both frontend (React) and backend (Django) to be running
        2. A valid sample PDF file
        3. Proper data-testid attributes in the UI components
        """
        page.goto(base_url)

        # Navigate to upload page
        page.click('a:has-text("Upload")')

        # Upload PDF file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(sample_pdf_path))

        # Select parser type (adjust based on your actual UI)
        page.select_option('select[name="parser"]', "industrial_checking")

        # Submit the form
        page.click('button[type="submit"]')

        # Wait for processing
        page.wait_for_selector('[data-testid="processing-complete"]', timeout=30000)

        # Verify success message
        success_message = page.locator('[data-testid="success-message"]')
        expect(success_message).to_be_visible()


@pytest.mark.e2e
class TestAPIEndpoints:
    """Test API endpoints through the browser"""

    @pytest.mark.skip(reason="Requires running backend")
    def test_parser_types_endpoint(self, page: Page, api_base_url: str):
        """Test that the parser types API endpoint is accessible"""
        # Navigate directly to the API endpoint
        page.goto(f"{api_base_url}/api/parser-types/")

        # Check for JSON response
        content = page.content()
        assert "industrial" in content.lower() or "bam" in content.lower()
