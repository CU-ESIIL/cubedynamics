"""Offline contracts for duplicate Sentinel-2 processing records."""

from __future__ import annotations

import dask.array as da
import numpy as np
import xarray as xr

from cubedynamics.data import sentinel2


class DuplicateSceneCubo:
    @staticmethod
    def create(**kwargs):
        values = da.from_array(
            np.arange(4 * 2 * 3 * 3, dtype="float32").reshape(4, 2, 3, 3),
            chunks=(1, 2, 3, 3),
        )
        return xr.DataArray(
            values,
            dims=("time", "band", "y", "x"),
            coords={
                "time": np.array(
                    ["2023-06-02", "2023-06-02", "2023-06-07", "2023-06-07"],
                    dtype="datetime64[ns]",
                ),
                "band": ["B04", "B08"],
                "y": [2, 1, 0],
                "x": [0, 1, 2],
                "id": (
                    "time",
                    ["old-a", "new-a", "old-b", "new-b"],
                ),
                "s2:generation_time": (
                    "time",
                    [
                        "2023-06-03T12:00:00Z",
                        "2024-09-11T12:00:00Z",
                        "2023-06-08T12:00:00Z",
                        "2024-09-27T12:00:00Z",
                    ],
                ),
                "epsg": 32613,
            },
            attrs={"epsg": 32613},
        )


def test_loader_keeps_latest_processing_record_without_loading_imagery(monkeypatch):
    monkeypatch.setattr(sentinel2, "cubo", DuplicateSceneCubo)

    result = sentinel2.load_s2_cube(
        lat=43.89,
        lon=-102.18,
        start="2023-06-01",
        end="2023-06-10",
        edge_size=3,
        bands=["B04", "B08"],
    )

    assert result.sizes["time"] == 2
    assert result.coords["id"].values.tolist() == ["new-a", "new-b"]
    assert result.attrs["duplicate_acquisitions_removed"] == 2
    assert result.attrs["duplicate_selection"].startswith("latest")
    assert isinstance(result.data, da.Array)
