"""The built site, in a real browser."""

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def test_built_page_shows_the_name(page, site_url):
    page.goto(site_url)
    expect(page.get_by_role("heading", level=1)).to_have_text("Omar Seteen")
