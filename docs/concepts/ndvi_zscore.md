# NDVI z-scores

## What is NDVI?

The **Normalized Difference Vegetation Index (NDVI)** measures vegetation
vigour by contrasting the high reflectance of healthy plants in the near
infrared (NIR) with their low reflectance in the red band:

\[
NDVI = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}
\]

Values range from -1 to 1. Dense, photosynthetically active vegetation
produces high NDVI, while bare soil, snow, or water produce lower values.

## Why standardize NDVI?

Each pixel experiences its own seasonal cycle and lighting geometry. To detect
unusual conditions (drought, disturbance, phenology shifts) we standardize each
pixel relative to its own history. This is done with a **z-score** over time:

\[
z = \frac{x_t - \mu_{pixel}}{\sigma_{pixel}}
\]

where \(\mu_{pixel}\) and \(\sigma_{pixel}\) are the pixel's mean and
standard deviation across the available time series. The resulting NDVI
z-score cube highlights anomalies rather than absolute greenness.

## Mapping to `cubedynamics`

The package provides two key helpers:

- `cubedynamics.indices.vegetation.compute_ndvi_from_s2` turns Sentinel-2
  Level-2A surface reflectance cubes into NDVI cubes.
- `cubedynamics.stats.anomalies.zscore_over_time` standardizes each pixel
  along the time dimension.

Together they produce the NDVI z-score cubes that downstream statistics and
visualizations consume.

## End-to-end example

```python
from cubedynamics.data.sentinel2 import load_s2_cube
from cubedynamics.indices.vegetation import compute_ndvi_from_s2
from cubedynamics.stats.anomalies import zscore_over_time

s2 = load_s2_cube(
    lat=43.89,
    lon=-102.18,
    start="2023-06-01",
    end="2023-06-30",
    edge_size=256,
)

ndvi = compute_ndvi_from_s2(s2)
ndvi_z = zscore_over_time(ndvi)
```
