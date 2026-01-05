# Datasets

*Spatiotemporal data sources supported by Climate Cube Math*

Climate Cube Math does not invent new datasets. It provides fast, structured, spatiotemporal access to authoritative environmental datasets commonly used in climate, ecology, and Earth system science. Datasets are accessed lazily whenever possible, cubes may be streamed rather than fully downloaded, and the cube abstraction preserves the scientific meaning of coordinates, units, and provenance.

## Sentinel-2 NDVI

### What this dataset is
The Sentinel-2 Level-2A constellation provides multispectral surface reflectance at 10–60 m resolution with a ~5-day revisit time over global land masses. Climate Cube Math derives the Normalized Difference Vegetation Index (NDVI) from the red (B04) and near-infrared (B08) bands at 10 m resolution, producing a `(time, y, x)` vegetation cube over the requested window.

### Who collects it and why
The European Space Agency (ESA) and the European Commission operate Sentinel-2 to deliver routine optical imagery for land monitoring, vegetation status, and disaster response. The atmospherically corrected Level-2A product is widely used for vegetation phenology and ecosystem monitoring, making it an authoritative source for NDVI analyses.

### How Climate Cube Math accesses it
Sentinel-2 scenes are streamed remotely through the `cubo` API, which signs and reads cloud-optimized GeoTIFF assets without downloading entire archives. NDVI is computed on-the-fly from the requested bands, and the resulting cube remains lazily evaluated so downstream verbs trigger IO only as needed. Long requests can be chunked temporally to avoid large STAC queries while preserving the VirtualCube-style streaming behavior.

### Important variables and dimensions
| Field | Meaning | Units |
|-----|--------|------|
| time | Observation timestamp | ISO date |
| y / x | Spatial coordinates in the native UTM projection | meters |
| NDVI | (NIR − Red) / (NIR + Red) vegetation index | unitless |
| band (optional, when returning raw bands) | Reflectance bands such as B04 (red) and B08 (NIR) | unitless reflectance |

### Citation
Didan, K. (2015). *MOD13Q1 MODIS/Terra Vegetation Indices (Version 6)*. NASA EOSDIS Land Processes DAAC. https://doi.org/10.5067/MODIS/MOD13Q1.006

## gridMET

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

## PRISM

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

## Landsat 8 (Microsoft Planetary Computer)

### What this dataset is
Landsat 8 Collection 2 Level-2 surface reflectance provides 30 m multispectral observations with a 16-day revisit cycle, covering global land surfaces. Climate Cube Math streams red and near-infrared bands to build `(time, band, y, x)` cubes suitable for NDVI and other spectral analyses.

### Who collects it and why
Landsat is jointly managed by the U.S. Geological Survey (USGS) and NASA to provide a continuous, medium-resolution record of Earth’s surface for land-cover change, vegetation health, and disaster monitoring. The consistent calibration and long temporal record make it a cornerstone for ecological and climate applications.

### How Climate Cube Math accesses it
The `landsat8_mpc_stream` helper queries the Microsoft Planetary Computer STAC API, signs cloud-optimized GeoTIFF assets, and opens them lazily with dask-backed raster readers. Scenes are stacked along time without downloading full scenes locally, so analyses such as NDVI operate on streamed tiles and only touch the requested AOI.

### Important variables and dimensions
| Field | Meaning | Units |
|-----|--------|------|
| time | Acquisition timestamp | ISO date |
| y / x | Spatial coordinates in the source CRS (projected meters) | meters |
| band | Spectral band labels (e.g., red, nir) | reflectance |
| SR_B4 / SR_B5 | Surface reflectance in the red / near-infrared | unitless reflectance |
| NDVI (derived) | (NIR − Red) / (NIR + Red) | unitless |

### Citation
USGS. (2020). *Landsat 8 Collection 2 (Level-2) Science Product User Guide* (LSDS-1618). U.S. Geological Survey and NASA. https://www.usgs.gov/landsat-missions/landsat-collection-2

## FIRED (Fire Event Reconstruction and Discussion)

### What this dataset is
FIRED provides event-level and per-day fire perimeter polygons for the conterminous United States and Alaska from November 2001 to March 2021. Daily footprints track fire growth through time, while event tables summarize ignition, containment, and size.

### Who collects it and why
FIRED was assembled by Balch, Iglesias, and collaborators to provide a consistent, research-grade record of wildland fire events for studying drivers, impacts, and fire–climate interactions. Its coverage and methodological transparency make it a common reference for fire science in North America.

### How Climate Cube Math accesses it
FIRED layers are pulled from a CU Scholar ZIP archive, extracted on-the-fly, and cached locally in a user directory. Functions load the requested layer (events or daily perimeters), reproject to EPSG:4326, and return GeoDataFrames ready to intersect with climate cubes. Users can opt into automatic downloads or rely on pre-populated cache files for offline analysis.

### Important variables and dimensions
| Field | Meaning | Units |
|-----|--------|------|
| id | FIRED event identifier | unitless |
| date | Observation date for daily perimeters | ISO date |
| geometry | Polygon footprint in EPSG:4326 | degrees |
| area_ha (if present) | Burned area for the polygon | hectares |

### Citation
Balch, J. K., Iglesias, V., Braswell, A., Rossi, M. W., Joseph, M. B., Mahood, A., Arkle, R. S., & Boer, M. M. (2020). FIRED: A global fire event database. *Scientific Data*, 7, 164. https://doi.org/10.1038/s41597-020-0524-5
