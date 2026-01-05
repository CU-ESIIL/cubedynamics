import numpy as np
import pytest
import xarray as xr

from cubedynamics.viewers.cube_viewer import _extract_faces, _infer_dims, write_cube_viewer


def test_write_cube_viewer_creates_html(tmp_path):
    data = np.linspace(-1, 1, 3 * 4 * 5).reshape(3, 4, 5)
    da = xr.DataArray(data, dims=("time", "y", "x"))

    out_file = tmp_path / "viewer.html"
    with pytest.warns(DeprecationWarning):
        result = write_cube_viewer(da, out_html=out_file, title="Test Cube")

    assert result.exists()
    text = result.read_text()
    assert "data:image/png;base64" in text
    assert "__TOP_TEXTURE__" not in text


def test_dimension_inference_and_faces():
    data = np.arange(120 * 3 * 4).reshape(120, 3, 4)
    da = xr.DataArray(data, dims=("lat", "lon", "depth"))

    time_dim, y_dim, x_dim = _infer_dims(da)
    assert time_dim == "lat"
    assert (y_dim, x_dim) == ("lon", "depth")

    top, front, side = _extract_faces(da, time_dim, y_dim, x_dim)

    np.testing.assert_array_equal(
        top, da.isel({time_dim: -1}).transpose(y_dim, x_dim).values
    )
    np.testing.assert_array_equal(
        front, da.isel({x_dim: 0}).transpose(time_dim, y_dim).values
    )
    np.testing.assert_array_equal(
        side, da.isel({y_dim: -1}).transpose(time_dim, x_dim).values
    )
