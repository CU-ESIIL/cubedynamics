"""Presentation checks only; numerical correctness lives in offline/source QA."""
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

pytestmark = [pytest.mark.browser, pytest.mark.integration]


def decoded_and_fitted(image, width):
    image.scroll_into_view_if_needed()
    image.evaluate("async image => { await image.decode(); }")
    assert image.evaluate("image => image.complete && image.naturalWidth >= 500 && image.naturalHeight >= 300")
    box = image.bounding_box()
    assert box and box["width"] > (310 if width == 390 else 250)
    assert box["x"] >= 0 and box["x"] + box["width"] <= width + 1


def readable(caption):
    expect(caption).to_be_visible()
    assert len(caption.inner_text()) > 70
    assert caption.evaluate("e => parseFloat(getComputedStyle(e).fontSize)") >= 14


def evidence(page, pytestconfig, width, name):
    directory = Path(pytestconfig.getoption("--site-report-dir")) / "visual-examples"
    directory.mkdir(parents=True, exist_ok=True)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    page.screenshot(path=str(directory / f"{width}-{name}.png"), full_page=False)


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("route,keys", [
    ("learn/verbs/", ("observed", "subset", "anomaly", "summary", "standardize", "export")),
    ("library/nouns/temperature/", ("observed",)),
    ("datasets/which_dataset/", ("sources",)),
    ("reference/verbs/anomaly/", ("anomaly",)),
    ("reference/verbs/threshold_state/", ("threshold",)),
])
def test_static_code_result_interpretation(page, site_base, pytestconfig, width, route, keys):
    page.set_viewport_size({"width": width, "height": 844})
    page.goto(site_base + route)
    for key in keys:
        section = page.locator(f'.cd-analysis-step[data-example="{key}"]')
        expect(section).to_have_count(1)
        expect(section.locator("pre code")).to_have_count(1)
        assert section.evaluate("""s => {
          const code = s.querySelector('pre'), result = s.querySelector('.cd-generated-result'),
                interpretation = s.querySelector('.cd-interpretation');
          return !!(code.compareDocumentPosition(result) & Node.DOCUMENT_POSITION_FOLLOWING)
            && !!(result.compareDocumentPosition(interpretation) & Node.DOCUMENT_POSITION_FOLLOWING);
        }""")
        if key == "export":
            table = section.get_by_role("table")
            expect(table).to_contain_text("Equal (asserted)")
            expect(table).to_contain_text("portable flag")
            section.locator(".cd-result-caption").scroll_into_view_if_needed()
            readable(section.locator(".cd-result-caption"))
        else:
            decoded_and_fitted(section.locator("figure img"), width)
            readable(section.locator("figcaption"))
        evidence(page, pytestconfig, width, route.replace("/", "-") + key)
    page.locator(".cd-example-setup summary").click()
    expect(page.locator(".cd-example-setup pre code")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")


@pytest.mark.parametrize("width", [1280, 390])
def test_native_notebook_code_result_pairs(page, site_base, pytestconfig, width):
    page.set_viewport_size({"width": width, "height": 844})
    page.goto(site_base + "vignettes/grammar_basics/")
    questions = page.locator(".cd-notebook-question")
    expect(questions).to_have_count(6)
    for question in questions.all():
        key = question.get_attribute("data-example")
        # Notebook inputs and outputs share a code cell; caption is its next cell.
        code_cell = question.locator("xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' jp-Cell ')][1]/following-sibling::div[1]")
        expect(code_cell.locator(".jp-InputArea pre")).to_have_count(1)
        caption = code_cell.locator("xpath=following-sibling::div[1]").locator(f'.cd-result-caption[data-example="{key}"]')
        if key == "export":
            table = code_cell.locator(".jp-OutputArea table")
            expect(table).to_contain_text("Equal (asserted)")
            expect(table).to_contain_text("portable flag")
            caption.scroll_into_view_if_needed()
        else:
            decoded_and_fitted(code_cell.locator(".jp-OutputArea img"), width)
        readable(caption)
        evidence(page, pytestconfig, width, f"notebook-{key}")
