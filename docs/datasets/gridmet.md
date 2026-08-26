# gridMET

### What this dataset is
gridMET is a gridded surface meteorology product for the contiguous United States at ~4 km (1/24°) resolution with daily observations back to 1979. Variables include precipitation, maximum/minimum temperature, humidity, vapor pressure deficit, and wind, arranged on a regular latitude–longitude grid.

## Quickstart

### Get the stream (CubeDynamics grammar)

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.gridmet(
    lat=40.0,
    lon=-105.25,
    start="2020-06-01",
    end="2020-06-30",
    variable="tmmx",
)

pipe(cube) | v.mean(over="time") | v.plot()
```

### Preview plot

![Reviewed gridMET source QA with a temperature map and AOI-mean time series](../assets/source_qa/gridmet_temperature.png)

This is a checksum-controlled observational gridMET extract over southwestern
South Dakota. It shows one daily maximum-temperature map and the ten-day
AOI-mean series; it is validation evidence rather than a decorative thumbnail.

### Regenerate this plot

1. Rebuild the small observational fixtures when source review is required:

    ```python
    python scripts/build_phase1_qa_fixtures.py
    ```

2. Run `python scripts/run_source_qa.py`. The offline workflow checks the
   fixture checksum, source and CRS, dates, bounds, coordinate orientation,
   grid resolution, missingness, and broad physical temperature range.

See the complete [Phase 1 source QA report](../data/phase1_qa.md).

### Who collects it and why
The dataset is produced by John Abatzoglou and collaborators at the University of Idaho to support ecological, hydrological, and fire-weather applications across CONUS. It blends PRISM climatology with NLDAS reanalysis to provide spatially consistent daily meteorology widely used in ecological forecasting and climate impact studies.

### How CubeDynamics accesses it
`load_gridmet_cube` reads authoritative annual NetCDF assets and exposes the
requested area and time window as a Dask-backed `(time, y, x)` object. It does
not silently create a cached or generated substitute. The current annual-file
retrieval is a documented Phase 1 efficiency limitation; the noun-first API is
`data.temperature(source="gridmet", ...)` and related climate nouns.

!!! important "Temporal frequency and safety"
    - Daily (`freq="D"`) is recommended for fire/event windows. Monthly start (`"MS"`) requests over short ranges can produce an empty time axis; the loader now raises with guidance instead of silently returning NaNs.
    - Set `allow_synthetic=False` (default) to require real data. When `True`, the loader fabricates data and records provenance (`source`, `is_synthetic`, `backend_error`, `freq`, `requested_start`, `requested_end`).

### Important variables and dimensions
| Field | Meaning | Units |
|-----|--------|------|
| time | Daily observation timestamp | ISO date |
| y / x (lat / lon) | Grid cell centers in geographic coordinates | degrees |
| pr | Precipitation | mm day⁻¹ |
| tmmx / tmmn | Daily maximum / minimum temperature | K |
| vpd | Vapor pressure deficit | kPa |
| vs / erc | Wind speed / energy release component | m s⁻¹ / index |

### Citation
Abatzoglou, J. T. (2013). Development of gridded surface meteorological data for ecological applications. *International Journal of Climatology*, 33(1), 121–131. https://doi.org/10.1002/joc.3413

See also: [Fire event vase + climate merge (fire_plot)](../recipes/fire_event_vase_hull.md)

---
Back to [Datasets Overview](index.md)
Next recommended page: [Which dataset should I use?](which_dataset.md)
