"""Rendered package-wide overview-manuscript checks."""

from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect


pytestmark = [pytest.mark.browser, pytest.mark.integration]


@pytest.mark.parametrize("width", [1280, 390])
def test_overview_manuscript_page_renders_and_links_downloads(
    page, site_base, pytestconfig, width
):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console",
        lambda message: errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.set_viewport_size({"width": width, "height": 900})
    response = page.goto(site_base + "documentation/overview_manuscript/", wait_until="load")
    assert response is not None and response.status == 200

    article = page.locator("article")
    expect(
        article.get_by_role("heading", name="CubeDynamics overview manuscript", exact=True)
    ).to_be_visible()
    text = article.inner_text()
    for phrase in (
        "CubeDynamics: An Inspectable Grammar for Environmental Data Analysis",
        "19 pages",
        "33 pages",
        "25 September 2026",
        "0.1.0rc3",
        "sources of truth",
    ):
        assert phrase in text
    expect(
        article.get_by_role("link", name="Download the overview manuscript", exact=False)
    ).to_have_count(1)
    expect(
        article.get_by_role("link", name="Download the supplement", exact=False)
    ).to_have_count(1)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    assert not errors

    evidence = Path(pytestconfig.getoption("--site-report-dir")) / "overview-manuscript"
    evidence.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(evidence / f"{width}-overview-manuscript.png"), full_page=False)
