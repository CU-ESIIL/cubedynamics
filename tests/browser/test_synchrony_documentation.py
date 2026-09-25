"""Rendered synchrony-documentation checks at desktop and narrow widths."""

from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

pytestmark = [pytest.mark.browser, pytest.mark.integration]


PAGES = (
    (
        "recipes/spatial_synchrony_signature/",
        "Local climate-tail synchrony: pairs, surfaces, summaries, and scaling",
        "workflow",
    ),
    (
        "synchrony/empirical_synchrony_decay/",
        "Empirical synchrony decay",
        "decay",
    ),
    (
        "synchrony/empirical_synchrony_range/",
        "Empirical local synchrony range",
        "range",
    ),
    (
        "reference/verbs/local_synchrony_pairs/",
        "local_synchrony_pairs",
        "pairs-reference",
    ),
    (
        "reference/verbs/",
        "Verbs by purpose",
        "verbs-by-purpose",
    ),
    (
        "synchrony/",
        "Synchrony",
        "synchrony-overview",
    ),
)


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("route,heading,slug", PAGES)
def test_synchrony_pages_render_and_fit(
    page, site_base, pytestconfig, width, route, heading, slug
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
    response = page.goto(site_base + route, wait_until="load")
    assert response is not None and response.status == 200

    article = page.locator("article")
    expect(article.get_by_role("heading", name=heading, exact=True)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    assert not errors

    text = article.inner_text()
    if slug == "workflow":
        for phrase in (
            "MEASURE S(i,j)",
            "S_p(dx,dy)",
            "R_common",
            "observational agreement",
            "blue for positive/cold-stronger",
            "red for negative/warm-stronger",
        ):
            assert phrase in text
        expect(article.locator("table")).to_have_count(2)
        assert article.locator("pre").count() >= 7
    elif slug == "decay":
        for phrase in ("d25", "d50", "d75", "Effective length", "Near slope"):
            assert phrase in text
        expect(article.locator("table")).to_have_count(1)
    elif slug == "range":
        assert "not the preferred general method" in text
        assert "not promoted into a general adaptive-radius rule" in text
    elif slug == "pairs-reference":
        assert "Maximum physical search/observation support" in text
        assert "Positive Delta means cold synchrony is stronger" in text
    elif slug == "verbs-by-purpose":
        for name in (
            "local_synchrony_pairs",
            "local_synchrony_surface",
            "synchrony_surface_diagnostics",
            "synchrony_signature",
            "empirical_synchrony_range",
            "empirical_synchrony_decay",
            "landscape_change_signature",
        ):
            expect(article.get_by_role("link", name=name, exact=True)).to_have_count(1)
    elif slug == "synchrony-overview":
        expect(
            article.get_by_role("link", name="Local Climate-Tail Surfaces", exact=True)
        ).to_be_visible()

    evidence = Path(pytestconfig.getoption("--site-report-dir")) / "synchrony-docs"
    evidence.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(evidence / f"{width}-{slug}.png"), full_page=False)


@pytest.mark.parametrize("width", [1280, 390])
def test_published_climate_synchrony_panel_uses_blue_positive_delta(
    page, site_base, pytestconfig, width
):
    page.set_viewport_size({"width": width, "height": 900})
    response = page.goto(
        site_base + "assets/figures/climate_synchrony_cube_panel.html",
        wait_until="load",
    )
    assert response is not None and response.status == 200
    expect(page.locator(".colorbar-title")).to_contain_text("red warm / blue cold")

    evidence = Path(pytestconfig.getoption("--site-report-dir")) / "synchrony-docs"
    evidence.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(evidence / f"{width}-climate-panel.png"), full_page=False)
