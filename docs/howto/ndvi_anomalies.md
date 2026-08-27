# NDVI anomalies

Use the [Sentinel-2 NDVI recipe](../recipes/s2_ndvi_zcube.md) to load observed
bands, derive NDVI and standardize it over the selected period. It requires live
provider access and optional satellite dependencies.

Read the [vegetation-index reference](../library/nouns/vegetation_index.md) for
direct NDVI loading and the [Sentinel-2 source notes](../library/sources/sentinel2.md)
for cloud, sampling and reflectance limitations. A short-period departure is
not a long-term vegetation-health baseline.
