# Climate & weather nouns

The same noun can have more than one scientifically defensible source flavor.
That choice affects coverage, resolution, methods, and revision policy, but it
does not change the CubeDynamics grammar.

## Temperature

```python
from cubedynamics import data, pipe, verbs as v

temperature = data.temperature(
    source="gridmet",
    statistic="maximum",
    bbox=[-105.75, 39.50, -104.75, 40.50],
    start="2024-01-01",
    end="2024-01-30",
)

result = pipe(temperature) | v.anomaly(dim="time") | v.plot()
```

`statistic` is explicit. gridMET publishes daily maximum and minimum
temperature, but not a native daily mean field; CubeDynamics will not silently
derive a mean during loading. PRISM supports `maximum`, `minimum`, and `mean`.

| Source | Coverage | Resolution | Time | Native temperature fields | Best when |
| --- | --- | --- | --- | --- | --- |
| gridMET | CONUS | 4,638.3 m | daily, 1979–present | `tmmx`, `tmmn` | a broad daily meteorological vocabulary and ecological/fire applications matter |
| PRISM | CONUS | approximately 4 km | daily, 1981–present | `tmax`, `tmin`, `tmean` | terrain-aware station interpolation and PRISM methodology matter |

gridMET metadata follow the [provider record in the Earth Engine data
catalog](https://developers.google.com/earth-engine/datasets/catalog/IDAHO_EPSCOR_GRIDMET).
PRISM coverage, variables, units, and revision behavior follow the [PRISM
dataset documentation](https://www.prism.oregonstate.edu/documents/PRISM_datasets.pdf)
and [data portal](https://prism.oregonstate.edu/data/).

## Precipitation

```python
rain = data.precipitation(
    source="prism",
    bbox=[-105.75, 39.50, -104.75, 40.50],
    start="2024-05-01",
    end="2024-05-31",
)

monthly_total = pipe(rain) | v.apply(lambda cube: cube.sum("time"))
```

Both flavors return a `precipitation` DataArray while preserving `pr` or `ppt`
as the original source variable in provenance. Values are daily amounts in
millimeters. Summing is analysis, so it remains a verb rather than hidden
inside the loader.

## Other implemented gridMET nouns

| Noun | Source field | Meaning | Units | Important limitation |
| --- | --- | --- | --- | --- |
| `vpd` | `vpd` | mean vapor-pressure deficit | kPa | not interchangeable with PRISM daily minimum/maximum VPD |
| `wind` | `vs` | 10 m wind velocity | m s⁻¹ | not gust speed |
| `humidity(statistic="maximum")` | `rmax` | maximum relative humidity | % | choose `maximum` or `minimum` explicitly |
| `radiation` | `srad` | surface downward shortwave radiation | W m⁻² | not net radiation |

## Streaming behavior

- PRISM production requests use daily server-side AOI subsets through the
  NCSCO THREDDS NetCDF Subset Service; Dask defers daily reads.
- The current gridMET driver reads authoritative annual NetCDF assets, then
  exposes the requested AOI/time window with Dask chunks. This is real data,
  but it is less network-efficient than server-side subsetting and is recorded
  as a Phase 1 limitation.
- Scientific noun functions force `allow_synthetic=False`. A source outage is
  an error, never an invitation to fabricate measurements.

## Limitations

Recent gridMET and PRISM products can be revised. The source flavor remains a
scientific choice. CubeDynamics does not automatically harmonize provider
methods, temperature units, or grids in Phase 1; those transformations belong
in explicit verbs.

