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

Positive values mean below-median/cold synchrony is stronger. Negative values
mean above-median/warm synchrony is stronger. This convenience API remains
available, but the old generated interactive demo is not part of the
publication site. Start with the [real PRISM states-and-events
vignette](../vignettes/states_and_events.ipynb) for a vetted synchrony analysis.
