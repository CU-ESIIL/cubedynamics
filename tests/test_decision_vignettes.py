"""Publication guardrails for the South Dakota Decision Lab."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import numpy as np
import xarray as xr

from cubedynamics import data
from cubedynamics import verbs as v


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "decision_vignettes"
FIXTURE = ROOT / "data" / "decision_vignettes" / "sd_working_lands_july_2024.nc"
PROVENANCE = FIXTURE.with_suffix(".provenance.json")
DEPENDENCY_PAGES = (
    "black_hills.md",
    "missouri_water.md",
    "habitat_squeeze.md",
    "communities.md",
)


def _notebook() -> dict:
    return json.loads((DOCS / "working_lands.ipynb").read_text(encoding="utf-8"))


def _notebook_source(kind: str) -> str:
    return "\n".join(
        "".join(cell["source"])
        for cell in _notebook()["cells"]
        if cell["cell_type"] == kind
    )


def test_decision_lab_catalog_and_nav_are_complete() -> None:
    expected = {
        "index.md",
        "black_hills.md",
        "missouri_water.md",
        "working_lands.ipynb",
        "habitat_squeeze.md",
        "communities.md",
        "wildcard.md",
        "validation.md",
    }
    assert expected <= {path.name for path in DOCS.iterdir()}

    nav = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    index = (DOCS / "index.md").read_text(encoding="utf-8")
    for name in expected:
        assert f"decision_vignettes/{name}" in nav
    for stem in (
        "black_hills",
        "missouri_water",
        "working_lands",
        "habitat_squeeze",
        "communities",
        "wildcard",
    ):
        assert f'href="{stem}/"' in index
    assert "Executable now" in index
    assert "Dependency design" in index


def test_dependency_designs_do_not_pretend_missing_apis_run() -> None:
    missing_nouns = {
        "buildings",
        "roads",
        "fire_history",
        "mining_claims",
        "protected_areas",
        "surface_water",
        "hydrography",
        "cropland",
        "critical_habitat",
        "population",
    }
    assert missing_nouns.isdisjoint(data.list_sources())
    assert not hasattr(v, "intersect")
    assert not hasattr(v, "summarize")

    required_headings = (
        "## The decision",
        "## The missing information",
        "## The nouns",
        "## The analytical sentence",
        "## What happened?",
        "## QA publication gate",
        "## Decision view",
        "## What this does and does not tell us",
        "## Fork this question",
    )
    for name in DEPENDENCY_PAGES:
        content = (DOCS / name).read_text(encoding="utf-8")
        assert "Dependency design · not executable yet" in content
        assert all(heading in content for heading in required_headings)
        assert not re.search(r"```python\s", content)
        assert "No overlap was computed" in content or "Nothing has been computed" in content or "Nothing has been calculated" in content or "No water-change result has been produced" in content


def test_working_lands_fixture_matches_provenance_and_physics() -> None:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    observed = xr.open_dataset(FIXTURE, engine="scipy").load()

    assert digest == provenance["fixture_sha256"]
    assert provenance["is_synthetic"] is False
    assert observed.attrs["is_synthetic"] == 0
    assert observed.sizes == {"time": 31, "y": 15, "x": 19}
    assert observed.temperature.attrs["scientific_noun"] == "temperature"
    assert observed.precipitation.attrs["scientific_noun"] == "precipitation"
    assert observed.temperature.attrs["source_flavor"] == "prism"
    assert observed.precipitation.attrs["source_flavor"] == "prism"
    assert bool(np.isfinite(observed.to_array()).all())
    assert -60 < float(observed.temperature.min()) < float(observed.temperature.max()) < 60
    assert 0 <= float(observed.precipitation.min()) < float(observed.precipitation.max()) < 500
    np.testing.assert_array_equal(observed.temperature.time, observed.precipitation.time)
    np.testing.assert_array_equal(observed.temperature.y, observed.precipitation.y)
    np.testing.assert_array_equal(observed.temperature.x, observed.precipitation.x)


def test_working_lands_notebook_is_offline_narrative_and_has_two_figures() -> None:
    notebook = _notebook()
    metadata = notebook["metadata"]["cubedynamics"]
    markdown = _notebook_source("markdown")
    code = _notebook_source("code")

    assert metadata["supported_decision_vignette"] is True
    assert metadata["supported_vignette"] is True
    assert metadata["network"] is False
    assert metadata["plot_required"] is True
    assert metadata["minimum_plot_outputs"] == 2
    assert metadata["data_fixture"] == (
        "data/decision_vignettes/sd_working_lands_july_2024.nc"
    )
    assert metadata["provenance"].endswith(".provenance.json")

    for heading in (
        "## The decision",
        "## The missing information",
        "## The nouns",
        "## QA",
        "## The analytical sentence",
        "## Decision view",
        "## What this does and does not tell us",
        "## Fork this question",
    ):
        assert heading in markdown
    assert "plt.show()" in code
    assert code.count("plt.show()") >= 2
    assert "v.quantile_state" in code
    assert "v.threshold_state" in code
    assert "v.overlap" in code
    assert "v.mean" in code
    assert "np.random" not in code
    assert "allow_synthetic" not in code
    assert "\nobserved\n" not in code
    assert "\ncoincidence_frequency\n" not in code


def test_working_lands_pipeline_uses_current_public_apis() -> None:
    assert callable(data.temperature)
    assert callable(data.precipitation)
    assert callable(v.quantile_state)
    assert callable(v.threshold_state)
    assert callable(v.overlap)
    assert callable(v.mean)

    builder = (ROOT / "scripts" / "build_sd_working_lands_fixture.py").read_text(
        encoding="utf-8"
    )
    assert "data.temperature(" in builder
    assert "data.precipitation(" in builder
    assert "allow_synthetic" not in builder
    assert "unexpectedly reported synthetic data" in builder


def test_wildcard_uses_only_current_api_names_and_sets_three_noun_gate() -> None:
    content = (DOCS / "wildcard.md").read_text(encoding="utf-8")
    normalized = " ".join(content.split())
    python_blocks = re.findall(r"```python\n(.*?)```", content, flags=re.DOTALL)
    code = "\n".join(python_blocks)

    assert "at least three CubeDynamics nouns" in normalized
    assert "at least two noun families" in normalized
    assert "data.some_noun" not in content
    for name in ("temperature", "precipitation"):
        assert f"data.{name}(" in code
        assert callable(getattr(data, name))
    for name in ("quantile_state", "threshold_state", "overlap", "mean"):
        assert f"v.{name}(" in code
        assert callable(getattr(v, name))


def test_default_vignette_runner_includes_decision_collection() -> None:
    runner = (ROOT / "scripts" / "run_vignettes.py").read_text(encoding="utf-8")
    assert "DECISION_VIGNETTE_DIR.glob" in runner
    assert "minimum_plot_outputs" in runner
    assert "_plot_output_count" in runner


def test_decision_qa_is_a_ci_publication_gate() -> None:
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )
    script = (ROOT / "scripts" / "run_decision_qa.py").read_text(encoding="utf-8")

    assert "python scripts/run_decision_qa.py" in workflow
    assert "artifacts/decision_qa/" in workflow
    for check in (
        "fixture_checksum",
        "observational_source",
        "coordinates_exactly_aligned",
        "pipe_matches_direct_logic",
        "frequency_is_bounded",
    ):
        assert check in script
