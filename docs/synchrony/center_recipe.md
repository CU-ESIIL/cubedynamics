# Center-Pixel Climate Recipe

`v.rolling_median_split_synchrony` remains available for backwards
compatibility and for a compact climate-tail recipe. It compares every pixel to
the center pixel, splits each pair into lower and upper quantile sets, and
computes Spearman synchrony in each set.

In the new grammar, this is a convenience recipe:

```text
quantile state -> severity synchrony -> reference mode
```

It is useful, but it is not the general definition of synchrony.

## Example

```python
sync = (
    pipe(prism_temperature)
    | v.rolling_median_split_synchrony(
        lower_var="tmin",
        upper_var="tmax",
        window_days=90,
        min_t=10,
        split_quantile=0.5,
        output_stride=30,
    )
).unwrap()

cold_minus_hot = sync["bottom_minus_top"]
```

## Existing Interactive Demo

Positive values mean below-median/cold synchrony is stronger. Negative values
mean above-median/warm synchrony is stronger.

<div class="interactive-embed">
  <iframe
    src="/cubedynamics/assets/figures/climate_median_split_synchrony_cube.html"
    title="Interactive climate median-split synchrony cube"
    loading="lazy"
  ></iframe>
  <p class="interactive-embed__fallback">
    If the climate synchrony cube does not load,
    <a href="/cubedynamics/assets/figures/climate_median_split_synchrony_cube.html" target="_blank" rel="noopener">open it in a new tab</a>.
  </p>
</div>

For the full recipe and reproduction commands, see
[Rolling climate synchrony vs center pixel](../recipes/climate_tail_dep_center.md).
