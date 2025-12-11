from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Optional

import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

from .time_hull import FireEventDaily, _largest_polygon


@dataclass
class HullClimateSummary:
    """
    Climate sample summary relative to a fire time-hull.

    Attributes
    ----------
    values_inside : np.ndarray
        Flattened climate values inside fire perimeters across all overlapping days.
    values_outside : np.ndarray
        Flattened climate values outside fire perimeters.
    per_day_mean : pd.Series
        Mapping from date (normalized) to mean climate inside the fire.
    """

    values_inside: np.ndarray
    values_outside: np.ndarray
    per_day_mean: pd.Series


def _infer_spatial_dims(da: xr.DataArray) -> Tuple[str, str]:
    """
    Infer spatial dimension names for a climate cube.

    Currently supports:
      - ('y', 'x')
      - ('lat', 'lon')

    Raises
    ------
    ValueError
        If no suitable pair of spatial dimensions can be found.
    """
    if "y" in da.dims and "x" in da.dims:
        return "y", "x"
    if "lat" in da.dims and "lon" in da.dims:
        return "lat", "lon"
    raise ValueError(f"Cannot infer spatial dims from {da.dims}")


def _infer_cube_epsg(da: xr.DataArray) -> Optional[int]:
    """
    Try to infer an EPSG code for the cube from attrs/coords/rioxarray.

    Returns
    -------
    int or None
        EPSG code if one can be determined, else None.
    """
    epsg = None

    # 1) From attrs["epsg"]
    if "epsg" in da.attrs:
        try:
            epsg = int(da.attrs["epsg"])
        except Exception:
            epsg = None

    # 2) From an 'epsg' coordinate
    if epsg is None and "epsg" in da.coords:
        try:
            coord = da["epsg"]
            if coord.ndim == 0:
                epsg = int(coord.values)
        except Exception:
            epsg = None

    # 3) From rioxarray
    if epsg is None and hasattr(da, "rio"):
        try:
            crs = da.rio.crs
            if crs is not None:
                epsg = crs.to_epsg()
        except Exception:
            epsg = None

    # 4) From attrs["crs"] via pyproj, if available
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
    da: xr.DataArray,
    *,
    date_col: str = "date",
    verbose: bool = False,
) -> HullClimateSummary:
    """
    Build inside vs outside climate samples using FIRED perimeters and a climate cube.

    Pixels are treated as areas: a pixel is "inside" if its cell polygon
    intersects the fire polygon for that time slice. If cell area cannot
    be inferred, fall back to testing point coverage at pixel centers.

    Parameters
    ----------
    event : FireEventDaily
        Fire event with daily perimeters.
    da : xarray.DataArray
        Climate cube with dims (time, y, x) or (time, lat, lon).
    date_col : str
        Column name for date in event.gdf.
    verbose : bool, default False
        If True, print sampling summaries for debugging.

    Returns
    -------
    HullClimateSummary
        Flattened inside/outside values and per-day mean inside fire.

    Raises
    ------
    ValueError
        If no overlapping timesteps yield any inside pixels.
    """
    time_vals = pd.to_datetime(da["time"].values)
    dates_clim = time_vals.normalize()

    # Restrict climate cube to event date window
    mask_time = (dates_clim >= event.t0) & (dates_clim <= event.t1)
    if not mask_time.any():
        raise ValueError("Climate cube has no timesteps overlapping the fire time window.")

    da_evt = da.isel(time=np.where(mask_time)[0])
    dates_evt = dates_clim[mask_time]

    # Spatial dims and coordinate grids
    y_dim, x_dim = _infer_spatial_dims(da_evt)
    y_vals = da_evt[y_dim].values
    x_vals = da_evt[x_dim].values

    ny = y_vals.size
    nx = x_vals.size

    XX, YY = np.meshgrid(x_vals, y_vals)  # shape (ny, nx)

    # Estimate pixel size
    dy = float(np.abs(y_vals[1] - y_vals[0])) if ny > 1 else 0.0
    dx = float(np.abs(x_vals[1] - x_vals[0])) if nx > 1 else 0.0
    use_area = dx > 0 and dy > 0

    # Precompute cell polygons if using area-based masking
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
            [cell_poly(XX[i, j], YY[i, j]) for j in range(nx)]
            for i in range(ny)
        ]

    # Align FIRED perimeters to cube CRS
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
    eg = eg.sort_values("date_norm").reset_index(drop=True)
    fired_dates = eg["date_norm"].to_numpy()

    inside_vals: list[np.ndarray] = []
    outside_vals: list[np.ndarray] = []
    per_day_mean: dict[pd.Timestamp, float] = {}

    # Center coords for fallback
    coords_flat = np.column_stack([XX.ravel(), YY.ravel()])

    for t_idx, date_t in enumerate(dates_evt):
        # Latest FIRED date <= this climate date
        mask_leq = fired_dates <= date_t
        if not mask_leq.any():
            continue
        fired_idx = np.where(mask_leq)[0][-1]
        row = eg.iloc[fired_idx]

        poly = _largest_polygon(row.geometry)
        if poly is None:
            continue

        pp_ = prep(poly)

        if use_area and cell_polys is not None:
            # Area-based: pixel is inside if cell polygon intersects fire polygon
            inside_mask = np.zeros((ny, nx), dtype=bool)
            for i in range(ny):
                for j in range(nx):
                    cell = cell_polys[i][j]
                    if cell.is_empty:
                        continue
                    if pp_.intersects(cell):
                        inside_mask[i, j] = True
        else:
            # Fallback: center-based covers() test
            inside_flat = np.fromiter(
                (pp_.covers(Point(float(x), float(y))) for x, y in coords_flat),
                dtype=bool,
                count=len(coords_flat),
            )
            inside_mask = inside_flat.reshape(YY.shape)

        slice_da = da_evt.isel(time=t_idx)
        vals = slice_da.values  # (ny, nx)

        inside = vals[inside_mask]
        outside = vals[~inside_mask]

        if inside.size == 0:
            continue

        inside_vals.append(inside.ravel())
        if outside.size:
            outside_vals.append(outside.ravel())

        per_day_mean[date_t] = float(np.nanmean(inside))

    if not inside_vals:
        raise ValueError(
            "No inside pixels found for this event/time combination, "
            "even after area-based masking."
        )

    values_inside = np.concatenate(inside_vals)
    values_outside = np.concatenate(outside_vals) if outside_vals else np.array([], dtype=float)
    if verbose:
        print(
            f"Climate samples collected: inside={values_inside.size}, outside={values_outside.size}, "
            f"per_day_mean={len(per_day_mean)} entries"
        )
    per_day_mean_series = pd.Series(per_day_mean).sort_index()

    return HullClimateSummary(
        values_inside=values_inside,
        values_outside=values_outside,
        per_day_mean=per_day_mean_series,
    )
