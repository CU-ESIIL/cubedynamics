"""Cheap browser-audit guardrails; no browser or network needed."""
import pytest
from scripts.site_browser_checks import check_link, page_url, site_pages
from scripts.check_external_links import discover, probe


def test_crawl_includes_standalone_viewers_and_quoted_routes(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").touch()
    (tmp_path / "assets/viewer.html").touch()
    assert site_pages(tmp_path) == ["assets/viewer.html", "index.html"]
    assert page_url("http://localhost/cubedynamics/", "learn/index.html") == "http://localhost/cubedynamics/learn/"
    assert page_url("http://localhost/cubedynamics/", "space name.html").endswith("space%20name.html")


def test_missing_rendered_anchor_and_http_failure_are_not_hidden():
    base = "http://localhost/cubedynamics/"
    link = {"url": base + "#missing", "samePage": True, "fragmentFound": False}
    assert "Missing rendered anchor" in check_link(link, base, None, {})
    link.update(url=base + "gone.html", samePage=False)
    assert "HTTP 404" in check_link(link, base, None, {(link["url"], False): (404, None)})


def test_external_links_are_deduplicated_and_fragments_removed(tmp_path):
    (tmp_path / "index.html").write_text('<a href="https://example.org/a#one">one</a><a href="https://example.org/a#two">two</a><a href="local.html">local</a>')
    assert discover(tmp_path) == ["https://example.org/a"]
    assert probe("http://127.0.0.1/private")["state"] == "unverified"


@pytest.mark.parametrize("head_status", [403, 404, 405, 501])
@pytest.mark.parametrize("get_status", [200, 404])
def test_external_head_fallback_streams_without_consuming_data(monkeypatch, head_status, get_status):
    calls = []
    class Response:
        url = "https://example.org/product.nc"
        def __init__(self, status): self.status_code = status
        def close(self): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Session:
        headers = {}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def head(self, url, **kwargs): return Response(head_status)
        def get(self, url, **kwargs):
            calls.append(kwargs)
            return Response(get_status)
    monkeypatch.setattr("scripts.check_external_links.requests.Session", Session)
    result = probe("https://example.org/product.nc")
    assert result["state"] == ("ok" if get_status == 200 else "failed")
    assert result["head_status"] == head_status
    assert result["method"] == "GET"
    assert calls == [{"stream": True, "timeout": 10}]
