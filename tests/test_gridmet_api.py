"""API coverage tests for the GRIDMET loader."""

from __future__ import annotations

import pytest

import cubedynamics as cd


def test_load_gridmet_cube_lat_lon_signature():
    cube = cd.load_gridmet_cube(
        lat=40.0,
        lon=-105.25,
        start="2000-01-01",
        end="2000-12-31",
        variable="pr",
        freq="MS",
        prefer_streaming=False,
    )

    assert "time" in cube.dims
    assert "y" in cube.dims
    assert "x" in cube.dims


def test_load_gridmet_cube_aoi_geojson_signature():
    aoi = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-105.35, 40.00],
                    [-105.35, 40.10],
                    [-105.20, 40.10],
                    [-105.20, 40.00],
                    [-105.35, 40.00],
                ]
            ],
        },
    }

    cube = cd.load_gridmet_cube(
        aoi_geojson=aoi,
        variable="pr",
        start="2000-01-01",
        end="2000-12-31",
        freq="MS",
        prefer_streaming=False,
    )

    assert "time" in cube.dims
    assert "y" in cube.dims
    assert "x" in cube.dims


def test_load_gridmet_cube_legacy_positional():
    bbox = [-105.35, 40.00, -105.20, 40.10]
    cube = cd.load_gridmet_cube("pr", "2000-01-01", "2000-12-31", bbox, "MS", None, False)

    assert "time" in cube.dims
    assert "y" in cube.dims
    assert "x" in cube.dims


def test_load_gridmet_cube_conflicting_aoi_raises():
    with pytest.raises(ValueError):
        cd.load_gridmet_cube(
            lat=40.0,
            lon=-105.25,
            bbox=[-105.35, 40.00, -105.20, 40.10],
            variable="pr",
            start="2000-01-01",
            end="2000-12-31",
        )
