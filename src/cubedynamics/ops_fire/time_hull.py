from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.ops import unary_union


@dataclass
class FireEventDaily:
    """
    One FIRED event with daily perimeters and basic metadata.

    Parameters
    ----------
    event_id :
        Identifier from the FIRED dataset.
    gdf :
        GeoDataFrame of daily perimeters for this event, sorted by date.
    t0, t1 :
        First and last dates (normalized to midnight) for which we have usable perimeters.
    centroid_lat, centroid_lon :
        Centroid of the union of all perimeters in EPSG:4326.
    """

    event_id: int | float | str
    gdf: gpd.GeoDataFrame
    t0: pd.Timestamp
    t1: pd.Timestamp
    centroid_lat: float
    centroid_lon: float


@dataclass
class TimeHull:
    """
    3D time-hull geometry for a single fire event.

    verts_km : (N, 3) array
        Vertices in (x_km, y_km, time_days) coordinates.
    tris : (M, 3) array
        Triangle indices into verts_km.
    t_days_vert : (N,) array
        Time coordinate (days since start) for each vertex.
    t_norm_vert : (N,) array
        Normalized time coordinate in [0, 1].
    metrics : dict
        Useful hull metrics such as:
          - 'scale_km'          : characteristic horizontal scale (km)
          - 'days'              : number of daily perimeters used
          - 'volume_km2_days'   : time-integrated area (km²·days)
          - 'surface_km_day'    : hull surface area in (km, km, days)
    """

    event: FireEventDaily
    verts_km: np.ndarray
    tris: np.ndarray
    t_days_vert: np.ndarray
    t_norm_vert: np.ndarray
    metrics: Dict[str, float]


def clean_event_daily_rows(
    gdf_daily: gpd.GeoDataFrame,
    event_id,
    id_col: str = "id",
    date_col: str = "date",
) -> Optional[gpd.GeoDataFrame]:
    """
    Return a cleaned, sorted per-day GeoDataFrame for a single FIRED event.

    Steps
    -----
    1. Subset to `event_id` using `id_col`.
    2. Convert `date_col` to normalized pd.Timestamp (midnight) and sort.
    3. For each date, ensure geometry is a single (Multi)Polygon and
       merge MultiPolygons with shapely.ops.unary_union.
    4. Drop consecutive duplicate geometries (no net change that day).

    Returns
    -------
    GeoDataFrame or None
        Cleaned rows for this event, or None if no usable geometries.
    """
    eg = gdf_daily[gdf_daily[id_col] == event_id].copy()
    if eg.empty:
        return None

    eg[date_col] = pd.to_datetime(eg[date_col], errors="coerce").dt.normalize()
    eg = eg.sort_values(date_col)

    rows: list[pd.Series] = []
    last_geom = None

    for _, row in eg.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        try:
            if isinstance(geom, MultiPolygon):
                geom = unary_union(geom)
        except Exception:
            # Fall back to original geometry on union failure
            pass

        if last_geom is not None and geom.equals(last_geom):
            # Skip consecutive duplicates (no change that day)
            continue

        r_copy = row.copy()
        r_copy.geometry = geom
        rows.append(r_copy)
        last_geom = geom

    if not rows:
        return None

    out = gpd.GeoDataFrame(rows, crs=gdf_daily.crs).reset_index(drop=True)
    return out


def _largest_polygon(geom) -> Optional[Polygon]:
    """
    Return the largest Polygon from a (Multi)Polygon geometry.

    Parameters
    ----------
    geom :
        Shapely geometry; may be Polygon, MultiPolygon, or something else.

    Returns
    -------
    Polygon or None
    """
    if geom is None or geom.is_empty:
        return None
    if isinstance(geom, Polygon):
        return geom
    if isinstance(geom, MultiPolygon):
        polys = [p for p in geom.geoms if isinstance(p, Polygon)]
        if not polys:
            return None
        return max(polys, key=lambda p: p.area)
    return None


