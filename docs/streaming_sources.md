# Streaming PRISM & gridMET

CubeDynamics treats climate data sources as interchangeable **streaming
backends**. Each loader returns a cube with identical axes and metadata so the
rest of the math stack can focus on statistics.

## PRISM

- Loader: `cubedynamics.load_prism_cube`
- Purpose: high-resolution precipitation and temperature summaries
- Strategy: use the THREDDS NetCDF Subset Service to request only the variables
  and pixels covering the AOI for each daily timestep

```python
import cubedynamics as cd

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2015-01-01",
    end="2020-12-31",
    variable="ppt",
    freq="D",
)
```

`load_prism_cube` requires one AOI input (`lat`/`lon`, `bbox`, or `aoi_geojson`).
The examples throughout the docs use the keyword-only form that mirrors the
public API. Daily requests are lazy Dask tasks with bounded 31-day time chunks;
the loader does not create a local archive cache.

## gridMET

- Loader: `cubedynamics.load_gridmet_cube`
- Purpose: daily meteorological drivers (temperature, precipitation, vapor
  pressure deficit)
- Strategy: Dask-backed cubes through the public loader; the lower-level
  `cubedynamics.streaming.stream_gridmet_to_cube` helper reads gridMET years
  over HTTP into memory, crops the AOI, and avoids writing local archives

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
```

Use `stream_gridmet_to_cube(...)` when you need to work directly with real
gridMET yearly files. It streams each requested year without writing files to
disk, but it is not a cloud-optimized range-read interface yet, so long global
runs should still be split by time and space.

## Global climate alternatives

- Loader: `cubedynamics.stream_global_climate_cube`
- Purpose: adapt already-open lazy climate archives such as ERA5, TerraClimate,
  CHIRPS, or other xarray/Zarr-backed datasets to CubeDynamics dimensions
- Strategy: normalize time/space dimensions to `(time, y, x)`, optionally crop
  an AOI, preserve lazy chunks, and avoid any package-managed cache/download

```python
import xarray as xr
import cubedynamics as cd

source = xr.open_zarr("s3://example-bucket/era5.zarr", chunks={"time": 31})

cube = cd.stream_global_climate_cube(
    source,
    variables=["t2m"],
    bbox=[-105.5, 39.8, -105.0, 40.2],
    source_name="era5_zarr",
)
```

This pathway is intentionally source-agnostic: CubeDynamics does not own the
cloud credential, catalog, or storage protocol. Open the remote dataset with the
right xarray backend, then hand the lazy object to CubeDynamics for consistent
cube semantics and downstream verbs.

## Sentinel-2 cubes

Remote-sensing chips stream into the same pipe + verbs grammar, so you can
combine vegetation signals with climate anomalies. All Sentinel helpers require
the `cubo` package, which is installed automatically with `cubedynamics`.

### All or selected bands

```python
import cubedynamics as cd

s2_all = cd.load_sentinel2_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2018-12-31",
)

s2_rgbn = cd.load_sentinel2_bands_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2018-12-31",
    bands=["B02", "B03", "B04", "B08"],
)
```

`load_sentinel2_cube` streams all bands (or a user-provided subset), returning a
`(time, y, x, band)` cube with consistent dimension order. The companion
`load_sentinel2_bands_cube` helper enforces that the band subset is explicitly
provided and raises ``ValueError`` when the list is empty.

### NDVI cubes

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.load_sentinel2_ndvi_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
)

pipe(ndvi) | v.show_cube_lexcube(title="Sentinel-2 NDVI (raw)")
```

`load_sentinel2_ndvi_cube` builds on the band loader to fetch B04/B08, computes
NDVI, and returns raw reflectance in the physical range `[-1, 1]`. Set
``return_raw=True`` to also grab the reflectance stack alongside the derived
NDVI cube. You can still manually reproduce the pipeline with `pipe(...) |
v.ndvi_from_s2(...)` if you need to adjust band names.

Prefer anomalies out of the box? Call `cd.load_sentinel2_ndvi_zscore_cube(...)`
to run `v.zscore(dim="time", keep_dim=True)` after NDVI so the output is a
standardized `(time, y, x)` cube.

The resulting cube highlights unusual greenness events (drought stress,
disturbance, rapid recovery). Because every cube shares `(time, y, x)` axes, you
can correlate NDVI anomalies with PRISM or gridMET cubes via `xr.corr` while the
`v.correlation_cube` factory is being implemented:

```python
import xarray as xr

ndvi_z = cd.load_sentinel2_ndvi_zscore_cube(...)
per_pixel_corr = xr.corr(ndvi_z, prism_anom_cube["ppt"], dim="time")
```

See also the [PRISM](recipes/prism_variance_cube.md) and
[gridMET](recipes/gridmet_variance_cube.md) worked examples for climate-only
pipelines. The `v.correlation_cube` factory is still under development and
currently raises `NotImplementedError`.

## Custom sources

Each loader implements the same contract: accept AOI geometry, variables, dates,
and streaming hints; return an `xarray` cube. Follow the existing modules to add
new sources (e.g., ERA5, SMAP) without changing downstream notebooks.
