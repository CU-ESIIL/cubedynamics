"""Offline transport contracts plus an explicitly enabled Boulder live check."""
import importlib
import os
from types import SimpleNamespace

import dask.array as da
import numpy as np
import pytest
import xarray as xr
from dask.callbacks import Callback

from cubedynamics import pipe, verbs as v

adapter = importlib.import_module("cubedynamics.verbs.landsat_mpc")
OPTIONS = dict(bbox=[-105.35, 39.90, -105.15, 40.10], start="2024-07-01",
               end="2024-09-01", epsg=32613, max_cloud_cover=20)


@pytest.fixture
def services(monkeypatch):
    import planetary_computer
    import pystac_client
    import stackstac

    calls = {}
    item = SimpleNamespace(id="LC09-test", properties={"proj:epsg": 32613},
                           assets={name: SimpleNamespace(extra_fields={"raster:bands": [{"scale": 2.75e-5, "offset": -0.2}]})
                                   for name in ("red", "nir08", "qa_pixel")})

    class Search:
        def items(self):
            calls["items"] = True
            return iter(calls.get("results", [item]))

        def get_items(self):
            pytest.fail("Deprecated get_items called")

    def search(**kwargs):
        calls["search"] = kwargs
        return Search()

    monkeypatch.setattr(pystac_client.Client, "open", lambda url: SimpleNamespace(search=search))

    def sign(value):
        calls.setdefault("signed", []).append(value)
        return value

    monkeypatch.setattr(planetary_computer, "sign", sign)
    cube = xr.DataArray(da.from_array(np.array([0.2, 0.6]).reshape(1, 2, 1, 1), chunks=1),
                        dims=("time", "band", "y", "x"),
                        coords={"band": ["red", "nir08"]})

    def stack(items, **kwargs):
        calls["stack"] = kwargs
        assert items == calls["signed"][-len(items):]
        return cube

    monkeypatch.setattr(stackstac, "stack", stack)
    calls["item"] = item
    return calls


def test_public_namespace_and_pipe_contract(services):
    assert callable(v.landsat_mpc)
    assert v.landsat_mpc is adapter.landsat_mpc
    stage = v.landsat_mpc(**OPTIONS, resolution=30, chunksize=128)
    assert "search" not in services  # factories do not discover until invoked
    tasks = []
    with Callback(pretask=lambda *args: tasks.append(args)):
        result = pipe(None) | stage
        cube = result.unwrap()
        ndvi = (cube.sel(band="nir08") - cube.sel(band="red")) / (
            cube.sel(band="nir08") + cube.sel(band="red"))
    assert not tasks
    assert ndvi.chunks is not None
    assert cube.dims == ("time", "band", "y", "x")
    assert cube.chunks is not None
    assert result.semantic_trace[-1].verb == "landsat_mpc"
    assert services["items"]
    assert services["search"]["collections"] == ["landsat-c2-l2"]
    assert services["search"]["datetime"] == "2024-07-01/2024-09-01"
    assert services["search"]["query"] == {"eo:cloud_cover": {"lt": 20}}
    assert services["stack"]["assets"] == ["red", "nir08"]
    assert services["stack"]["bounds_latlon"] == tuple(OPTIONS["bbox"])
    assert services["stack"]["epsg"] == 32613
    assert services["stack"]["resolution"] == 30
    assert services["stack"]["chunksize"] == 128
    assert services["stack"]["rescale"] is True
    np.testing.assert_allclose(cube.compute().data.ravel(), [0.2, 0.6])
    np.testing.assert_allclose(ndvi.compute(), 0.5)
    assert callable(v.landsat_mpc)  # still callable after loading submodule


def test_direct_calls_and_common_crs(services):
    options = {**OPTIONS, "epsg": None}
    assert v.landsat_mpc(None, **options).chunks is not None
    assert v.landsat_mpc(value=None, **options).chunks is not None
    assert services["stack"]["epsg"] == 32613
    services["item"].properties = {"proj:code": "EPSG:32613"}
    v.landsat_mpc(None, **options)
    assert services["stack"]["epsg"] == 32613


def test_missing_or_mixed_crs_requires_explicit_epsg(services):
    options = {**OPTIONS, "epsg": None}
    services["item"].properties = {}
    with pytest.raises(ValueError, match="Specify epsg="):
        v.landsat_mpc(None, **options)
    services["item"].properties = {"proj:epsg": 32613}
    services["item"].assets["nir08"].extra_fields["proj:code"] = "EPSG:32614"
    with pytest.raises(ValueError, match="Specify epsg="):
        v.landsat_mpc(None, **options)


def test_reflectance_requires_scaling_metadata(services):
    services["item"].assets["red"].extra_fields = {}
    with pytest.raises(ValueError, match="lacks STAC scale/offset"):
        v.landsat_mpc(None, **OPTIONS)


def test_existing_ndvi_verb_is_compatible(services):
    cube = v.landsat_mpc(None, **OPTIONS)
    ndvi = (pipe(cube) | v.ndvi_from_s2(nir_band="nir08", red_band="red")).unwrap()
    assert ndvi.chunks is not None
    np.testing.assert_allclose(ndvi.compute(), 0.5)


def test_empty_and_missing_assets_fail_honestly(services):
    with pytest.raises(ValueError, match="lacks requested assets"):
        v.landsat_mpc(None, **OPTIONS, bands=("invented",))
    services["results"] = []
    with pytest.raises(RuntimeError, match="No Landsat items"):
        v.landsat_mpc(None, **OPTIONS)


@pytest.mark.parametrize("overrides", [dict(bbox=[1, 0, 0, 1]), dict(bands="red"),
                                      dict(bands=()), dict(bands=("red", "red")),
                                      dict(max_cloud_cover=101), dict(resolution=0),
                                      dict(platforms=())])
