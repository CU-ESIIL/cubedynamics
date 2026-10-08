# Landsat streaming and NDVI

Use the [Landsat MPC workflow](../datasets/landsat8_mpc.md) for the complete
example, scaling contract, CRS selection, QA limitations and live-test command.

```python
from cubedynamics import pipe, verbs as v

cube = pipe(None) | v.landsat_mpc(
    bbox=[-105.35, 39.90, -105.15, 40.10],
    start="2024-07-01", end="2024-09-01",
    bands=("red", "nir08"), max_cloud_cover=20,
    epsg=32613, resolution=30, chunksize=1024,
)
da = cube.unwrap()
red, nir = da.sel(band="red"), da.sel(band="nir08")
ndvi = (nir - red) / (nir + red)
```

This is physical surface reflectance; do not scale it again. Both arrays remain
Dask-backed until computation. Scene cloud filtering does not mask cloudy
pixels. `landsat8_mpc` remains available for Landsat 8 compatibility.
