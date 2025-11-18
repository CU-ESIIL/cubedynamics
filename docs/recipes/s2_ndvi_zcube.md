# Sentinel-2 NDVI z-score cube + Lexcube

This recipe walks through an end-to-end workflow to produce NDVI z-score cubes
from Sentinel-2 Level-2A data and visualize the results with the Lexcube
widget.

1. **Load Sentinel-2** – `load_s2_cube` requests a chip centered on your
   latitude/longitude, with configurable time range, edge length, spatial
   resolution, and maximum cloud fraction.
2. **Compute NDVI** – `compute_ndvi_from_s2` reads the red and NIR bands and
   produces an NDVI cube.
3. **Compute z-scores** – `zscore_over_time` standardizes each pixel along the
   time dimension to highlight anomalies.
4. **Optional coarsening/striding** – `coarsen_and_stride` reduces spatial and
   temporal resolution to make exploratory visualization faster.
5. **Lexcube visualization** – `show_cube_lexcube` renders the cube in an
   interactive widget, and `plot_median_over_space` creates a QA time series of
   the spatial median.

```python
from cubedynamics.data.sentinel2 import load_s2_cube
from cubedynamics.indices.vegetation import compute_ndvi_from_s2
from cubedynamics.stats.anomalies import zscore_over_time
from cubedynamics.utils.chunking import coarsen_and_stride
from cubedynamics.viz.lexcube_viz import show_cube_lexcube
from cubedynamics.viz.qa_plots import plot_median_over_space

# 1. Load Sentinel-2 cube
s2 = load_s2_cube(
    lat=43.89,
    lon=-102.18,
    start="2023-06-01",
    end="2023-09-30",
    edge_size=512,
    resolution=10,
    cloud_lt=40,
)

# 2. Compute NDVI
ndvi = compute_ndvi_from_s2(s2)

# 3. Compute NDVI z-scores per pixel
ndvi_z = zscore_over_time(ndvi)

# 4. Optional: coarsen spatially and subsample in time
ndvi_z_ds = coarsen_and_stride(
    ndvi_z,
    coarsen_factor=4,
    time_stride=2,
)

# 5. Lexcube visualization
widget = show_cube_lexcube(
    ndvi_z_ds.clip(-3, 3),
    title="Sentinel-2 NDVI z-scores (coarsened)",
    cmap="RdBu_r",
    vmin=-3,
    vmax=3,
)

# In a notebook: widget.plot()

# 6. QA plot of median z-score over space
ax = plot_median_over_space(
    ndvi_z_ds,
    ylabel="Median NDVI z-score",
    title="Median NDVI z-score over time",
)
# In a notebook: display(ax.figure)
```

The same pattern works for other sensors as long as you can derive the target
index cube and feed it into the anomaly functions.
