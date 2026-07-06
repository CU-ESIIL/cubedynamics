# Rolling correlation & tail dependence

## Rolling windows in time

Rolling statistics look at a fixed-width window (e.g., 90 days) that slides
through time. At each step we compute a summary from only the values inside the
window, producing a new cube aligned to the window center. This approach keeps
temporal context while remaining responsive to recent dynamics.

## Correlation vs a reference pixel

When studying spatial synchrony we often compare every pixel to a single
reference location. In `cubedynamics` the default reference is the center
pixel in the requested climate cube. The function
`cubedynamics.stats.correlation.rolling_corr_vs_center` computes the
Pearson correlation between each pixel and the reference pixel within every
rolling window. The resulting cube reveals how tightly each pixel's climate
fluctuations track the anchor over time.

## Tail dependence

Mean correlation can miss asymmetric extremes. Tail dependence focuses on the
degree to which two pixels vary together during unusually low or high
conditions. The helper
`cubedynamics.stats.tails.rolling_tail_dep_vs_center` implements a rolling
Spearman correlation after splitting each pixel and the center reference at
their respective window quantiles. With `b=0.5`, the bottom set contains dates
when both values are at or below their medians, while the top set contains
dates when both values are above their medians. The helper returns bottom, top,
and bottom-minus-top synchrony cubes.

## Conceptual snippets

```python
from cubedynamics.stats.correlation import rolling_corr_vs_center
from cubedynamics.stats.tails import rolling_tail_dep_vs_center

corr_cube = rolling_corr_vs_center(tmin, window_days=90, min_t=10)

bottom_tail, top_tail, diff_tail = rolling_tail_dep_vs_center(
    tmin, window_days=90, min_t=10, b=0.5
)
```

For temperature analyses, compare below-median synchrony from `tmin` with
above-median synchrony from `tmax` to distinguish coordinated cold conditions
from coordinated hot conditions.
