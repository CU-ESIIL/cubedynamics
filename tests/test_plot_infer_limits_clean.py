import numpy as np
import dask.array as da
import xarray as xr

from cubedynamics.plotting.cube_plot import ScaleFillContinuous


class SyntheticError(RuntimeError):
    pass


def test_infer_limits_handles_bad_assets():
    base = da.from_array(np.arange(20.0).reshape(5, 2, 2), chunks=(1, 2, 2))

    def maybe_fail(block, block_id=None):
        if block_id and block_id[0] == 3:
            raise SyntheticError("synthetic failure")
        return block

    failing = base.map_blocks(maybe_fail, dtype=base.dtype)
    cube = xr.DataArray(
        failing,
        dims=("time", "y", "x"),
        coords={"time": np.arange(5), "y": [0, 1], "x": [0, 1]},
        name="test",
    )

    scale = ScaleFillContinuous()
    vmin, vmax = scale.infer_limits(cube)

    assert vmin < vmax
    assert vmin == 0.0
    assert vmax == 19.0