def _sample_ring_equal_steps(poly: Polygon, n_samples: int = 100) -> Optional[np.ndarray]:
    """
    Sample `n_samples` points along the polygon's exterior at equal arc length.

    Parameters
    ----------
    poly : Polygon
        Input polygon (assumed valid).
    n_samples : int
        Number of sample points along the exterior.

    Returns
    -------
    np.ndarray or None
        Array of shape (n_samples, 2) with (x, y) coordinates in the
        polygon's CRS, or None if sampling is not possible.
    """
    if poly is None or poly.is_empty:
        return None

    ring = LineString(poly.exterior.coords)
    # Drop duplicate closing vertex
    if len(ring.coords) > 1 and ring.coords[0] == ring.coords[-1]:
        ring = LineString(list(ring.coords)[:-1])

    L = ring.length
    if not np.isfinite(L) or L <= 0:
        return None

    s = np.linspace(0, L, n_samples, endpoint=False)
    pts = np.array([ring.interpolate(dist).coords[0] for dist in s], dtype=float)

    if not np.all(np.isfinite(pts)):
        return None
    return pts


def _tri_area(p: np.ndarray, q: np.ndarray, r: np.ndarray) -> float:
    """
    Area of a 3D triangle (p, q, r).

    Parameters
    ----------
    p, q, r : np.ndarray, shape (3,)
        3D vertices.

    Returns
    -------
    float
        Triangle area.
    """
    return 0.5 * float(np.linalg.norm(np.cross(q - p, r - p)))


def build_fire_event(
    gdf_daily: gpd.GeoDataFrame,
    event_id,
    *,
    id_col: str = "id",
    date_col: str = "date",
) -> FireEventDaily:
    """
    Clean a single FIRED event and return a FireEventDaily object.

    Parameters
    ----------
    gdf_daily : GeoDataFrame
        FIRED daily perimeters (many events).
    event_id :
        Event identifier to extract.
    id_col : str
        Column name containing event IDs.
    date_col : str
        Column name containing date.

    Returns
    -------
    FireEventDaily
        Cleaned event with centroid and time span.

    Raises
    ------
    ValueError
        If no usable perimeters are found for this event.
    """
    eg_clean = clean_event_daily_rows(gdf_daily, event_id, id_col=id_col, date_col=date_col)
    if eg_clean is None or eg_clean.empty:
        raise ValueError(f"No usable daily perimeters found for event_id={event_id!r}")

    # Ensure lat/lon CRS for centroid calculation
    if eg_clean.crs is None:
        eg_clean = eg_clean.set_crs("EPSG:4326")
    elif eg_clean.crs.to_string().upper() != "EPSG:4326":
        eg_clean = eg_clean.to_crs("EPSG:4326")

    dates = pd.to_datetime(eg_clean[date_col], errors="coerce").dt.normalize()
    t0 = dates.min()
    t1 = dates.max()

    union_geom = unary_union(eg_clean.geometry.values)
    centroid = union_geom.centroid
    centroid_lat = float(centroid.y)
    centroid_lon = float(centroid.x)

    return FireEventDaily(
        event_id=event_id,
        gdf=eg_clean,
        t0=t0,
        t1=t1,
        centroid_lat=centroid_lat,
        centroid_lon=centroid_lon,
    )


