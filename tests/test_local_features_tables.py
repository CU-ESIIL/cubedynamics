"""Synthetic private feature/table fixtures; no proprietary data or network."""
import json

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon, box

from cubedynamics import data, pipe


def features():
    return gpd.GeoDataFrame({"site_id": ["001", "002"], "measurement": [2., 4.]},
                            geometry=[Point(10, 40), Point(11, 41)], crs="EPSG:4326")


@pytest.mark.parametrize("kind", ["geojson", "gpkg", "parquet"])
@pytest.mark.parametrize("geometry", ["points", "polygons"])
def test_features_preserve_geometry_crs_and_columns(tmp_path, kind, geometry):
    expected = features()
    if geometry == "polygons":
        expected.geometry = [box(10, 40, 11, 41), box(11, 41, 12, 42)]
    path = tmp_path / f"private.{kind}"
    kwargs = {}
    if kind == "parquet":
        pytest.importorskip("pyarrow")
        expected.to_parquet(path)
    else:
        if kind == "gpkg":
            kwargs["layer"] = "plots"
        expected.to_file(path, driver="GPKG" if kind == "gpkg" else "GeoJSON", **kwargs)
    frame = data.open_local_features(path, dataset_id="lab/plots", revision="v2", **kwargs)
    assert frame.crs == expected.crs
    assert frame.geometry.equals(expected.geometry)
    assert frame.site_id.tolist() == ["001", "002"]
    assert frame.measurement.tolist() == [2, 4]
    provenance = json.loads(frame.attrs["local_source_provenance"])
    assert provenance["dataset_id"] == "lab/plots"
    assert provenance["revision"] == "v2"
    assert provenance["files"][0]["path"] == str(path)
    # Project callables can operate on features without a forced raster step.
    assert (pipe(frame) | (lambda f: f.measurement.mean())).unwrap() == 3
    with pytest.raises(ValueError, match="max_features"):
        data.open_local_features(path, dataset_id="lab/plots", max_features=1, **kwargs)
    with pytest.raises(ValueError, match="conflicts"):
        data.open_local_features(path, dataset_id="lab/plots", crs="EPSG:3857", **kwargs)


def test_geopackage_requires_explicit_layer(tmp_path):
    path = tmp_path / "plots.gpkg"
    features().to_file(path, layer="plots", driver="GPKG")
    with pytest.raises(ValueError, match="layer"):
        data.open_local_features(path, dataset_id="lab")


def test_unknown_crs_requires_explicit_assignment(tmp_path, monkeypatch):
    path = tmp_path / "private.geojson"
    path.write_text("{}")
    frame = gpd.GeoDataFrame({"site_id": ["001"]}, geometry=[Point(10, 40)])
    monkeypatch.setattr(gpd, "read_file", lambda *a, **k: frame.copy())
    with pytest.raises(ValueError, match="no CRS"):
        data.open_local_features(path, dataset_id="lab")
    assigned = data.open_local_features(path, dataset_id="lab", crs="EPSG:4326")
    assert assigned.crs.to_epsg() == 4326
    assert frame.crs is None


@pytest.mark.parametrize("bad", [None, Point(), Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])])
def test_invalid_geometry_is_not_repaired(tmp_path, monkeypatch, bad):
    path = tmp_path / "private.geojson"
    path.write_text("{}")
    frame = features()
    frame.loc[0, "geometry"] = bad
    monkeypatch.setattr(gpd, "read_file", lambda *a, **k: frame)
    with pytest.raises(ValueError, match="geometry"):
        data.open_local_features(path, dataset_id="lab")


