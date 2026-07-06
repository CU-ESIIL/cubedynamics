# Sentinel-2 → NDVI z-score cube → rolling-window tail-dependence vs center pixel → Lexcube

This end-to-end recipe mirrors the R-style tail-dependence workflow: stream
Sentinel-2 L2A data with `cubo`, compute NDVI, standardize per pixel, and
calculate rolling median-split Spearman correlations against the center pixel.
The example uses a fixed 90-day window, optional spatial coarsening and time
striding to stay within memory limits, and visualizes the bottom-tail, top-tail,
and difference cubes with Lexcube.

> **Dependencies**: `cubo` (installed with `cubedynamics`), `lexcube`, `xarray`,
> `rioxarray`, `matplotlib`. Uncomment the `pip install` line if needed.

```python
# Requirements (uncomment if needed in your environment):
# !pip install -q lexcube xarray rioxarray

from __future__ import annotations
import warnings
import gc

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

import cubo
import lexcube

# -------------------------------------------------------------------
# Helper functions: ranks + partial tail Spearman
# -------------------------------------------------------------------

def _rank_1d(a: np.ndarray) -> np.ndarray:
    """Return average ranks, including for tied values."""
    a = np.asarray(a)
    order = np.argsort(a, kind="mergesort")
    sorted_values = a[order]
    ranks = np.empty(a.size, dtype=float)
    start = 0
    while start < a.size:
        stop = start + 1
        while stop < a.size and sorted_values[stop] == sorted_values[start]:
            stop += 1
        ranks[order[start:stop]] = (start + 1 + stop) / 2.0
        start = stop
    return ranks


def partial_tail_spearman(
    x: np.ndarray,
    y: np.ndarray,
    b: float = 0.5,
    min_t: int = 5,
) -> tuple[float, float, float]:
    """
    Spearman synchrony below and above per-series quantile thresholds.

    x, y : 1D arrays (time series)
    b    : tail fraction (0.5 splits each series at its median)
    min_t: minimum number of valid observations to compute a tail statistic

    Returns:
        (left_tail_corr, right_tail_corr, left_minus_right)
    """
    x = np.asarray(x)
    y = np.asarray(y)

    # Drop NaNs
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    n = x.size

    if n < min_t:
        return np.nan, np.nan, np.nan

    lower_mask = (x <= np.quantile(x, b)) & (y <= np.quantile(y, b))
    upper_mask = (x > np.quantile(x, 1.0 - b)) & (y > np.quantile(y, 1.0 - b))

    def tail_corr(tail_mask: np.ndarray) -> float:
        if tail_mask.sum() < min_t:
            return np.nan
        u = _rank_1d(x[tail_mask])
        v = _rank_1d(y[tail_mask])
        u = u - u.mean()
        v = v - v.mean()
        denom = np.sqrt(np.sum(u**2) * np.sum(v**2))
        return np.sum(u * v) / denom if denom > 0 else np.nan

    cor_left = tail_corr(lower_mask)
    cor_right = tail_corr(upper_mask)

    return cor_left, cor_right, cor_left - cor_right


# -------------------------------------------------------------------
# 0) User parameters
# -------------------------------------------------------------------
LAT = 43.89   # Kyle, South Dakota
LON = -102.18
START = "2023-06-01"
END   = "2024-09-30"

EDGE_SIZE  = 1028   # raw pixels on a side
RESOLUTION = 10     # meters
CLOUD_LT   = 40     # max global cloud cover %

STD_EPS    = 1e-4   # min std for valid z-scores
MIN_T      = 5      # min time steps inside a window before computing stats

# 💾 MEMORY CONTROL KNOBS
COARSEN_FACTOR = 4   # 1 = none, 2 = 2x2 blocks, 4 = 4x4, etc.
TIME_STRIDE    = 2   # 1 = keep all times, 2 = every other, etc.

# Rolling window parameters (fixed window length in days)
WINDOW_DAYS = 90

# Tail dependence parameter
TAIL_B = 0.5   # split each series at its rolling-window median

# Display parameters
CORR_VMIN, CORR_VMAX = -2.0, 2.0
CORR_CMAP            = "RdBu_r"

# -------------------------------------------------------------------
# 1) Build Sentinel-2 cube (B04=Red, B08=NIR)
# -------------------------------------------------------------------
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    s2 = cubo.create(
        lat=LAT,
        lon=LON,
        collection="sentinel-2-l2a",
        bands=["B04", "B08"],
        start_date=START,
        end_date=END,
        edge_size=EDGE_SIZE,
        resolution=RESOLUTION,
        query={"eo:cloud_cover": {"lt": CLOUD_LT}},
    )

# Ensure dims ordering is (time, y, x, band)
if "band" in s2.dims and s2.dims[0] == "band":
    s2 = s2.transpose("time", "y", "x", "band")

# Optional chunking for dask-based workflows
s2 = s2.chunk({"time": -1, "y": 256, "x": 256})

print("Raw Sentinel-2 cube:", s2)

# -------------------------------------------------------------------
# 2) Compute NDVI through time (NO spyndex)
# -------------------------------------------------------------------
NIR = s2.sel(band="B08")  # (time, y, x)
RED = s2.sel(band="B04")

eps = 1e-6
ndvi = (NIR - RED) / (NIR + RED + eps)
ndvi = ndvi.rename("ndvi").astype("float32")
ndvi.attrs.update({
    "long_name": "Normalized Difference Vegetation Index",
    "formula": "(B08 - B04) / (B08 + B04)",
    "bands": "B08(NIR), B04(Red)",
})

# Free S2 cube to save memory
del s2, NIR, RED
gc.collect()

print("NDVI cube shape:", ndvi.shape)

# -------------------------------------------------------------------
# 3) NDVI z-scores per pixel
# -------------------------------------------------------------------
ndvi_mean = ndvi.mean(dim="time", skipna=True)
ndvi_std  = ndvi.std(dim="time", skipna=True)
valid_std = ndvi_std > STD_EPS

ndvi_z = xr.where(
    valid_std,
    (ndvi - ndvi_mean) / ndvi_std,
    np.nan
)
ndvi_z = ndvi_z.rename("ndvi_zscore").astype("float32")
ndvi_z.attrs.update({
    "long_name": "Standardized NDVI anomaly (z-score)",
    "definition": "z = (NDVI - mean_t NDVI) / std_t NDVI at each pixel",
    "baseline_period": f"{START} to {END}",
    "note": f"Pixels with std < {STD_EPS} set to NaN.",
})

del ndvi, ndvi_mean, ndvi_std
gc.collect()

print("NDVI z-score cube shape (pre-downsampling):", ndvi_z.shape)

# -------------------------------------------------------------------
# 4) Optional spatial coarsening + temporal subsampling
# -------------------------------------------------------------------
if COARSEN_FACTOR > 1:
    ndvi_z = ndvi_z.coarsen(
        y=COARSEN_FACTOR,
        x=COARSEN_FACTOR,
        boundary="trim"
    ).mean()
    ndvi_z.attrs["coarsen_factor"] = COARSEN_FACTOR

if TIME_STRIDE > 1:
    ndvi_z = ndvi_z.isel(time=slice(0, None, TIME_STRIDE))
    ndvi_z.attrs["time_stride"] = TIME_STRIDE

ndvi_z = ndvi_z.chunk({"time": -1, "y": 256, "x": 256})

time = ndvi_z["time"]
T = ndvi_z.sizes["time"]
print(f"NDVI z cube shape after downsampling: {ndvi_z.shape} (time, y, x)")
print(f"Number of time steps after downsampling: T = {T}")

# -------------------------------------------------------------------
# 5) Build tail-dependence cubes vs center pixel (fixed rolling window)
# -------------------------------------------------------------------

# Identify the center pixel on the coarsened grid
y_size = ndvi_z.sizes["y"]
x_size = ndvi_z.sizes["x"]
y_center_idx = y_size // 2
x_center_idx = x_size // 2

# Full time series of the reference (center) pixel
ref_full = ndvi_z.isel(y=y_center_idx, x=x_center_idx)  # (time,)

print(
    "Reference pixel (coarsened grid):",
    f"y={float(ndvi_z['y'].values[y_center_idx])},",
    f"x={float(ndvi_z['x'].values[x_center_idx])}"
)
print(f"Using rolling window of {WINDOW_DAYS} days.")
print(f"Minimum time steps per window: MIN_T = {MIN_T}")
print(f"Tail split parameter b = {TAIL_B}")

tail_left_slices  = []  # bottom tail dependence
tail_right_slices = []  # top tail dependence
tail_diff_slices  = []  # bottom - top

for ti in range(T):
    t_end = time.values[ti]
    t_start = t_end - np.timedelta64(WINDOW_DAYS, "D")

    # Subset to the rolling window [t_start, t_end]
    ndvi_sub = ndvi_z.sel(time=slice(t_start, t_end))   # (time, y, x)
    ref_sub  = ref_full.sel(time=slice(t_start, t_end)) # (time,)

    # Require at least MIN_T observations in the window
    if ndvi_sub.sizes["time"] < MIN_T:
        continue

    # Vectorized partial tail Spearman across (y, x)
    tail_left, tail_right, tail_diff = xr.apply_ufunc(
        partial_tail_spearman,
        ndvi_sub,
        ref_sub,
        input_core_dims=[["time"], ["time"]],
        output_core_dims=[[], [], []],
        vectorize=True,
        dask="parallelized",
        kwargs={"b": TAIL_B, "min_t": MIN_T},
        output_dtypes=[np.float32, np.float32, np.float32],
    )

    # Attach time coordinate (window end time) and collect slices
    for arr, collection in [
        (tail_left,  tail_left_slices),
        (tail_right, tail_right_slices),
        (tail_diff,  tail_diff_slices),
    ]:
        arr = arr.expand_dims("time")
        arr = arr.assign_coords(time=("time", [t_end]))
        collection.append(arr)

    del ndvi_sub, ref_sub, tail_left, tail_right, tail_diff
    gc.collect()

if not tail_left_slices:
    raise RuntimeError(
        f"No tail-dependence slices computed; T={T}, MIN_T={MIN_T}, "
        f"WINDOW_DAYS={WINDOW_DAYS}. Try reducing MIN_T or WINDOW_DAYS, "
        "or ensuring enough valid observations."
    )

# Concatenate into three cubes
tail_left_cube  = xr.concat(tail_left_slices,  dim="time").rename("tail_dep_bottom")
tail_right_cube = xr.concat(tail_right_slices, dim="time").rename("tail_dep_top")
tail_diff_cube  = xr.concat(tail_diff_slices,  dim="time").rename("tail_dep_diff")

shared_attrs = {
    "min_time_points": MIN_T,
    "reference_pixel_y": float(ndvi_z["y"].values[y_center_idx]),
    "reference_pixel_x": float(ndvi_z["x"].values[x_center_idx]),
    "coarsen_factor": COARSEN_FACTOR,
    "time_stride": TIME_STRIDE,
    "window_days": WINDOW_DAYS,
    "tail_b": TAIL_B,
    "note": (
        "Spearman synchrony after splitting each series at its own quantile; "
        "left=bottom set, right=top set, diff=left-right."
    ),
}

tail_left_cube.attrs.update({
    "long_name": "Below-median Spearman synchrony vs center pixel",
    **shared_attrs,
})
tail_right_cube.attrs.update({
    "long_name": "Above-median Spearman synchrony vs center pixel",
    **shared_attrs,
})
tail_diff_cube.attrs.update({
    "long_name": "Difference in tail dependence (bottom - top) vs center pixel",
    **shared_attrs,
})

del ndvi_z, ref_full
gc.collect()

print("Tail-dependence cube shapes:",
      "bottom:", tail_left_cube.shape,
      "top:", tail_right_cube.shape,
      "diff:", tail_diff_cube.shape)

# -------------------------------------------------------------------
# 6) QA: median tail-dependence difference over space through time
# -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 3))
tail_diff_med = tail_diff_cube.median(dim=["y", "x"], skipna=True).to_series()
tail_diff_med.plot(ax=ax)
ax.axhline(0.0, ls="--", lw=1, alpha=0.7)
ax.set_ylabel("Median bottom - top tail dep")
ax.set_xlabel("Date")
ax.set_ylim(CORR_VMIN, CORR_VMAX)
ax.set_title(f"Median tail-dependence difference (rolling {WINDOW_DAYS} days)")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# -------------------------------------------------------------------
# 7) Lexcube visualization (example: tail_diff_cube)
# -------------------------------------------------------------------

# Clip to the desired color range before plotting
corr_display = tail_diff_cube.clip(CORR_VMIN, CORR_VMAX)

w = lexcube.Cube3DWidget(
    corr_display,
    cmap=CORR_CMAP,
    vmin=CORR_VMIN,
    vmax=CORR_VMAX,
    title=(
        f"Tail-dependence difference (bottom - top) vs center pixel "
        f"(rolling {WINDOW_DAYS} days) • coarsen={COARSEN_FACTOR} "
        f"• t_stride={TIME_STRIDE} • b={TAIL_B}"
    ),
)

w.plot()
```

**Tips**

- Increase `TIME_STRIDE` or `COARSEN_FACTOR` if memory becomes an issue.
- Lower `MIN_T` or `WINDOW_DAYS` if you see the runtime error about missing
  tail-dependence slices.
- Swap `lexcube.Cube3DWidget` for `pipe(... ) | v.show_cube_lexcube(...)` if
  you prefer the CubeDynamics visualization verbs.
- To target a different reference pixel, change the `y_center_idx`/`x_center_idx`
  selections before computing the rolling window.
