# GRIDMET variance / z-score cube

This recipe demonstrates how to load GRIDMET temperature data, compute
temporal anomalies, and aggregate the results spatially for QA plots.

```python
from climate_cube_math.data.gridmet import load_gridmet_cube
from climate_cube_math.stats.anomalies import temporal_anomaly, zscore_over_time
from climate_cube_math.stats.spatial import spatial_coarsen_mean
from climate_cube_math.viz.qa_plots import plot_median_over_space

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

tmax = gridmet["tmax"]
tmax_anom = temporal_anomaly(tmax, dim="time")
tmax_z = zscore_over_time(tmax_anom)

tmax_z_coarse = spatial_coarsen_mean(tmax_z, factor_y=2, factor_x=2)

ax = plot_median_over_space(
    tmax_z_coarse,
    ylabel="Median tmax z-score",
    title="GRIDMET tmax anomalies (median over space)",
)
```
