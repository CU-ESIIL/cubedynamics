"""Follow the reference journeys through visible links, at both viewport sizes."""
from pathlib import Path
import re
from urllib.parse import urljoin

import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

pytestmark = [pytest.mark.browser, pytest.mark.integration]


@pytest.mark.parametrize("width", [1280, 390])
def test_reference_navigation_journeys(page, site_base, pytestconfig, width):
    page.set_viewport_size({"width": width, "height": 844})
    article = page.get_by_role("article")
    evidence = Path(pytestconfig.getoption("--site-report-dir")) / "navigation"
    evidence.mkdir(parents=True, exist_ok=True)

    def checkpoint(route, heading, name):
        expect(page).to_have_url(site_base + route)
        expect(article.get_by_role("heading", name=heading, exact=True)).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), route
        page.screenshot(path=str(evidence / f"{width}-{name}.png"), full_page=False)

    def home_section(name):
        page.goto(site_base)
        if width > 1000:
            page.get_by_role("navigation", name="Tabs", exact=True).get_by_role("link", name=name, exact=True).click()
        else:
            # The Home directory stays usable when the tab strip is hidden.
            article.get_by_role("link", name=re.compile(rf"^{name} ")).click()

    # 1. Home -> Library -> noun; 2. noun -> source flavor.
    home_section("Library")
    article.get_by_role("link", name="temperature", exact=True).click()
    checkpoint("library/nouns/temperature/", "temperature", "temperature")
    expect(article.get_by_role("heading", name="Differences among source flavors", exact=True)).to_have_count(1)
    article.get_by_role("link", name="prism", exact=True).click()
    checkpoint("library/sources/prism/", "prism", "source")

    # 3. Home -> Documents -> verbs; 4. category -> implemented operation.
    home_section("Documents")
    checkpoint("documentation/", "Documents", "documents")
    article.get_by_role("link", name="Browse verbs by purpose", exact=True).click()
    checkpoint("reference/verbs/", "Verbs by purpose", "categories")
    for name in ("fit_model", "correlation_cube", "vase_demo"):
        expect(article.get_by_role("link", name=name, exact=True)).to_have_count(0)
    expect(article.get_by_role("link", name="month_filter", exact=True)).to_have_count(1)
    article.get_by_role("link", name="Transform", exact=True).click()
    article.get_by_role("link", name="mean", exact=True).click()
    checkpoint("reference/verbs/mean/", "mean", "verb")

    # 5. Verb -> related vignette; 6. vignette -> noun reference.
    expect(article.get_by_role("link", name="Learn: verbs", exact=True)).to_have_count(1)
    article.get_by_role("link", name="04 · Read the analysis from left to right", exact=True).click()
    checkpoint("vignettes/grammar_basics/", "04 · Read the analysis from left to right", "vignette")
    article.get_by_role("link", name="temperature", exact=True).click()
    checkpoint("library/nouns/temperature/", "temperature", "vignette-to-noun")

    # 7. Documents -> distinct, still-reachable developer material.
    home_section("Documents")
    article.get_by_role("link", name="Developer documentation →", exact=True).click()
    checkpoint("developer/", "Developer documentation", "developer")
    expect(article.get_by_role("link", name="Viewer invariants", exact=True)).to_have_count(1)

    # The complete namespace remains a second, accessible route.
    home_section("Documents")
    article.get_by_role("link", name="All public callables (A–Z)", exact=True).click()
    checkpoint("reference/verbs/a-z/", "All public callables (A–Z)", "all-callables")
    for name in ("mean", "fit_model", "correlation_cube", "month_filter"):
        expect(article.get_by_role("link", name=name, exact=True)).to_have_count(1)


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("noun,source,lesson", [
    ("elevation", "usgs_3dep", "elevation_landscape"),
    ("roads", "overture", "roads_local_network"),
    ("streamflow", "usgs", "streamflow_snapshots"),
])
def test_noun_source_lesson_download_journey(page, site_base, pytestconfig, width, noun, source, lesson):
    page.set_viewport_size({"width": width, "height": 844})
    article = page.get_by_role("article")
    page.goto(site_base + "library/")
    article.get_by_role("link", name=noun, exact=True).click()
    expect(page).to_have_url(site_base + f"library/nouns/{noun}/")
    expect(article.get_by_role("heading", name="Returned data", exact=True)).to_have_count(1)
    image = article.locator("img").first
    image.scroll_into_view_if_needed()
    expect(image).to_be_visible()
    assert image.evaluate("img => img.complete && img.naturalWidth > 100")
    article.get_by_role("link", name=source, exact=True).click()
    expect(page).to_have_url(site_base + f"library/sources/{source}/")
    article.get_by_role("link", name=noun, exact=True).click()
    article.get_by_role("link", name="Full lesson", exact=True).click()
    expect(page).to_have_url(site_base + f"vignettes/{lesson}/")
    download = article.get_by_role("link", name="Download this notebook", exact=True)
    expect(download).to_have_count(1)
    href = download.get_attribute("href")
    response = page.request.get(urljoin(page.url, href))
    assert response.ok
    assert response.json()["metadata"]["cubedynamics"]["supported_vignette"]
    expect(article.locator("img")).to_have_count(3)
    for image in article.locator("img").all():
        image.scroll_into_view_if_needed()
        assert image.evaluate("img => img.complete && img.naturalWidth > 100")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    evidence = Path(pytestconfig.getoption("--site-report-dir")) / "noun-lessons"
    evidence.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(evidence / f"{width}-{noun}.png"), full_page=False)
    article.get_by_role("link", name=noun, exact=True).click()
    expect(page).to_have_url(site_base + f"library/nouns/{noun}/")
