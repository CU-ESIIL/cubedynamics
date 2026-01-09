from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from IPython.display import IFrame

from cubedynamics.plotting.cube_viewer import cube_from_dataarray


def test_cube_viewer_emits_interactive_markup(tmp_path):
    data = xr.DataArray(
        np.arange(4 * 8 * 8, dtype=float).reshape(4, 8, 8),
        dims=("time", "y", "x"),
        coords={
            "time": pd.date_range("2023-01-01", periods=4, freq="D"),
            "y": np.arange(8),
            "x": np.arange(8),
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

    # DOM structure invariants (documented in docs/cube_viewer.md)
    assert 'class="cube-figure"' in html
    assert 'id="cube-figure-' in html
    assert 'id="cube-container"' not in html  # container uses class only
    assert 'class="cube-container"' in html
    assert 'id="cube-wrapper-' in html
    assert 'id="cube-rotation-' in html
    assert 'id="cube-drag-' in html
    assert 'id="cube-js-warning-' in html
    assert 'id="cd-drift-center-v1-js"' in html
    assert 'addEventListener("pointerdown"' in html
    assert 'addEventListener("wheel"' in html
    assert 'passive: false' in html
    assert 'document.getElementById("cube-figure-' in html
    assert (tmp_path / "viewer.html").exists()


def test_cube_viewer_wraps_html_in_iframe(tmp_path):
    data = xr.DataArray(
        np.arange(4 * 4 * 4, dtype=float).reshape(4, 4, 4),
        dims=("time", "y", "x"),
        name="demo",
    )

    iframe = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "viewer.html"),
        show_progress=False,
        thin_time_factor=1,
    )

    assert isinstance(iframe, IFrame)
    path = Path(getattr(iframe, "cube_viewer_path"))
    assert path.exists()
    html = path.read_text()
    assert "cube-figure-" in html
    assert "cube-canvas-" in html