def compute_time_hull_geometry(
    event: FireEventDaily,
    *,
    date_col: str = "date",
    z_col: str = "event_day",
    n_ring_samples: int = 100,
    n_theta: int = 96,
    crs_epsg_xy: int = 5070,
    center_each_day: bool = True,
) -> TimeHull:
    """
    Build a 3D ruled time-hull geometry from FIRED daily perimeters.

    The hull is parameterized in a local metric CRS as:

        (x_km, y_km, z_days),

    where z_days is typically 1..N (or taken from `z_col` if present).

    Parameters
    ----------
    event : FireEventDaily
        Event with daily perimeters (in EPSG:4326).
    date_col : str
        Column name containing per-day dates.
    z_col : str
        Column that can provide an integer day index; if absent, use 1..N.
    n_ring_samples : int
        Number of perimeter samples per day for ring reconstruction.
    n_theta : int
        Number of support directions around the hull.
    crs_epsg_xy : int
        EPSG code for metric projection used for area and radius calculations.
    center_each_day : bool
        If True, subtract daily centroid from each day's ring so that hull
        is centered around the origin in x,y.

    Returns
    -------
    TimeHull
        Hull vertices, triangles, and metrics.

    Raises
    ------
    ValueError
        If fewer than 2 valid perimeters are available.
    """
    eg = event.gdf.copy()
    eg[date_col] = pd.to_datetime(eg[date_col], errors="coerce")
    eg = eg.sort_values(date_col).reset_index(drop=True)

    # z coordinate: use event_day if present, else 1..N
    if z_col in eg.columns:
        Z = eg[z_col].to_numpy(float)
    else:
        Z = np.arange(1, len(eg) + 1, dtype=float)

    # Project to metric CRS for sampling
    if crs_epsg_xy is not None:
        try:
            eg = eg.to_crs(epsg=crs_epsg_xy)
        except Exception:
            # If projection fails, proceed in whatever CRS we have
            pass

    rings: list[np.ndarray] = []
    areas_m2: list[float] = []

    for geom in eg.geometry:
        poly = _largest_polygon(geom)
        if poly is None:
            continue

        xy = _sample_ring_equal_steps(poly, n_samples=n_ring_samples)
        if xy is None:
            continue

        if center_each_day:
            xy = xy - xy.mean(axis=0)

        rings.append(xy)
        areas_m2.append(float(poly.area))

    if len(rings) < 2:
        raise ValueError(f"Not enough valid perimeters to build a hull for event {event.event_id!r}")

    # Build support directions in the plane
    thetas = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    U = np.stack([np.cos(thetas), np.sin(thetas)], axis=1)  # (T, 2)
    M = len(rings)
    T = n_theta

    # Support radii per day
    R = np.zeros((M, T), dtype=float)
    for i, xy in enumerate(rings):
        # Project sampled ring onto each direction and take max radius
        R[i, :] = (U @ xy.T).max(axis=1)

    # 3D points in meters (assuming projected CRS units are meters)
    P_m = np.zeros((M, T, 3), dtype=float)
    P_m[:, :, 0] = R * U[None, :, 0]
    P_m[:, :, 1] = R * U[None, :, 1]
    P_m[:, :, 2] = np.array(Z[:M], float)[:, None]

    # Convert to (km, km, days)
    P_km = np.empty_like(P_m)
    P_km[:, :, 0] = P_m[:, :, 0] / 1000.0
    P_km[:, :, 1] = P_m[:, :, 1] / 1000.0
    P_km[:, :, 2] = P_m[:, :, 2]

    # Metrics: horizontal scale, days, volume, surface
    rmax_m = float(np.nanmax(np.sqrt(P_m[:, :, 0] ** 2 + P_m[:, :, 1] ** 2)))
    scale_km = rmax_m / 1000.0
    days = float(M)

    Z_use = np.array(Z[:M], float)
    areas_use = np.array(areas_m2[:M], float)
    if len(Z_use) >= 2:
        hull_volume_m2_days = float(np.trapezoid(areas_use, Z_use))
    else:
        hull_volume_m2_days = 0.0
    hull_volume_km2_days = hull_volume_m2_days / 1e6

    # Surface area via triangles in (km, km, days)
    tris: list[tuple[int, int, int]] = []
    surface = 0.0

    for i in range(M - 1):
        for j in range(T):
            jn = (j + 1) % T

            v1k = P_km[i, j]
            v2k = P_km[i, jn]
            v3k = P_km[i + 1, jn]
            v4k = P_km[i + 1, j]

            surface += _tri_area(v1k, v2k, v3k) + _tri_area(v1k, v3k, v4k)

            idx_v1 = i * T + j
            idx_v2 = i * T + jn
            idx_v3 = (i + 1) * T + jn
            idx_v4 = (i + 1) * T + j

            tris.append((idx_v1, idx_v2, idx_v3))
            tris.append((idx_v1, idx_v3, idx_v4))

    hull_surface_km_day = float(surface)

    verts_km = P_km.reshape(-1, 3)
    tris_arr = np.asarray(tris, dtype=int)

    # Per-vertex time coordinate (days since first)
    Z_grid = np.array(Z[:M], float)[:, None] * np.ones((1, T), float)
    t_days_vert = Z_grid.ravel()
    z_min = float(Z_grid.min())
    z_max = float(Z_grid.max())
    z_rng = max(1e-9, z_max - z_min)
    t_norm_vert = (t_days_vert - z_min) / z_rng

    metrics = {
        "scale_km": scale_km,
        "days": days,
        "volume_km2_days": hull_volume_km2_days,
        "surface_km_day": hull_surface_km_day,
    }

    return TimeHull(
        event=event,
        verts_km=verts_km,
        tris=tris_arr,
        t_days_vert=t_days_vert,
        t_norm_vert=t_norm_vert,
        metrics=metrics,
    )
