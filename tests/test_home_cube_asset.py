"""The hero is a themed real-data library viewer, not a separate renderer."""
import xarray as xr
import numpy as np
import pytest
import json
from types import SimpleNamespace

from scripts.build_real_data_assets import FIXTURE, ROOT, build_hero_html, check_gallery, example_cube, load_fixture
from scripts.hero_examples import EXAMPLES, PRISM, GRIDMET, LANDS, SENTINEL
from scripts.docs_hooks import on_page_markdown


def test_hero_uses_readable_theme_and_reviewed_measurements():
    with xr.open_dataset(FIXTURE, engine="scipy") as dataset:
        cube = dataset.tmax.load()
    original = cube.copy(deep=True)
    html = build_hero_html(cube)
    xr.testing.assert_identical(cube, original)
    assert cube.attrs["units"] == "degC"
    assert -25 <= float(cube.min()) <= float(cube.max()) <= 20
    assert 'href="../styles/hero-cube.css"' in html
    assert 'name="viewport"' in html
    assert "Daily maximum temperature (°C)" in html
    assert "--cube-axis-color: #213e46" in html
    assert "--cube-legend-color: #213e46" in html
    assert 'data-cb-min="-25.00" data-cb-max="20.00"' in html
    assert '"min_label": "01 Jan 2024"' in html
    assert '"max_label": "30 Jan 2024"' in html
    for control in ("in", "out", "reset"):
        assert f'data-cube-control="{control}"' in html
    assert 'addEventListener("keydown"' in html


def test_gallery_inventory_and_assets_are_current():
    check_gallery()
    assert len({e["id"] for e in EXAMPLES}) == len(EXAMPLES)
    assert len({e["path"] for e in EXAMPLES}) == len(EXAMPLES)
    # Cover every variable/band in the four supported raster fixtures.
    raw = {(e.get("fixture"), e.get("variable"), e.get("transform")) for e in EXAMPLES}
    assert {(PRISM, name, None) for name in ("tmax", "tmin", "diurnal_range")} <= raw
    assert {(LANDS, name, None) for name in ("temperature", "precipitation")} <= raw
    assert (GRIDMET, "temperature", None) in raw
    assert {(SENTINEL, "surface_reflectance", band) for band in ("B04", "B08", "ndvi")} <= raw


@pytest.mark.parametrize("example", [e for e in EXAMPLES if e["kind"] == "cube"], ids=lambda e: e["id"])
def test_every_gallery_cube_preserves_real_coordinates_and_units(example, monkeypatch):
    monkeypatch.setattr("requests.sessions.Session.request", lambda *a, **k: pytest.fail("Gallery requested network"))
    dataset = load_fixture(example["fixture"])
    before = dataset.copy(deep=True)
    cube = example_cube(example, dataset)
    xr.testing.assert_identical(dataset, before)
    assert cube.attrs["is_synthetic"] == 0
    assert cube.attrs["units"] == example["units"]
    assert np.isin(cube.time, dataset.time).all()
    assert np.isin(cube.x, dataset.x).all() and np.isin(cube.y, dataset.y).all()
    html = build_hero_html(cube, example)
    assert html.count('class="cd-face ') == 6
    assert str(cube.time.dt.year.values[0]) in html
    if example["fixture"] == SENTINEL:
        assert '"name": "Easting (m)"' in html
        assert '"name": "Northing (m)"' in html
    transform = example.get("transform")
    if transform in ("anomaly", "zscore"):
        window = dataset.tmax.sel(time=slice("2024-01-10", "2024-01-20"))
        expected = window - window.mean("time")
        if transform == "zscore":
            expected = expected / window.std("time")
        np.testing.assert_allclose(cube, expected, atol=1e-6)
    elif transform == "state":
        np.testing.assert_array_equal(cube, dataset.tmax < -10)
    elif transform == "ndvi":
        red, nir = (dataset.surface_reflectance.sel(band=b) for b in ("B04", "B08"))
        np.testing.assert_allclose(cube, (nir - red) / (nir + red), atol=1e-6)


def test_gallery_rejects_unverified_fixture(tmp_path, monkeypatch):
    from scripts import build_real_data_assets as builder
    monkeypatch.setattr(builder, "FIXTURE", tmp_path / "placeholder.nc")
    (tmp_path / "bad.nc").write_bytes(b"not reviewed")
    (tmp_path / "bad.provenance.json").write_text(json.dumps({"fixture_sha256": "wrong"}))
    with pytest.raises(RuntimeError, match="provenance hash"):
        load_fixture("bad")


def test_homepage_renders_every_option_and_noscript_link():
    source = (ROOT / "docs/index.md").read_text()
    output = on_page_markdown(source, SimpleNamespace(file=SimpleNamespace(src_uri="index.md")),
                              {"docs_dir": ROOT / "docs"}, None)
    assert "<!-- HERO_EXAMPLE_OPTIONS -->" not in output
    for example in EXAMPLES:
        assert f'value="{example["path"]}"' in output
        assert f'href="{example["path"]}"' in output
        assert (ROOT / "docs" / example["path"]).is_file()
        lesson = ROOT / "docs" / example["lesson"].rstrip("/")
        assert lesson.with_suffix(".md").exists() or lesson.with_suffix(".ipynb").exists()
