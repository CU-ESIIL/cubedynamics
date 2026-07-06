# Rolling climate synchrony vs center pixel

This recipe measures whether unusually cold and unusually hot conditions occur
synchronously across a region. It compares every PRISM grid cell with the
center cell in rolling windows, splitting each cell and the reference at their
own window medians before calculating synchrony.

Steps:

1. Load daily PRISM minimum- and maximum-temperature cubes.
2. Compute below-median synchrony from minimum temperature.
3. Compute above-median synchrony from maximum temperature.
4. View the cold-minus-hot difference as a cube.
5. Plot spatially summarized synchrony through time.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.viz.qa_plots import plot_tail_dependence_over_time

temperature = cd.load_prism_cube(
    bbox=[-105.75, 39.50, -104.75, 40.50],
    start="2020-01-01",
    end="2022-12-31",
    variables=["tmin", "tmax"],
    freq="D",
    chunks={"time": 180},
)

sync = (pipe(temperature) | v.rolling_median_split_synchrony(
    lower_var="tmin",
    upper_var="tmax",
    window_days=90,
    min_t=10,
    split_quantile=0.5,
)).unwrap()

cold_sync = sync["bottom_synchrony"]
hot_sync = sync["top_synchrony"]
cold_minus_hot = sync["bottom_minus_top"]

# Interactive cube: positive values indicate stronger cold synchrony.
diff_viewer = (pipe(cold_minus_hot.clip(-2, 2)) | v.plot(
    title="PRISM temperature synchrony: cold minus warm",
    cmap="RdBu_r",
    clim=(-2, 2),
)).unwrap()

# Flat plot: regional median cold, warm, and difference synchrony.
ax = plot_tail_dependence_over_time(
    cold_sync,
    hot_sync,
    cold_minus_hot,
    title="Median PRISM temperature synchrony (rolling 90 days)",
    labels=("below-median tmin", "above-median tmax", "cold - hot"),
)
```

With `b=0.5`, each rolling comparison uses separate medians for the grid cell
and center cell. The cold set contains dates when both daily minimum
temperatures are at or below their medians. The hot set contains dates when
both daily maximum temperatures are above their medians. Spearman synchrony is
calculated independently in each set. Positive difference values indicate
stronger cold synchrony; negative values indicate stronger hot synchrony.

The verb accepts a `(time, y, x)` `xarray.DataArray` for a single-variable
analysis or a `Dataset` with separate lower/upper variables. To study
precipitation instead, request PRISM `ppt`; a gridMET cube works too.
