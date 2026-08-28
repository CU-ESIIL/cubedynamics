"""Small MkDocs adapters for reference navigation and notebook links."""
import html
from pathlib import Path, PurePosixPath
import posixpath
import re
from urllib.parse import urlsplit, urlunsplit

from mkdocs.utils import get_relative_url


def on_config(config):
    # Put individual callables behind A-Z, not ahead of conceptual browsing.
    verb_pages = sorted((Path(config["docs_dir"]) / "reference/verbs").glob("*.md"))
    for group in config["nav"]:
        for entry in group.get("Documents", []):
            for item in entry.get("Verbs", []):
                if "All public callables" in item:
                    item["All public callables"] = [
                        {"A–Z inventory": "reference/verbs/a-z.md"},
                        *[{p.stem: f"reference/verbs/{p.name}"} for p in verb_pages
                          if p.stem not in {"index", "a-z", "compatibility", "planned"}],
                    ]
        if "Library" in group:
            # Read the catalog-generated directory so new nouns automatically
            # join their scientific category without another manual nav edit.
            entries = [{"All nouns": "library/index.md"}]
            current = None
            for line in (Path(config["docs_dir"]) / "library/index.md").read_text().splitlines():
                if line.startswith("## "):
                    current, title = [], line[3:]
                match = re.search(r"\[([^]]+)\]\((nouns/[^)]+\.md)\)", line)
                if match and current is not None:
                    if not current:
                        entries.append({title: current})
                    current.append({match[1]: "library/" + match[2]})
            entries.extend(e for e in group["Library"] if any(key in e for key in
                ("Browse sources", "Source QA evidence")))
            for entry in entries:
                if "Browse sources" in entry:
                    entry["Browse sources"] = [{"All sources": "library/sources/index.md"},
                        *[{p.stem: f"library/sources/{p.name}"} for p in sorted((Path(config["docs_dir"]) / "library/sources").glob("*.md")) if p.stem != "index"]]
            group["Library"] = entries
    return config


def rewrite_notebook_links(output, page, files):
    """nbconvert leaves source .md links unchanged; resolve via MkDocs files.

    Only rewrite actual anchor tags targeting known source documents. Code
    examples, iframe srcdoc content, downloads and external URLs are untouched.
    """
    source_dir = str(PurePosixPath(page.file.src_uri).parent)

    def replace(match):
        url = urlsplit(html.unescape(match.group(2)))
        if url.scheme or url.netloc or not url.path.endswith((".md", ".ipynb")):
            return match.group(0)
        source = posixpath.normpath(posixpath.join(source_dir, url.path))
        target = files.get_file_from_path(source)
        if target is None:
            return match.group(0)  # Let the link checker report unknown targets.
        target_url = target.url
        if url.path.endswith(".ipynb") and url.query == "download=1":
            # MkDocs-Jupyter places the original notebook beside the rendered page.
            target_url = target.url.rstrip("/") + "/" + PurePosixPath(target.src_uri).name
        relative = get_relative_url(target_url, page.url)
        href = urlunsplit(("", "", relative, url.query, url.fragment))
        return match.group(1) + html.escape(href, quote=True) + match.group(3)

    return re.sub(r'(<a\b[^>]*\bhref=")([^"]+)(")', replace, output)


def on_post_page(output, page, config):
    if page.file.src_uri.endswith(".ipynb"):
        return rewrite_notebook_links(output, page, _files)
    return output


def on_files(files, config):
    global _files
    _files = files
    return files


def on_page_content(html_content, page, config, files):
    source = page.file.src_uri
    labels = (("library/nouns/", "Library · Noun reference"),
              ("data/source_projects/", "Documents · Source engineering and validation"),
              ("library/sources/", "Library · Source reference"),
              ("library/", "Library · Data directory"),
              ("reference/", "Documents · Verb reference"),
              ("api/", "Documents · API reference"),
              ("documentation/", "Documents · Reference directory"),
              ("developer/", "Documents · Developer documentation"),
              ("dev/", "Documents · Developer documentation"),
              ("learn/", "Learn · Tutorial"))
    for prefix, label in labels:
        if source.startswith(prefix):
            return f'<div class="cd-manual"><p class="cd-page-type">{label}</p>{html_content}</div>'
    return html_content
