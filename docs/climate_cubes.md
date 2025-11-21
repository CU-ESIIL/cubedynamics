# Climate cubes

**In plain English:**  
Climate cubes are gridded datasets (like PRISM or gridMET) arranged as time, latitude, and longitude. CubeDynamics loads them with one line and now streams massive requests through VirtualCube so you can study whole decades safely.

**What this page helps you do:**  
- Understand what a climate cube is and how to load one
- See how streaming tiles keep memory low on big pulls
- Debug and visualize very large climate cubes

## Climate cubes in practice

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

daily_temp = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="1980-01-01",
    end="2020-12-31",
    variable="tmean",
)

# Stream a long-term spatial average without extra code
spatial_mean = pipe(daily_temp) | v.mean(dim=("y", "x"))
```

Even though this request covers 40+ years, CubeDynamics tiles it automatically.

## Working With Large Datasets (New in 2025)

CubeDynamics can now work with extremely large climate or NDVI datasets — 
even decades of data or very large spatial areas — without loading everything 
into memory at once.

It does this using a new system called **VirtualCube**, which streams data in 
small 'tiles'. You can think of these tiles as puzzle pieces. CubeDynamics 
processes each piece, keeps track of running statistics, and never holds the 
whole puzzle in memory.

## Behind the scenes: climate cubes and tiles

- **Time tiles**: Long spans are split into year or multi-year windows. Running statistics mean you still get a single output array.
- **Spatial tiles**: Very wide bounding boxes are broken into smaller rectangles. Each tile is downloaded and processed, then merged.
- **Same verbs**: `v.anomaly`, `v.variance`, and other reductions work the same because they update incremental stats as tiles arrive.

## Visualization and streaming

Plotting verbs stream tiles into the figure rather than loading everything. For example:

```python
pipe(daily_temp) | v.variance(dim="time") | v.plot_timeseries()
```

If the AOI is continental, expect the plot to update after each tile finishes; reduce the date span to speed it up.

## Update (2025): New `v.plot` cube viewer

We’ve added a new HTML-based cube viewer wired into `verbs.plot`, which visualizes any `(time, y, x)` DataArray as a rotatable “Lexcube-style” cube.

### Basic usage

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2024-12-31",
)

pipe(ndvi) | v.plot(kind="cube")
```

This call:
- Infers which dimension is time and which are spatial (y, x).
- Extracts three faces of the cube: a map face at the most recent timestep, a time–y curtain at x=0, and a time–x curtain at y=max.
- Applies a colormap and unified color scaling based on the 2nd and 98th percentiles of all face values.
- Renders a CSS 3D cube that you can rotate (drag) and zoom (scroll) with a colorbar at the bottom.

### Viewer experience

- Lexcube-style axis labels sit just outside the cube so names and min/max endpoints are visible without a tall block of axis text beneath the figure.
- Progress prints inline in the notebook output while faces are encoded instead of displaying a blocking loading screen.

### Customization

```python
pipe(ndvi) | v.plot(
    kind="cube",
    out_html="ndvi_cube.html",
    cmap="RdBu_r",
    size_px=420,
    thin_time_factor=4,
)
```

- `out_html`: filename for the generated HTML cube.
- `cmap`: matplotlib colormap name.
- `size_px`: pixel size of the cube faces.
- `thin_time_factor`: if time is very long, only every Nth time step is used when building the curtains to speed up rendering.

### When to use the cube viewer

Use `v.plot(kind="cube")` when you care about the **geometry of the data cube** itself—e.g., understanding how variance and anomalies are arranged along both spatial and temporal axes for NDVI, PRISM, or climate cubes.

For map-first tasks (zoom, pan, overlay boundaries), see the new `v.map()` function below.

## Update (2025): New `v.map()` for map-style visualization

Most climate and NDVI workflows in `cubedynamics` produce grids that are naturally viewed as **maps**. To support this, we’ve added a new `v.map()` verb that uses a MapGL-style engine (via `pydeck`) to render DataArrays as interactive maps.

### Basic usage

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2020-01-01",
    end="2020-12-31",
)

# Map-style NDVI view (last time slice)
pipe(ndvi) | v.map()
```

This call:
- Accepts (y, x) or (time, y, x) DataArrays.
- If a time dimension is present, selects the last timestep by default.
- Infers spatial dimensions (y, x) and approximate lon/lat bounds from the DataArray coordinates.
- Converts the selected slice to a PNG with a chosen colormap.
- Uses a pydeck.BitmapLayer to render the PNG as a map, positioned at the correct geographic bounds.
- Opens an interactive map that you can pan and zoom inside Jupyter.

### Time selection and options

```python
# First timestep, custom colormap
pipe(ndvi) | v.map(time_index=0, cmap="viridis")

