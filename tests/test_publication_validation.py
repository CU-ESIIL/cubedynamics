"""Fast guardrails for the real-data publication validation contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import xarray as xr
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_validation


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "fixtures" / "real_data" / "prism_boulder_january_2024.nc"
PROVENANCE = DATA.with_suffix(".provenance.json")


@pytest.mark.parametrize("fixture,provenance", run_validation.VIGNETTE_INPUTS.items())
def test_publication_accepts_only_integrity_verified_real_inputs(fixture, provenance):
    metadata = {"data_fixture": fixture, "provenance": provenance}
    assert run_validation.vignette_input_verified(metadata)
    assert not run_validation.vignette_input_verified({**metadata, "data_fixture": "invented.nc"})
    assert not run_validation.vignette_input_verified({**metadata, "provenance": "invented.json"})


def test_publication_rejects_damaged_or_missing_station_snapshot(tmp_path, monkeypatch):
    name = "tests/fixtures/real_data/usgs_streamflow"
    shutil.copytree(ROOT / name, tmp_path / name)
    monkeypatch.setattr(run_validation, "ROOT", tmp_path)
    metadata = {"data_fixture": name, "provenance": f"{name}/provenance.json"}
    assert run_validation.vignette_input_verified(metadata)
    body = next((tmp_path / name).glob("boulder/bodies/*"))
    body.write_bytes(b"corrupt response")
    assert not run_validation.vignette_input_verified(metadata)
    body.unlink()
    assert not run_validation.vignette_input_verified(metadata)


def test_prism_vignette_fixture_matches_provenance_and_physics() -> None:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    dataset = xr.open_dataset(DATA, engine="scipy").load()

    assert digest == provenance["fixture_sha256"]
    assert dataset.attrs["source"] == "PRISM Group, Oregon State University"
    assert dataset.attrs["is_synthetic"] == 0
    assert provenance["is_synthetic"] is False
    assert dict(dataset.sizes) == {"time": 30, "y": 24, "x": 24}
    assert len(provenance["source_archives"]) == 60
    assert all(record["url"] and record["sha256"] for record in provenance["source_archives"])
    assert bool(np.isfinite(dataset.to_array()).all())
    assert bool((dataset.tmin <= dataset.tmax).all())
    np.testing.assert_allclose(
        dataset.diurnal_range, dataset.tmax - dataset.tmin, rtol=0, atol=1e-5
    )


def test_validation_pages_and_ci_gate_are_publication_visible() -> None:
    nav = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")

    for page in ("index.md", "data.md", "cube.md", "contrast.md", "methods.md"):
        assert (ROOT / "docs" / "validation" / page).exists()
        assert f"validation/{page}" in nav
    assert "python scripts/run_validation.py --run-vignettes" in workflow


def test_fixture_builder_is_reproducible_from_checked_in_provenance() -> None:
    builder = (ROOT / "scripts" / "build_vignette_data.py").read_text(encoding="utf-8")
    assert "DEFAULT_SOURCE_MANIFEST = DEFAULT_PROVENANCE" in builder
    assert "--download-missing" in builder
    assert "SHA-256 mismatch" in builder

    asset_builder = (ROOT / "scripts" / "build_real_data_assets.py").read_text(
        encoding="utf-8"
    )
    assert "provenance[\"fixture_sha256\"]" in asset_builder
    assert "Website asset refuses generated measurement data" in asset_builder
    homepage_cube = ROOT / "docs" / "assets" / "figures" / "prism_boulder_tmax_cube.html"
    assert "Observed PRISM daily maximum temperature" in homepage_cube.read_text(
        encoding="utf-8"
    )


def test_public_learning_routes_do_not_promote_generated_examples() -> None:
    pages = [
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "vignettes" / "index.md",
        ROOT / "docs" / "synchrony" / "index.md",
        ROOT / "docs" / "synchrony" / "biology_coupling.md",
        ROOT / "docs" / "synchrony" / "primitives.md",
        ROOT / "docs" / "synchrony" / "state_events.md",
        ROOT / "docs" / "synchrony" / "center_recipe.md",
        ROOT / "docs" / "capabilities" / "fire-vase.md",
        ROOT / "docs" / "workflows" / "fire_analysis.md",
        ROOT / "docs" / "recipes" / "index.md",
        ROOT / "docs" / "viz" / "index.md",
    ]
    forbidden = (
        "synthetic example",
        "synthetic cube",
        "synthetic fire",
        "fire_vase_synthetic",
        "fireeventdaily.example()",
        "fire_vase_panel_sample",
        "synchrony_occurrence_cube",
        "synchrony_coupling_lag_curve",
        "synchrony_severity_cube",
        "synchrony_event_timing_duration_panel",
        "climate_median_split_synchrony_cube",
        "synchrony_event_diagnostics",
    )
    for page in pages:
        content = page.read_text(encoding="utf-8").lower()
        assert not any(phrase in content for phrase in forbidden), page

    site_config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for historical_asset in (
        "recipes/fire_vase_synthetic.md",
        "recipes/climate_tail_dep_center.md",
        "recipes/ghosh_tail_association.md",
        "assets/figures/fire_vase_panel_sample.html",
        "assets/figures/synchrony_occurrence_cube.html",
        "assets/figures/synchrony_metric_comparison.png",
        "assets/figures/synchrony_coupling_lag_curve.png",
        "assets/figures/synchrony_severity_cube.html",
        "assets/figures/synchrony_event_timing_duration_panel.html",
        "assets/figures/climate_median_split_synchrony_cube.html",
        "assets/figures/synchrony_event_diagnostics.png",
    ):
        assert historical_asset in site_config
