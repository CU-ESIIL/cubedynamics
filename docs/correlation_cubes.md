# Correlation & synchrony cubes

Correlation cubes capture how each pixel in a climate cube co-varies with a
reference pixel or a driver variable. CubeDynamics ships rolling statistics and
lexcube builders tuned for NDVI synchrony, drought detection, and anomaly
tracking.

## Rolling correlation vs anchor pixels

```python
from cubedynamics.stats.correlation import rolling_corr_vs_center

corr_cube = rolling_corr_vs_center(
    ndvi_z_cube,
    window_days=90,
    min_t=5,
)
```

The output is a cube aligned to the center of each rolling window and stores the
Pearson correlation for every pixel relative to the anchor pixel (by default the
center of the spatial chip). Swap in a custom anchor by passing coordinates or a
mask.

## Tail dependence lexcubes

```python
from cubedynamics.stats.tails import rolling_tail_dep_vs_center

bottom_tail, top_tail, diff_tail = rolling_tail_dep_vs_center(
    ndvi_z_cube,
    window_days=90,
    min_t=5,
    b=0.5,
)
```

Tail dependence cubes highlight asymmetric stress events. Use them to detect
areas that co-experience low NDVI (drought, disturbance) even when overall
correlation remains modest.

## Cross-dataset correlation

Lexcubes can also correlate separate datasets, such as NDVI vs PRISM
precipitation anomalies:

```python
from cubedynamics.lexcubes.correlations import correlation_cube

lexcube = correlation_cube(
    driver_cube=prism_anom,
    response_cube=ndvi_z_cube,
    window="30D",
)
```

The resulting dataset contains the rolling correlation, lag, and metadata so you
can immediately export to NetCDF, GeoTIFF, or dashboards.
