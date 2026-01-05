# PRISM

### What this dataset is
PRISM (Parameter-elevation Regressions on Independent Slopes Model) provides gridded precipitation and temperature analyses for the United States at approximately 4 km resolution. Monthly and daily fields span the late 20th century to present on a regular latitude–longitude grid, capturing fine-scale orographic effects.

### Who collects it and why
The PRISM Climate Group at Oregon State University produces the dataset to deliver high-quality, terrain-aware climate normals and time series. It is widely used for hydrology, ecology, and agricultural studies where spatial detail and long-term consistency are critical.

### How Climate Cube Math accesses it
`load_prism_cube` mirrors the gridMET contract: it first attempts remote streaming, cropping the requested AOI and resampling to the desired temporal frequency, then chunks the result for lazy evaluation. If the streaming backend is unavailable, it falls back to a small synthetic download while preserving coordinate metadata. AOIs can be expressed as point buffers, bounding boxes, or GeoJSON, enabling rapid exploratory analyses without full archive downloads.

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
