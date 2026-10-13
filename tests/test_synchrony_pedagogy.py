"""Regression checks for the synchrony teaching deck's empirical claims."""

from __future__ import annotations

import importlib.util
import builtins
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_synchrony_pedagogy.py"


def _module():
    spec = importlib.util.spec_from_file_location("build_synchrony_pedagogy", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_evidence_checks_import_without_optional_pdf_renderer(monkeypatch, tmp_path):
    original_import = builtins.__import__
    attempted = []

    def without_reportlab(name, *args, **kwargs):
        if name == "reportlab" or name.startswith("reportlab."):
            attempted.append(name)
            raise ModuleNotFoundError("ReportLab deliberately unavailable", name="reportlab")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_reportlab)
    module = _module()
    assert len(module.PAGE_GUIDE) == 55
    assert attempted == [], "Import-only checks must not request a PDF renderer"
    output = tmp_path / "deck.pdf"
    with pytest.raises(RuntimeError, match="pip install reportlab"):
        module.assemble_pdf([], output)
    assert not output.exists()
    assert not output.with_suffix(".partial.pdf").exists()


def test_page_plan_is_complete_and_each_empirical_page_has_artifact_keys() -> None:
    module = _module()
    assert len(module.PAGE_GUIDE) == 55
    provenance = {
        str(page): {
            "data_class": "REAL PRISM" if page in {1, 2} else "CONCEPTUAL",
            "empirical_keys": ["pair"] if page in {1, 2} else [],
        }
        for page in range(1, 56)
    }
    module.validate_page_provenance(provenance)
    provenance["2"]["empirical_keys"] = []
    try:
        module.validate_page_provenance(provenance)
    except ValueError as exc:
        assert "missing artifact keys" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("missing empirical provenance was accepted")


@pytest.mark.integration
def test_pair_values_are_recomputed_and_match_current_stack() -> None:
    """Explicit research-artifact check: missing retained inputs must fail."""
    module = _module()
    evidence = module.load_empirical_evidence()
    pair = evidence["pair"]
    with xr.open_dataset(module.DEFAULT_STACK) as stack:
        cy, cx = pair["comparison_grid"]
        center = pair["center"]
        np.testing.assert_allclose(pair["cold"], float(stack.cold_synchrony[center, cy, cx]), atol=1e-6)
        np.testing.assert_allclose(pair["warm"], float(stack.warm_synchrony[center, cy, cx]), atol=1e-6)
        np.testing.assert_allclose(pair["delta"], float(stack.delta_s[center, cy, cx]), atol=1e-6)
        assert pair["cold_n"] == int(stack.cold_joint_count[center, cy, cx])
        assert pair["warm_n"] == int(stack.warm_joint_count[center, cy, cx])


@pytest.mark.integration
def test_alignment_representation_window_and_station_numbers_are_live() -> None:
    """Requires the complete ignored feasibility bundle, not a clone fixture."""
    module = _module()
    evidence = module.load_empirical_evidence()
    base = module.DEFAULT_FEASIBILITY

    similarity = pd.read_csv(base / "relative_vs_absolute_similarity.csv")
    delta40 = similarity.query("metric == 'delta_s' and radius_km == 40")
    assert evidence["alignment"]["pearson_relative"] == delta40.pearson_relative.median()
    assert evidence["alignment"]["pearson_absolute"] == delta40.pearson_absolute.median()
    assert evidence["alignment"]["gradient_relative"] == delta40.gradient_similarity_relative.median()
    assert evidence["alignment"]["gradient_absolute"] == delta40.gradient_similarity_absolute.median()

    representations = pd.read_csv(base / "baseline_representation_comparison.csv").set_index("representation")
    for name, value in evidence["representations"].items():
        assert value == representations.loc[name, "median_normalized_rmse"]

    windows = pd.read_csv(base / "observation_window_sensitivity.csv")
    assert evidence["windows"] == windows.to_dict(orient="records")

    station = json.loads((base / "station_qc_provenance.json").read_text())["pair_summary"]
    assert evidence["stations"]["cold_r"] == station["cold"]["correlation"]
    assert evidence["stations"]["warm_r"] == station["warm"]["correlation"]
    assert evidence["stations"]["delta_r"] == station["delta"]["correlation"]


