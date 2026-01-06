# PRISM

### What this dataset is
PRISM (Parameter-elevation Regressions on Independent Slopes Model) provides gridded precipitation and temperature analyses for the United States at approximately 4 km resolution. Monthly and daily fields span the late 20th century to present on a regular latitude–longitude grid, capturing fine-scale orographic effects.

## Quickstart

### Get the stream (CubeDynamics grammar)

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    variables=["ppt"],
    start="2020-01-01",
    end="2020-02-01",
    aoi={"min_lat": 39.8, "max_lat": 40.2, "min_lon": -105.4, "max_lon": -105.0},
)

pipe(cube["ppt"]) | v.mean(dim="time") | v.plot()
```

### Preview plot

![PRISM preview](../assets/datasets/prism-preview.png)

!!! note
    Image placeholder — after running the code below locally, save a screenshot to `docs/assets/datasets/prism-preview.png`.

### Regenerate this plot

1. Execute the Quickstart snippet locally to build the precipitation cube.
2. Capture the CubePlot viewer for export:

    ```python
    viewer = (pipe(cube["ppt"]) | v.mean(dim="time") | v.plot()).unwrap()
    viewer.save("docs/assets/datasets/prism-preview.html")
    ```

3. Open `docs/assets/datasets/prism-preview.html` in a browser and save a 1200×700 px PNG screenshot to `docs/assets/datasets/prism-preview.png`.

### Who collects it and why
The PRISM Climate Group at Oregon State University produces the dataset to deliver high-quality, terrain-aware climate normals and time series. It is widely used for hydrology, ecology, and agricultural studies where spatial detail and long-term consistency are critical.

### How CubeDynamics accesses it
`load_prism_cube` mirrors the gridMET contract: it first attempts remote streaming, cropping the requested AOI and resampling to the desired temporal frequency, then chunks the result for lazy evaluation. If the streaming backend is unavailable, it falls back to a small synthetic download while preserving coordinate metadata. AOIs can be expressed as point buffers, bounding boxes, or GeoJSON, enabling rapid exploratory analyses without full archive downloads.

!!! important "Temporal frequency and safety"
    - Daily (`freq="D"`) is preferred for event-scale analyses; monthly end (`"ME"`) windows over a few days can yield zero timestamps.
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
