import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics.streaming import VirtualCube


def _fake_loader_factory(base: xr.DataArray):
    def loader(start=None, end=None, bbox=None, **_kwargs):
        da = base
        if start is not None or end is not None:
            start_ts = pd.to_datetime(start) if start is not None else pd.to_datetime(base.time.values[0])
            end_ts = pd.to_datetime(end) if end is not None else pd.to_datetime(base.time.values[-1])
            da = da.sel(time=slice(start_ts, end_ts))

        if bbox is not None:
            xmin, ymin, xmax, ymax = bbox
            da = da.sel(x=slice(xmin, xmax), y=slice(ymin, ymax))

        return da

    return loader


def _make_tilers(times, bbox):
    def time_tiler(_kwargs):
        for ts in times:
            yield {"start": ts, "end": ts}

    def spatial_tiler(_kwargs):
        xmin, ymin, xmax, ymax = bbox
        mid_y = ymin + (ymax - ymin) / 2
        yield {"bbox": (xmin, ymin, xmax, mid_y)}
        yield {"bbox": (xmin, np.nextafter(mid_y, ymax), xmax, ymax)}

    return time_tiler, spatial_tiler


def test_virtual_cube_tiles_and_materialize_match():
    times = pd.date_range("2020-01-01", periods=3, freq="D")
    y = np.arange(2)
    x = np.arange(3)
    data = np.zeros((times.size, y.size, x.size))
    for t_idx, t_val in enumerate(times):
        for yi, y_val in enumerate(y):
            for xi, _ in enumerate(x):
                data[t_idx, yi, xi] = t_idx + y_val + 10 * xi

    base = xr.DataArray(data, coords={"time": times, "y": y, "x": x}, dims=("time", "y", "x"), name="fake")

    loader = _fake_loader_factory(base)
    time_tiler, spatial_tiler = _make_tilers(times, (x.min(), y.min(), x.max(), y.max()))

    vc = VirtualCube(
        dims=("time", "y", "x"),
        coords_metadata={},
        loader=loader,
        loader_kwargs={},
        time_tiler=time_tiler,
        spatial_tiler=spatial_tiler,
    )

    tiles = list(vc.iter_tiles())
    assert len(tiles) == 6  # 3 time tiles x 2 spatial tiles
    assert all(isinstance(tile, xr.DataArray) for tile in tiles)

    expected_shapes = {(1, 1, 3)}
    assert {tile.shape for tile in tiles} == expected_shapes

    combined = xr.combine_by_coords(tiles)
    if isinstance(combined, xr.Dataset) and len(combined.data_vars) == 1:
        combined = combined[next(iter(combined.data_vars))]
    materialized = vc.materialize().transpose(*combined.dims)
    xr.testing.assert_allclose(materialized, combined)
    xr.testing.assert_allclose(materialized, base)