@pytest.fixture
def controlled_evidence(tmp_path, monkeypatch):
    """Deterministic unit controls; never substitute for empirical deck inputs."""
    module = _module()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    axis = np.arange(20)
    t = np.arange(60, dtype=float)
    offsets = axis[:, None] + axis[None, :]
    # Every cell is an affine transform of the same sequence: rank r=1,
    # thirty jointly selected observations in each half, cold-minus-warm=0.
    cube = xr.Dataset(
        {"tmin": (("time", "y", "x"), t[:, None, None] + offsets),
         "tmax": (("time", "y", "x"), 2 * t[:, None, None] + offsets + 5)},
        coords={"time": pd.date_range("2000-01-01", periods=60), "y": axis, "x": axis},
        attrs={"data_class": "SYNTHETIC UNIT CONTROL"},
    )
    shape = (400, 20, 20)
    stack = xr.Dataset(
        {"cold_synchrony": (("center", "y", "x"), np.ones(shape)),
         "warm_synchrony": (("center", "y", "x"), np.ones(shape)),
         "delta_s": (("center", "y", "x"), np.zeros(shape)),
         "cold_joint_count": (("center", "y", "x"), np.full(shape, 30)),
         "warm_joint_count": (("center", "y", "x"), np.full(shape, 30)),
         "distance_km": (("center", "y", "x"), np.full(shape, 3.)),
         "center_y": ("center", np.repeat(axis, 20)),
         "center_x": ("center", np.tile(axis, 20))},
        coords={"center": np.arange(400), "y": axis, "x": axis},
        attrs={"window_start": "2000-01-01", "window_end": "2000-02-29",
               "window_days": 60, "split_quantile": .5,
               "min_time_points_per_tail": 10, "data_class": "SYNTHETIC UNIT CONTROL"},
    )
    cube_path, stack_path, colorado_path = [tmp_path / name for name in ("cube.nc", "stack.nc", "colorado.nc")]
    cube.to_netcdf(cube_path, engine="scipy")
    stack.to_netcdf(stack_path, engine="scipy")
    cube.isel(time=0).to_netcdf(colorado_path, engine="scipy")
    pd.DataFrame({"metric": ["delta_s", "delta_s"], "radius_km": [40, 40],
                  "pearson_relative": [.2, .6], "pearson_absolute": [.1, .3],
                  "gradient_similarity_relative": [.4, .8],
                  "gradient_similarity_absolute": [.2, .4]}).to_csv(tmp_path / "relative_vs_absolute_similarity.csv", index=False)
    pd.DataFrame({"representation": ["radial_plus_directional"],
                  "median_normalized_rmse": [.25], "surface_count": [400]}).to_csv(tmp_path / "baseline_representation_comparison.csv", index=False)
    pd.DataFrame({"window": [60], "value": [.5]}).to_csv(tmp_path / "observation_window_sensitivity.csv", index=False)
    pd.DataFrame({"station_i": ["CONTROL_A"], "station_j": ["CONTROL_B"],
                  "station_cold": [.8], "station_warm": [.6],
                  "station_delta": [.2]}).to_csv(tmp_path / "station_prism_pair_synchrony.csv", index=False)
    pd.DataFrame({"station": ["CONTROL_A", "CONTROL_B"]}).to_csv(tmp_path / "station_manifest.csv", index=False)
    (tmp_path / "station_qc_provenance.json").write_text(json.dumps({
        "pair_summary": {"station_count": 2, "pair_count": 1,
                         "cold": {"correlation": .8}, "warm": {"correlation": .6},
                         "delta": {"correlation": .2}},
        "prism_contribution_status": "SYNTHETIC UNIT CONTROL"}))
    (tmp_path / "feasibility_summary.json").write_text(json.dumps({
        "directed_relationship_count": 160000, "canonical_pair_count": 79800}))
    return module.load_empirical_evidence(tmp_path, stack_path, cube_path, colorado_path)


def test_controlled_pair_recomputation_has_known_rank_truth(controlled_evidence):
    pair = controlled_evidence["pair"]
    assert pair["cold"] == pytest.approx(1)
    assert pair["warm"] == pytest.approx(1)
    assert pair["delta"] == pytest.approx(0)
    assert (pair["cold_n"], pair["warm_n"]) == (30, 30)


def test_controlled_report_values_and_source_hashes(controlled_evidence):
    assert controlled_evidence["alignment"]["pearson_relative"] == pytest.approx(.4)
    assert controlled_evidence["alignment"]["gradient_absolute"] == pytest.approx(.3)
    assert controlled_evidence["representations"] == {"radial_plus_directional": .25}
    assert controlled_evidence["windows"] == [{"window": 60, "value": .5}]
    assert controlled_evidence["stations"]["contribution_status"] == "SYNTHETIC UNIT CONTROL"
    assert all(len(record["sha256"]) == 64 for record in controlled_evidence["sources"].values())


def test_missing_empirical_artifacts_are_errors(tmp_path):
    module = _module()
    with pytest.raises(FileNotFoundError):
        module.load_empirical_evidence(tmp_path, tmp_path / "missing.nc")
