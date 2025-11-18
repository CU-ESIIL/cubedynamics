"""Basic import and pipe integration tests for cubedynamics."""

import numpy as np
import xarray as xr

import cubedynamics as cd


def test_import_cubedynamics_has_version():
    """Ensure the package exposes a version attribute."""

    assert hasattr(cd, "__version__")


def test_pipe_anomaly_variance_chain():
    """Smoke-test chaining simple pipe verbs if available."""

    da = xr.DataArray(
        np.arange(6),
        dims=["time"],
        coords={"time": np.arange(6)},
    )

    if cd.pipe is None or cd.anomaly is None or cd.variance is None:
        return

    result = cd.pipe(da) | cd.anomaly(dim="time") | cd.variance(dim="time")

    out = getattr(result, "unwrap", lambda: result)()
    assert isinstance(out, xr.DataArray)
