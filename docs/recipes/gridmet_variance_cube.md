# Daily temperature variability with gridMET

Live-data recipe · requires provider access. No new live result is certified by
this documentation refactor.

## Question

How variable was daily maximum temperature across a Boulder-area grid during
June 2024? This is within-month variability, not a long-term climate trend.

## Data used

The [temperature noun](../library/nouns/temperature.md) with
[source `gridmet`](../library/sources/gridmet.md) supplies daily maximum
temperature in kelvin. The query below selects a small CONUS bounding box and
one month. Keep the returned source/revision attributes with the result.

## Analysis

Run the blocks in order after the [installation steps](../quickstart.md).
The loader is lazy; plotting is an explicit request to retrieve the values.

```python
from cubedynamics import data, pipe, verbs as v
import matplotlib.pyplot as plt

tmax = data.temperature(
    source="gridmet", statistic="maximum",
    bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-06-01", end="2024-06-30",
)
assert tmax.dims == ("time", "y", "x")
assert tmax.attrs["units"] == "K"
print(tmax.sizes, tmax.attrs)
```

## Grammar / pipeline

```python
variability = (
    pipe(tmax)
    | v.month_filter([6, 7, 8])
    | v.variance(dim="time", keep_dim=False)
).unwrap()
```

## Plain-language interpretation

Keep summer observations, then compute temporal variance independently at each
grid cell. Here the request contains only June, so the month filter does not add
July or August. Extend the acquisition dates to examine a whole summer.

## Result

```python
variability.plot(cbar_kwargs={"label": "Daily maximum temperature variance (K²)"})
plt.title("Within-June temperature variability · gridMET · 2024")
plt.show()
```

This map describes variability over the requested dates. It is not a map of
temperature itself, forecast uncertainty, or long-term warming. Missing values
and the number of observations per cell matter.

To ask a different question—when temperatures were high relative to each cell's
own June distribution—standardize first, then summarize space:

```python
standardized = (pipe(tmax) | v.zscore(dim="time")).unwrap()
standardized.mean(("y", "x")).plot()
plt.ylabel("Mean within-June z-score (dimensionless)")
plt.show()
```

The spatial mean is unweighted. Standardization removes each cell's absolute
temperature level; it is not a second variance estimate.

## Reproduce

Use `python -m pip install -e '.[vignettes]'` from a cloned repository and run the
blocks in Jupyter. Requires working gridMET access; this page is not an executed
offline notebook. Inspect source identity, date counts, units and finite values,
and save query/revision metadata alongside any published output. For an
offline-tested equivalent of the operations, see the notebook below.

## See also

- [Observed PRISM verb gallery](../vignettes/verbs_gallery.ipynb)
- [variance](../reference/verbs/variance.md) and [zscore](../reference/verbs/zscore.md)
- [PRISM precipitation anomalies](prism_variance_cube.md)
- [Source methods and QA](../datasets/gridmet.md)
