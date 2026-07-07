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
4. Visualize the difference cube and review bottom/top/diff synchrony through time.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.stats.tails import rolling_tail_dep_vs_center
from cubedynamics.utils.chunking import coarsen_and_stride
from cubedynamics.viz.qa_plots import plot_tail_dependence_over_time

s2 = cd.load_sentinel2_cube(
    lat=43.89,
    lon=-102.18,
    start="2023-06-01",
    end="2024-09-30",
    edge_size=1028,
    resolution=10,
    cloud_lt=40,
)

ndvi_z = (
    pipe(s2)
    | v.ndvi_from_s2()
    | v.zscore(dim="time")
)
ndvi_z_ds = coarsen_and_stride(ndvi_z, coarsen_factor=4, time_stride=2)

# Rolling tail-dependence cubes vs center pixel
bottom_tail_cube, top_tail_cube, diff_tail_cube = rolling_tail_dep_vs_center(
    ndvi_z_ds,
    window_days=90,
    min_t=5,
    b=0.5,
)

# Visualize the difference cube with the cube viewer
diff_clip = diff_tail_cube.clip(-1, 1)
diff_viewer = (pipe(diff_clip) | v.plot(
    title="Tail-dependence difference (bottom - top) vs center pixel",
    cmap="RdBu_r",
    clim=(-1, 1),
)).unwrap()

# Flat QA: median synchrony through time
ax = plot_tail_dependence_over_time(
    bottom_tail_cube,
    top_tail_cube,
    diff_tail_cube,
    title="Median tail-dependence synchrony (rolling 90 days)",
    ylim=(-1, 1),
)
```

Positive difference values highlight areas that tend to share low NDVI events
with the center pixel more often than high NDVI events, which can be an early
indicator of coordinated stress.
