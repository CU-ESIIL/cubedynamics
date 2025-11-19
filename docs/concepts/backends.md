# Climate data backends

`cubedynamics` treats "climate cube" sources as interchangeable once they
provide the standard `(time, y, x)` layout. The data loaders expose
consistent knobs and return dask-backed `xarray.Dataset` objects so the rest
of the math stack can focus on statistics instead of I/O details.

## Sentinel-2

* Loader: `cubedynamics.load_sentinel2_cube` / `cubedynamics.load_sentinel2_ndvi_cube`
* Purpose: multispectral reflectance for vegetation index and QA work.
* Typical recipe: compute NDVI with `cubedynamics.verbs.ndvi_from_s2` and then
  derive z-scores or temporal anomalies with `cubedynamics.verbs.zscore` or the
  anomaly helpers.

## GRIDMET

* Loader: `cubedynamics.load_gridmet_cube`
* Purpose: daily meteorological drivers (temperature, precipitation, etc.).
* Streaming-first design: attempts to return a lazily-evaluated cube, falling
  back to an in-memory download only when streaming is not available.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

precip = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)

pr_z = pipe(precip) | v.zscore(dim="time")
```

## PRISM

* Loader: `cubedynamics.load_prism_cube`
* Purpose: high-resolution precipitation and temperature summaries.
* Uses the same streaming-first contract as GRIDMET.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

aoi = {
    "min_lon": -105.4,
    "max_lon": -105.3,
    "min_lat": 40.0,
    "max_lat": 40.1,
}

prism = cd.load_prism_cube(
    start="2000-01-01",
    end="2000-12-31",
    aoi=aoi,
)

ppt_z = pipe(prism["ppt"]) | v.zscore(dim="time")
```

Each loader keeps the cube streaming whenever possible, emits a warning when
falling back to downloads, and never writes to disk inside the library.
