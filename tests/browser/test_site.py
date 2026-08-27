"""Run with pytest tests/browser -m browser after a strict MkDocs build."""
import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

from scripts.site_browser_checks import activate_embeds, audit_page, page_url

pytestmark = [pytest.mark.browser, pytest.mark.integration]


def test_every_built_page(page, site_base, site_path, link_cache, report_page):
    report = audit_page(page, page_url(site_base, site_path), site_base, link_cache)
    report_page(report, page)
    assert not report["errors"], "\n".join(report["errors"])


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("route", ["", "learn/", "library/", "documentation/", "vignettes/"])
def test_primary_destinations_fit_viewport(page, site_base, route, width):
    page.set_viewport_size({"width": width, "height": 844})
    page.goto(site_base + route)
    expect(page.locator("article h1")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "Page overflows horizontally"
    if width > 1000:
        tabs = page.get_by_role("navigation", name="Tabs", exact=True)
        expect(tabs.get_by_role("link")).to_have_text(["Home", "Learn", "Library", "Documents", "Vignettes"])


def test_home_cube_loads_rotates_and_zooms(page, site_base):
    page.goto(site_base)
    activate_embeds(page)
    frame = page.frame_locator("[data-deferred-embed] iframe")
    surface = frame.locator(".cube-drag-surface")
    wrapper = frame.locator(".cube-wrapper")
    cube = frame.locator(".cd-cube")
    expect(surface).to_be_visible()
    expect(cube).to_be_visible()
    expect(cube.locator(".cd-face")).to_have_count(6)
    surface.scroll_into_view_if_needed()
    before = wrapper.evaluate("el => getComputedStyle(el).getPropertyValue('--rot-y')")
    box = surface.bounding_box()
    assert box and box["width"] > 0 and box["height"] > 0
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 65, y + 25, steps=8)
    page.mouse.up()
    page.wait_for_function("({frame, before}) => getComputedStyle(document.querySelector(frame).contentDocument.querySelector('.cube-wrapper')).getPropertyValue('--rot-y') !== before", arg={"frame": "[data-deferred-embed] iframe", "before": before})
    zoom = wrapper.evaluate("el => getComputedStyle(el).getPropertyValue('--zoom')")
    surface.hover()
    page.mouse.wheel(0, 100)
    page.wait_for_function("before => getComputedStyle(document.querySelector('[data-deferred-embed] iframe').contentDocument.querySelector('.cube-wrapper')).getPropertyValue('--zoom') !== before", arg=zoom)


def test_repository_link_does_not_require_github_metadata(page, site_base):
    page.goto(site_base)
    expect(page.locator(".md-header__source a")).to_have_attribute(
        "href", "https://github.com/CU-ESIIL/cubedynamics"
    )
    # No metadata component means Material does not query releases/stars/forks.
    expect(page.locator('[data-md-component="source"]')).to_have_count(0)
