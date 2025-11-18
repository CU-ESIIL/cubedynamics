# Climate data backends

`cubedynamics` treats "climate cube" sources as interchangeable once they
provide the standard `(time, y, x)` layout.  The data loaders expose
consistent knobs and return dask-backed `xarray.Dataset` objects so the rest
of the math stack can focus on statistics instead of I/O details.

## Sentinel-2

* Loader: `climate_cube_math.data.sentinel2.load_s2_cube`
* Purpose: multispectral reflectance for vegetation index and QA work.
* Typical recipe: compute NDVI with
  `climate_cube_math.indices.vegetation.compute_ndvi_from_s2` and then derive
  z-scores or temporal anomalies with `climate_cube_math.stats.anomalies`.

## GRIDMET

* Loader: `climate_cube_math.data.gridmet.load_gridmet_cube`
* Purpose: daily meteorological drivers (temperature, precipitation, etc.).
* Streaming-first design: attempts to return a lazily-evaluated cube, falling
  back to an in-memory download only when streaming is not available.

```python
from climate_cube_math.data.gridmet import load_gridmet_cube
from climate_cube_math.stats.anomalies import zscore_over_time

aoi = {
    "min_lon": -105.4,
    "max_lon": -105.3,
    "min_lat": 40.0,
    "max_lat": 40.1,
}

gridmet = load_gridmet_cube(
    variables=["tmax"],
    start="2000-01-01",
    end="2000-12-31",
    aoi=aoi,
    prefer_streaming=True,
)

tmax_z = zscore_over_time(gridmet["tmax"])
```

## PRISM

* Loader: `climate_cube_math.data.prism.load_prism_cube`
* Purpose: high-resolution precipitation and temperature summaries.
* Uses the same streaming-first contract as GRIDMET.

```python
from climate_cube_math.data.prism import load_prism_cube
from climate_cube_math.stats.anomalies import zscore_over_time

aoi = {
    "min_lon": -105.4,
    "max_lon": -105.3,
    "min_lat": 40.0,
    "max_lat": 40.1,
}

prism = load_prism_cube(
    variables=["ppt"],
    start="2000-01-01",
    end="2000-12-31",
    aoi=aoi,
    prefer_streaming=True,
)

ppt_z = zscore_over_time(prism["ppt"])
```

Each loader keeps the cube streaming whenever possible, emits a warning when
falling back to downloads, and never writes to disk inside the library.
