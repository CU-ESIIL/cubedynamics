from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics.plotting.cube_viewer import cube_from_dataarray


def test_cube_viewer_rotation_target_uses_wrapper(tmp_path):
    data = xr.DataArray(
        np.arange(2 * 3 * 3, dtype=float).reshape(2, 3, 3),
        dims=("time", "y", "x"),
        coords={
            "time": pd.date_range("2023-01-01", periods=2, freq="D"),
            "y": np.arange(3),
            "x": np.arange(3),
        },
        name="demo",
    )

    html = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "viewer.html"),
        return_html=True,
        show_progress=False,
        thin_time_factor=1,
    )

    assert "const rotationTarget = cubeWrapper || scene" in html
    assert "const rotationTarget = scene || cubeWrapper" not in html
    assert 'scene.style.setProperty("--rot-x"' not in html

    scene_block = html.split(".cube-scene {", 1)[1].split("}", 1)[0]
    assert "--rot-x" not in scene_block
    assert "--rot-y" not in scene_block
    assert "--zoom" not in scene_block
