# gridMET AOI variance

The gridMET example mirrors the PRISM workflow but operates on a polygon AOI to highlight the grammar's flexibility.

## Story

We stream gridMET temperature (tmmx) data for a Boulder AOI, compute anomalies, convert to z-scores, and aggregate spatially for QA plots. This narrative folds in the earlier "GRIDMET variance / z-score cube" recipe without dropping any context.

## Code

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.stats.anomalies import temporal_anomaly
from cubedynamics.stats.spatial import spatial_coarsen_mean
from cubedynamics.viz.qa_plots import plot_median_over_space

tmax = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="tmmx",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)

tmax_anom = temporal_anomaly(tmax, dim="time")
tmax_z = pipe(tmax_anom) | v.zscore(dim="time")

tmax_z_coarse = spatial_coarsen_mean(tmax_z, factor_y=2, factor_x=2)

ax = plot_median_over_space(
    tmax_z_coarse,
    ylabel="Median tmax z-score",
    title="gridMET tmmx anomalies (median over space)",
)
```

## Pipe-only summary

If you prefer to keep everything in verbs, the following snippet filters to summer months and computes variance directly:

```python
pipe(tmax) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```

## Related examples

- [PRISM JJA variance](prism_jja_variance.md)
- [Sentinel-2 NDVI z-score cube](s2_ndvi_zscore.md)
