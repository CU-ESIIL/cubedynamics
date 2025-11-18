# GRIDMET variance / z-score cube

This recipe demonstrates how to load GRIDMET temperature data, compute
temporal anomalies, and aggregate the results spatially for QA plots.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.stats.anomalies import temporal_anomaly
from cubedynamics.stats.spatial import spatial_coarsen_mean
from cubedynamics.viz.qa_plots import plot_median_over_space

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

tmax = cd.load_gridmet_cube(
    aoi_geojson=boulder_aoi,
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
    title="GRIDMET tmax anomalies (median over space)",
)
```

See also:

- [PRISM precipitation anomaly / z-score cube](prism_variance_cube.md) for
  high-resolution precipitation summaries.
- [Sentinel-2 NDVI anomaly (z-score) cube](s2_ndvi_zcube.md) for vegetation
  dynamics that can be compared against the GRIDMET cube with
  `v.correlation_cube`.
