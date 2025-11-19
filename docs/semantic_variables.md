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
