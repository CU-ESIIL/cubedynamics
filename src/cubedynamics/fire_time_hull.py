from __future__ import annotations

"""
Self-contained helpers for fire time-hull geometry and GRIDMET climate sampling.

This module intentionally avoids importing cubedynamics internals to steer clear
of circular imports. It contains lightweight dataclasses and utilities adapted
from the fire/time-hull prototype used in notebooks.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import plotly.graph_objects as go
import requests
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep


@dataclass
class TemporalSupport:
    """Simple description of temporal coverage for a dataset."""

    start: pd.Timestamp
    end: pd.Timestamp

    def contains(self, start: pd.Timestamp, end: pd.Timestamp) -> bool:
        return pd.Timestamp(start) >= self.start and pd.Timestamp(end) <= self.end


GRIDMET_SUPPORT = TemporalSupport(
    start=pd.Timestamp("1979-01-01"), end=pd.Timestamp("2100-01-01")
)


def load_fired_conus_ak(
    which: str = "daily", prefer: str = "gpkg", *, cache_dir: str | Path | None = None
) -> gpd.GeoDataFrame:
    """Lightweight loader for FIRED CONUS/AK sample data used in the prototype."""

    base_url = "https://scholar.colorado.edu/downloads"
    file_map = {
        "daily": "0r967610j",
        "events": "r494vn88x",
    }
    if which not in file_map:
        raise ValueError("which must be 'daily' or 'events'")

    ext = "gpkg" if prefer == "gpkg" else "geojson"
    cache_dir = Path(cache_dir or Path.home() / ".cache" / "cubedynamics" / "fired")
    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = cache_dir / f"fired_{which}.{ext}"

    if not filename.exists():
        url = f"{base_url}/{file_map[which]}.{ext}"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        filename.write_bytes(resp.content)

    return gpd.read_file(filename)


@dataclass
class FireEventDaily:
    event_id: Any
    gdf: gpd.GeoDataFrame
    t0: pd.Timestamp
    t1: pd.Timestamp
    centroid_lat: float
    centroid_lon: float


@dataclass
class TimeHull:
    event: FireEventDaily
    verts_km: np.ndarray
    tris: np.ndarray
    t_days_vert: np.ndarray
    t_norm_vert: np.ndarray
    metrics: Dict[str, float]


@dataclass
class ClimateCube:
    da: xr.DataArray


@dataclass
class HullClimateSummary:
    values_inside: np.ndarray
    values_outside: np.ndarray
    per_day_mean: pd.Series


def clean_event_daily_rows(
    gdf_daily: gpd.GeoDataFrame,
    event_id,
    id_col: str = "id",
    date_col: str = "date",
) -> Optional[gpd.GeoDataFrame]:
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
            pass

        if last_geom is not None and geom.equals(last_geom):
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
    if poly is None or poly.is_empty:
        return None

    ring = LineString(poly.exterior.coords)
    if len(ring.coords) > 1 and ring.coords[0] == ring.coords[-1]:
        ring = LineString(list(ring.coords)[:-1])

    L = ring.length
    if not np.isfinite(L) or L <= 0:
        return None

    distances = np.linspace(0.0, L, n_samples, endpoint=False)
    coords = [ring.interpolate(d) for d in distances]
    return np.array([[p.x, p.y] for p in coords], dtype=float)


def _tri_area(p1, p2, p3) -> float:
    a = np.asarray(p2) - np.asarray(p1)
    b = np.asarray(p3) - np.asarray(p1)
    cross = np.cross(a, b)
    return 0.5 * float(np.linalg.norm(cross))


def pick_event_with_joint_support(
    fired_daily: gpd.GeoDataFrame,
    *,
    climate_support: TemporalSupport,
    time_buffer_days: int = 0,
    min_days: int = 3,
    id_col: str = "id",
    date_col: str = "date",
) -> Any:
    for eid in fired_daily[id_col].unique():
        eg = clean_event_daily_rows(fired_daily, eid, id_col=id_col, date_col=date_col)
        if eg is None or eg.empty:
            continue
        dates = pd.to_datetime(eg[date_col], errors="coerce").dt.normalize()
        if dates.nunique() < min_days:
            continue
        start = dates.min() - pd.Timedelta(days=time_buffer_days)
        end = dates.max() + pd.Timedelta(days=time_buffer_days)
        if climate_support.contains(start, end):
            return eid
    raise ValueError("No event found with requested joint temporal support")


def build_fire_event(
    fired_daily: gpd.GeoDataFrame,
    event_id,
    *,
    date_col: str = "date",
) -> FireEventDaily:
    eg_clean = clean_event_daily_rows(fired_daily, event_id, id_col="id", date_col=date_col)
    if eg_clean is None or eg_clean.empty:
        raise ValueError(f"No usable daily perimeters found for event_id={event_id!r}")

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
    verbose: bool = False,
) -> TimeHull:
    eg = event.gdf.copy()
    eg[date_col] = pd.to_datetime(eg[date_col], errors="coerce")
    eg = eg.sort_values(date_col).reset_index(drop=True)

    if z_col in eg.columns:
        Z = eg[z_col].to_numpy(float)
    else:
        Z = np.arange(1, len(eg) + 1, dtype=float)

    if crs_epsg_xy is not None:
        try:
            eg = eg.to_crs(epsg=crs_epsg_xy)
        except Exception:
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

    thetas = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    U = np.stack([np.cos(thetas), np.sin(thetas)], axis=1)
    M = len(rings)
    T = n_theta

    R = np.zeros((M, T), dtype=float)
    for i, xy in enumerate(rings):
        R[i, :] = (U @ xy.T).max(axis=1)

    P_m = np.zeros((M, T, 3), dtype=float)
    P_m[:, :, 0] = R * U[None, :, 0]
    P_m[:, :, 1] = R * U[None, :, 1]
    P_m[:, :, 2] = np.array(Z[:M], float)[:, None]

    P_km = np.empty_like(P_m)
    P_km[:, :, 0] = P_m[:, :, 0] / 1000.0
    P_km[:, :, 1] = P_m[:, :, 1] / 1000.0
    P_km[:, :, 2] = P_m[:, :, 2]

    rmax_m = float(np.nanmax(np.sqrt(P_m[:, :, 0] ** 2 + P_m[:, :, 1] ** 2)))
    scale_km = rmax_m / 1000.0
    days = float(M)

    Z_use = np.array(Z[:M], float)
    areas_use = np.array(areas_m2[:M], float)
    if len(Z_use) >= 2:
        integrator = getattr(np, "trapezoid", None)
        if integrator is None:
            hull_volume_m2_days = float(np.trapz(areas_use, x=Z_use))
        else:
            hull_volume_m2_days = float(integrator(areas_use, Z_use))
    else:
        hull_volume_m2_days = 0.0
    hull_volume_km2_days = hull_volume_m2_days / 1e6

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

    if verbose:
        print("TimeHull metrics:", metrics)

    return TimeHull(
        event=event,
        verts_km=verts_km,
        tris=tris_arr,
        t_days_vert=t_days_vert,
        t_norm_vert=t_norm_vert,
        metrics=metrics,
    )


def _gridmet_urls_for_var_years(variable: str, years: Iterable[int]) -> List[str]:
    return [f"https://www.northwestknowledge.net/metdata/data/{variable}_{y}.nc" for y in years]


def _download_gridmet_files_to_cache(urls: Sequence[str], cache_dir: Path) -> List[Path]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for url in urls:
        fname = cache_dir / Path(url).name
        if not fname.exists():
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            fname.write_bytes(resp.content)
        paths.append(fname)
    return paths


def _load_real_gridmet_cube(
    lat: float,
    lon: float,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    variable: str = "tmmx",
    cache_dir: str | Path | None = None,
) -> xr.DataArray:
    cache_dir = Path(cache_dir or Path.home() / ".cache" / "cubedynamics" / "gridmet")
    years = range(start.year, end.year + 1)
    urls = _gridmet_urls_for_var_years(variable, years)
    paths = _download_gridmet_files_to_cache(urls, cache_dir)

    ds = xr.open_mfdataset([str(p) for p in paths], combine="by_coords")
    if "day" in ds.dims:
        ds = ds.rename({"day": "time"})
    ds = ds.sel(time=slice(start, end))

    # nearest grid point
    y_name = "lat" if "lat" in ds.coords else "y"
    x_name = "lon" if "lon" in ds.coords else "x"
    da = ds[variable].sel({y_name: lat, x_name: lon}, method="nearest")
    da = da.assign_coords({"lat": da[y_name], "lon": da[x_name]})
    da = da.drop_vars([c for c in [y_name, x_name] if c in da.coords and c not in ["lat", "lon"]])
    da = da.expand_dims({"y": [float(da.lat.values)], "x": [float(da.lon.values)]})
    da = da.transpose("time", "y", "x")
    da = da.assign_attrs({"gridmet_source": "real"})
    return da


def _load_synthetic_gridmet_cube(
    lat: float,
    lon: float,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    variable: str = "tmmx",
) -> xr.DataArray:
    times = pd.date_range(start, end, freq="D")
    y = np.linspace(lat - 0.1, lat + 0.1, 5)
    x = np.linspace(lon - 0.1, lon + 0.1, 5)
    rng = np.random.default_rng(42)
    data = rng.normal(loc=0.0, scale=1.0, size=(len(times), len(y), len(x)))
    da = xr.DataArray(
        data,
        coords={"time": times, "y": y, "x": x},
        dims=("time", "y", "x"),
        name=variable,
        attrs={"gridmet_source": "synthetic"},
    )
    return da


def load_gridmet_cube(
    lat: float,
    lon: float,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    variable: str = "tmmx",
    prefer_synthetic: bool = False,
    cache_dir: str | Path | None = None,
) -> xr.DataArray:
    if prefer_synthetic:
        return _load_synthetic_gridmet_cube(lat, lon, start, end, variable=variable)

    try:
        return _load_real_gridmet_cube(lat, lon, start, end, variable=variable, cache_dir=cache_dir)
    except Exception:
        return _load_synthetic_gridmet_cube(lat, lon, start, end, variable=variable)


def load_climate_cube_for_event(
    event: FireEventDaily,
    *,
    time_buffer_days: int = 14,
    variable: str = "tmmx",
    prefer_synthetic: bool = False,
) -> ClimateCube:
    start = event.t0 - pd.Timedelta(days=time_buffer_days)
    end = event.t1 + pd.Timedelta(days=time_buffer_days)
    da = load_gridmet_cube(
        event.centroid_lat,
        event.centroid_lon,
        start,
        end,
        variable=variable,
        prefer_synthetic=prefer_synthetic,
    )
    return ClimateCube(da=da)


def _infer_spatial_dims(da: xr.DataArray) -> Tuple[str, str]:
    if "y" in da.dims and "x" in da.dims:
        return "y", "x"
    if "lat" in da.dims and "lon" in da.dims:
        return "lat", "lon"
    raise ValueError(f"Cannot infer spatial dims from {da.dims}")


def _infer_cube_epsg(da: xr.DataArray) -> Optional[int]:
    epsg = None
    if "epsg" in da.attrs:
        try:
            epsg = int(da.attrs["epsg"])
        except Exception:
            epsg = None

    if epsg is None and "epsg" in da.coords:
        try:
            coord = da["epsg"]
            if coord.ndim == 0:
                epsg = int(coord.values)
        except Exception:
            epsg = None

    if epsg is None and hasattr(da, "rio"):
        try:
            crs = da.rio.crs
            if crs is not None:
                epsg = crs.to_epsg()
        except Exception:
            epsg = None

    if epsg is None and "crs" in da.attrs:
        try:
            import pyproj

            crs = pyproj.CRS.from_user_input(da.attrs["crs"])
            epsg = crs.to_epsg()
        except Exception:
            epsg = None

    return epsg


def build_inside_outside_climate_samples(
    event: FireEventDaily,
    cube: ClimateCube,
    *,
    date_col: str = "date",
) -> HullClimateSummary:
    da = cube.da
    time_vals = pd.to_datetime(da["time"].values)
    dates_clim = time_vals.normalize()

    mask_time = (dates_clim >= event.t0) & (dates_clim <= event.t1)
    if not mask_time.any():
        raise ValueError("Climate cube has no timesteps overlapping the fire time window.")

    da_evt = da.isel(time=np.where(mask_time)[0])
    dates_evt = dates_clim[mask_time]

    y_dim, x_dim = _infer_spatial_dims(da_evt)
    y_vals = da_evt[y_dim].values
    x_vals = da_evt[x_dim].values

    ny = y_vals.size
    nx = x_vals.size

    XX, YY = np.meshgrid(x_vals, y_vals)

    dy = float(np.abs(y_vals[1] - y_vals[0])) if ny > 1 else 0.0
    dx = float(np.abs(x_vals[1] - x_vals[0])) if nx > 1 else 0.0
    use_area = dx > 0 and dy > 0

    cell_polys = None
    if use_area:
        half_dx = dx / 2.0
        half_dy = dy / 2.0

        def cell_poly(xc, yc) -> Polygon:
            return Polygon(
                [
                    (xc - half_dx, yc - half_dy),
                    (xc + half_dx, yc - half_dy),
                    (xc + half_dx, yc + half_dy),
                    (xc - half_dx, yc + half_dy),
                ]
            )

        cell_polys = [
            [cell_poly(XX[i, j], YY[i, j]) for j in range(nx)] for i in range(ny)
        ]

    eg = event.gdf.copy()

    cube_epsg = _infer_cube_epsg(da_evt)
    if cube_epsg is None:
        cube_crs_str = "EPSG:4326"
    else:
        cube_crs_str = f"EPSG:{cube_epsg}"

    if eg.crs is None:
        eg = eg.set_crs("EPSG:4326")
    if eg.crs.to_string().upper() != cube_crs_str.upper():
        eg = eg.to_crs(cube_crs_str)

    eg["date_norm"] = pd.to_datetime(eg[date_col], errors="coerce").dt.normalize()

    values_inside: list[float] = []
    values_outside: list[float] = []
    per_day_mean: dict[pd.Timestamp, float] = {}

    for idx_t, t_date in enumerate(dates_evt):
        mask_day = eg["date_norm"] == t_date
        if not mask_day.any():
            continue
        g_row = eg.loc[mask_day].iloc[0]
        poly = _largest_polygon(g_row.geometry)
        if poly is None:
            continue

        poly_prep = prep(poly)
        da_slice = da_evt.isel(time=idx_t)
        vals = da_slice.values

        inside_mask = np.zeros((ny, nx), dtype=bool)
        if use_area and cell_polys is not None:
            for i in range(ny):
                for j in range(nx):
                    inside_mask[i, j] = poly_prep.intersects(cell_polys[i][j])
        else:
            pts = [Polygon([(xx, yy)]) for xx, yy in zip(XX.ravel(), YY.ravel())]
            inside_flat = np.array([poly_prep.contains(p.centroid) for p in pts])
            inside_mask = inside_flat.reshape((ny, nx))

        vals_inside = vals[inside_mask]
        vals_outside = vals[~inside_mask]

        if vals_inside.size:
            per_day_mean[t_date] = float(np.nanmean(vals_inside))
        else:
            per_day_mean[t_date] = np.nan

        values_inside.append(vals_inside.ravel())
        values_outside.append(vals_outside.ravel())

    values_inside_flat = np.concatenate(values_inside) if values_inside else np.array([])
    values_outside_flat = np.concatenate(values_outside) if values_outside else np.array([])

    return HullClimateSummary(
        values_inside=values_inside_flat,
        values_outside=values_outside_flat,
        per_day_mean=pd.Series(per_day_mean),
    )


def plot_climate_filled_hull(
    hull: TimeHull,
    summary: HullClimateSummary,
    *,
    title_prefix: str = "GRIDMET",
    var_label: str = "value",
    save_prefix: Optional[str] = None,
    color_limits: Optional[Tuple[float, float]] = None,
) -> go.Figure:
    verts = np.asarray(hull.verts_km)
    tris = np.asarray(hull.tris)

    intensities = None
    if isinstance(summary, HullClimateSummary) and summary.per_day_mean.size:
        day_vals = np.asarray(summary.per_day_mean.sort_index().values, dtype=float)
        M = int(hull.metrics.get("days", day_vals.size if day_vals.size else 0) or 0)
        if M > 0 and day_vals.size:
            if len(day_vals) < M:
                day_vals = np.pad(day_vals, (0, M - len(day_vals)), mode="edge")
            elif len(day_vals) > M:
                day_vals = day_vals[:M]
            layer_indices = np.clip((hull.t_days_vert - 1).astype(int), 0, len(day_vals) - 1)
            intensities = day_vals[layer_indices]

    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=verts[:, 0],
                y=verts[:, 1],
                z=verts[:, 2],
                i=tris[:, 0],
                j=tris[:, 1],
                k=tris[:, 2],
                intensity=intensities,
                colorscale="Viridis",
                showscale=True,
                cmin=None if color_limits is None else color_limits[0],
                cmax=None if color_limits is None else color_limits[1],
                colorbar=dict(title=var_label),
                opacity=0.8,
            )
        ],
    )

    fig.update_layout(
        title=f"{title_prefix}: {var_label}",
        scene=dict(
            xaxis_title="x (km)",
            yaxis_title="y (km)",
            zaxis_title="time (days)",
        ),
        template="plotly_white",
    )

    if save_prefix:
        try:
            fig.write_image(f"{save_prefix}.png")
        except Exception:
            pass

    return fig


def plot_inside_outside_hist(
    summary: HullClimateSummary,
    *,
    bins: int = 40,
    var_label: str = "value",
):
    import matplotlib.pyplot as plt

    inside = np.asarray(summary.values_inside).ravel()
    outside = np.asarray(summary.values_outside).ravel()

    plt.figure(figsize=(5, 3))
    if inside.size:
        plt.hist(
            inside,
            bins=bins,
            alpha=0.6,
            density=True,
            label="inside",
            histtype="stepfilled",
        )
    if outside.size:
        plt.hist(
            outside,
            bins=bins,
            alpha=0.6,
            density=True,
            label="outside",
            histtype="step",
        )

    plt.xlabel(var_label)
    plt.ylabel("Density")
    plt.title(f"{var_label}: inside vs outside fire perimeters")
    plt.legend()
    plt.tight_layout()
    plt.show()


def _hull_grid(hull: TimeHull) -> tuple[np.ndarray, int, int]:
    """
    Recover the (M, T, 3) grid from a TimeHull, where:
      M = number of days (layers)
      T = number of angular samples per layer

    Assumes verts_km are laid out as consecutive "rings" over time,
    as produced by compute_time_hull_geometry.
    """
    verts = hull.verts_km  # shape (M*T, 3)
    days = int(round(hull.metrics.get("days", 0)))
    if days <= 0:
        raise ValueError("Hull has non-positive 'days' metric; cannot reshape.")

    n_verts = verts.shape[0]
    if n_verts % days != 0:
        raise ValueError(
            f"Cannot reshape verts into (days, T, 3): "
            f"{n_verts} vertices not divisible by days={days}"
        )

    T = n_verts // days
    P = verts.reshape(days, T, 3)
    return P, days, T


def compute_derivative_hull(
    hull: TimeHull,
    *,
    order: int = 1,
    eps: float = 1e-6,
) -> TimeHull:
    """
    Build a derivative-based hull from an existing TimeHull.

    Parameters
    ----------
    hull
        Base TimeHull in km,km,days from compute_time_hull_geometry.
    order
        1 → derivative hull encodes perimeter *speed* (km/day).
        2 → derivative hull encodes perimeter *acceleration* (km/day²).
    eps
        Small tolerance to avoid division by zero when normalizing.

    Returns
    -------
    TimeHull
        A new hull with the same topology (tris) and time coordinates,
        but with radius at each (day, theta) proportional to speed or
        acceleration, respectively.
    """
    if order not in (1, 2):
        raise ValueError("order must be 1 or 2")

    P, M, T = _hull_grid(hull)      # (M, T, 3)
    xy = P[..., :2]                 # (M, T, 2), km coordinates

    # First derivative of perimeter position in time: km/day
    dxy_dt = np.gradient(xy, axis=0)  # central differences along time axis
    speed = np.linalg.norm(dxy_dt, axis=-1)  # (M, T), km/day

    if order == 1:
        field = speed
        field_name = "speed_km_per_day"
    else:
        # Second derivative of spread speed: km/day²
        accel = np.gradient(speed, axis=0)
        field = accel
        field_name = "accel_km_per_day2"

    # Use derivative magnitude as new radius, preserving angular direction
    r_orig = np.linalg.norm(xy, axis=-1)  # (M, T)
    U = np.zeros_like(xy)                 # unit directions (M, T, 2)

    mask = r_orig > eps
    U[mask] = xy[mask] / r_orig[mask][..., None]
    U[~mask] = np.array([1.0, 0.0])  # arbitrary direction for degenerate centers

    R_new = np.abs(field)  # radius encodes magnitude of derivative field

    P_new = np.zeros_like(P)
    P_new[..., :2] = R_new[..., None] * U
    P_new[..., 2]  = P[..., 2]  # keep same time (days)

    verts_new = P_new.reshape(-1, 3)

    rmax = float(np.nanmax(R_new)) if np.isfinite(R_new).any() else 0.0
    metrics = {
        "scale_km": rmax,
        "days": float(M),
        "volume_km2_days": np.nan,   # not meaningful for derivatives
        "surface_km_day": np.nan,    # not meaningful for derivatives
        "field_name": field_name,
    }

    return TimeHull(
        event=hull.event,
        verts_km=verts_new,
        tris=hull.tris,
        t_days_vert=hull.t_days_vert,
        t_norm_vert=hull.t_norm_vert,
        metrics=metrics,
    )


def plot_derivative_hull(
    base_hull: TimeHull,
    deriv_hull: TimeHull,
    *,
    order: int = 1,
    title_prefix: str = "Fire derivative hull",
) -> go.Figure:
    """
    Plot a derivative hull with color and radius encoding the same
    derivative quantity (speed or acceleration).

    base_hull is used to recompute the underlying derivative field
    (speed or acceleration) so that intensity and geometry agree.
    """
    P, M, T = _hull_grid(base_hull)
    xy = P[..., :2]

    # First derivative: km/day
    dxy_dt = np.gradient(xy, axis=0)
    speed = np.linalg.norm(dxy_dt, axis=-1)  # (M, T)

    if order == 1:
        field = speed
        var_label = "Perimeter speed (km/day)"
    else:
        accel = np.gradient(speed, axis=0)
        field = accel
        var_label = "Perimeter acceleration (km/day²)"

    intensities = np.abs(field).ravel()

    verts = deriv_hull.verts_km
    tris  = deriv_hull.tris
    x, y, z = verts[:, 0], verts[:, 1], verts[:, 2]
    i, j, k = tris.T

    if np.isfinite(intensities).any():
        vmin = float(np.nanpercentile(intensities, 5))
        vmax = float(np.nanpercentile(intensities, 95))
    else:
        vmin, vmax = 0.0, 1.0

    mesh = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=i,
        j=j,
        k=k,
        intensity=intensities,
        colorscale="Viridis",
        cmin=vmin,
        cmax=vmax,
        opacity=0.8,
        flatshading=True,
        colorbar=dict(title=var_label),
        name="Derivative hull",
    )

    title = (
        f"{title_prefix} – Event {base_hull.event.event_id} "
        f"| order={order}"
    )

    fig = go.Figure(data=[mesh])
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=60, b=0),
        showlegend=False,
    )
    return fig

