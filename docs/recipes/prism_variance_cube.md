# PRISM precipitation anomaly / z-score cube

PRISM cubes complement GRIDMET by offering high-resolution precipitation
records.  This recipe loads monthly precipitation, computes anomalies, and
spatially coarsens the results for downstream QA plots.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.stats.anomalies import temporal_anomaly
from cubedynamics.stats.spatial import spatial_coarsen_mean

aoi = {
    "min_lon": -105.4,
    "max_lon": -105.3,
    "min_lat": 40.0,
    "max_lat": 40.1,
}

prism = cd.load_prism_cube(
    variable="ppt",
    start="2000-01-01",
    end="2005-12-31",
    aoi=aoi,
)

ppt = prism["ppt"]
ppt_anom = temporal_anomaly(ppt, dim="time")
ppt_z = pipe(ppt_anom) | v.zscore(dim="time")
ppt_z_coarse = spatial_coarsen_mean(ppt_z, factor_y=2, factor_x=2)
```

See also:

- [GRIDMET variance / z-score cube](gridmet_variance_cube.md) for AOI-wide
  meteorological drivers.
- [Sentinel-2 NDVI anomaly (z-score) cube](s2_ndvi_zcube.md) for vegetation
  anomalies that can be correlated with the PRISM cube using
  `v.correlation_cube`.
