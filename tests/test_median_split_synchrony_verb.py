"""Tests for the rolling median-split synchrony verb."""

from __future__ import annotations

from pathlib import Path

import dask.array as da
import numpy as np
import pytest
import xarray as xr
from scipy.stats import rankdata

from cubedynamics import pipe, verbs as v
from cubedynamics.utils.reference import center_pixel_indices


def _temperature_dataset(*, dask_backed: bool = False) -> xr.Dataset:
    time = np.datetime64("2024-01-01") + np.arange(12).astype("timedelta64[D]")
    y = np.arange(3)
    x = np.arange(3)
    tmin_center = np.linspace(-8.0, 4.0, time.size)
    tmax_center = np.linspace(5.0, 24.0, time.size)
    tmin = np.empty((time.size, y.size, x.size), dtype=np.float32)
    tmax = np.empty_like(tmin)

    for yi in range(y.size):
        for xi in range(x.size):
            offset = yi * 0.2 - xi * 0.1
            tmin[:, yi, xi] = tmin_center + offset
            tmax[:, yi, xi] = tmax_center + offset

    if dask_backed:
        tmin = da.from_array(tmin, chunks=(4, 2, 2))
        tmax = da.from_array(tmax, chunks=(4, 2, 2))

    coords = {"time": time, "y": y, "x": x}
    return xr.Dataset(
        {
            "tmin": xr.DataArray(tmin, dims=("time", "y", "x"), coords=coords),
            "tmax": xr.DataArray(tmax, dims=("time", "y", "x"), coords=coords),
        }
    )


def test_rolling_median_split_synchrony_supports_direct_and_pipe_calls() -> None:
    temperature = _temperature_dataset()
    verb = v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=20,
        min_t=5,
    )

    direct = verb(temperature)
    piped = (pipe(temperature) | verb).unwrap()

    xr.testing.assert_identical(direct, piped)
    assert list(direct.data_vars) == [
        "bottom_synchrony",
        "top_synchrony",
        "bottom_minus_top",
    ]
    assert direct["bottom_synchrony"].attrs["source_variable"] == "tmin"
    assert direct["top_synchrony"].attrs["source_variable"] == "tmax"
    assert direct["bottom_synchrony"].attrs["units"] == "1"
    assert direct["top_synchrony"].attrs["units"] == "1"
    assert direct["bottom_minus_top"].attrs["units"] == "1"
    assert direct.attrs["reference"] == "center_pixel"


def test_rolling_median_split_synchrony_accepts_one_dataarray() -> None:
    tmin = _temperature_dataset()["tmin"]

    result = v.rolling_median_split_synchrony(window_days=20, min_t=5)(tmin)

    assert result["bottom_synchrony"].attrs["source_variable"] == "tmin"
    assert result["top_synchrony"].attrs["source_variable"] == "tmin"
    np.testing.assert_allclose(
        result["bottom_minus_top"],
        result["bottom_synchrony"] - result["top_synchrony"],
        atol=1e-7,
        equal_nan=True,
    )


def test_rolling_median_split_synchrony_preserves_dask_laziness() -> None:
    temperature = _temperature_dataset(dask_backed=True)

    result = v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=20,
        min_t=5,
    )(temperature)

    assert all(variable.chunks is not None for variable in result.data_vars.values())
    center = result.isel(time_window_end=-1, y=1, x=1).compute()
    assert np.isfinite(center["bottom_synchrony"])
    assert np.isfinite(center["top_synchrony"])


def test_rolling_median_split_synchrony_can_stride_long_daily_streams() -> None:
    result = v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=20,
        min_t=3,
        output_stride=3,
    )(_temperature_dataset())

    assert result.sizes["time_window_end"] == 3
    assert result.attrs["output_stride"] == 3
    assert result["bottom_synchrony"].attrs["output_stride"] == 3


def test_rolling_median_split_synchrony_accepts_explicit_output_times() -> None:
    requested = [
        np.datetime64("2024-01-06"),
        np.datetime64("2024-01-10"),
    ]

    result = v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=20,
        min_t=3,
        output_times=requested,
    )(_temperature_dataset())

    np.testing.assert_array_equal(result["time_window_end"].values, requested)


def test_rolling_median_split_synchrony_rejects_invalid_stride() -> None:
    with pytest.raises(ValueError, match="output_stride"):
        v.rolling_median_split_synchrony(output_stride=0)(
            _temperature_dataset()["tmin"]
        )


def test_rolling_median_split_synchrony_requires_dataset_variable_names() -> None:
    with pytest.raises(ValueError, match="require lower_var and upper_var"):
        v.rolling_median_split_synchrony()(_temperature_dataset())


def test_real_prism_pair_manual_tail_masks_match_center_recipe() -> None:
    """The visual walkthrough's manual pair audit matches the public verb."""

    path = Path(__file__).parent / "fixtures" / "real_data" / "prism_boulder_january_2024.nc"
    with xr.open_dataset(path, engine="scipy") as source:
        observed = source[["tmin", "tmax"]].load()

    center_y, center_x = center_pixel_indices(observed["tmin"])
    # Preserve the walkthrough focal and center values in a tiny 3 x 3 cube;
    # the center utility still chooses the original center series at (1, 1).
    subset = observed.isel(y=[15, center_y, 0], x=[0, center_x, 23])
    result = v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=90,
        min_t=10,
        split_quantile=0.5,
        output_times=[subset.time.values[-1]],
    )(subset).compute()

    def manual(left: np.ndarray, right: np.ndarray, *, upper: bool) -> float:
        valid = np.isfinite(left) & np.isfinite(right)
        left = left[valid]
        right = right[valid]
        if upper:
            mask = (left > np.quantile(left, 0.5)) & (right > np.quantile(right, 0.5))
        else:
            mask = (left <= np.quantile(left, 0.5)) & (right <= np.quantile(right, 0.5))
        return float(np.corrcoef(rankdata(left[mask]), rankdata(right[mask]))[0, 1])

    cold_manual = manual(subset.tmin[:, 0, 0].values, subset.tmin[:, 1, 1].values, upper=False)
    warm_manual = manual(subset.tmax[:, 0, 0].values, subset.tmax[:, 1, 1].values, upper=True)
    cold_package = float(result.bottom_synchrony.isel(time_window_end=0, y=0, x=0))
    warm_package = float(result.top_synchrony.isel(time_window_end=0, y=0, x=0))
    difference = float(result.bottom_minus_top.isel(time_window_end=0, y=0, x=0))

    np.testing.assert_allclose(cold_manual, cold_package, atol=1e-7, rtol=0)
    np.testing.assert_allclose(warm_manual, warm_package, atol=1e-7, rtol=0)
    np.testing.assert_allclose(difference, cold_package - warm_package, atol=1e-7, rtol=0)
