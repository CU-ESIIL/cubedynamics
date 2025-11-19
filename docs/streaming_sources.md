# Streaming PRISM & gridMET

CubeDynamics treats climate data sources as interchangeable **streaming
backends**. Each loader returns a cube with identical axes and metadata so the
rest of the math stack can focus on statistics.

## PRISM

- Loader: `cubedynamics.load_prism_cube`
- Purpose: high-resolution precipitation and temperature summaries
- Strategy: use STAC manifests and HTTP range requests to read only the pixels
  covering your AOI and date window

```python
import cubedynamics as cd

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2015-01-01",
    end="2020-12-31",
    variable="ppt",
)
```

`load_prism_cube` requires one AOI input (`lat`/`lon`, `bbox`, or `aoi_geojson`).
The examples throughout the docs use the keyword-only form that mirrors the
public API.

## gridMET

- Loader: `cubedynamics.load_gridmet_cube`
- Purpose: daily meteorological drivers (temperature, precipitation, vapor
  pressure deficit)
- Strategy: chunked downloads over object storage, falling back to cached tiles
  when streaming is unavailable

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

## Sentinel-2 cubes

Remote-sensing chips stream into the same pipe + verbs grammar, so you can
combine vegetation signals with climate anomalies. All Sentinel helpers require
the `cubo` package.

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
