"""Opt-in built-site fixtures; ordinary offline tests need no browser/build."""
from pathlib import Path
import hashlib
import pytest

from scripts.site_browser_checks import serve_site, site_pages, write_report


def pytest_addoption(parser):
    parser.addoption("--site-dir", default="site", help="Existing strict MkDocs build to audit")
    parser.addoption("--site-report-dir", default="artifacts/browser", help="Browser evidence directory")


def pytest_generate_tests(metafunc):
    if "site_path" in metafunc.fixturenames:
        paths = site_pages(Path(metafunc.config.getoption("--site-dir")))
        metafunc.parametrize("site_path", paths or ["index.html"])


@pytest.fixture(scope="session")
def site_base(pytestconfig):
    root = Path(pytestconfig.getoption("--site-dir")).resolve()
    assert (root / "index.html").is_file(), "Build the site with mkdocs build --strict first"
    with serve_site(root) as base:
        yield base


@pytest.fixture(scope="session")
def link_cache():
    return {}


@pytest.fixture(scope="session")
def site_reports(pytestconfig):
    reports = []
    yield reports
    write_report(Path(pytestconfig.getoption("--site-report-dir")) / "crawl.json", {
        "pages": reports,
        "page_count": len(reports),
        "failed_pages": sum(bool(p["errors"]) for p in reports),
        "images": sum(f["images"] for p in reports for f in p["frames"]),
        "backgrounds": sum(f["backgrounds"] for p in reports for f in p["frames"]),
    })


@pytest.fixture
def report_page(pytestconfig, request, site_reports):
    def record(report, page):
        site_reports.append(report)
        stem = hashlib.sha256(request.node.nodeid.encode()).hexdigest()[:16]
        directory = Path(pytestconfig.getoption("--site-report-dir")) / "pages"
        write_report(directory / f"{stem}.json", report)
        if report["errors"]:
            page.screenshot(path=str(directory / f"{stem}.png"), full_page=False)
    return record


@pytest.fixture(autouse=True)
def no_analytics(request):
    if "page" not in request.fixturenames:
        return
    page = request.getfixturevalue("page")
    # Do not send CI visits to the production analytics account. This is the
    # only request exclusion; images, fonts, scripts and frames still load.
    for pattern in ("**://*.google-analytics.com/**", "**://www.googletagmanager.com/**"):
        page.route(pattern, lambda route: route.fulfill(status=204))
