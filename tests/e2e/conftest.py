import pytest
from playwright.sync_api import Page, expect

# Playwright fixtures are automatically provided by pytest-playwright
# including: page, browser, context, browser_name, etc.

@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application"""
    return "http://localhost:3000"

@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for the Django API"""
    return "http://localhost:5000"

@pytest.fixture
def authenticated_page(page: Page, base_url: str):
    """
    Fixture for an authenticated page session.
    Modify this based on your actual authentication flow.
    """
    page.goto(base_url)
    # Add authentication logic here if needed
    # For example:
    # page.fill('input[name="username"]', 'testuser')
    # page.fill('input[name="password"]', 'testpass')
    # page.click('button[type="submit"]')
    # page.wait_for_url(f"{base_url}/dashboard")

    return page

@pytest.fixture
def sample_pdf_path():
    """Path to a sample PDF for upload testing"""
    from pathlib import Path
    # Use the same fixtures from the parent conftest
    return Path(__file__).parent.parent / "fixtures" / "sample_statement.pdf"
