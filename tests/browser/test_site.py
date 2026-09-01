"""Run with pytest tests/browser -m browser after a strict MkDocs build."""
import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

from scripts.site_browser_checks import activate_embeds, audit_page, page_url
from scripts.hero_examples import EXAMPLES

pytestmark = [pytest.mark.browser, pytest.mark.integration]


def test_outside_user_installation_journey(page, site_base):
    page.goto(site_base)
    page.get_by_role("link", name="Installation status and release instructions").click()
    expect(page.locator("article h1")).to_have_text("Installation & setup")
    expect(page.get_by_role("heading", name="Public release candidate")).to_be_visible()
    assert "cubedynamics==0.1.0rc1" in page.locator("article").inner_text()
    page.locator("article").get_by_role("link", name="Quickstart", exact=True).click()
    expect(page.get_by_role("heading", name="First executable example — public reviewed observations")).to_be_visible()
    assert "hashlib.sha256(payload)" in page.locator("article").inner_text()
    page.locator("article").get_by_role("link", name="installation and release instructions").click()
    page.locator("article").get_by_role("link", name="RC release notes").click()
    expect(page.locator("article h1")).to_have_text("0.1.0rc1 release notes")
    expect(page.get_by_role("heading", name="Outside-user acceptance findings")).to_be_visible()
    article = page.locator("article").inner_text()
    assert "published as 0.1.0rc1" in article
    assert "subsequent, separately versioned candidate" in article


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
    if route == "":
        assert page.locator(".cd-hero-copy h1").evaluate("""el => {
          const range = document.createRange();
          range.selectNodeContents(el);
          const box = range.getBoundingClientRect();
          return box.left >= 0 && box.right <= innerWidth + 1;
        }"""), "Homepage title is clipped by the viewport"
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


@pytest.mark.parametrize("width", [1280, 390])
def test_home_cube_readability_and_controls(page, site_base, width):
    page.set_viewport_size({"width": width, "height": 844})
    page.goto(site_base)
    activate_embeds(page)
    frame = page.frame_locator("[data-deferred-embed] iframe")
    title = frame.locator(".colorbar-title")
    expect(title).to_have_text("Daily maximum temperature (°C)")
    expect(frame.locator(".cb-tick")).to_have_count(5)
    expect(frame.locator('.cd-axis-x .cd-axis-name')).to_have_text("Longitude")
    expect(frame.locator('.cd-axis-y .cd-axis-name')).to_have_text("Latitude")
    expect(frame.locator('.cd-axis-time .cd-axis-end--min')).to_have_text("30 Jan 2024")
    expect(frame.locator('.cd-axis-time .cd-axis-end--max')).to_have_text("01 Jan 2024")
    # Relative positions and computed styles catch the former white-on-white
    # legend, clipped iframe layout, and cube/legend overlap in either theme.
    report = title.evaluate("""el => {
      const doc = el.ownerDocument;
      const win = doc.defaultView;
      const rect = selector => doc.querySelector(selector).getBoundingClientRect();
      const legend = rect('.cube-legend-panel');
      const stage = rect('.cube-main');
      return {
        ink: win.getComputedStyle(el).color,
        paper: win.getComputedStyle(doc.querySelector('.cube-legend-card')).backgroundColor,
        stageAboveLegend: stage.bottom <= legend.top + 1,
        legendFits: legend.bottom <= win.innerHeight + 1,
        noOverflow: doc.documentElement.scrollWidth <= win.innerWidth + 1,
        datesFit: [...doc.querySelectorAll('.cd-axis-time .cd-axis-end span')].every(label => {
          const box = label.getBoundingClientRect();
          return box.left >= 0 && box.right <= win.innerWidth && box.bottom < legend.top;
        }),
        facesFit: [...doc.querySelectorAll('.cd-face')].every(face => {
          const box = face.getBoundingClientRect();
          return box.bottom < legend.top && box.top > stage.top;
        })
      };
    }""")
    assert report == {
        "ink": "rgb(33, 62, 70)", "paper": "rgb(255, 255, 255)",
        "stageAboveLegend": True, "legendFits": True,
        "noOverflow": True, "datesFit": True, "facesFit": True,
    }
    wrapper = frame.locator(".cube-wrapper")
    surface = frame.locator(".cube-drag-surface")
    before = wrapper.get_attribute("style")
    surface.focus()
    surface.press("ArrowRight")
    assert wrapper.get_attribute("style") != before
    # Compose the rotations actually used by the browser. Every label face
    # must cancel both camera rotations and the time axis's local rotation.
    assert wrapper.evaluate("""el => {
      const doc = el.ownerDocument, win = doc.defaultView;
      const matrix = el => new win.DOMMatrixReadOnly(win.getComputedStyle(el).transform);
      const rotation = matrix(doc.querySelector('.cube-rotation'));
      return [...doc.querySelectorAll('.cd-axis-name .cd-axis-label-face')].every(face => {
        const combined = rotation.multiply(matrix(face.closest('.cd-axis-group'))).multiply(matrix(face));
        return ['m12', 'm13', 'm21', 'm23', 'm31', 'm32'].every(k => Math.abs(combined[k]) < .00001)
          && combined.m11 > 0 && combined.m22 > 0 && combined.m33 > 0;
      });
    }""")
    frame.get_by_role("button", name="Zoom in", exact=True).click()
    frame.get_by_role("button", name="Reset view", exact=True).click()
    assert wrapper.get_attribute("style") == before


