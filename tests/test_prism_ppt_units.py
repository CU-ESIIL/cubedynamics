from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

import cubedynamics.data.prism as prism


def test_prism_ppt_units_are_mm(monkeypatch):
    def fake_stream(variables, start, end, aoi, freq, show_progress=True):
        coords = {
            "time": pd.date_range("2000-01-01", periods=1, freq="D"),
            "y": np.array([40.0]),
            "x": np.array([-105.25]),
        }
        da = xr.DataArray(
            np.ones((1, 1, 1)),
            coords=coords,
            dims=("time", "y", "x"),
            name="ppt",
            attrs={"units": "synthetic"},
        )
        return xr.Dataset({"ppt": da})

    monkeypatch.setattr(prism, "_open_prism_streaming", fake_stream)

    da = prism.load_prism_cube(
        lat=40.0,
        lon=-105.25,
        start="2000-01-01",
        end="2000-01-02",
        variable="ppt",
    )

    assert isinstance(da, xr.DataArray)
    assert da.name == "ppt"
    assert da.attrs.get("units") == "mm"
