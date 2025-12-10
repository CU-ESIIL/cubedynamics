import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon

from cubedynamics.ops_fire.time_hull import FireEventDaily, compute_time_hull_geometry


def _synthetic_fire_event(n_days: int = 3) -> FireEventDaily:
    rows = []
    for d in range(n_days):
        size = 0.01 * (d + 1)
        poly = Polygon(
            [
                (0.0, 0.0),
                (size, 0.0),
                (size, size),
                (0.0, size),
            ]
        )
        rows.append(
            {
                "id": 1,
                "date": pd.Timestamp("2000-01-01") + pd.Timedelta(days=d),
                "geometry": poly,
            }
        )

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    event = FireEventDaily(
        event_id=1,
        gdf=gdf,
        t0=pd.Timestamp("2000-01-01"),
        t1=pd.Timestamp("2000-01-01") + pd.Timedelta(days=n_days - 1),
        centroid_lat=size / 2.0,
        centroid_lon=size / 2.0,
    )
    return event


def test_compute_time_hull_geometry_basic():
    event = _synthetic_fire_event(n_days=3)
    hull = compute_time_hull_geometry(event, n_ring_samples=16, n_theta=12)

    assert hull.metrics["days"] == 3.0
    assert hull.metrics["scale_km"] > 0
    assert hull.verts_km.shape[1] == 3
    assert hull.tris.shape[1] == 3
    assert hull.tris.shape[0] > 0
