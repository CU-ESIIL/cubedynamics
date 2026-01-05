# gridMET

### What this dataset is
gridMET is a gridded surface meteorology product for the contiguous United States at ~4 km (1/24°) resolution with daily observations back to 1979. Variables include precipitation, maximum/minimum temperature, humidity, vapor pressure deficit, and wind, arranged on a regular latitude–longitude grid.

### Who collects it and why
The dataset is produced by John Abatzoglou and collaborators at the University of Idaho to support ecological, hydrological, and fire-weather applications across CONUS. It blends PRISM climatology with NLDAS reanalysis to provide spatially consistent daily meteorology widely used in ecological forecasting and climate impact studies.

### How Climate Cube Math accesses it
`load_gridmet_cube` attempts a streaming backend first, opening yearly NetCDF files over HTTP and subsetting the requested area and time range before chunking into a VirtualCube-like Dask structure. When streaming is unavailable it falls back to a small cached download while preserving the same `(time, y, x)` interface. Users request AOIs by point, bounding box, or GeoJSON, enabling fast analysis without retrieving the full continental archive.

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

---
Back to [Datasets Overview](index.md)  
Next recommended page: [Which dataset should I use?](which_dataset.md)
