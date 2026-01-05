# Spatial & CRS Dataset Contract

## Purpose and scope
This document defines the canonical spatial and coordinate reference system (CRS) contract for cube-based verbs. It is an internal, normative spec that every spatial verb (e.g., `v.clip`, `v.mask`, `v.zonal_stats`, `v.fire_plot`) must follow to ensure consistent behavior across datasets and to enable shared tests.

## Cube invariants
- **Time dimension required**: A `time` dimension must exist and be parseable to pandas `DatetimeIndex` via `normalize_dates`.
- **Exactly two spatial dimensions**: Cubes must expose exactly two spatial dimensions. Preferred names are `("y", "x")`; the fallback is `("lat", "lon")`.
- **Ambiguity must fail**: If spatial dimensions cannot be uniquely determined, verbs must raise a clear error instead of guessing.

## CRS inference contract
Spatial verbs must use the shared `infer_epsg` helper and respect the following precedence:
1. `da.attrs["epsg"]`
2. Scalar coordinate named `"epsg"`
3. `da.rio.crs.to_epsg()` (if available)
4. `da.attrs["crs"]` parsed via `pyproj`
5. **Required fallback heuristic**:
   - If dims are `("lat", "lon")` ⇒ EPSG:4326.
   - If dims are `("y", "x")` and `max(|x|) <= 180` and `max(|y|) <= 90` ⇒ EPSG:4326.
   - Else raise a clear `ValueError` (unknown CRS).

## Geometry reprojection rule
Reproject vector inputs into the cube's CRS once. Never reproject the cube to the vector CRS within verbs; downstream operations assume cube grids stay untouched.

## Spatial membership semantics
- **Boundary-inclusive**: Membership is defined by `covers(Point(x, y))`; `contains()` is disallowed because it excludes boundary pixels.
- **Correctness-first path**: Use prepared geometry + per-pixel point tests as the reference implementation.
- **Optional fast path**: `rasterio.features.rasterize(..., all_touched=True)` may be used only when `fast=True`. Default must be `fast=False`, and the docs for verbs must call out the approximation.

## Time alignment contract (event-based)
For cube timestamp `t`, select the latest geometry date `<= t` after day-level normalization. This allows event polygons to be matched to the nearest prior observation without stepping into the future.

## Dataset compatibility table
| Dataset | Expected grid | Metadata quirks | Contract behavior |
| --- | --- | --- | --- |
| gridMET | `lat/lon` in degrees | CRS metadata often missing | Default to EPSG:4326 via fallback heuristic. |
| PRISM | `lat/lon` in degrees | CRS metadata often missing | Same as gridMET: fallback to EPSG:4326. |
| Sentinel-2 NDVI | Projected meters (UTM) | EPSG commonly stored as scalar coord | Use scalar EPSG; reproject vectors to cube CRS. |

## How to use this contract
Use the shared helpers from `cubedynamics.fire_time_hull` until a dedicated module is extracted. Example invocation inside a verb:

```python
from cubedynamics.fire_time_hull import infer_spatial_dims, infer_epsg, normalize_dates

def clip(da, geometry, *, fast=False):
    y_dim, x_dim = infer_spatial_dims(da)
    epsg = infer_epsg(da)
    dates = normalize_dates(da["time"].values)
    # reproject geometry to epsg, enforce membership semantics, etc.
```

Testing with synthetic cubes (no network):

```python
import numpy as np
import pandas as pd
import xarray as xr

def gridmet_like():
    return xr.DataArray(
        np.zeros((2, 2, 2)),
        dims=("time", "lat", "lon"),
        coords={"time": pd.date_range("2020-01-01", periods=2)},
        name="tmean",
    )

def prism_like():
    return xr.DataArray(
        np.ones((2, 2, 2)),
        dims=("time", "lat", "lon"),
        coords={"time": pd.date_range("2020-02-01", periods=2)},
        name="ppt",
    )

def sentinel2_like():
    return xr.DataArray(
        np.full((2, 2, 2), 5),
        dims=("time", "y", "x"),
        coords={
            "time": pd.date_range("2020-03-01", periods=2),
            "epsg": 32613,
        },
        name="ndvi",
    )
```

## Required test fixtures
- **gridMET-like cube**: Degrees, missing CRS metadata; exercises fallback to EPSG:4326.
- **PRISM-like cube**: Degrees, missing CRS metadata; same fallback as gridMET.
- **Sentinel-2-like cube**: Projected meters with scalar `epsg=326xx`; ensures vectors are reprojected to cube CRS.

## Non-goals
This contract does **not** define resampling behavior, cube reprojection strategies, fractional coverage calculations, or performance tuning beyond the optional rasterize fast path.

## Reviewer checklist
- [ ] Time dimension present and normalized via `normalize_dates`.
- [ ] Spatial dimensions resolved by `infer_spatial_dims` (error on ambiguity).
- [ ] EPSG inferred via contract precedence with clear fallback/error.
- [ ] Vector geometries reprojected to cube CRS; cube grid never reprojected.
- [ ] Membership uses boundary-inclusive semantics; fast path gated behind `fast=True`.
- [ ] Tests cover required synthetic cube fixtures.
