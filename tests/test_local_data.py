"""Synthetic file fixtures exercise lazy private-storage access offline."""
import json

import dask.array as da
import numpy as np
import pytest
import xarray as xr

from cubedynamics import data, pipe, verbs as v


def write_cube(path, day=1, x=(10, 11)):
    cube = xr.Dataset(
        {"moisture": (("time", "lat", "lon"), np.full((1, 2, 2), day, dtype=float)),
         "quality": (("time", "lat", "lon"), np.ones((1, 2, 2)))},
        coords={"time": [np.datetime64(f"2024-01-{day:02d}", "ns")], "lat": [41, 40], "lon": list(x)},
        attrs={"crs": "EPSG:4326", "is_synthetic": 1, "provenance": "unit test"},
    )
    cube.moisture.attrs["units"] = "m3 m-3"
    cube.to_netcdf(path, engine="h5netcdf")
    return cube


def test_local_netcdf_lazy_pipe_and_provenance(tmp_path):
    path = tmp_path / "private.nc"
    expected = write_cube(path)
    with data.open_local_cube(path, dataset_id="lab/moisture", revision="run-42",
                              variables=["moisture"], chunks={"time": 1}) as cube:
        assert isinstance(cube.moisture.data, da.Array)
        assert cube.moisture.attrs == expected.moisture.attrs
        assert cube.attrs["crs"] == "EPSG:4326"
        assert cube.attrs["is_synthetic"] == 1
        assert cube.attrs["provenance"] == "unit test"
        assert tuple(cube.moisture.dims) == ("time", "lat", "lon")
        record = json.loads(cube.attrs["local_source_provenance"])
        assert record["dataset_id"] == "lab/moisture"
        assert record["revision"] == "run-42"
        assert record["files"][0]["path"] == str(path.resolve())
        assert record["files"][0]["size_bytes"] == path.stat().st_size
        mean = (pipe(cube) | v.mean(dim="time")).unwrap()
        assert isinstance(mean.moisture.data, da.Array)
        xr.testing.assert_equal(cube.compute(), expected[["moisture"]])


def test_multifile_glob_and_explicit_list(tmp_path):
    paths = [tmp_path / f"day-{day}.nc" for day in (2, 1)]
    for day, path in zip((2, 1), paths):
        write_cube(path, day)
    for source in (paths, str(tmp_path / "*.nc")):
        with data.open_local_cube(source, dataset_id="private") as cube:
            assert isinstance(cube.moisture.data, da.Array)
            assert cube.sizes["time"] == 2
            np.testing.assert_equal(cube.moisture[:, 0, 0].compute().values, [1, 2])
            assert json.loads(cube.attrs["local_source_provenance"])["revision"] is None


def test_mismatched_spatial_grid_fails(tmp_path):
    write_cube(tmp_path / "one.nc")
    write_cube(tmp_path / "two.nc", 2, x=(11, 12))
    with pytest.raises(ValueError):
        data.open_local_cube(str(tmp_path / "*.nc"), dataset_id="private")


def test_open_does_not_execute_data_tasks(tmp_path):
    from dask.callbacks import Callback
    write_cube(tmp_path / "one.nc")
    tasks = []
    with Callback(pretask=lambda *args: tasks.append(args)):
        with data.open_local_cube(tmp_path / "one.nc", dataset_id="private") as cube:
            assert isinstance(cube.moisture.data, da.Array)
    assert tasks == []


def test_missing_variables_close_backend(tmp_path, monkeypatch):
    write_cube(tmp_path / "one.nc")
    closed = []
    dataset = xr.Dataset({"value": ("time", [1])})
    dataset.set_close(lambda: closed.append(True))
    monkeypatch.setattr(xr, "open_dataset", lambda *a, **k: dataset)
    with pytest.raises(KeyError):
        data.open_local_cube(tmp_path / "one.nc", dataset_id="private", variables=["missing"])
    assert closed == [True]


@pytest.mark.parametrize("source,exception", [("absent*.nc", FileNotFoundError),
    ([], ValueError), ("https://example.org/private.nc", ValueError)])
def test_invalid_paths(tmp_path, source, exception, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(exception):
        data.open_local_cube(source, dataset_id="private")


def test_duplicate_files_and_empty_identity_fail(tmp_path):
    path = tmp_path / "one.nc"
    write_cube(path)
    with pytest.raises(ValueError, match="Duplicate"):
        data.open_local_cube([path, path], dataset_id="private")
    with pytest.raises(ValueError, match="dataset_id"):
        data.open_local_cube(path, dataset_id=" ")


def test_zarr_lazy_read(tmp_path):
    pytest.importorskip("zarr")
    expected = write_cube(tmp_path / "one.nc")
    path = tmp_path / "private.zarr"
    expected.to_zarr(path)
    with data.open_local_cube(path, dataset_id="private", chunks={"time": 1}) as cube:
        assert isinstance(cube.moisture.data, da.Array)
        assert json.loads(cube.attrs["local_source_provenance"])["format"] == "zarr"
        xr.testing.assert_equal(cube.compute(), expected)
