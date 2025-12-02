# Landsat-8 streaming from Microsoft Planetary Computer

This example shows how to use the `landsat8_mpc` verb to stream Landsat-8 Collection 2 Level-2 surface reflectance from Microsoft Planetary Computer as a time–band–space cube, then compute NDVI.

```python
from cubedynamics import pipe, verbs as v

# Boulder-ish bounding box
bbox = [-105.35, 39.9, -105.15, 40.1]

cube = (
    pipe(None)
    | v.landsat8_mpc(
        bbox=bbox,
        start="2019-07-01",
        end="2019-08-01",
        band_aliases=("red", "nir"),
        max_cloud_cover=50,
        chunks_xy={"x": 1024, "y": 1024},
    )
).unwrap()

print(cube)
# DataArray(time, band, y, x) with band ~ ["red", "nir"]

red = cube.sel(band="red")
nir = cube.sel(band="nir")
ndvi = (nir - red) / (nir + red)
ndvi.name = "NDVI"

# Plot all timesteps with the CubePlot viewer
pipe(ndvi) | v.plot(time_dim="time")
```

Because the underlying arrays are dask-backed, nothing is fully loaded into memory until you compute or plot.

Note: This verb uses Microsoft Planetary Computer’s STAC API and signed COG URLs via the planetary_computer Python SDK. No AWS credentials are needed.
