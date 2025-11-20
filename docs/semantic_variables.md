# Semantic variable loaders

**In plain English:**  
Semantic loaders give you common variables (temperature, precipitation, NDVI) without memorizing provider field names. They now return VirtualCubes automatically for large AOIs or long time ranges so you can request decades of data safely.

**What this page helps you do:**  
- Pick the right semantic loader for climate or NDVI
- See how loaders behave when streaming activates
- Debug tile settings when you want to peek under the hood

## Simple semantic requests

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(lat=40.0, lon=-105.25, start="1985", end="2024")
pipe(ndvi) | v.mean(dim=("y", "x"))
```

The code above streams automatically if the span is large. You do not need to change the verb chain.

## Working With Large Datasets (New in 2025)

CubeDynamics can now work with extremely large climate or NDVI datasets — 
even decades of data or very large spatial areas — without loading everything 
into memory at once.

It does this using a new system called **VirtualCube**, which streams data in 
small 'tiles'. You can think of these tiles as puzzle pieces. CubeDynamics 
processes each piece, keeps track of running statistics, and never holds the 
whole puzzle in memory.

## Loader tips for streaming

- Add `streaming_strategy="virtual"` to force streaming.
- Use `time_tile="5y"` or similar if you want to control time slices.
- Large bounding boxes may trigger spatial tiles; call `.debug_tiles()` to see the layout.

## Example: NDVI z-scores at scale

```python
ndvi_z = cd.ndvi_zscore(
    bbox=[-125, 24, -66.5, 49],
    start="1984",
    end="2024",
)

# Streamed anomaly over space
anomaly_ts = pipe(ndvi_z) | v.anomaly(dim="time") | v.mean(dim=("y", "x"))
```

## Debugging semantic loaders

- `print(loader_output)` shows whether you received a VirtualCube.
- `.debug_tiles()` prints time and spatial slices used for streaming.
- `.materialize()` turns the virtual object into an in-memory cube; use only for small AOIs.

---

## Legacy Technical Reference (kept for context)
# Semantic variable loaders

**In plain English:**  
These helpers give you common climate variables like temperature or NDVI without remembering provider-specific codes.
You ask for "temperature" and CubeDynamics calls the right loader under the hood.

**You will learn:**  
- How to request temperature cubes with one function call
- How to grab anomalies and z-scores without custom code
- How to fall back to raw loaders when you need full control

## What this is

Semantic loaders are small wrappers around the PRISM, gridMET, and Sentinel-2 helpers.
They turn friendly names such as `temperature` or `ndvi` into the correct provider variables and return standard `(time, y, x)` cubes.

## Why it matters

Remembering that gridMET uses `pr` while PRISM uses `ppt` is error-prone.
Semantic helpers smooth that friction so new researchers can focus on questions instead of variable catalogs.
They also encourage consistent naming when you share notebooks with students or community partners.

## How to use it

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# Daily mean temperature (gridMET by default)
temp = cd.temperature(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
)

# Minimum and maximum temperature with explicit sources
tmin = cd.temperature_min(
    lat=40.0, lon=-105.25,
    start="2000-01-01", end="2020-12-31",
    source="gridmet",
)

tmax = cd.temperature_max(
    lat=40.0, lon=-105.25,
    start="2000-01-01", end="2020-12-31",
    source="prism",
)

# An anomaly cube using the same API
tanom = cd.temperature_anomaly(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    source="gridmet",
    kind="mean",
)

pipe(tanom) | v.show_cube_lexcube(title="GridMET temperature anomaly")
```
These calls delegate to the provider-specific loaders, so you keep the convenience without losing accuracy.

A second example shows NDVI:

```python
ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
    source="sentinel2",
)

ndvi_z = pipe(ndvi) | v.zscore(dim="time")
```
`cd.ndvi` now returns raw NDVI; standardize explicitly with ``v.zscore``. The
``as_zscore`` flag is deprecated and will be removed in a future release.

---

## Original Reference (kept for context)
# Semantic variable loaders

CubeDynamics now provides a thin "semantic" layer on top of the sensor-specific
loaders so you can work with common variables like temperature and NDVI with a
single function call.

## Temperature cubes

Use `cd.temperature`, `cd.temperature_min`, and `cd.temperature_max` to request
mean, minimum, or maximum daily temperature from PRISM or gridMET without
memorizing provider-specific variable names:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

temp = cd.temperature(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    # default: gridMET
)

tmin = cd.temperature_min(
    lat=40.0, lon=-105.25,
    start="2000-01-01", end="2020-12-31",
    source="gridmet",
)

tmax = cd.temperature_max(
    lat=40.0, lon=-105.25,
    start="2000-01-01", end="2020-12-31",
    source="prism",
)
```

Behind the scenes, these helpers delegate to `cd.load_prism_cube` and
`cd.load_gridmet_cube` with the appropriate variable names.

## Temperature anomalies

`cd.temperature_anomaly` wraps the temperature loaders and the `v.anomaly` verb
to compute anomalies along the time axis:

```python
tanom = cd.temperature_anomaly(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    source="gridmet",
    kind="mean",
)

pipe(tanom) | v.show_cube_lexcube(title="GridMET temperature anomaly")
```

## NDVI cubes

For greenness dynamics, use `cd.ndvi`:

```python
ndvi_z = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
    source="sentinel2",
    as_zscore=True,
)
```

When `as_zscore=True`, this calls `cd.load_sentinel2_ndvi_zscore_cube` and
returns an NDVI z-score cube. When `as_zscore=False`, it computes raw NDVI from
Sentinel-2 bands using `v.ndvi_from_s2`.

As always, you can fall back to the sensor-specific loaders when you need full
control over band selection, cloud filtering, or temporal aggregation.
