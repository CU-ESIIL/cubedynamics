"""Built-site link and notebook-source link conversion regressions."""
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_site_links import check


def test_link_check_reports_missing_files_and_fragments(tmp_path):
    (tmp_path / "index.html").write_text('<a href="target.html#good">OK</a><a href="target.html#bad">bad</a><a href="missing.html">missing</a>')
    (tmp_path / "target.html").write_text('<h1 id="good">Title</h1>')
    errors = check(tmp_path)
    assert len(errors) == 2
    assert any("missing anchor" in e for e in errors)
    assert any("missing file" in e for e in errors)


def test_notebook_links_use_built_urls_without_rewriting_code_or_downloads():
    pytest.importorskip("mkdocs")
    from docs_hooks import rewrite_notebook_links
    page = SimpleNamespace(file=SimpleNamespace(src_uri="vignettes/lesson.ipynb"), url="vignettes/lesson/")
    files = SimpleNamespace(get_file_from_path=lambda path: SimpleNamespace(url="learn/") if path == "learn/index.md" else None)
    original = '<a href="../learn/index.md#shared-setup">Learn</a><code>../learn/index.md</code><a href="lesson.ipynb">Download</a>'
    result = rewrite_notebook_links(original, page, files)
    assert 'href="../../learn/#shared-setup"' in result
    assert '<code>../learn/index.md</code>' in result
    assert 'href="lesson.ipynb"' in result
