# Relating climate and NDVI

Method guide · this is not an executed cross-source correlation result.

## Question

Do vegetation departures covary with a climate variable over a chosen study
period? This question requires comparable spatial support and temporal sampling;
loading two cubes is not enough.

## Data used

Choose a climate noun such as [temperature](../library/nouns/temperature.md) or
[precipitation](../library/nouns/precipitation.md), and the
[vegetation-index noun](../library/nouns/vegetation_index.md). Record each source,
CRS, units, acquisition dates, pixel support and quality decisions.

## Grammar / pipeline

Prepare each field separately, then compare them only after explicitly aligning
their observational support. There is no implemented `v.correlation_cube`
verb; see its [availability note](../reference/verbs/correlation_cube.md).

## Plain-language interpretation

A climate grid cell and a satellite pixel do not represent the same area.
Likewise, a daily climate total and an irregular cloud-filtered acquisition do
not represent the same time interval. Standardizing values does not resolve
either mismatch.

## Analysis

1. Choose a target CRS and grid. Reproject/resample explicitly with a method
   appropriate to the quantity; [align_cube](../reference/verbs/align_cube.md)
   is not a general-purpose reprojection engine.
2. Define the temporal support (for example, an antecedent precipitation window
   for each valid satellite acquisition). Avoid inventing observations across
   cloud gaps.
3. Apply quality masks, require enough paired observations and record valid
   counts. Check dimensions, coordinates and CRS before comparison.
4. On already harmonized xarray inputs, `xr.align(left, right, join="exact")`
   can reject mismatched indexes; `xr.corr(left, right, dim="time")` computes
   Pearson correlation. Neither establishes scientific comparability for you.
5. Plot correlation alongside paired counts, and assess sensitivity to window,
   aggregation, seasonality and autocorrelation.

## Result

No cross-source result is presented on this page. Correlation is descriptive,
not evidence of a causal vegetation response. A reproducible analysis must
supply the alignment, quality control and paired-count diagnostics above.

## Reproduce

Begin with the [PRISM recipe](../recipes/prism_variance_cube.md) and
[Sentinel-2 recipe](../recipes/s2_ndvi_zcube.md). Both require live access.
This method guide is not a turnkey notebook and is not certified by the offline
vignette runner.

## See also

- [State and event synchrony notebook](../vignettes/states_and_events.ipynb)
- [Source compatibility](../datasets/compatibility.md)
- [Spatial data contract](../design/spatial_dataset_contract.md)