@pytest.mark.parametrize("width", [1280, 390])
def test_home_gallery_loads_only_selected_example(page, site_base, width):
    page.set_viewport_size({"width": width, "height": 844})
    requests, errors = [], []
    page.on("request", lambda req: requests.append(req.url))
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(site_base)
    activate_embeds(page)
    select = page.get_by_role("combobox", name="Explore an example")
    expect(select).to_be_enabled()
    expect(select.locator("option")).to_have_count(len(EXAMPLES))
    assert select.evaluate("""el => {
      const art = el.closest('.cd-hero-art').getBoundingClientRect();
      const box = el.getBoundingClientRect();
      const frame = document.querySelector('#hero-cube-frame').getBoundingClientRect();
      return box.top >= art.top && box.bottom <= frame.top && box.left >= art.left && box.right <= art.right;
    }"""), "The selector is clipped by the hero container"
    assert {url for url in requests if url.endswith(".html") and "/assets/figures/" in url} == {site_base + EXAMPLES[0]["path"]}
    for example in EXAMPLES:
        select.select_option(example["path"])
        frame = page.frame_locator("#hero-cube-frame")
        expect(page.locator("#hero-cube-frame")).to_have_attribute("src", site_base + example["path"])
        expect(page.locator("#hero-cube-description")).to_have_text(example["description"])
        expect(page.locator("#hero-cube-open")).to_have_attribute("href", example["path"])
        expect(page.locator("#hero-cube-lesson")).to_have_attribute("href", example["lesson"])
        expect(page.locator("[data-deferred-embed]")).to_have_attribute("data-loaded", "true")
        expect(page.locator("#hero-cube-frame")).to_have_count(1)
        if example["kind"] == "cube":
            expect(frame.locator(".cube-title")).to_have_text(example["title"])
            expect(frame.locator(".colorbar-title")).to_have_text(example["legend"])
            expect(frame.locator(".cd-face")).to_have_count(6)
            assert frame.locator(".cube-legend-panel").evaluate("el => el.getBoundingClientRect().bottom <= innerHeight + 1"), example["id"]
            # Each switch gets a fresh, functioning library camera.
            surface = frame.locator(".cube-drag-surface")
            wrapper = frame.locator(".cube-wrapper")
            before = wrapper.get_attribute("style")
            surface.focus()
            surface.press("ArrowLeft")
            assert wrapper.get_attribute("style") != before
            frame.get_by_role("button", name="Reset view").click()
            assert wrapper.get_attribute("style") == before
        else:
            expect(frame.locator(".js-plotly-plot canvas").first).to_be_visible(timeout=30000)
            expect(page.locator("#hero-cube-kind")).to_have_text("Specialized fire hull · Plotly")
        response = page.request.get(site_base + example["lesson"])
        assert response.status == 200, example["lesson"]
        response.dispose()
    assert not errors


def test_home_gallery_quick_switches_and_returns_to_default(page, site_base):
    page.goto(site_base)
    activate_embeds(page)
    select = page.get_by_role("combobox", name="Explore an example")
    for example in [EXAMPLES[6], EXAMPLES[10], EXAMPLES[2], EXAMPLES[0]]:
        select.select_option(example["path"])
    frame = page.frame_locator("#hero-cube-frame")
    expect(frame.locator(".colorbar-title")).to_have_text(EXAMPLES[0]["legend"])
    expect(page.locator("[data-deferred-embed]")).to_have_attribute("data-loaded", "true")
    expect(page.locator("#hero-cube-open")).to_have_attribute("href", EXAMPLES[0]["path"])


def test_home_gallery_without_javascript_has_all_standalone_links(browser, site_base):
    context = browser.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        page.goto(site_base)
        for example in EXAMPLES:
            expect(page.locator(f'.cd-html-cube-hero noscript a[href="{example["path"]}"]')).to_be_visible()
    finally:
        context.close()
