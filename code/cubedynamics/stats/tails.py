"""Tail dependence utilities."""

from __future__ import annotations

from typing import Tuple

import numpy as np
import xarray as xr

from ..utils.reference import center_pixel_indices, center_pixel_series


def _rank_1d(a: np.ndarray) -> np.ndarray:
    """Simple 1D rank function (1..n) with ordinal tie handling."""

    order = np.argsort(a, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    return ranks


def partial_tail_spearman(
    x: np.ndarray,
    y: np.ndarray,
    b: float = 0.5,
    min_t: int = 5,
) -> Tuple[float, float, float]:
    """Partial Spearman correlations in lower and upper tails."""

    mask = ~(np.isnan(x) | np.isnan(y))
    x_valid = x[mask]
    y_valid = y[mask]
    n = x_valid.size
    if n < min_t:
        return (np.nan, np.nan, np.nan)

    u = _rank_1d(x_valid) / (n + 1.0)
    v = _rank_1d(y_valid) / (n + 1.0)
    uv_sum = u + v
    left_mask = (uv_sum > 0.0) & (uv_sum < 2.0 * b)
    right_mask = (uv_sum > 2.0 * b) & (uv_sum < 2.0)

    u_mean = u.mean()
    v_mean = v.mean()
    u_var = np.var(u, ddof=1)
    v_var = np.var(v, ddof=1)
    denom = (n - 1) * np.sqrt(u_var * v_var)
    if denom <= 0 or np.isnan(denom):
        return (np.nan, np.nan, np.nan)

    def _tail_corr(mask: np.ndarray) -> float:
        idx = np.where(mask)[0]
        if idx.size < min_t:
            return float("nan")
        cov = np.sum((u[idx] - u_mean) * (v[idx] - v_mean))
        return float(cov / denom)

    left = _tail_corr(left_mask)
    right = _tail_corr(right_mask)
    diff = left - right if not np.isnan(left) and not np.isnan(right) else np.nan
    return (left, right, diff)


def rolling_tail_dep_vs_center(
    zcube: xr.DataArray,
    window_days: int = 90,
    min_t: int = 5,
    b: float = 0.5,
    time_dim: str = "time",
) -> tuple[xr.DataArray, xr.DataArray, xr.DataArray]:
    """Build rolling-window tail-dependence cubes vs the center pixel."""

    ref = center_pixel_series(zcube, time_dim=time_dim)
    end_dim = f"{time_dim}_window_end"
    bottoms: list[xr.DataArray] = []
    tops: list[xr.DataArray] = []
    diffs: list[xr.DataArray] = []
    end_times: list[np.datetime64] = []

    for t_end in zcube[time_dim].values:
        t_start = t_end - np.timedelta64(window_days, "D")
        cube_sub = zcube.sel({time_dim: slice(t_start, t_end)})
        ref_sub = ref.sel({time_dim: slice(t_start, t_end)})
        if cube_sub.sizes.get(time_dim, 0) < min_t:
            continue
        bottom, top, diff = xr.apply_ufunc(
            partial_tail_spearman,
            cube_sub,
            ref_sub,
            input_core_dims=[[time_dim], [time_dim]],
            output_core_dims=[[], [], []],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[np.float32, np.float32, np.float32],
            kwargs={"b": b, "min_t": min_t},
        )
        bottoms.append(bottom.expand_dims({end_dim: [t_end]}))
        tops.append(top.expand_dims({end_dim: [t_end]}))
        diffs.append(diff.expand_dims({end_dim: [t_end]}))
        end_times.append(t_end)

    if not end_times:
        template = zcube.isel({time_dim: slice(0, 0)}).rename({time_dim: end_dim})
        empty = xr.full_like(template, np.nan, dtype="float32")
        return empty, empty.copy(), empty.copy()

    bottom_cube = xr.concat(bottoms, dim=end_dim)
    top_cube = xr.concat(tops, dim=end_dim)
    diff_cube = xr.concat(diffs, dim=end_dim)
    coords = {end_dim: np.array(end_times)}
    bottom_cube = bottom_cube.assign_coords(coords)
    top_cube = top_cube.assign_coords(coords)
    diff_cube = diff_cube.assign_coords(coords)

    y_idx, x_idx = center_pixel_indices(zcube)
    for da in (bottom_cube, top_cube, diff_cube):
        da.attrs.update(
            {
                "reference_pixel_y": y_idx,
                "reference_pixel_x": x_idx,
                "window_days": window_days,
                "min_time_points": min_t,
                "tail_b": b,
            }
        )

    bottom_cube.attrs["long_name"] = "Bottom-tail Spearman vs center"
    top_cube.attrs["long_name"] = "Top-tail Spearman vs center"
    diff_cube.attrs["long_name"] = "Bottom minus top tail Spearman"
    return bottom_cube, top_cube, diff_cube
