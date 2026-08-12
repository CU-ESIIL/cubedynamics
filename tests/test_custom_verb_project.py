from __future__ import annotations

import numpy as np
import xarray as xr

from cubedynamics import pipe
from examples.custom_verb_project import heat_stress


def _temperature_cube() -> xr.DataArray:
    return xr.DataArray(
        np.array([[[33.0, 36.0]], [[35.0, 38.0]]]),
        dims=("time", "y", "x"),
        coords={"time": ["2026-07-01", "2026-07-02"], "y": [0], "x": [0, 1]},
        name="temperature",
        attrs={"units": "degC"},
    )


def test_project_verb_matches_direct_and_pipe_use():
    cube = _temperature_cube()

    direct = heat_stress(threshold=35.0)(cube)
    composed = (pipe(cube) | heat_stress(threshold=35.0)).unwrap()

    xr.testing.assert_identical(direct, composed)
    assert direct["state"].sum().item() == 3
    assert direct.attrs["project_verb"] == "heat_stress"
    assert direct.attrs["units"] == "degC"


def test_project_verb_requires_time_dimension():
    cube = _temperature_cube().isel(time=0, drop=True)

    try:
        heat_stress()(cube)
    except ValueError as exc:
        assert "time" in str(exc)
    else:
        raise AssertionError("heat_stress accepted a cube without time")
