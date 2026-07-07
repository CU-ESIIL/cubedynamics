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

pipe(cube) | v.mean(dim="time") | v.plot()
```

### Customizing the view

```python
pipe(cube) | v.plot(camera={"eye": {"x": 2.2, "y": 1.6, "z": 1.3}})
```

### Preview plot

![PRISM preview](../assets/datasets/prism-preview.png)

!!! note
    Image placeholder — after running the code below locally, save a screenshot to `docs/assets/datasets/prism-preview.png`.

### Regenerate this plot

1. Execute the Quickstart snippet locally to build the precipitation cube.
2. Capture the CubePlot viewer for export:

    ```python
    viewer = (pipe(cube) | v.mean(dim="time") | v.plot()).unwrap()
    viewer.save("docs/assets/datasets/prism-preview.html")
    ```

3. Open `docs/assets/datasets/prism-preview.html` in a browser and save a 1200×700 px PNG screenshot to `docs/assets/datasets/prism-preview.png`.

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
