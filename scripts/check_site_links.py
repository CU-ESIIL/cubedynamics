#!/usr/bin/env python3
"""Check built-site local links and fragments, including notebook HTML links."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "name" in attrs:
            self.ids.add(attrs["name"])
        for attr in ("href", "src", "data-src"):
            if attrs.get(attr):
                self.links.append(attrs[attr])


def check(root):
    root = root.resolve()
    parsed = {}
    # Viewer assets are standalone applications, not MkDocs navigation pages.
    for path in root.rglob("*.html"):
        if "assets" in path.relative_to(root).parts:
            continue
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
        parsed[path] = parser
    errors = []
    for path, parser in parsed.items():
        for href in parser.links:
            url = urlsplit(href)
            if url.scheme or url.netloc or href.startswith("//"):
                continue
            raw = unquote(url.path)
            if raw.startswith("/cubedynamics/"):
                target = root / raw.removeprefix("/cubedynamics/")
            elif raw.startswith("/"):
                target = root / raw.lstrip("/")
            else:
                target = (path.parent / raw).resolve() if raw else path
            if target.is_dir():
                target /= "index.html"
            if not target.exists():
                errors.append(f"{path.relative_to(root)} -> {href} (missing file)")
            elif url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
                errors.append(f"{path.relative_to(root)} -> {href} (missing anchor)")
    return sorted(set(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_dir", type=Path, nargs="?", default=Path("site"))
    args = parser.parse_args()
    if not (args.site_dir / "index.html").exists():
        raise SystemExit("Build the MkDocs site first")
    errors = check(args.site_dir)
    if errors:
        raise SystemExit("\n".join(errors))
    print("PASS: built-site internal files and anchors resolve")


if __name__ == "__main__":
    main()
