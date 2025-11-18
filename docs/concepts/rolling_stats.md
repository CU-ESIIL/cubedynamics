# Rolling correlation & tail dependence

## Rolling windows in time

Rolling statistics look at a fixed-width window (e.g., 90 days) that slides
through time. At each step we compute a summary from only the values inside the
window, producing a new cube aligned to the window center. This approach keeps
temporal context while remaining responsive to recent dynamics.

## Correlation vs a reference pixel

When studying spatial synchrony we often compare every pixel to a single
reference location. In `cubedynamics` the default reference is the center
pixel in the requested Sentinel-2 chip. The function
`cubedynamics.stats.correlation.rolling_corr_vs_center` computes the
Pearson correlation between each pixel and the reference pixel within every
rolling window. The resulting cube reveals how tightly each pixel's NDVI
fluctuations track the anchor over time.

## Tail dependence

Mean correlation can miss asymmetric extremes. Tail dependence focuses on the
probability that two pixels jointly experience unusually low (bottom tail) or
high (top tail) values. The helper
`cubedynamics.stats.tails.rolling_tail_dep_vs_center` implements a rolling
partial Spearman correlation restricted to the lower or upper tail of the data.
It returns three cubes: bottom-tail, top-tail, and their difference (bottom -
top). Large positive differences indicate areas that co-experience stress with
the center pixel more often than they share unusually high NDVI.

## Conceptual snippets

```python
from cubedynamics.stats.correlation import rolling_corr_vs_center
from cubedynamics.stats.tails import rolling_tail_dep_vs_center

corr_cube = rolling_corr_vs_center(ndvi_z, window_days=90, min_t=5)

bottom_tail, top_tail, diff_tail = rolling_tail_dep_vs_center(
    ndvi_z, window_days=90, min_t=5, b=0.5
)
```

By chaining these functions onto an NDVI z-score cube we transform the original
vegetation signal into diagnostics of synchrony and shared extremes.