def test_invalid_inputs(services, overrides):
    with pytest.raises(ValueError):
        v.landsat_mpc(None, **{**OPTIONS, **overrides})
    assert "search" not in services


def test_legacy_landsat8_labels_chunks_and_platform(services):
    cube = (pipe(None) | v.landsat8_mpc(**OPTIONS, chunks_xy={"x": 128, "y": 64})).unwrap()
    assert cube.band.data.tolist() == ["red", "nir"]
    assert cube.dtype == np.float32
    assert cube.chunks is not None
    assert services["search"]["query"]["platform"] == {"in": ["landsat-8"]}
    assert services["stack"]["chunksize"] == (1, 1, 64, 128)
    assert callable(v.landsat_mpc)


def test_real_stackstac_scaling_once_and_lazy_local_cogs(tmp_path, monkeypatch):
    """Actual stackstac raster path: known DN must become physical reflectance once."""
    import datetime
    import planetary_computer
    import pystac
    import pystac_client
    import rasterio
    from rasterio.transform import from_origin

    item = pystac.Item("local", geometry=None, bbox=OPTIONS["bbox"],
                       datetime=datetime.datetime(2024, 7, 1, tzinfo=datetime.timezone.utc),
                       properties={"proj:epsg": 32613})
    for name, dn in (("red", 10000), ("nir08", 20000), ("qa_pixel", 64)):
        path = tmp_path / f"{name}.tif"
        with rasterio.open(path, "w", driver="GTiff", height=32, width=32, count=1,
                           dtype="uint16", crs="EPSG:32613",
                           transform=from_origin(480000, 4430000, 30, 30), nodata=0) as dst:
            dst.write(np.full((1, 32, 32), dn, dtype="uint16"))
        item.add_asset(name, pystac.Asset(str(path), media_type="image/tiff",
                       extra_fields={"proj:shape": [32, 32],
                                     "proj:transform": [30, 0, 480000, 0, -30, 4430000],
                                     "raster:bands": ([{"nodata": 1}] if name == "qa_pixel" else
                                                       [{"scale": 0.0000275, "offset": -0.2,
                                                         "nodata": 0}])}))
    monkeypatch.setattr(pystac_client.Client, "open", lambda url: SimpleNamespace(
        search=lambda **kwargs: SimpleNamespace(items=lambda: iter([item]))))
    monkeypatch.setattr(planetary_computer, "sign", lambda item: item)
    tasks = []
    with Callback(pretask=lambda *args: tasks.append(args)):
        cube = v.landsat_mpc(None, **OPTIONS, bands=("red", "nir08", "qa_pixel"))
    assert not tasks
    assert cube.chunks is not None
    values = cube.compute()
    qa = values.sel(band="qa_pixel").data
    np.testing.assert_allclose(qa[np.isfinite(qa)], 64)
    red = values.sel(band="red")
    nir = values.sel(band="nir08")
    np.testing.assert_allclose(red.data[np.isfinite(red.data)], 0.075)
    np.testing.assert_allclose(nir.data[np.isfinite(nir.data)], 0.35)
    assert np.isfinite(red.data).sum() > 0
    ndvi = (nir - red) / (nir + red)
    np.testing.assert_allclose(ndvi.data[np.isfinite(ndvi.data)], 0.275 / 0.425)


@pytest.mark.online
@pytest.mark.integration
@pytest.mark.streaming
@pytest.mark.skipif(os.getenv("CUBEDYNAMICS_TEST_LANDSAT_MPC") != "1",
                    reason="Set CUBEDYNAMICS_TEST_LANDSAT_MPC=1 for live MPC")
def test_boulder_live_mpc():
    from pyproj import Transformer

    cube = (pipe(None) | v.landsat_mpc(**OPTIONS, resolution=30, chunksize=128)).unwrap()
    assert cube.sizes["time"] > 0
    assert cube.dims == ("time", "band", "y", "x")
    assert cube.band.data.tolist() == ["red", "nir08"]
    assert cube.chunks is not None
    assert cube.attrs["epsg"] == 32613
    np.testing.assert_allclose(np.diff(cube.x.data), 30)
    np.testing.assert_allclose(np.diff(cube.y.data), -30)
    bounds = Transformer.from_crs(4326, 32613, always_xy=True).transform_bounds(*OPTIONS["bbox"])
    actual = (float(cube.x.min()), float(cube.y.min()) - 30,
              float(cube.x.max()) + 30, float(cube.y.max()))
    np.testing.assert_allclose(actual, bounds, atol=31, rtol=0)
    # Check three small patches across the rectangle, not every pixel or scene.
    finite = []
    for fraction in (0.25, 0.5, 0.75):
        y, x = (int(cube.sizes[d] * fraction) for d in ("y", "x"))
        subset = cube.isel(time=slice(0, 3), y=slice(y, y + 32), x=slice(x, x + 32))
        red, nir = subset.sel(band="red", drop=True), subset.sel(band="nir08", drop=True)
        ndvi = (nir - red) / (nir + red)
        assert ndvi.chunks is not None
        computed = xr.Dataset({"red": red, "nir": nir, "ndvi": ndvi}).compute()
        values = computed.red.data
        values = values[np.isfinite(values)]
        if values.size:
            assert -0.1 < np.median(values) < 1.5
            assert np.quantile(values, 0.9) > 0.01  # double scaling collapses near -0.2
            finite.extend(computed.ndvi.data[np.isfinite(computed.ndvi.data)].tolist())
    assert finite
    assert -1 <= np.median(finite) <= 1
    print(f"Boulder MPC sizes={dict(cube.sizes)}, EPSG=32613, resolution=30 m, "
          f"finite NDVI samples={len(finite)}, median NDVI={np.median(finite):.6f}")
