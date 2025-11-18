# PRISM precipitation anomaly / z-score cube

PRISM cubes complement GRIDMET by offering high-resolution precipitation
records.  This recipe loads monthly precipitation, computes anomalies, and
spatially coarsens the results for downstream QA plots.

```python
from cubedynamics import stream_prism_to_cube
from cubedynamics.stats.anomalies import temporal_anomaly, zscore_over_time
from cubedynamics.stats.spatial import spatial_coarsen_mean

aoi = {
    "min_lon": -105.4,
    "max_lon": -105.3,
    "min_lat": 40.0,
    "max_lat": 40.1,
}

prism = stream_prism_to_cube(
    variables=["ppt"],
    start="2000-01-01",
    end="2005-12-31",
    aoi=aoi,
    prefer_streaming=True,
)

ppt = prism["ppt"]
ppt_anom = temporal_anomaly(ppt, dim="time")
ppt_z = zscore_over_time(ppt_anom)
ppt_z_coarse = spatial_coarsen_mean(ppt_z, factor_y=2, factor_x=2)
```
