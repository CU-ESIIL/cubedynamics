# `landsat8_mpc`

## Overview
`landsat8_mpc` streams Landsat 8 Collection 2 Level-2 surface reflectance directly from the Microsoft Planetary Computer (MPC) STAC API. The verb signs COG URLs using the `planetary_computer` SDK and stacks the requested bands into a lazy, dask-backed DataArray with dimensions `(time, band, y, x)`.

## Required arguments
- `bbox` – `[min_lon, min_lat, max_lon, max_lat]` geographic bounding box.
- `start` – ISO start date string (e.g., `"2019-07-01"`).
- `end` – ISO end date string (e.g., `"2019-08-01"`).

## Optional arguments
- `band_aliases` – tuple of band aliases to pull (default `("red", "nir")`).
- `max_cloud_cover` – maximum allowed `eo:cloud_cover` percentage (default `50`).
- `chunks_xy` – optional dask chunk sizes for `x` and `y` (e.g., `{ "x": 1024, "y": 1024 }`).
- `stac_url` – STAC API endpoint, defaults to the MPC service.

## Return structure
A lazy :class:`xarray.DataArray` backed by dask with dimensions `(time, band, y, x)`. Data are not loaded until you compute or plot.

## Basic usage
```python
from cubedynamics import pipe, verbs as v

bbox = [-105.35, 39.9, -105.15, 40.1]
cube = (
    pipe(None)
    | v.landsat8_mpc(
        bbox=bbox,
        start="2019-07-01",
        end="2019-08-01",
    )
).unwrap()
```

## NDVI example
After streaming, compute NDVI from the red and near-infrared bands:

```python
red = cube.sel(band="red")
nir = cube.sel(band="nir")
ndvi = (nir - red) / (nir + red)
```

## Notes
- This verb uses MPC-signed STAC assets; no additional credentials are required.
- Because the DataArray is dask-backed, subsequent analysis and visualization remain lazy until execution.
