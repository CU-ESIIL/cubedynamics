# First cube (PRISM)

This walkthrough recreates the original getting-started notebook with updated notes for 2025. You will load a PRISM precipitation cube, compute summer variance, and compare it with a gridMET AOI example.

## Load and inspect the cube

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

cube
```

`load_prism_cube` accepts exactly one AOI definition: a `lat`/`lon` point, a bounding box via `bbox=[min_lon, min_lat, max_lon, max_lat]`, or a GeoJSON Feature/FeatureCollection via `aoi_geojson`. The older positional signature is deprecated but still works for legacy notebooks.

## Pipe it through verbs

```python
jja_var = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.month_filter([6, 7, 8])
    | v.variance(dim="time")
).unwrap()
```

Because `Pipe` implements `_repr_html_`, notebooks display the wrapped DataArray/Dataset automatically. Call `.unwrap()` when you need to assign the result mid-cell.

## Compare with gridMET

The same grammar applies to GRIDMET cubes. Stream a polygon AOI, filter to summer months, and compute variance:

```python
cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)

pipe(cube) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```

## Next steps

- Switch the loader to `cd.load_sentinel2_ndvi_zscore_cube` (or `cd.load_sentinel2_ndvi_cube` + `v.zscore(dim="time")`) for vegetation workflows.
- Visualize any cube inline with `pipe(cube) | v.show_cube_lexcube(title="My Cube")`.
- Follow the [Examples & Recipes](../examples/prism_jja_variance.md) section for narrated analyses.
