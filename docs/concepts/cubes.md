# What is a cube?

A **cube** is an `xarray.DataArray` or `xarray.Dataset` whose values are organized along shared space-time axes such as `(time, y, x)` for single-band cubes or `(time, y, x, band)` for multispectral collections. Every pixel stores the value of an environmental variable (e.g., NDVI, temperature, precipitation) measured at `(y, x)` and instant `time`.

![Cube axes diagram](../assets/img/cube_axes.png){ .cube-image }

## Loading a PRISM cube

```python
import cubedynamics as cd

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

cube
```

`load_prism_cube` streams the requested area/time window from PRISM into memory as a cube so you can immediately apply verbs. Swap in `load_gridmet_cube`, `load_sentinel2_ndvi_cube` (raw NDVI), `load_sentinel2_ndvi_zscore_cube` (standardized NDVI), or any custom loader that returns an `xarray` object with the standard axes.

## Why cubes?

Satellite constellations (Sentinel-2, Landsat), gridded climate products (gridMET, PRISM), and model reanalyses naturally produce cube-shaped data because measurements are already tied to regular spatiotemporal coordinates. By sticking with `xarray`, CubeDynamics benefits from labeled dimensions, lazy loading (`dask`), and metadata-aware computations.

CubeDynamics focuses on **streaming cubes** instead of requiring large local downloads. Utilities such as `cubedynamics.load_sentinel2_cube` wrap remote APIs (e.g., Cubo) so you can request an area/time window and immediately operate on the returned cube in notebooks or scripts.

## Correctness & cube shapes

- **PRISM/gridMET loaders** (`load_prism_cube`, `load_gridmet_cube`) return `xarray.Dataset` objects with dims `(time, y, x)` per variable, or a single-variable `xarray.DataArray` when `variable="ppt"` (or another single variable) is requested. Pass exactly one AOI description: `lat`/`lon`, `bbox=[min_lon, min_lat, max_lon, max_lat]`, or `aoi_geojson` (GeoJSON Feature/FeatureCollection).
- **Sentinel-2 loaders**:
  - `load_sentinel2_cube` and `load_sentinel2_bands_cube` return multispectral stacks with dims `(time, y, x, band)`.
  - `load_sentinel2_ndvi_cube` returns raw NDVI reflectance with dims `(time, y, x)` and optionally the underlying bands when `return_raw=True`.
  - `load_sentinel2_ndvi_zscore_cube` applies `v.zscore(dim="time", keep_dim=True)` so the cube stays `(time, y, x)` and remains Lexcube-ready.
- **Reducers & verbs**: `v.mean`, `v.variance`, and `v.zscore` keep the reduced dimension as length 1 when `keep_dim=True` (the default), so you can still send the result to `v.show_cube_lexcube`. `v.anomaly` and `v.zscore` always preserve the incoming shape because they broadcast their summaries back over the original cube.
- **Lexcube requirements**: The visualization verb expects a 3D `(time, y, x)` cube (Dataset with exactly one data variable works as well). Use `keep_dim=True` on reducers when you plan to visualize the output; set it to `False` only when you are intentionally collapsing to a 2D map for other plotting libraries.

## Cube processing layers

The original documentation described four conceptual layers that remain relevant today:

1. **Data layer** – load space-time cubes (`load_sentinel2_cube`, `load_prism_cube`, `load_gridmet_cube`).
2. **Indices & anomalies layer** – derive vegetation indices and z-scores (`from cubedynamics import verbs as v`; `v.ndvi_from_s2`, `v.zscore`, `v.anomaly`).
3. **Synchrony layer** – measure rolling correlation and tail dependence versus a reference pixel (`rolling_corr_vs_center`, `rolling_tail_dep_vs_center`). A dedicated `v.correlation_cube` verb is reserved for a future streaming implementation and currently raises `NotImplementedError`.
4. **Visualization layer** – explore cubes interactively with the Lexcube widget (`v.show_cube_lexcube`) and QA plots (`plot_median_over_space`).

## Earth System Data Cube context

CubeDynamics builds on the Earth System Data Cube (ESDC) paradigm: treat spatiotemporal grids as analysis-ready cubes that can flow into machine learning or statistical analyses. Unlike infrastructure-focused systems (Open Data Cube, Earth System Data Lab), CubeDynamics emphasizes a **grammar of analysis**. Any cube—PRISM, gridMET, Sentinel-2 NDVI via Cubo, Lexcube outputs, or DeepESDL—becomes a first-class citizen in the same `pipe(cube) | verbs` interface.
