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
    output_stride=30,
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

## Interactive synchrony cube

The interactive cube below shows the same idea as a compact demonstration:
positive values mean below-median/cold synchrony is stronger, while negative
values mean above-median/warm synchrony is stronger.

<div class="interactive-embed">
  <iframe
    src="/cubedynamics/assets/figures/climate_median_split_synchrony_cube.html"
    title="Interactive climate median-split synchrony cube"
    loading="lazy"
  ></iframe>
  <p class="interactive-embed__fallback">
    If the interactive synchrony cube doesn’t load,
    <a href="/cubedynamics/assets/figures/climate_median_split_synchrony_cube.html" target="_blank" rel="noopener">open it in a new tab</a>.
  </p>
</div>

Recreate the embedded output locally:

```bash
python examples/median_split_synchrony_demo.py \
  --output-dir artifacts/median-split-demo

cp artifacts/median-split-demo/median_split_synchrony_cube.html \
  docs/assets/figures/climate_median_split_synchrony_cube.html

cp artifacts/median-split-demo/median_split_synchrony_diagnostic.png \
  docs/assets/figures/climate_median_split_synchrony_diagnostic.png
```

This demo uses deterministic synthetic PRISM-like `tmin` and `tmax` cubes, so it
is fast and offline. It also writes
`median_split_synchrony_diagnostic.png`, a static diagnostic panel with flat
cube faces, cold/hot/difference synchrony traces, a variance map, and a value
distribution. The longer PRISM command below recreates the real-data version of
the workflow.

With `b=0.5`, each rolling comparison uses separate medians for the grid cell
and center cell. The cold set contains dates when both daily minimum
temperatures are at or below their medians. The hot set contains dates when
both daily maximum temperatures are above their medians. Spearman synchrony is
calculated independently in each set. Positive difference values indicate
stronger cold synchrony; negative values indicate stronger hot synchrony.

The verb accepts a `(time, y, x)` `xarray.DataArray` for a single-variable
analysis or a `Dataset` with separate lower/upper variables. To study
precipitation instead, request PRISM `ppt`; a gridMET cube works too.

For the complete daily PRISM record without a local input cache, run:

```bash
python examples/real_prism_median_split_synchrony.py \
  --output-dir artifacts/prism-full-record
```

The example defaults to 1981 through the last complete calendar year and
evaluates every 30th daily timestamp. It streams server-cropped `tmin` and
`tmax` subsets with four workers, then saves only the computed synchrony cube
and plots.
