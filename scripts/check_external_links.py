#!/usr/bin/env python3
"""Bounded external-link availability check; separate from the browser gate.

Never downloads scientific products. HEAD first; servers rejecting HEAD or
reporting a missing page get a streamed GET whose body is not consumed.
Authentication/rate limits are reported
as unverified, not silently treated as working links.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import ipaddress
import json
from pathlib import Path
from urllib.parse import urldefrag, urlsplit

import requests


class ExternalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        url = dict(attrs).get("href", "")
        if tag == "a" and urlsplit(url).scheme in {"http", "https"}:
            self.urls.add(urldefrag(url)[0])


def discover(root, crawl_report=None):
    parser = ExternalLinks()
    for path in root.rglob("*.html"):
        parser.feed(path.read_text(encoding="utf-8"))
    if crawl_report and crawl_report.exists():
        for page in json.loads(crawl_report.read_text())["pages"]:
            parser.urls.update(urldefrag(url)[0] for url in page["external_links"])
    # Absolute references to this site's public URL are tested on the local
    # build by the browser suite, rather than probing the previous deployment.
    return sorted(url for url in parser.urls if not url.startswith("https://cu-esiil.github.io/cubedynamics/"))


def probe(url, timeout=10):
    host = urlsplit(url).hostname or ""
    if host in {"localhost", ""} or host.endswith((".local", ".internal")):
        return {"url": url, "state": "unverified", "reason": "non-public host"}
    try:
        if not ipaddress.ip_address(host).is_global:
            return {"url": url, "state": "unverified", "reason": "non-public IP"}
    except ValueError:
        pass
    try:
        with requests.Session() as session:
            session.headers["User-Agent"] = "CubeDynamics-documentation-link-check/1.0"
            response = session.head(url, allow_redirects=True, timeout=timeout)
            head_status = response.status_code
            method = "HEAD"
            # Some sites (including Google Help) incorrectly return 404 for
            # HEAD on a working article. Confirm with GET before reporting it.
            if head_status in {403, 404, 405, 501}:
                response.close()
                response = session.get(url, stream=True, timeout=timeout)
                method = "GET"
            with response:
                status = response.status_code
                return {"url": url, "final_url": response.url, "status": status,
                        "method": method, "head_status": head_status,
                        "state": "ok" if 200 <= status < 400 else "unverified" if status in {401, 403, 429} else "failed"}
    except requests.RequestException as exc:
        return {"url": url, "state": "unverified", "reason": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_dir", type=Path)
    parser.add_argument("--crawl-report", type=Path)
    parser.add_argument("--report", type=Path, default=Path("artifacts/browser/external-links.json"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not (args.site_dir / "index.html").is_file():
        parser.error("Build the site first")
    urls = discover(args.site_dir, args.crawl_report)
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
        results = list(pool.map(probe, urls))
    report = {"checked": len(results), "results": results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    unresolved = [r for r in results if r["state"] != "ok"]
    print(f"External links: {len(results) - len(unresolved)} available, {len(unresolved)} failed or unverified; see {args.report}")
    return int(bool(unresolved))


if __name__ == "__main__":
    raise SystemExit(main())
