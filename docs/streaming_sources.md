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

boulder_aoi = {
    "type": "Feature",
    "properties": {"name": "Boulder, CO"},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-105.35, 40.00],
            [-105.35, 40.10],
            [-105.20, 40.10],
            [-105.20, 40.00],
            [-105.35, 40.00],
        ]],
    },
}

cube = cd.load_gridmet_cube(
    aoi_geojson=boulder_aoi,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)
```

## Sentinel-2 → NDVI anomaly (z-score) cube

Remote-sensing chips stream into the same pipe + verbs grammar, so you can
combine vegetation signals with climate anomalies. Use
`cd.load_sentinel2_ndvi_cube` (requires the `cubo` package) for a one-function
workflow:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi_z = cd.load_sentinel2_ndvi_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
)

pipe(ndvi_z) | v.show_cube_lexcube(title="Sentinel-2 NDVI z-score")
```

The helper streams Sentinel-2 Level-2A imagery via `cubo`, computes NDVI from
bands B08 (NIR) and B04 (red), and runs `v.zscore(dim="time")` so the returned
cube is standardized across time. Set ``return_raw=True`` to also grab the raw
reflectance stack and intermediate NDVI cube. You can still manually reproduce
the pipeline with `pipe(...) | v.ndvi_from_s2(...) | v.zscore(...)` if you need a
different stacking order.

The resulting cube highlights unusual greenness events (drought stress,
disturbance, rapid recovery). Because every cube shares `(time, y, x)` axes, you
can correlate NDVI anomalies with PRISM or gridMET cubes using
`v.correlation_cube`:

```python
corr_cube = (
    pipe(ndvi_z)
    | v.correlation_cube(prism_anom_cube, dim="time")
).unwrap()
```

See also the [PRISM](recipes/prism_variance_cube.md) and
[gridMET](recipes/gridmet_variance_cube.md) worked examples for climate-only
pipelines.

## Custom sources

Each loader implements the same contract: accept AOI geometry, variables, dates,
and streaming hints; return an `xarray` cube. Follow the existing modules to add
new sources (e.g., ERA5, SMAP) without changing downstream notebooks.
