"""Small MkDocs adapters for reference navigation and notebook links."""
import html
from pathlib import Path, PurePosixPath
import posixpath
import re
from urllib.parse import urlsplit, urlunsplit

from mkdocs.utils import get_relative_url


def on_config(config):
    # Reference pages inherit their Documents tab and a useful alphabetical
    # sidebar without hand-maintaining 51 names in mkdocs.yml.
    verb_pages = sorted((Path(config["docs_dir"]) / "reference/verbs").glob("*.md"))
    for group in config["nav"]:
        for entry in group.get("Documents", []):
            if "Verbs and callable helpers" in entry:
                entry["Verbs and callable helpers"] = [
                    {"Index": "reference/verbs/index.md"},
                    *[{path.stem: f"reference/verbs/{path.name}"} for path in verb_pages if path.stem != "index"],
                ]
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
        relative = get_relative_url(target.url, page.url)
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
              ("library/sources/", "Library · Source reference"),
              ("library/", "Library · Data directory"),
              ("reference/", "Documents · Verb reference"),
              ("api/", "Documents · API reference"),
              ("documentation/", "Documents · Reference directory"),
              ("learn/", "Learn · Tutorial"))
    for prefix, label in labels:
        if source.startswith(prefix):
            return f'<div class="cd-manual"><p class="cd-page-type">{label}</p>{html_content}</div>'
    return html_content
