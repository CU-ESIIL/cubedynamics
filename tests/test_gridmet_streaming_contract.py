"""Offline gridMET streaming contract tests."""

from __future__ import annotations

import dask.array as da
from dask import delayed
import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics.data.gridmet import load_gridmet_cube
from cubedynamics.streaming.gridmet import stream_gridmet_to_cube


def test_load_gridmet_cube_streaming_path_preserves_lazy_data(monkeypatch, recwarn) -> None:
    def fake_streaming(variables, start, end, aoi, freq, show_progress=False):
        times = pd.date_range(start, end, freq=freq)
        y = np.array([40.0, 40.05])
        x = np.array([-105.4, -105.35])
        data = da.ones((len(times), y.size, x.size), chunks=(2, 1, 1))
        return xr.Dataset(
            {
                name: xr.DataArray(
                    data,
                    dims=("time", "y", "x"),
                    coords={"time": times, "y": y, "x": x},
                    name=name,
                )
                for name in variables
            }
        )

    monkeypatch.setattr(
        "cubedynamics.data.gridmet._open_gridmet_streaming",
        fake_streaming,
    )

    cube = load_gridmet_cube(
        variable="tmmx",
        bbox=[-105.4, 40.0, -105.35, 40.05],
        start="2001-01-01",
        end="2001-01-05",
        freq="D",
        prefer_streaming=True,
        show_progress=False,
    )

    assert cube.attrs["source"] == "gridmet_streaming"
    assert cube.attrs["is_synthetic"] is False
    assert cube["tmmx"].chunks is not None
    assert not any("streaming backend unavailable" in str(w.message) for w in recwarn)


def test_load_gridmet_cube_does_not_compute_lazy_streaming_values(monkeypatch) -> None:
    def fail_if_computed():
        raise AssertionError("lazy gridMET values should not be computed by the loader")

    def fake_streaming(variables, start, end, aoi, freq, show_progress=False):
        times = pd.date_range(start, end, freq=freq)
        y = np.array([40.0, 40.05])
        x = np.array([-105.4, -105.35])
        data = da.from_delayed(
            delayed(fail_if_computed)(),
            shape=(len(times), y.size, x.size),
            dtype=float,
        )
        return xr.Dataset(
            {
                name: xr.DataArray(
                    data,
                    dims=("time", "y", "x"),
                    coords={"time": times, "y": y, "x": x},
                    name=name,
                )
                for name in variables
            }
        )

    monkeypatch.setattr(
        "cubedynamics.data.gridmet._open_gridmet_streaming",
        fake_streaming,
    )

    cube = load_gridmet_cube(
        variable="tmmx",
        bbox=[-105.4, 40.0, -105.35, 40.05],
        start="2001-01-01",
        end="2001-01-02",
        freq="D",
        prefer_streaming=True,
        show_progress=False,
    )

    assert cube.attrs["source"] == "gridmet_streaming"
    assert cube["tmmx"].chunks is not None


def test_stream_gridmet_to_cube_reads_each_year_once(monkeypatch) -> None:
    calls: list[int] = []

    def fake_year(variable: str, year: int, chunks=None) -> xr.Dataset:
        calls.append(year)
        times = pd.date_range(f"{year}-01-01", periods=2, freq="D")
        lat = xr.DataArray([40.1, 40.0], dims="lat")
        lon = xr.DataArray([-105.4, -105.3], dims="lon")
        data = da.full(
            (times.size, lat.size, lon.size),
            fill_value=float(year),
            chunks=(1, 1, 1),
        )
        return xr.Dataset(
            {
                variable: xr.DataArray(
                    data,
                    dims=("time", "lat", "lon"),
                    coords={"time": times, "lat": lat, "lon": lon},
                )
            }
        )

    monkeypatch.setattr("cubedynamics.streaming.gridmet._open_gridmet_year", fake_year)

    aoi = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-105.4, 40.0],
                    [-105.4, 40.1],
                    [-105.3, 40.1],
                    [-105.3, 40.0],
                    [-105.4, 40.0],
                ]
            ],
        },
    }
    cube = stream_gridmet_to_cube(
        aoi_geojson=aoi,
        variable="tmmx",
        start="2001-01-01",
        end="2002-01-02",
        chunks={"time": 1},
        show_progress=False,
    )

    assert calls == [2001, 2002]
    assert cube.name == "tmmx"
    assert cube.chunks is not None
    assert cube.sizes["lat"] == 2
    assert cube.sizes["lon"] == 2
