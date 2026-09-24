"""Regression tests for the non-production relational-convolution experiment."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from relational_convolution_feasibility import (  # noqa: E402
    symmetric_synthetic_field,
    synthetic_benchmark,
    translated_edge_support,
)


CASES = (
    "uniform",
    "isotropic_distance_decay",
    "smooth_geographic_gradient",
    "directional_anisotropy",
    "sharp_geographic_transition",
    "nonmonotonic_radial",
    "spatially_varying_distance",
    "noise_only",
    "transition_plus_distance",
    "anisotropy_no_transition",
)


def test_all_synthetic_relationship_fields_are_symmetric() -> None:
    for case in CASES:
        values, _, metadata = symmetric_synthetic_field(case)
        flat = values.reshape(values.shape[0], values.shape[0])
        np.testing.assert_allclose(flat, flat.T, atol=1e-12, rtol=0, equal_nan=True)
        assert metadata["pair_symmetry_max_error"] < 1e-12


def test_translated_transition_separates_boundary_from_distance_and_anisotropy() -> None:
    benchmark = synthetic_benchmark().set_index("case")
    assert benchmark.loc["sharp_geographic_transition", "translated_transition_edge_ratio"] > 20
    assert benchmark.loc["transition_plus_distance", "translated_transition_edge_ratio"] > 20
    for case in (
        "isotropic_distance_decay",
        "directional_anisotropy",
        "nonmonotonic_radial",
        "spatially_varying_distance",
        "noise_only",
        "anisotropy_no_transition",
    ):
        assert benchmark.loc[case, "translated_transition_edge_ratio"] < 1.6


def test_edge_support_excludes_gradients_incident_to_focal_self() -> None:
    values, distance, _ = symmetric_synthetic_field(
        "smooth_geographic_gradient", size=9, radius_cells=4
    )
    result = translated_edge_support(values, distance, radius=4)
    assert result.attrs["self_edge_policy"].startswith("gradients incident")
    assert float(result.east_west_contributing_surface_count.max()) < values.shape[0]
    assert np.isfinite(result.east_west_transition_evidence.values).any()


def test_noise_is_deterministic_and_not_endpoint_duplication() -> None:
    first, distance, _ = symmetric_synthetic_field("noise_only", size=9, radius_cells=4)
    second, _, _ = symmetric_synthetic_field("noise_only", size=9, radius_cells=4)
    np.testing.assert_allclose(first, second, equal_nan=True)
    support = translated_edge_support(first, distance, radius=4)
    assert int(np.nanmax(support.east_west_contributing_surface_count.values)) <= first.shape[0] - 2
