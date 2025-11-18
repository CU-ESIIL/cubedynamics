# Rolling tail-dependence cubes vs center pixel (Sentinel-2 NDVI z-scores)

Tail-dependence statistics reveal whether extremes in one pixel align with
extremes in another. This recipe computes bottom- and top-tail dependence
against the center pixel, plus their difference, using NDVI z-score cubes as
input.

Steps:

1. Load Sentinel-2 data and compute NDVI z-scores.
2. Optionally coarsen/stride for tractable rolling windows.
3. Call `rolling_tail_dep_vs_center` to compute bottom, top, and difference
   cubes.
4. Visualize the difference cube with Lexcube and review QA medians.

```python
from cubedynamics.data.sentinel2 import load_s2_cube
from cubedynamics.indices.vegetation import compute_ndvi_from_s2
from cubedynamics.stats.anomalies import zscore_over_time
from cubedynamics.stats.tails import rolling_tail_dep_vs_center
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
ndvi_z_ds = coarsen_and_stride(ndvi_z, coarsen_factor=4, time_stride=2)

# Rolling tail-dependence cubes vs center pixel
bottom_tail_cube, top_tail_cube, diff_tail_cube = rolling_tail_dep_vs_center(
    ndvi_z_ds,
    window_days=90,
    min_t=5,
    b=0.5,
)

# Visualize the difference cube with Lexcube
diff_widget = show_cube_lexcube(
    diff_tail_cube.clip(-1, 1),
    title="Tail-dependence difference (bottom - top) vs center pixel",
    cmap="RdBu_r",
    vmin=-1,
    vmax=1,
)

# In a notebook: diff_widget.plot()

# QA: median tail-dependence difference over space
ax = plot_median_over_space(
    diff_tail_cube,
    ylabel="Median bottom - top tail dep",
    title="Median tail-dependence difference (rolling 90 days)",
    ylim=(-1, 1),
)
```

Positive difference values highlight areas that tend to share low NDVI events
with the center pixel more often than high NDVI events, which can be an early
indicator of coordinated stress.
