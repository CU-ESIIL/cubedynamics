import dask.array as dsa
import numpy as np
import xarray as xr

from cubedynamics.plotting.cube_plot import (
    CubeAes,
    CubeLayer,
    CubePlot,
    ScaleFillContinuous,
    _infer_aes_from_data,
    geom_cube,
    geom_outline,
    geom_path3d,
    geom_slice,
    CubeFacet,
    stat_space_mean,
    stat_time_anomaly,
    stat_time_mean,
    CoordCube,
    theme_cube_studio,
)
from cubedynamics.plotting.cube_viewer import cube_from_dataarray


def test_cube_aes_inference_and_defaults():
    data = xr.DataArray(np.arange(8).reshape(2, 2, 2), dims=("time", "y", "x"), name="demo")
    aes = _infer_aes_from_data(data)
    assert aes.fill == "demo"
    assert CubeAes().alpha is None


def test_geom_helpers_return_layers():
    assert geom_cube().geom == "cube"
    assert geom_slice(axis="time").geom == "slice"
    assert geom_outline().geom == "outline"
    assert geom_path3d().geom == "path3d"


def test_cubeplot_defaults_add_layer():
    data = xr.DataArray(np.ones((2, 2, 2)), dims=("time", "y", "x"))
    cp = CubePlot(data, show_progress=False)
    assert cp.layers and cp.layers[0].geom == "cube"


def test_stat_functions_support_dask():
    darr = dsa.arange(16).reshape(2, 2, 4)
    data = xr.DataArray(darr, dims=("time", "y", "x"))
    mean_da = stat_time_mean(data, CubeAes(), {"time_dim": "time"})
    assert mean_da.shape == (2, 4)

    anomaly = stat_time_anomaly(data, CubeAes(), {"time_dim": "time"})
    assert anomaly.shape == data.shape

    spatial = stat_space_mean(data, CubeAes(), {"dims": ("y", "x")})
    assert spatial.shape == (2,)


def test_scale_fill_limits_and_legend(tmp_path):
    data = xr.DataArray(np.linspace(0, 1, 8).reshape(2, 2, 2), dims=("time", "y", "x"), name="vals")
    scale = ScaleFillContinuous(name="Legend Name")
    limits = scale.infer_limits(data)
    assert limits[0] <= 0 and limits[1] >= 1

    html = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "cube.html"),
        legend_title=scale.name,
        fill_limits=limits,
        fill_breaks=[0.0, 0.5, 1.0],
        theme=theme_cube_studio(),
        show_progress=False,
        return_html=True,
    )
    assert "Legend Name" in html
    assert "cube-label" in html
    assert "firebrick" in html  # axis color wired through CSS


def test_coordcube_injected_into_html(tmp_path):
    data = xr.DataArray(np.ones((2, 2, 2)), dims=("time", "y", "x"))
    coord = CoordCube(elev=10.0, azim=15.0, zoom=1.2)
    html = cube_from_dataarray(
        data,
        out_html=str(tmp_path / "coord.html"),
        coord=coord,
        show_progress=False,
        return_html=True,
    )
    assert 'data-rot-x="10.0"' in html
    assert 'data-rot-y="15.0"' in html
    assert 'data-zoom="1.2"' in html


def test_caption_and_theme_blocks_render():
    data = xr.DataArray(np.ones((2, 2, 2)), dims=("time", "y", "x"))
    cp = CubePlot(
        data,
        caption={"id": 5, "title": "NDVI anomaly", "text": "**Markdown** + $\\nabla$"},
    )
    html = cp.to_html()
    assert "cube-caption-label" in html
    assert "cube-caption-title" in html
    assert "cube-caption-text" in html
    assert "--cube-bg-color" in html
    assert "--cube-title-color" in html


def test_streaming_iterates_time_slices(monkeypatch):
    data = xr.DataArray(np.arange(40).reshape(5, 2, 4), dims=("time", "y", "x"))
    calls = []
    original_isel = xr.DataArray.isel

    def _wrapped(self, indexers=None, **kwargs):
        if indexers and "time" in indexers:
            calls.append(indexers["time"])
        return original_isel(self, indexers=indexers, **kwargs)

    monkeypatch.setattr(xr.DataArray, "isel", _wrapped)
    cube_from_dataarray(data, show_progress=False, thin_time_factor=2, return_html=True)
    assert calls == [0, 2, 4]


def test_facets_render_multiple_panels(tmp_path):
    data = xr.DataArray(
        np.arange(16).reshape(2, 2, 2, 2),
        dims=("scenario", "time", "y", "x"),
        coords={"scenario": ["base", "alt"]},
    )
    cp = CubePlot(data, facet=CubeFacet(by="scenario"), show_progress=False, out_html=str(tmp_path / "facet.html"))
    html = cp.to_html()
    assert html.count("cube-facet-panel") >= 2
    assert "cube-legend-title" in html
    assert "cube-facet-label" in html


def test_save_exports_html(tmp_path):
    data = xr.DataArray(np.ones((2, 2, 2)), dims=("time", "y", "x"))
    path = tmp_path / "figure1.html"
    cp = CubePlot(data, title="export" , show_progress=False)
    cp.save(path)
    assert path.exists()
