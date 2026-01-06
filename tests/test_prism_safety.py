import numpy as np
import pandas as pd
import pytest
import xarray as xr

from cubedynamics.data.prism import load_prism_cube

from tests.helpers.contracts import (
    assert_not_all_nan,
    assert_provenance_attrs,
    assert_spatiotemporal_cube_contract,
)


def _empty_time_dataset(variable: str = "ppt") -> xr.Dataset:
    coords = {"time": pd.DatetimeIndex([]), "y": np.array([40.0, 40.1]), "x": np.array([-105.2, -105.1])}
    data = xr.DataArray(
        np.empty((0, 2, 2)),
        coords=coords,
        dims=("time", "y", "x"),
        name=variable,
    )
    return xr.Dataset({variable: data})


def _all_nan_dataset(variable: str = "ppt") -> xr.Dataset:
    coords = {
        "time": pd.date_range("2018-07-17", periods=3, freq="D"),
        "y": np.array([40.0, 40.1]),
        "x": np.array([-105.2, -105.1]),
    }
    data = xr.DataArray(
        np.full((3, 2, 2), np.nan),
        coords=coords,
        dims=("time", "y", "x"),
        name=variable,
    )
    return xr.Dataset({variable: data})


def test_prism_empty_time_raises_without_synthetic(monkeypatch):
    def _stub_streaming(*args, **kwargs):
        return _empty_time_dataset()

    monkeypatch.setattr("cubedynamics.data.prism._open_prism_streaming", _stub_streaming)

    with pytest.raises(RuntimeError, match="empty time.*ME"):
        load_prism_cube(
            lat=40.0,
            lon=-105.0,
            start="2018-07-17",
            end="2018-07-25",
            variable="ppt",
            freq="ME",
            prefer_streaming=True,
            show_progress=False,
            allow_synthetic=False,
        )


def test_prism_empty_time_allows_synthetic(monkeypatch):
    def _stub_streaming(*args, **kwargs):
        return _empty_time_dataset()

    monkeypatch.setattr("cubedynamics.data.prism._open_prism_streaming", _stub_streaming)

    ds = load_prism_cube(
        lat=40.0,
        lon=-105.0,
        start="2018-07-17",
        end="2018-07-25",
        variable="ppt",
        freq="ME",
        prefer_streaming=True,
        show_progress=False,
        allow_synthetic=True,
    )

    assert_spatiotemporal_cube_contract(ds)
    assert_provenance_attrs(
        ds,
        expected_source="synthetic",
        expected_is_synthetic=True,
        require_freq=True,
    )
    assert "empty time" in ds.attrs.get("backend_error", "")


@pytest.mark.parametrize("allow_synthetic", [False, True])
def test_prism_all_nan_handling(monkeypatch, allow_synthetic):
    def _stub_streaming(*args, **kwargs):
        return _all_nan_dataset()

    monkeypatch.setattr("cubedynamics.data.prism._open_prism_streaming", _stub_streaming)

    if not allow_synthetic:
        with pytest.raises(RuntimeError, match="all-NaN"):
            load_prism_cube(
                lat=40.0,
                lon=-105.0,
                start="2018-07-17",
                end="2018-07-25",
                variable="ppt",
                prefer_streaming=True,
                show_progress=False,
                allow_synthetic=False,
            )
    else:
        ds = load_prism_cube(
            lat=40.0,
            lon=-105.0,
            start="2018-07-17",
            end="2018-07-25",
            variable="ppt",
            prefer_streaming=True,
            show_progress=False,
            allow_synthetic=True,
        )
        assert_spatiotemporal_cube_contract(ds)
        assert_provenance_attrs(
            ds,
            expected_source="synthetic",
            expected_is_synthetic=True,
            require_freq=True,
        )
        assert_not_all_nan(ds)
        assert "all-NaN" in ds.attrs.get("backend_error", "")