# Larger map canvas
pipe(ndvi) | v.map(height=800, width=1000)
```

Key parameters:
- `time_index`: which index along the time dimension to render (defaults to the last available step).
- `cmap`: matplotlib colormap name.
- `vmin`, `vmax`: override automatic percentile-based color scaling.
- `height`, `width`: size of the rendered pydeck map in pixels.

### Optional: time slider (if enabled)

If you enable the slider wrapper in `vis_map.py`, you can use a simple time slider to scrub through the DataArray over time:

```python
pipe(ndvi) | v.map(kind="slider")
```

This creates:
- An IntSlider over the time dimension.
- A pydeck map that updates when you move the slider.

### `v.map()` vs. `v.plot(kind="cube")`

- `v.map()` is for **map-centered** exploration: zooming, panning, and overlaying boundaries with full geographic context.
- `v.plot(kind="cube")` is for **cube geometry**: seeing spatial and temporal slices simultaneously on three faces of a cube.

Both operate on the same underlying `(time, y, x)` DataArrays, and you can switch between them depending on your diagnostic needs.

## Debugging climate cube streaming

- Force streaming: `cd.load_prism_cube(..., streaming_strategy="virtual")`
- Inspect tiles: call `.debug_tiles()` on the returned cube.
- Force full load: `.materialize()` (use only on small AOIs).
- Adjust tiles: pass `time_tile` or `spatial_tile` to loaders to shrink chunks.

---

## Legacy Technical Reference (kept for context)
# Climate cubes

**In plain English:**  
A climate cube is a stack of maps through time, usually arranged as `(time, y, x)` with an optional `band` axis.
CubeDynamics loads these cubes for you so you can analyze them with clear, chained verbs.

**You will learn:**  
- How to create cubes from PRISM, gridMET, or Sentinel-2
- How to run quick statistics without reshaping data
- How to keep cubes ready for visualization or export

## What this is

Climate cubes are `xarray` objects with consistent dimensions and metadata.
CubeDynamics loaders take care of coordinate reference systems, chunking, and naming so every cube works with the same verbs.

## Why it matters

Having time and space aligned in one object makes downstream analysis much simpler.
You can filter, standardize, or correlate data without worrying about mismatched grids.
This structure also matches how educators explain maps stacked through time, which helps new learners.

## How to use it

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)

pipe(cube) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```
This streams monthly precipitation, keeps only summer months, and computes their variance.

You can create other cubes with the same pattern: `cd.load_prism_cube` for PRISM, `cd.load_sentinel2_cube` for Sentinel-2 bands, or `cd.load_sentinel2_ndvi_cube` for NDVI reflectance.
Each loader accepts one area-of-interest definition (`lat`/`lon`, `bbox`, or `aoi_geojson` when supported) so your code stays explicit.

## Exporting and visualizing

```python
pipe(cube) \
    | v.anomaly(dim="time") \
    | v.show_cube_lexcube(title="Summer anomaly", cmap="RdBu_r")
```
This shows the mean-centered cube in Lexcube and returns the cube so you can continue processing.
Use IO verbs like `v.to_netcdf("out.nc")` when you want to save results without breaking the chain.

---

## Original Reference (kept for context)
# Climate cubes

Climate cubes are the core abstraction in CubeDynamics. They are `xarray`
objects with shared `(time, y, x)` axes (and optional `band` or `variable`
dimensions) produced by the streaming loaders.

## Creating cubes

```python
import cubedynamics as cd

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)
print(cube.dims)
```

The loader harmonizes CRS, attaches metadata, and returns a lazily-evaluated
`xarray.Dataset`. Other loaders follow the same interface (`cd.load_prism_cube`,
`cd.load_sentinel2_cube`, `cd.load_sentinel2_ndvi_cube`,
`cd.load_sentinel2_ndvi_zscore_cube`), using the keyword-only AOI grammar:
pick a `lat`/`lon` point, a `[min_lon, min_lat, max_lon, max_lat]` bounding box,
or a GeoJSON Feature/FeatureCollection via `aoi_geojson` (for loaders that
support it).

## Derived diagnostics

Once a cube exists, run statistics directly on the labeled dimensions:

```python
from cubedynamics import pipe, verbs as v

ndvi_z = pipe(ndvi_cube) | v.zscore(dim="time")
var_cube = pipe(cube) | v.variance(dim="time")
```

Every helper keeps the input axes intact so that downstream visualizations and
exports can consume the resulting lexcube without regridding.

## Exporting cubes

`cubedynamics` exposes helpers like `cube.to_netcdf(...)`, `cube.to_zarr(...)`,
and visualization verbs such as `v.show_cube_lexcube` for interactive dashboards.
Large analyses rely on chunked writes through `dask` so the same scripts run in
cloud environments.
