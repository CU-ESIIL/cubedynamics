"""Reusable browser assertions for the built site (no scientific data requests).

Imported by tests/browser; Playwright stays an optional test dependency.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import quote, unquote, urldefrag, urlsplit
import json

from scripts.check_site_links import Links


def site_pages(root: Path) -> list[str]:
    """Include standalone viewer HTML, not only pages reachable from the nav."""
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*.html"))


@contextmanager
def serve_site(root: Path):
    """Mount at the real Pages prefix to catch broken absolute/relative URLs."""
    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            # Preserve self.path so directory redirects retain the Pages prefix.
            return super().translate_path(path[len("/cubedynamics"):])

        def do_GET(self):
            if not self.path.startswith("/cubedynamics/"):
                self.send_error(404)
                return
            super().do_GET()

        def do_HEAD(self):
            if not self.path.startswith("/cubedynamics/"):
                self.send_error(404)
                return
            super().do_HEAD()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(root)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/cubedynamics/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def page_url(base: str, path: str) -> str:
    return base + quote(path[:-10] if path.endswith("index.html") else path, safe="/")


def same_origin(url: str, base: str) -> bool:
    return urlsplit(url)[:2] == urlsplit(base)[:2]


def short_url(url: str) -> str:
    # Embedded notebook figures can be megabytes: do not fill reports with them.
    return url[:140] + "…" if len(url) > 160 else url


# Decode actual <img> elements, including selected srcset candidates, lazy images
# and inline PNG/SVG notebook outputs. Check CSS backgrounds as well (cube faces).
CHECK_IMAGES = r"""async () => {
  const failures = [];
  const images = [...document.images];
  for (const img of images) img.loading = 'eager';
  const decode = async (img, label) => {
    let timer;
    try {
      await Promise.race([
        img.decode(),
        new Promise((_, reject) => { timer = setTimeout(() => reject(Error('decode timeout')), 12000); })
      ]);
      if (!img.complete || img.naturalWidth === 0 || img.naturalHeight === 0) throw Error('empty image');
    } catch (e) { failures.push({image: label.slice(0,160), reason: String(e)}); }
    finally { clearTimeout(timer); }
  };
  await Promise.all(images.map(img => decode(img, img.currentSrc || img.src || '<missing src>')));
  const backgrounds = new Set();
  for (const el of document.querySelectorAll('*')) {
    for (const pseudo of [null, '::before', '::after']) {
      const style = getComputedStyle(el, pseudo);
      for (const match of style.backgroundImage.matchAll(/url\(["']?(.*?)["']?\)/g)) backgrounds.add(match[1]);
    }
  }
  await Promise.all([...backgrounds].map(url => {
    const img = new Image(); img.src = url; return decode(img, url);
  }));
  return {images: images.length, backgrounds: backgrounds.size, failures};
}"""

READ_LINKS = """() => [...document.querySelectorAll('a[href]')].map(a => {
  const target = new URL(a.getAttribute('href'), document.baseURI);
  const current = new URL(document.baseURI);
  const samePage = target.origin === current.origin && target.pathname === current.pathname && target.search === current.search;
  let fragment = target.hash.slice(1);
  try { fragment = decodeURIComponent(fragment); } catch (_) {}
  return {url: target.href, samePage,
    fragmentFound: !fragment || !!document.getElementById(fragment) || !!document.getElementsByName(fragment).length};
})"""


def activate_embeds(page):
    """Use the visible load controls; never manufacture an iframe src in tests."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    for wrapper in page.locator("[data-deferred-embed]").all():
        wrapper.scroll_into_view_if_needed()
        button = wrapper.locator("button")
        if button.count() and button.is_visible():
            try:
                button.click(timeout=2000)
            except PlaywrightTimeoutError:
                # The idle/visibility loader may complete between is_visible
                # and click. A disappeared button is fine only if it loaded.
                if wrapper.get_attribute("data-loaded") != "true":
                    raise
        # Load events alone also fire for 404 documents. Network checks and the
        # nonempty-frame assertion below separately verify successful loading.
        page.wait_for_function("el => el.dataset.loaded === 'true'", arg=wrapper.element_handle(), timeout=15000)
    # Ordinary lazy iframes (not wrapped by the site's deferred loader).
    for frame in page.locator("iframe").all():
        frame.scroll_into_view_if_needed()

        source = frame.get_attribute("src")
        if not source or source == "about:blank":
            continue
        # A lazy iframe has an already-loaded initial about:blank document.
        # Frame.wait_for_load_state("load") can therefore return before the
        # requested navigation even starts. Match the browsing context to the
        # element's resolved src and wait for that document to finish instead;
        # otherwise page teardown can cancel a still-active navigation and
        # surface a misleading net::ERR_ABORTED in the crawl.
        page.wait_for_function(
            """frame => {
              const expected = new URL(frame.getAttribute('src'), document.baseURI).href;
              try {
                return frame.contentWindow.location.href === expected
                  && frame.contentDocument.readyState === 'complete';
              } catch (_) {
                return false;
              }
            }""",
            arg=frame.element_handle(),
            timeout=30000,
        )
    for frame in page.frames:
        frame.wait_for_load_state("load", timeout=20000)


def check_link(link, base, request, cache):
    url = link["url"]
    public_prefix = "https://cu-esiil.github.io/cubedynamics/"
    if url.startswith(public_prefix):
        url = base + url[len(public_prefix):]
    if urlsplit(url).scheme not in {"http", "https"} or not same_origin(url, base):
        return None
    target, fragment = urldefrag(url)
    if link["samePage"]:
        return None if link["fragmentFound"] else f"Missing rendered anchor: {short_url(url)}"
    key = (target, bool(fragment))
    if key not in cache:
        response = request.get(target, timeout=15000) if fragment else request.head(target, timeout=15000)
        try:
            ids = None
            if fragment and "text/html" in response.headers.get("content-type", ""):
                parser = Links()
                parser.feed(response.text())
                ids = parser.ids
            cache[key] = (response.status, ids)
        finally:
            response.dispose()
    status, ids = cache[key]
    if not 200 <= status < 400:
        return f"HTTP {status}: {short_url(url)}"
    if fragment and ids is not None and unquote(fragment) not in ids:
        return f"Missing target anchor: {short_url(url)}"
    return None


def audit_page(page, url, base, link_cache):
    report = {"url": url, "errors": [], "external_links": [], "frames": [], "network_failures": []}
    errors = report["errors"]
    page.on("pageerror", lambda error: errors.append(f"JavaScript: {error}"))
    page.on("console", lambda msg: errors.append(f"Console: {msg.text}") if msg.type == "error" else None)

    def failed_request(request):
        report["network_failures"].append({"url": short_url(request.url), "reason": request.failure})
        errors.append(f"Request failed: {short_url(request.url)}: {request.failure}")

    def response_received(response):
        if response.status >= 400:
            errors.append(f"Resource HTTP {response.status}: {short_url(response.url)}")

    page.on("requestfailed", failed_request)
    page.on("response", response_received)
    try:
        response = page.goto(url, wait_until="load", timeout=30000)
        if response is None or response.status != 200:
            errors.append(f"Page did not return 200: {response.status if response else 'no response'}")
        activate_embeds(page)
        for frame in page.frames:
            # Cross-origin frames are evaluated by Playwright, not parent-page JS.
            if frame != page.main_frame:
                assert frame.url != "about:blank", "An embedded viewer stayed blank"
                assert frame.locator("body").inner_html().strip(), f"Empty iframe: {frame.url}"
            result = frame.evaluate(CHECK_IMAGES)
            report["frames"].append({"url": short_url(frame.url), **result})
            errors.extend(f"Image in {short_url(frame.url)}: {f}" for f in result["failures"])
            for link in frame.evaluate(READ_LINKS):
                if urlsplit(link["url"]).scheme in {"http", "https"} and not same_origin(link["url"], base):
                    report["external_links"].append(link["url"])
                problem = check_link(link, base, page.request, link_cache)
                if problem:
                    errors.append(problem)
    except Exception as exc:
        errors.append(f"Browser check: {type(exc).__name__}: {exc}")
    report["external_links"] = sorted(set(report["external_links"]))
    report["errors"] = sorted(set(errors))
    return report


def write_report(path: Path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
