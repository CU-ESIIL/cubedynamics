# Sentinel-2 NDVI z-score cube

The complete example is maintained in the [Sentinel-2 recipe](../recipes/s2_ndvi_zcube.md).
It loads observed red/NIR bands, derives NDVI, standardizes the selected time
period and plots the result. Live STAC and asset access are required.

For direct index loading, use the [vegetation-index noun](../library/nouns/vegetation_index.md).
For raw bands, use [surface reflectance](../library/nouns/surface_reflectance.md);
the NDVI loader is not a substitute for a raw-band loader.

[Interactive viewer example](ndvi_cube_viewer.md) ·
[Source limitations](../library/sources/sentinel2.md)
