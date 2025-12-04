import numpy as np
import xarray as xr

from cubedynamics.verbs import landsat_vis_ndvi


def _synthetic_landsat_stack():
    time = 4
    y = 200
    x = 200
    y_coords = np.arange(y)
    x_coords = np.arange(x)
    yy, xx = np.meshgrid(y_coords, x_coords, indexing="ij")

    base = np.full((time, y, x), np.nan, dtype=np.float32)
    rotated_mask = (yy + xx > 80) & (xx - yy < 120) & (yy - xx < 150)

    red = base.copy()
    nir = base.copy()
    for t in range(time):
        red[t][rotated_mask] = 0.2 + 0.05 * t + (yy[rotated_mask] / y) * 0.1
        nir[t][rotated_mask] = 0.4 + 0.02 * t + (xx[rotated_mask] / x) * 0.1

    stack = np.stack([red, nir], axis=1)
    return xr.DataArray(
        stack,
        dims=("time", "band", "y", "x"),
        coords={
            "time": np.arange(time),
            "band": ["red", "nir"],
            "y": y_coords,
            "x": x_coords,
        },
        name="landsat_stack",
    )


def test_landsat_vis_ndvi_downsamples_and_crops():
    stack = _synthetic_landsat_stack()

    ndvi = landsat_vis_ndvi(
        bbox=[0, 0, 1, 1],
        start="2020-01-01",
        end="2020-02-01",
        max_y=64,
        max_x=64,
        max_time=4,
        stack_da=stack,
    )

    assert ndvi.dims == ("time", "y", "x")
    assert ndvi.sizes["y"] <= 64
    assert ndvi.sizes["x"] <= 64
    assert ndvi.sizes["time"] <= 4

    assert np.isfinite(ndvi.isel(y=0)).any()
    assert np.isfinite(ndvi.isel(y=-1)).any()
    assert np.isfinite(ndvi.isel(x=0)).any()
    assert np.isfinite(ndvi.isel(x=-1)).any()

    finite_vals = ndvi.values[np.isfinite(ndvi.values)]
    assert finite_vals.size > 0
    assert np.unique(np.round(finite_vals, 3)).size > 1
