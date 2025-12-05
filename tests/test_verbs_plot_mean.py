import numpy as np
import pandas as pd
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.plotting.multicube_plot import MultiCubePlot


def test_plot_mean_attaches_viewer_and_returns_original_cube():
    times = pd.date_range("2024-01-01", periods=3, freq="D")
    da = xr.DataArray(
        np.arange(3 * 2 * 2, dtype=float).reshape(3, 2, 2),
        coords={"time": times, "y": [0, 1], "x": [0, 1]},
        dims=("time", "y", "x"),
        name="ndvi",
    )

    result = pipe(da) | v.plot_mean()

    assert result.unwrap() is da

    viewer = getattr(da, "_cd_last_viewer", None)
    assert isinstance(viewer, MultiCubePlot)

    config = viewer._to_config()
    assert config["mode"] == "paired"
    assert [cube["label"] for cube in config["cubes"]] == ["Mean", "Variance"]

    expected_mean = da.mean(dim="time").values.tolist()
    expected_var = da.var(dim="time", ddof=1).values.tolist()
    assert config["cubes"][0]["data"]["values"] == expected_mean
    assert config["cubes"][1]["data"]["values"] == expected_var

    html = viewer._repr_html_()
    assert html.count("<canvas class=\"cubeplot-canvas\"></canvas>") == 1
    assert "cubeplot-paired-" in html

