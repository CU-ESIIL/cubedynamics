# Rolling correlation cube vs center pixel (Sentinel-2 NDVI z-scores)

This guide extends the NDVI z-score workflow by computing rolling correlation
between every pixel and the center pixel of the cube. The output highlights
areas that move in sync with the reference location.

Steps:

1. Load Sentinel-2 data and compute NDVI z-scores (same as previous recipe).
2. Downsample for faster rolling statistics (optional but recommended).
3. Use `rolling_corr_vs_center` to compute correlation cubes.
4. Visualize with Lexcube and inspect QA summaries.

```python
from cubedynamics.data.sentinel2 import load_s2_cube
from cubedynamics.indices.vegetation import compute_ndvi_from_s2
from cubedynamics.stats.anomalies import zscore_over_time
from cubedynamics.stats.correlation import rolling_corr_vs_center
from cubedynamics.utils.chunking import coarsen_and_stride
from cubedynamics.viz.lexcube_viz import show_cube_lexcube
from cubedynamics.viz.qa_plots import plot_median_over_space

s2 = load_s2_cube(
    lat=43.89,
    lon=-102.18,
    start="2023-06-01",
    end="2024-09-30",
    edge_size=1028,
    resolution=10,
    cloud_lt=40,
)

ndvi = compute_ndvi_from_s2(s2)
ndvi_z = zscore_over_time(ndvi)

# Downsample for performance
ndvi_z_ds = coarsen_and_stride(ndvi_z, coarsen_factor=4, time_stride=2)

# Rolling correlation vs center pixel
corr_cube = rolling_corr_vs_center(
    ndvi_z_ds,
    window_days=90,
    min_t=5,
)

# Lexcube visualization of correlation cube
corr_widget = show_cube_lexcube(
    corr_cube.clip(-1, 1),
    title="Rolling correlation vs center pixel (NDVI z-scores)",
    cmap="RdBu_r",
    vmin=-1,
    vmax=1,
)

# In a notebook: corr_widget.plot()

# QA: median correlation over space
ax = plot_median_over_space(
    corr_cube,
    ylabel="Median correlation",
    title="Median corr vs center (rolling 90 days)",
    ylim=(-1, 1),
)
```

Use the resulting cube to identify coherent ecological zones, potential
teleconnections, or areas where vegetation dynamics are decoupled from the
reference site.
