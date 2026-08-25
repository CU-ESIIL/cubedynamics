"""Guardrails for the publication-facing narrative vignette collection."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIGNETTE_DIR = ROOT / "docs" / "vignettes"
EXPECTED = {
    "cube_from_arrays.ipynb",
    "cube_from_tidy_table.ipynb",
    "cube_from_dataset.ipynb",
    "grammar_basics.ipynb",
    "verbs_gallery.ipynb",
    "states_and_events.ipynb",
    "custom_verb_project.ipynb",
    "lazy_composition.ipynb",
}


def _read_notebook(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_vignette_catalog_is_complete() -> None:
    actual = {path.name for path in VIGNETTE_DIR.glob("*.ipynb")}
    assert EXPECTED <= actual


def test_supported_vignettes_are_offline_and_plotting() -> None:
    for name in EXPECTED:
        notebook = _read_notebook(VIGNETTE_DIR / name)
        metadata = notebook["metadata"]["cubedynamics"]
        code_source = "\n".join(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        )

        assert metadata["supported_vignette"] is True
        assert metadata["network"] is False
        assert metadata["plot_required"] is True
        assert metadata["data_fixture"] == "data/vignettes/prism_boulder_january_2024.nc"
        assert metadata["provenance"] == (
            "data/vignettes/prism_boulder_january_2024.provenance.json"
        )
        assert "plt.show()" in code_source
        assert "np.random" not in code_source
        assert "default_rng" not in code_source


def test_vignettes_follow_the_narrative_lesson_structure() -> None:
    for name in EXPECTED:
        notebook = _read_notebook(VIGNETTE_DIR / name)
        markdown_source = "\n".join(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "markdown"
        )
        code_source = "\n".join(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        )

        assert "## Context" in markdown_source
        assert "## Question" in markdown_source
        assert "## Analysis story" in markdown_source
        assert "## Pipe" in markdown_source
        assert "## Figure" in markdown_source
        assert "## What the figure tells us" in markdown_source
        assert "pipe(" in code_source
        assert ").unwrap()" in code_source
        assert "hackathon" not in markdown_source.lower()
        assert "hackathon" not in code_source.lower()


def test_vignette_index_links_every_supported_notebook() -> None:
    index = (VIGNETTE_DIR / "index.md").read_text(encoding="utf-8")
    for name in EXPECTED:
        assert f'href="{Path(name).stem}/"' in index
    assert "Keep the analytical sentence short" in index
    assert "Context" in index
    assert "Interpretation" in index
    assert "hackathon" not in index.lower()


def test_array_cube_viewer_is_isolated_from_the_document_page() -> None:
    notebook = _read_notebook(VIGNETTE_DIR / "cube_from_arrays.ipynb")
    code_source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )

    assert "viewer_srcdoc = escape(viewer.to_html(), quote=True)" in code_source
    assert 'sandbox="allow-scripts"' in code_source
    assert "HTML(viewer.to_html())" not in code_source


def test_vignette_runner_forces_inline_plot_output() -> None:
    runner = (ROOT / "scripts" / "run_vignettes.py").read_text(encoding="utf-8")

    assert 'os.environ["MPLBACKEND"] = INLINE_MATPLOTLIB_BACKEND' in runner
    assert (
        'INLINE_MATPLOTLIB_BACKEND = "module://matplotlib_inline.backend_inline"'
        in runner
    )
