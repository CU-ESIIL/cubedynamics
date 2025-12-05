# Climate–NDVI correlation cube

Correlation cubes capture how vegetation anomalies co-vary with climate drivers. This example merges the earlier correlation notes with the new pipe-first grammar.

## Load climate and NDVI cubes

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

prism_cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

ndvi = cd.load_sentinel2_ndvi_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
)
ndvi_z = pipe(ndvi) | v.zscore(dim="time")
```

## Prepare anomalies

```python
climate_anom = (
    pipe(prism_cube)
    | v.anomaly(dim="time")
).unwrap()["ppt"]
```

## Compute per-pixel correlations

```python
import xarray as xr

corr = xr.corr(ndvi_z, climate_anom, dim="time")
```

The output stores Pearson coefficients per pixel along the shared `(y, x)` grid. Use it to spot areas where vegetation responds strongly to precipitation anomalies. The `v.correlation_cube` factory is reserved for a future streaming implementation and currently raises `NotImplementedError`.

## Rolling correlation vs anchor pixels

`cubedynamics.rolling_corr_vs_center` and `cubedynamics.rolling_tail_dep_vs_center` extend the idea to within-cube synchrony (e.g., NDVI vs center pixel). They operate on any `(time, y, x)` cube:

```python
from cubedynamics import rolling_corr_vs_center

rolling = rolling_corr_vs_center(ndvi_z, window_days=90, min_t=5)
```

## Related documentation

- [Correlation & synchrony cubes](../howto/correlation_cubes.md)
- [Sentinel-2 NDVI z-score cube](s2_ndvi_zscore.md)
- [Verbs – Stats](../reference/verbs_stats.md)
