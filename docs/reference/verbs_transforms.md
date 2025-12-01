# Transform verbs

Transform verbs reshape or filter cubes before you compute downstream statistics. All functions live under `cubedynamics.verbs` and can be chained via `pipe(cube) | v.verb(...)`.

### `v.anomaly(dim="time")`

Compute anomalies by subtracting the mean along a given dimension. The output keeps the same shape as the input cube so Lexcube visualization remains valid.

```python
from cubedynamics import pipe, verbs as v

anom = (
    pipe(cube)
    | v.anomaly(dim="time")
).unwrap()
```

- **Parameters**: `dim` – dimension name (e.g., `"time"`).
- **Notes**: Preserves metadata and alignment across coordinates.

### `v.month_filter(months)`

Filter the cube to only certain calendar months. The verb drops timesteps outside the requested month list.

```python
jja = pipe(cube) | v.month_filter([6, 7, 8])
```

- **Parameters**: `months` – iterable of month numbers (1–12).
- **Notes**: Requires a datetime-like `time` coordinate.

### `v.ndvi_from_s2(nir_band="B08", red_band="B04")`

Derive NDVI from Sentinel-2 reflectance cubes. The incoming object must expose a `band` dimension containing the requested near-infrared (`nir_band`) and red (`red_band`) entries. The verb returns a `(time, y, x)` NDVI cube with float32 reflectance values in `[-1, 1]`.

```python
ndvi = (
    pipe(s2_cube)
    | v.ndvi_from_s2()
).unwrap()
```

- **Parameters**: `nir_band`, `red_band` – band names present in the cube.
- **Notes**: Works with cubes loaded via `cd.load_sentinel2_cube` (legacy alias `load_s2_cube`) or `cubo.create`.

### `v.landsat8_mpc(...)`

Stream Landsat-8 Collection 2 Level-2 surface reflectance from Microsoft Planetary Computer. The verb pulls SR_B4 (red) and SR_B5 (nir) by default, stacks them into a `(time, band, y, x)` cube, and leaves the data lazy/dask-backed for downstream math like NDVI.

```python
from cubedynamics import pipe, verbs as v

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

red = cube.sel(band="red")
nir = cube.sel(band="nir")
ndvi = (nir - red) / (nir + red)
```

- **Parameters**: `bbox`, `start`, `end`, `band_aliases`, `max_cloud_cover`, `chunks_xy`, `stac_url`.
- **Notes**: Uses MPC's STAC API and `planetary_computer.pc.sign` for HTTPS COGs; no AWS credentials required.

Use these verbs as building blocks ahead of stats like variance or correlation. Rolling synchrony helpers such as `cubedynamics.rolling_corr_vs_center` and `cubedynamics.rolling_tail_dep_vs_center` live outside the `verbs` namespace.
