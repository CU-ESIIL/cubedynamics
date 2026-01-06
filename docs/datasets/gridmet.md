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

pipe(cube) | v.mean(dim="time") | v.plot()
```

### Preview plot

![gridMET preview](../assets/datasets/gridmet-preview.png)

!!! note
    Image placeholder — after running the code below locally, save a screenshot to `docs/assets/datasets/gridmet-preview.png`.

### Regenerate this plot

1. Run the Quickstart code block in a local Python session or notebook.
2. Capture the viewer returned by the pipe:

    ```python
    viewer = (pipe(cube) | v.mean(dim="time") | v.plot()).unwrap()
    viewer.save("docs/assets/datasets/gridmet-preview.html")
    ```

3. Open `docs/assets/datasets/gridmet-preview.html` in a browser and take a 1200×700 px PNG screenshot saved to `docs/assets/datasets/gridmet-preview.png`.

### Who collects it and why
The dataset is produced by John Abatzoglou and collaborators at the University of Idaho to support ecological, hydrological, and fire-weather applications across CONUS. It blends PRISM climatology with NLDAS reanalysis to provide spatially consistent daily meteorology widely used in ecological forecasting and climate impact studies.

### How CubeDynamics accesses it
`load_gridmet_cube` attempts a streaming backend first, opening yearly NetCDF files over HTTP and subsetting the requested area and time range before chunking into a VirtualCube-like Dask structure. When streaming is unavailable it falls back to a small cached download while preserving the same `(time, y, x)` interface. Users request AOIs by point, bounding box, or GeoJSON, enabling fast analysis without retrieving the full continental archive.

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
| vpd | Vapor pressure deficit | Pa |
| vs / erc | Wind speed / energy release component | m s⁻¹ / index |

### Citation
Abatzoglou, J. T. (2013). Development of gridded surface meteorological data for ecological applications. *International Journal of Climatology*, 33(1), 121–131. https://doi.org/10.1002/joc.3413

See also: [Fire event vase + climate merge (fire_plot)](../recipes/fire_event_vase_hull.md)

---
Back to [Datasets Overview](index.md)
Next recommended page: [Which dataset should I use?](which_dataset.md)
