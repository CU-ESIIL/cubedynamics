# PRISM JJA variance

This recipe computes June–July–August precipitation variance from PRISM for a Boulder, CO point. It extends the original "PRISM precipitation anomaly / z-score cube" guide and adds Lexcube-ready context.

## Story

PRISM cubes complement gridMET by offering higher-resolution precipitation records. We stream a monthly cube, compute anomalies, filter to summer months, and collapse the time dimension with `v.variance` for a single summary layer.

## Code

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
    freq="D",
)

jja_var = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.month_filter([6, 7, 8])
    | v.variance(dim="time")
).unwrap()
```

`v.variance` defaults to `keep_dim=True`, so the `time` dimension remains in the result (length 1) and stays Lexcube-ready. Set `keep_dim=False` when you intentionally want a 2D map:

```python
jja_map = pipe(cube) | v.month_filter([6, 7, 8]) | v.variance(dim="time", keep_dim=False)
```

Because the cube stays in `xarray`, you can coarsen it, clip to focus on extremes, or export to NetCDF with `v.to_netcdf`. Reuse the same grammar for other PRISM variables (`tmax`, `tdmean`) by switching the `variable` parameter.

## Optional: Lexcube visualization

```python
pipe(jja_var) | v.show_cube_lexcube(title="PRISM JJA precipitation variance")
```

Lexcube previews help verify that AOI and time selections are correct before you compute downstream stats or share results. For larger regions, stride or coarsen the cube prior to visualization.

## Related examples

- [gridMET AOI variance](gridmet_aoi_variance.md)
- [Sentinel-2 NDVI z-score cube](s2_ndvi_zscore.md)
- [Climate–NDVI correlation cube](climate_ndvi_correlation.md)
