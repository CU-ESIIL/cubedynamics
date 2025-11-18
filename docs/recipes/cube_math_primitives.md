# Climate cube math primitives: temporal + spatial operators

This recipe shows how to chain the temporal and spatial primitives introduced in
`cubedynamics` to build reusable pipelines. The example assumes you already
have a cube `cube` with dimensions `(time, y, x)`.

```python
import xarray as xr

from cubedynamics.stats.anomalies import (
    rolling_mean,
    temporal_anomaly,
    temporal_difference,
)
from cubedynamics.stats.spatial import spatial_coarsen_mean

# 1. Compute anomalies relative to the full time span
anoms = temporal_anomaly(cube, dim="time")

# 2. Take month-to-month differences to highlight changes
monthly_change = temporal_difference(anoms, lag=1, dim="time")

# 3. Smooth the differences with a 3-step rolling mean
smooth_change = rolling_mean(monthly_change, window=3, dim="time")

# 4. Reduce spatial resolution by averaging 4×4 tiles (e.g., 1 km -> 4 km)
coarse_change = spatial_coarsen_mean(smooth_change, factor_y=4, factor_x=4)
```

Because these functions are thin wrappers around `xarray`, the entire pipeline is
lazy and works with both in-memory and Dask-backed cubes. Swap in other temporal
or spatial primitives as needed—for example, follow the coarsening step with a
threshold mask or a spatial smoothing filter.
