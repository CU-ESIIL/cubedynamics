import numpy as np
import xarray as xr

from cubedynamics import pipe, verbs as v


def test_rolling_tail_dep_vs_center_shape_and_nans():
    np.random.seed(0)
    time = np.arange(20)
    y = np.arange(3)
    x = np.arange(4)
    data = xr.DataArray(
        np.random.randn(len(time), len(y), len(x)),
        dims=("time", "y", "x"),
        coords={"time": time, "y": y, "x": x},
        name="ndvi",
    )

    out = (pipe(data) | v.rolling_tail_dep_vs_center(window=5, dim="time", min_periods=5)).unwrap()

    assert out.dims == data.dims
    assert out.shape == data.shape

    # First few windows should be missing because of min_periods
    early = out.isel(time=slice(0, 4))
    assert np.isnan(early).all()

    # Later windows should contain finite values for most pixels
    later = out.isel(time=slice(6, None))
    assert np.isfinite(later.values).any()
