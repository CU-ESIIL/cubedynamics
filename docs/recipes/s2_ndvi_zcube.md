# Sentinel-2 NDVI departures

Live-data recipe · optional satellite dependencies and provider access required.
No new satellite result is certified by this documentation refactor.

## Question

How does each pixel's NDVI vary relative to its own observed summer distribution?
This describes the selected acquisitions, not a long-term vegetation-health
baseline or a causal response to climate.

## Data used

[Sentinel-2 Level-2A](../library/sources/sentinel2.md) red (B04) and near-infrared
(B08) bands near 43.89°N, 102.18°W, June–September 2023. The
[surface-reflectance noun](../library/nouns/surface_reflectance.md) keeps the
source choice visible. Cloud filtering is not complete pixel-level quality
screening.

## Analysis

Follow [installation](../quickstart.md) and the
[satellite setup notes](../datasets/sentinel2_ndvi.md). Check acquisition dates,
cloud/missing-data patterns, scaling and source provenance.

```python
from cubedynamics import data, pipe, verbs as v
import matplotlib.pyplot as plt

s2 = data.surface_reflectance(
    source="sentinel2", variables=["B04", "B08"],
    lat=43.89, lon=-102.18,
    start="2023-06-01", end="2023-09-30",
    edge_size=128, resolution=10, cloud_lt=40,
)
print(s2.sizes, s2.attrs)
```

## Grammar / pipeline

```python
ndvi_z = (
    pipe(s2)
    | v.ndvi_from_s2(nir_band="B08", red_band="B04")
    | v.zscore(dim="time")
).unwrap()
```

## Plain-language interpretation

Derive NDVI from matched red/NIR bands, then standardize each pixel across
available acquisitions. Setup stays outside the analytical sentence. Inspect
calibration/offset handling in the source notes before treating the ratio as
scientifically comparable across products.

## Result

```python
ndvi_z.median(("y", "x")).plot()
plt.ylabel("Spatial median NDVI z-score (dimensionless)")
plt.title("Selected Sentinel-2 acquisitions · summer 2023")
plt.show()

# The canonical HTML viewer attaches to the pipe; display it in Jupyter.
from IPython.display import display
display(pipe(ndvi_z) | v.plot(title="Sentinel-2 NDVI departures"))
```

Cloud contamination, unequal sampling and constant pixels can dominate the
pattern. A low z-score is not by itself evidence of drought. The optional
[`show_cube_lexcube` helper and verb](../api/viz.md) use a separate optional
widget integration; this example uses the canonical HTML viewer.

## Reproduce

Install the repository and required satellite dependencies, then execute the
blocks in Jupyter with working STAC/asset access. Record item identities,
source/serving revision, query, valid acquisitions and QA decisions. This
live-data recipe is not an offline-tested notebook.

## See also

- [NDVI as a noun](../library/nouns/vegetation_index.md)
- [ndvi_from_s2](../reference/verbs/ndvi_from_s2.md) and [zscore](../reference/verbs/zscore.md)
- [Climate/NDVI alignment requirements](../examples/climate_ndvi_correlation.md)
- [Landsat example](../examples/landsat8_mpc.md)
