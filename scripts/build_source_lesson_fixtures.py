#!/usr/bin/env python3
"""Freeze small teaching inputs from explicit, previously acquired real snapshots.

No downloads. Refuses overwrite; upstream raw-body identities remain in each
manifest. These extracts are for reproducible lessons, not new certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import xarray as xr

from cubedynamics.data.three_dep import elevation
from cubedynamics.data.roads import roads

ROOT = Path(__file__).resolve().parents[1]
BBOX = (-105.285, 40.008, -105.270, 40.020)


def freeze(artifacts: Path, output: Path) -> None:
    if output.exists():
        raise ValueError("Fixture directory exists; review changes instead of overwriting")
    terrain = elevation(bbox=(-105.300, 39.985, -105.291, 39.994),
                        snapshot_dir=artifacts / "three_dep_pinned/boulder", offline=True)
    networks = {
        source: roads(source=source, bbox=BBOX,
                      release="2026-08-19.0" if source == "overture" else None,
                      snapshot_dir=artifacts / ("overture_coalesced" if source == "overture" else "osm") / "boulder",
                      offline=True)
        for source in ("overture", "osm")
    }
    output.mkdir(parents=True)
    terrain.to_netcdf(output / "elevation.nc", engine="scipy")
    with xr.open_dataarray(output / "elevation.nc", engine="scipy") as restored:
        xr.testing.assert_equal(terrain, restored.load())
    for source, frame in networks.items():
        path = output / f"roads_{source}.geojson"
        path.write_text(frame.to_json(drop_id=True))
        restored = gpd.GeoDataFrame.from_features(json.loads(path.read_text()), crs="EPSG:4326")
        assert restored.source_feature_id.tolist() == frame.source_feature_id.tolist()
        assert restored.native.tolist() == frame.native.tolist()
        assert all(a.equals_exact(b, 0) for a, b in zip(restored.geometry, frame.geometry))
    manifests = {
        "elevation": {
            "source": {"provider": "USGS 3DEP", "product": "1/3 arc-second native elevation window"},
            "time_coverage": ["Static terrain; tile version USGS_13_n40w106_20260630"],
            "files": ["elevation.nc"], "native_metadata": dict(terrain.attrs),
            "limitations": "One 99x99 native window; no resampling, datum conversion, or vertical-accuracy certification.",
        },
        "roads": {
            "source": {"provider": "Overture Maps Foundation and OpenStreetMap contributors",
                       "product": "Native mapped road segments, Boulder"},
            "time_coverage": ["Overture release 2026-08-19.0; OSM retrieval recorded in native metadata"],
            "files": ["roads_overture.geojson", "roads_osm.geojson"],
            "native_metadata": {source: dict(frame.attrs) for source, frame in networks.items()},
            "attribution": "© OpenStreetMap contributors; Overture Maps Foundation. ODbL 1.0; preserve attribution and applicable database-license obligations.",
            "limitations": "Not independent ground truth or a routable network. OSM node-in-bbox selection can omit long crossing ways. Native classes are not harmonized.",
        },
    }
    for name, record in manifests.items():
        record["files"] = {f: hashlib.sha256((output / f).read_bytes()).hexdigest() for f in record["files"]}
        record.update(is_synthetic=False, generated_by="scripts/build_source_lesson_fixtures.py",
                      transformation="Exact serialized bounded adapter result; no new measurements or simplification")
        (output / f"{name}.provenance.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Frozen three real teaching inputs under {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-artifacts", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "tests/fixtures/real_data/source_lessons")
    args = parser.parse_args()
    freeze(args.from_artifacts, args.output)
