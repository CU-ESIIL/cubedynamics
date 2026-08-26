# Scientific data vocabulary

CubeDynamics data access begins with the scientific thing you need, not the
agency endpoint that stores it:

```python
from cubedynamics import data, pipe, verbs as v

temperature = data.temperature(
    source="prism",
    statistic="maximum",
    bbox=[-105.75, 39.50, -104.75, 40.50],
    start="2024-01-01",
    end="2024-01-30",
)

result = pipe(temperature) | v.anomaly(dim="time")
```

`data.temperature(...)` answers *what enters the analysis*. The pipe answers
*what happens next*. Selecting gridMET instead changes the source flavor, not
the analytical sentence.

## Implemented Phase 1 nouns

| Family | Scientific noun | Source flavors |
| --- | --- | --- |
| Climate & weather | `temperature` | `gridmet`, `prism` |
| Climate & weather | `precipitation` | `gridmet`, `prism` |
| Climate & weather | `vpd` | `gridmet` |
| Climate & weather | `wind` | `gridmet` |
| Climate & weather | `humidity` | `gridmet` |
| Climate & weather | `radiation` | `gridmet` |
| Surface observation | `surface_reflectance` | `sentinel2` |
| Vegetation | `vegetation_index` | `sentinel2` |

These are the integrations that exist now. Daymet, ERA5, TerraClimate, HLS,
Landsat, MODIS, water, terrain, feature, infrastructure, and exposure nouns are
planned phases—not aliases for unimplemented work.

## Discover sources without learning backends

```python
data.sources("temperature")
# ('gridmet', 'prism')

data.describe("temperature", source="prism")
```

The description includes provider, product, source variables, coverage,
resolution, access mechanism, and limitations. Every returned cube also
records this information in attributes, including the original source field,
query, CRS, retrieval time, normalization, and whether the result is raw,
normalized, or derived.

## Source-specific loaders remain available

Existing `load_gridmet_cube`, `load_prism_cube`, `load_s2_cube`, and
`load_s2_ndvi_cube` imports remain supported. Use them when the provider product
itself is part of the research question. New user-facing lessons should prefer
scientific nouns.

## Read next

- [Climate & weather nouns](climate_weather.md)
- [Surface observation nouns](surface_observation.md)
- [Phase 1 source QA](phase1_qa.md)
- [Pipe and verbs](../concepts/pipe_and_verbs.md)