@pytest.mark.parametrize("kind", ["csv", "tsv", "parquet"])
def test_table_batches_projection_types_and_provenance(tmp_path, kind):
    expected = pd.DataFrame({"site_id": ["001", "002", "003"], "value": [1., 2., 3.],
                             "unused": ["x"] * 3})
    path = tmp_path / f"private.{kind}"
    kwargs = {}
    if kind == "parquet":
        pytest.importorskip("pyarrow")
        expected.to_parquet(path, row_group_size=1)
    else:
        expected.to_csv(path, sep="\t" if kind == "tsv" else ",", index=False)
        kwargs["dtype"] = {"site_id": "string"}
    batches = list(data.open_local_table(path, dataset_id="lab/stations", revision="v3",
                                        columns=["value", "site_id"], batch_size=2, **kwargs))
    assert all(0 < len(frame) <= 2 for frame in batches)
    combined = pd.concat(batches, ignore_index=True)
    assert combined.columns.tolist() == ["value", "site_id"]
    assert combined.site_id.tolist() == ["001", "002", "003"]
    assert combined.value.tolist() == [1, 2, 3]
    for frame in batches:
        provenance = json.loads(frame.attrs["local_source_provenance"])
        assert provenance["dataset_id"] == "lab/stations"
        assert provenance["revision"] == "v3"
        assert provenance["files"][0]["size_bytes"] == path.stat().st_size
    with pytest.raises(ValueError):
        list(data.open_local_table(path, dataset_id="lab", columns=["missing"]))


def test_csv_early_close_releases_reader(tmp_path, monkeypatch):
    path = tmp_path / "private.csv"
    pd.DataFrame({"value": [1, 2, 3]}).to_csv(path, index=False)
    original = pd.read_csv
    readers = []
    def capture(*args, **kwargs):
        reader = original(*args, **kwargs)
        readers.append(reader)
        return reader
    monkeypatch.setattr(pd, "read_csv", capture)
    iterator = data.open_local_table(path, dataset_id="lab", batch_size=1)
    assert readers == []  # No measurement reads until iteration starts.
    next(iterator)
    assert not readers[0].handles.handle.closed
    iterator.close()
    assert readers[0].handles.handle.closed


def test_header_only_table_yields_no_measurements(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("site_id,value\n")
    assert list(data.open_local_table(path, dataset_id="lab")) == []


def test_geoparquet_cannot_silently_become_plain_table(tmp_path):
    pytest.importorskip("pyarrow")
    path = tmp_path / "private.parquet"
    features().to_parquet(path)
    with pytest.raises(ValueError, match="GeoParquet"):
        list(data.open_local_table(path, dataset_id="lab"))


@pytest.mark.parametrize("invalid", [0, -1, True, 1.5])
def test_row_limits_are_positive_integers(tmp_path, invalid):
    path = tmp_path / "private.csv"
    path.write_text("value\n1\n")
    with pytest.raises(ValueError, match="batch_size"):
        data.open_local_table(path, dataset_id="lab", batch_size=invalid)
    with pytest.raises(ValueError, match="max_features"):
        data.open_local_features(path, dataset_id="lab", max_features=invalid)


def test_paths_and_columns_fail_explicitly(tmp_path):
    with pytest.raises(ValueError, match="filesystem"):
        data.open_local_features("https://example.test/private.geojson", dataset_id="lab")
    with pytest.raises(FileNotFoundError):
        data.open_local_table(tmp_path / "missing.csv", dataset_id="lab")
    path = tmp_path / "private.csv"
    path.write_text("value\n1\n")
    with pytest.raises(ValueError, match="sequence"):
        data.open_local_table(path, dataset_id="lab", columns="value")


def test_parquet_nullable_integer_identifiers_remain_exact(tmp_path):
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq
    path = tmp_path / "identifiers.parquet"
    large_id = 2**60 + 1
    pq.write_table(pa.table({"record_id": pa.array([large_id, None], type=pa.int64())}), path)
    batch = next(data.open_local_table(path, dataset_id="lab", batch_size=2))
    assert batch.record_id.iloc[0] == large_id
    assert pd.isna(batch.record_id.iloc[1])
    assert batch.record_id.dtype == pd.ArrowDtype(pa.int64())
