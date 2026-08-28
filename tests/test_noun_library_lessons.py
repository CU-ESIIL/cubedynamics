"""First-class noun references and real offline lessons must stay in sync."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import matplotlib.pyplot as plt
from PIL import Image
import pytest
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_reference_docs as reference
import build_source_vignettes as builder
from noun_reference import NOUNS, SOURCES
from source_lesson_content import LESSONS
from docs_hooks import rewrite_notebook_links


@pytest.mark.parametrize("noun", sorted(NOUNS))
def test_nouns_have_peer_references_sources_and_lessons(noun):
    pages = reference.generate()
    info = NOUNS[noun]
    text = pages[f"library/nouns/{noun}.md"]
    assert f"](nouns/{noun}.md)" in pages["library/index.md"]
    for heading in reference.NOUN_SECTIONS:
        assert f"## {heading}\n" in text
    assert reference.signature(info["callable"]) in text
    assert f"from cubedynamics.data.{info['module']} import {noun}" in text
    assert f"vignettes/{info['lesson']}.ipynb" in text
    assert f"generated/nouns/{noun}-1.png" in text
    assert "no production serving revision" in text
    for source in info["sources"]:
        assert SOURCES[source]["profile"] in reference.data.list_qa_profiles()
        for heading in reference.SOURCE_SECTIONS:
            assert f"## {heading}\n" in pages[f"library/sources/{source}.md"]


@pytest.mark.parametrize("noun", sorted(LESSONS))
def test_real_lesson_code_executes_offline_and_every_step_plots(noun, monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr("requests.sessions.Session.request", lambda *a, **k: pytest.fail("Lesson requested network"))
    shown = []
    monkeypatch.setattr(plt, "show", lambda: shown.append(bool(plt.gcf().axes)))
    namespace = {}
    try:
        for index, (_, _, code, _) in enumerate(LESSONS[noun]["steps"]):
            exec(compile(code, f"{noun}-{index}", "exec"), namespace)
            plt.close("all")
        assert shown == [True, True, True]
        if noun == "elevation":
            terrain = namespace["terrain"]
            assert terrain.shape == (99, 99) and terrain.attrs["is_synthetic"] == 0
            assert terrain.attrs["units"] == "m"
            assert float(terrain.min()) == pytest.approx(1886.041015625)
            assert float(terrain.max()) == pytest.approx(2363.25048828125)
            xr.testing.assert_allclose(namespace["profile"], terrain.mean("y"))
        else:
            assert {s: len(f) for s, f in namespace["networks"].items()} == {"overture": 528, "osm": 611}
            assert all(f.is_valid.all() and f.source_feature_id.is_unique for f in namespace["networks"].values())
            assert all((s > 0).all() for s in namespace["lengths"].values())
    finally:
        plt.close("all")


def test_noun_figures_are_current_and_decodable():
    manifest = json.loads((builder.ASSETS / "manifest.json").read_text())
    assert manifest["inputs"] == builder.evidence_inputs()
    assert len(manifest["outputs"]) == 7
    for name, digest in manifest["outputs"].items():
        path = builder.ASSETS / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        with Image.open(path) as image:
            assert min(image.size) > 100
            assert any(low != high for low, high in image.convert("RGB").getextrema())


@pytest.mark.parametrize("noun", sorted(LESSONS))
def test_noun_notebooks_match_builders(noun):
    lesson = LESSONS[noun]
    path = ROOT / f"docs/vignettes/{lesson['stem']}.ipynb"
    assert json.loads(path.read_text()) == builder.notebook(noun, lesson)


def test_notebook_download_points_to_copied_file_not_rendered_page():
    source = "vignettes/elevation_landscape.ipynb"
    page = SimpleNamespace(file=SimpleNamespace(src_uri=source), url="vignettes/elevation_landscape/")
    target = SimpleNamespace(src_uri=source, url=page.url)
    files = SimpleNamespace(get_file_from_path=lambda path: target if path == source else None)
    html = '<a href="elevation_landscape.ipynb?download=1">Download</a>'
    result = rewrite_notebook_links(html, page, files)
    assert 'href="elevation_landscape.ipynb?download=1"' in result
