"""
E2E tests for the Django REST API using Playwright.

These tests interact with the API endpoints directly through browser requests.
"""

import pytest
from playwright.sync_api import Page, expect, APIRequestContext
import json


@pytest.mark.e2e
class TestDjangoAPI:
    """Test Django REST API endpoints"""

    @pytest.fixture(scope="class")
    def api_context(self, playwright) -> APIRequestContext:
        """Create an API request context for testing"""
        context = playwright.request.new_context(
            base_url="http://localhost:5000",
            extra_http_headers={
                "Content-Type": "application/json",
            },
        )
        yield context
        context.dispose()

    @pytest.mark.skip(reason="Requires running Django backend")
    def test_parser_types_api(self, api_context: APIRequestContext):
        """Test the parser types endpoint"""
        response = api_context.get("/api/parser-types/")

        assert response.ok
        data = response.json()

        # Verify response structure
        assert isinstance(data, list)
        assert len(data) > 0

        # Check that known parsers are present
        parser_ids = [parser.get("id") for parser in data]
        assert "industrial_checking" in parser_ids

    @pytest.mark.skip(reason="Requires running Django backend and sample PDF")
    def test_upload_and_process_flow(
        self, api_context: APIRequestContext, sample_pdf_path
    ):
        """
        Test the complete upload and process workflow via API.

        This test:
        1. Uploads a PDF file
        2. Processes the file
        3. Checks the status
        4. Downloads the result
        """
        # Step 1: Upload file
        with open(sample_pdf_path, "rb") as pdf_file:
            upload_response = api_context.post(
                "/api/upload/",
                multipart={
                    "files": {
                        "name": "sample.pdf",
                        "mimeType": "application/pdf",
                        "buffer": pdf_file.read(),
                    },
                    "parserType": "industrial_checking",
                    "accountHolder": "husband",
                },
            )

        assert upload_response.ok
        upload_data = upload_response.json()
        session_id = upload_data.get("session_id")
        assert session_id is not None

        # Step 2: Process the uploaded files
        process_response = api_context.post(f"/api/process/{session_id}/")
        assert process_response.ok

        # Step 3: Check processing status
        status_response = api_context.get(f"/api/status/{session_id}/")
        assert status_response.ok
        status_data = status_response.json()

        # The status should indicate completion or processing
        assert status_data.get("status") in ["processing", "completed"]

        # Step 4: If completed, try to download results
        if status_data.get("status") == "completed":
            download_response = api_context.get(f"/api/download/{session_id}/")
            assert download_response.ok

            # Verify we got CSV data
            content_type = download_response.headers.get("content-type", "")
            assert "csv" in content_type.lower() or "text" in content_type.lower()

    @pytest.mark.skip(reason="Requires running Django backend")
    def test_cleanup_session(self, api_context: APIRequestContext):
        """Test session cleanup endpoint"""
        # This test would need a valid session_id
        # For now, we'll just test with a dummy ID to verify endpoint exists
        session_id = "00000000-0000-0000-0000-000000000000"

        response = api_context.delete(f"/api/cleanup/{session_id}/")

        # We expect either success or 404 (session not found)
        assert response.status in [200, 204, 404]


@pytest.mark.e2e
@pytest.mark.slow
class TestFullUserJourney:
    """Test complete user journeys through the application"""

    @pytest.mark.skip(reason="Requires running frontend and backend")
    def test_complete_pdf_processing_journey(
        self, page: Page, base_url: str, sample_pdf_path
    ):
        """
        Test the complete user journey from upload to download.

        This is a comprehensive E2E test that verifies:
        1. User can access the application
        2. User can upload a PDF
        3. User can select parser type
        4. User can process the PDF
        5. User can see processing status
        6. User can download results
        """
        # 1. Access application
        page.goto(base_url)
        expect(page).to_have_url(base_url + "/")

        # 2. Navigate to upload (adjust based on your UI)
        upload_button = page.locator(
            'a:has-text("Upload"), button:has-text("Upload")'
        ).first
        if upload_button.count() > 0:
            upload_button.click()

        # 3. Upload PDF file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(sample_pdf_path))

        # 4. Select parser and account holder
        page.select_option('select[name="parser"]', "industrial_checking")
        page.select_option('select[name="accountHolder"]', "husband")

        # 5. Submit for processing
        process_button = page.locator(
            'button[type="submit"], button:has-text("Process")'
        ).first
        process_button.click()

        # 6. Wait for processing to complete
        page.wait_for_selector(
            '[data-testid="processing-complete"]', timeout=60000
        )

        # 7. Verify success
        success_indicator = page.locator('[data-testid="success-message"]')
        expect(success_indicator).to_be_visible()

        # 8. Download results
        download_button = page.locator(
            'a:has-text("Download"), button:has-text("Download")'
        ).first
        if download_button.count() > 0:
            with page.expect_download() as download_info:
                download_button.click()

            download = download_info.value
            # Verify download
            assert download.suggested_filename.endswith(".csv")
