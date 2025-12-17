import geopandas as gpd
import pytest
from shapely.geometry import Point

from cubedynamics import fire_time_hull


def test_load_fired_missing_cache_download_disabled(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        fire_time_hull.load_fired_conus_ak(
            which="daily", prefer="gpkg", cache_dir=cache_dir, download=False
        )


def test_load_fired_downloads_and_reads(monkeypatch, tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    called = {}

    def fake_download(**kwargs):
        called.update(kwargs)
        out = kwargs["out_path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("stub")

    gdf = gpd.GeoDataFrame(
        {"value": [1]}, geometry=[Point(0, 0)], crs="EPSG:3857"
    )

    def fake_read(path):
        called["read_path"] = path
        return gdf

    monkeypatch.setattr(
        fire_time_hull, "_download_and_extract_fired_to_cache", fake_download
    )
    monkeypatch.setattr(gpd, "read_file", fake_read)

    loaded = fire_time_hull.load_fired_conus_ak(
        which="daily",
        prefer="gpkg",
        cache_dir=cache_dir,
        download=True,
        dataset_page="https://example.com/landing",
        download_id="abc123",
        timeout=5,
    )

    assert called["which"] == "daily"
    assert called["prefer"] == "gpkg"
    assert called["dataset_page"] == "https://example.com/landing"
    assert called["download_id"] == "abc123"
    assert called["timeout"] == 5
    assert called["out_path"].name.endswith(".gpkg")
    assert called["read_path"].name.endswith(".gpkg")
    assert isinstance(loaded, gpd.GeoDataFrame)
    assert loaded.crs.to_string() == "EPSG:4326"
    assert loaded.equals(gdf.to_crs("EPSG:4326"))
