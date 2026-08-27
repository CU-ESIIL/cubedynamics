# Daily precipitation anomalies with PRISM

Live-data recipe · requires provider access. The historical URL is retained;
this workflow computes standardized anomalies, not variance.

## Question

Which June days were relatively wet within each Boulder-area grid cell?
The reference distribution is this single month, not a climate normal.

## Data used

The [precipitation noun](../library/nouns/precipitation.md) with
[source `prism`](../library/sources/prism.md) supplies daily totals in millimeters.
The query selects June 2024 and a small bounding box. PRISM is a CONUS product.

## Analysis

Run the blocks in order after [installation](../quickstart.md). Inspect returned
coordinates, date counts and provenance before interpreting the plot.

```python
from cubedynamics import data, pipe, verbs as v
import matplotlib.pyplot as plt

ppt = data.precipitation(
    source="prism",
    bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-06-01", end="2024-06-30",
)
assert ppt.dims == ("time", "y", "x")
assert ppt.attrs["units"] == "mm"
print(ppt.sizes, ppt.attrs)
```

## Grammar / pipeline

```python
ppt_z = (pipe(ppt) | v.zscore(dim="time")).unwrap()
```

## Plain-language interpretation

At each grid cell, subtract its mean daily precipitation and divide by its
standard deviation over the requested month. An additional anomaly step is
unnecessary. This preserves day-to-day departures while removing absolute
rainfall levels.

## Result

```python
ppt_z.mean(("y", "x")).plot()
plt.ylabel("Mean within-June precipitation z-score (dimensionless)")
plt.title("PRISM · Boulder region · June 2024")
plt.show()
```

The spatial mean is unweighted. Precipitation is often skewed and zero-inflated;
these z-scores are not a drought index or a normal-probability statement.
Inspect dry/constant cells and the
[standard-deviation safeguards](../reference/verbs/zscore.md).

## Reproduce

Install with `python -m pip install -e '.[vignettes]'` from a clone and run the
blocks in Jupyter. Requires live PRISM NcSS access; it is not part of offline
notebook certification. Record source/revision attributes, complete dates,
missingness and units. Do not replace unavailable observations with synthetic
values.

## See also

- [PRISM methods and QA](../datasets/prism.md)
- [zscore](../reference/verbs/zscore.md)
- [gridMET temperature variability](gridmet_variance_cube.md)
- [Offline observed-data notebooks](../vignettes/index.md)
