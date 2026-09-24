"""Regression locks for the audited hot/cold/Delta semantics."""

from __future__ import annotations

import inspect

import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, to_hex
import numpy as np
import pytest
import rasterio
import xarray as xr

from cubedynamics.stats.tails import one_tail_spearman
from cubedynamics.synchrony.baseline import nonstacked_synchrony_summary
from cubedynamics.synchrony.production import local_synchrony_pairs
from scripts import run_nonstacked_conus_baseline as conus


def _companion(mode: str) -> np.ndarray:
    base = np.arange(40, dtype=float)
    weak = np.asarray(
        [20, 39, 21, 38, 22, 37, 23, 36, 24, 35, 25, 34, 26, 33, 27, 32, 28, 31, 29, 30],
        dtype=float,
    )
    if mode == "strong":
        return base.copy()
    if mode == "weak_lower":
        return np.concatenate((weak - 20, base[20:]))
    if mode == "weak_upper":
        return np.concatenate((base[:20], weak))
    raise ValueError(mode)


def _pairs(cold_mode: str, warm_mode: str) -> tuple[xr.Dataset, xr.Dataset]:
    base = np.arange(40, dtype=float)
    cube = xr.Dataset(
        {
            "tmin": (
                ("time", "y", "x"),
                np.stack((base, _companion(cold_mode)), axis=1)[:, None, :],
            ),
            "tmax": (
                ("time", "y", "x"),
                np.stack((base, _companion(warm_mode)), axis=1)[:, None, :],
            ),
        },
        coords={
            "time": np.datetime64("2024-01-01") + np.arange(40).astype("timedelta64[D]"),
            "y": [40.0],
            "x": [-105.0, -104.5],
        },
    )
    cube.y.attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    cube.x.attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    pairs = local_synchrony_pairs(
        cube,
        lower_var="tmin",
        upper_var="tmax",
        output_mask=np.ones((1, 2), dtype=bool),
        computation_mask=np.ones((1, 2), dtype=bool),
        max_radius_km=100,
        window_days=39,
        min_t=10,
        split_quantile=0.5,
    )
    return cube, pairs


def _nonself_value(pairs: xr.Dataset, name: str) -> float:
    nonself = pairs.source_index.values != pairs.target_index.values
    return float(pairs[name].values[nonself][0])


@pytest.fixture(scope="module")
def known_cases() -> dict[str, tuple[xr.Dataset, xr.Dataset]]:
    return {
        "cold_stronger": _pairs("strong", "weak_upper"),
        "warm_stronger": _pairs("weak_lower", "strong"),
        "equal": _pairs("strong", "strong"),
    }


def test_lower_tail_is_cold(known_cases) -> None:
    cube, pairs = known_cases["cold_stronger"]
    expected, count = one_tail_spearman(
        cube.tmin.values[:, 0, 0], cube.tmin.values[:, 0, 1], tail="lower", min_t=10
    )
    assert pairs.attrs["lower_variable"] == "tmin"
    assert "cold joint <= thresholds" in pairs.attrs["split_definition"]
    np.testing.assert_allclose(_nonself_value(pairs, "cold_synchrony"), expected)
    assert _nonself_value(pairs, "cold_joint_count") == count


def test_upper_tail_is_warm(known_cases) -> None:
    cube, pairs = known_cases["warm_stronger"]
    expected, count = one_tail_spearman(
        cube.tmax.values[:, 0, 0], cube.tmax.values[:, 0, 1], tail="upper", min_t=10
    )
    assert pairs.attrs["upper_variable"] == "tmax"
    assert "warm joint > thresholds" in pairs.attrs["split_definition"]
    np.testing.assert_allclose(_nonself_value(pairs, "warm_synchrony"), expected)
    assert _nonself_value(pairs, "warm_joint_count") == count


def test_delta_is_cold_minus_warm(known_cases) -> None:
    for _, pairs in known_cases.values():
        cold = _nonself_value(pairs, "cold_synchrony")
        warm = _nonself_value(pairs, "warm_synchrony")
        np.testing.assert_allclose(_nonself_value(pairs, "delta_s"), cold - warm)
        assert pairs.delta_s.attrs["definition"] == "pairwise cold_synchrony - warm_synchrony"


def test_positive_delta_means_cold_stronger(known_cases) -> None:
    _, pairs = known_cases["cold_stronger"]
    assert _nonself_value(pairs, "cold_synchrony") > _nonself_value(pairs, "warm_synchrony")
    assert _nonself_value(pairs, "delta_s") > 0


def test_negative_delta_means_warm_stronger(known_cases) -> None:
    _, pairs = known_cases["warm_stronger"]
    assert _nonself_value(pairs, "warm_synchrony") > _nonself_value(pairs, "cold_synchrony")
    assert _nonself_value(pairs, "delta_s") < 0


def test_zero_delta_means_equal(known_cases) -> None:
    _, pairs = known_cases["equal"]
    np.testing.assert_allclose(
        _nonself_value(pairs, "cold_synchrony"),
        _nonself_value(pairs, "warm_synchrony"),
    )
    np.testing.assert_allclose(_nonself_value(pairs, "delta_s"), 0.0, atol=0, rtol=0)


def test_center_collapse_preserves_delta_semantics(known_cases) -> None:
    _, pairs = known_cases["warm_stronger"]
    summary = nonstacked_synchrony_summary(pairs, radii_km=(100.0,))
    delta = summary.delta_pair_median.values[0, 0]
    finite = delta[np.isfinite(delta)]
    assert np.all(finite < 0)
    assert summary.delta_pair_median.attrs["definition"] == (
        "median of nonself pairwise (cold_synchrony - warm_synchrony)"
    )


def test_delta_raster_preserves_sign(tmp_path, monkeypatch) -> None:
    values = np.asarray([[-0.75, 0.0], [0.25, np.nan]], dtype=float)
    result = xr.Dataset(
        {
            "delta_pair_median": (
                ("time_window_end", "radius_km", "y", "x"), values[None, None]
            ),
            "output_mask": (("y", "x"), np.ones((2, 2), dtype=bool)),
        },
        coords={
            "time_window_end": [np.datetime64("2024-01-30")],
            "radius_km": [100.0],
            "y": [40.0, 39.5],
            "x": [-105.0, -104.5],
        },
    )
    monkeypatch.setattr(conus, "ROOT", tmp_path)
    monkeypatch.setattr(conus, "OUTPUT", tmp_path / "output")
    monkeypatch.setattr(conus, "RASTERS", ("delta_pair_median",))
    conus._write_rasters(result)
    with rasterio.open(tmp_path / "output" / "rasters" / "delta_pair_median_100km.tif") as source:
        raster = source.read(1)
        np.testing.assert_allclose(raster[0, :], values[0, :].astype("float32"))
        assert raster[1, 0] > 0
        assert raster[1, 1] == source.nodata
        assert source.tags()["sign_convention"] == "Delta = cold synchrony - warm synchrony"


def test_conus_delta_plot_color_contract() -> None:
    source = inspect.getsource(conus._figures)
    assert 'cmap="RdBu"' in source
    assert "TwoSlopeNorm(0, -limit, limit)" in source
    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    cmap = plt.get_cmap("RdBu")
    assert to_hex(cmap(norm(-1))).startswith("#67")
    assert to_hex(cmap(norm(1))).startswith("#05")
