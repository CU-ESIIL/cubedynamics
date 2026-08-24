"""Guardrails for the publication-facing hackathon notebook lab."""

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


def test_hackathon_vignette_catalog_is_complete() -> None:
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
        assert "plt.show()" in code_source


def test_vignette_index_links_every_supported_notebook() -> None:
    index = (VIGNETTE_DIR / "index.md").read_text(encoding="utf-8")
    for name in EXPECTED:
        assert f"({name})" in index
