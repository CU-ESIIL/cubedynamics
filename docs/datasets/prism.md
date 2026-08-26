# PRISM

### What this dataset is
PRISM (Parameter-elevation Regressions on Independent Slopes Model) provides gridded precipitation and temperature analyses for the United States at approximately 4 km resolution. Monthly and daily fields span the late 20th century to present on a regular latitude–longitude grid, capturing fine-scale orographic effects.

## Quickstart

### Get the stream (CubeDynamics grammar)

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    variable="ppt",
    start="2020-01-01",
    end="2020-02-01",
    bbox=[-105.4, 39.8, -105.0, 40.2],
    freq="D",
)

pipe(cube) | v.mean(over="time") | v.plot()
```

### Customizing the view

```python
pipe(cube) | v.plot(camera={"eye": {"x": 2.2, "y": 1.6, "z": 1.3}})
```

### Reviewed source-QA plot

![PRISM minimum-temperature source QA with a spatial map and temporal summary](../assets/source_qa/prism_temperature.png)

This is a checked-in rendering of a real, checksum-controlled PRISM extract,
not synthetic example data. The accompanying QA checks provenance, CRS, time
ordering, finite coverage, physical temperature bounds, minimum/maximum
consistency, and overlap with the requested area of interest.

### Reproduce the validation

Run the publication QA workflow from the repository root:

```bash
python scripts/run_source_qa.py
```

The command writes the figure and a machine-readable result to
`artifacts/source_qa/`. See the [Phase 1 source-QA report](../data/phase1_qa.md)
for the exact checks, evidence, and current limitations.

### Who collects it and why
The PRISM Climate Group at Oregon State University produces the dataset to deliver high-quality, terrain-aware climate normals and time series. It is widely used for hydrology, ecology, and agricultural studies where spatial detail and long-term consistency are critical.

### How CubeDynamics accesses it
`load_prism_cube` streams daily data through the NCSCO THREDDS NetCDF Subset Service. The server crops each daily PRISM grid to the requested AOI, and Dask defers those requests until computation. AOIs can be expressed as point buffers, bounding boxes, or GeoJSON, avoiding full-CONUS archive downloads. Default time chunks are bounded at 31 days so a small computation does not pull the complete record. Synthetic fallback is available only when explicitly enabled with `allow_synthetic=True`.

!!! important "Temporal frequency and safety"
    - The real NcSS backend currently requires daily `freq="D"`. Aggregate the lazy daily cube downstream when monthly values are needed.
    - Keep `allow_synthetic=False` (default) for science use. When `True`, synthetic data are generated and flagged with provenance (`source`, `is_synthetic`, `backend_error`, `freq`, `requested_start`, `requested_end`).

### Important variables and dimensions
| Field | Meaning | Units |
|-----|--------|------|
| time | Observation timestamp | ISO date |
| y / x (lat / lon) | Grid cell centers in geographic coordinates | degrees |
| ppt | Precipitation | mm (monthly totals or daily amounts) |
| tmax / tmin / tdmean | Maximum / minimum / dew-point temperature | °C |

### Citation
Daly, C., Halbleib, M., Smith, J. I., Gibson, W. P., Doggett, M. K., Taylor, G. H., Curtis, J., & Pasteris, P. P. (2008). Physiographically sensitive mapping of climatological temperature and precipitation across the conterminous United States. *International Journal of Climatology*, 28(15), 2031–2064. https://doi.org/10.1002/joc.1688

---
Back to [Datasets Overview](index.md)  
Next recommended page: [Which dataset should I use?](which_dataset.md)
