"""Prove the browser checks can fail; these are DOM fixtures, not science data."""
import pytest

pytest.importorskip("playwright.sync_api")
pytest.importorskip("pytest_playwright")
from scripts.site_browser_checks import audit_page, serve_site

pytestmark = [pytest.mark.browser, pytest.mark.integration]


@pytest.mark.parametrize(("body", "expected"), [
    ('<img src="broken.png">', "Image"),
    ('<div style="background-image:url(broken.png)">face</div>', "Image"),
    ('<a href="missing.html">broken</a>', "HTTP 404"),
    ('<a href="#missing">broken</a>', "Missing rendered anchor"),
    ('<script>throw Error("control failure")</script>', "JavaScript"),
    ('<script>console.error("control failure")</script>', "Console"),
    ('<iframe src="missing.html"></iframe>', "HTTP 404"),
    ('<iframe src="about:blank"></iframe>', "stayed blank"),
])
def test_detector_rejects_bad_page(page, tmp_path, body, expected):
    (tmp_path / "index.html").write_text(f"<!doctype html><html><body>{body}</body></html>")
    (tmp_path / "broken.png").write_text("not an image even though HTTP returns 200")
    with serve_site(tmp_path) as base:
        report = audit_page(page, base, base, {})
    assert any(expected in error for error in report["errors"]), report


def test_detector_accepts_inline_svg_and_lazy_frame(page, tmp_path):
    (tmp_path / "image.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>')
    (tmp_path / "target.html").write_text('<h1 id="result">Result</h1>')
    (tmp_path / "index.html").write_text('''<!doctype html><html><body>
      <a href="target.html#result">Result</a><img loading="lazy" src="image.svg">
      <iframe loading="lazy" src="target.html" style="margin-top:2000px"></iframe>
      </body></html>''')
    with serve_site(tmp_path) as base:
        report = audit_page(page, base, base, {})
    assert not report["errors"], report
    assert len(report["frames"]) == 2


def test_directory_redirect_preserves_pages_prefix(page, tmp_path):
    (tmp_path / "lesson").mkdir()
    (tmp_path / "lesson/index.html").write_text('<h1 id="result">Result</h1>')
    (tmp_path / "index.html").write_text('<a href="lesson#result">Result</a>')
    with serve_site(tmp_path) as base:
        report = audit_page(page, base, base, {})
        page.get_by_role("link", name="Result").click()
        assert page.url == base + "lesson/#result"
    assert not report["errors"], report
