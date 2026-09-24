"""Regression checks for the synchrony teaching deck's empirical claims."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_synchrony_pedagogy.py"


def _module():
    spec = importlib.util.spec_from_file_location("build_synchrony_pedagogy", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_pair_values_are_recomputed_and_match_current_stack() -> None:
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


def test_alignment_representation_window_and_station_numbers_are_live() -> None:
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
