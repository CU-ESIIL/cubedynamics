# Sentinel-2 NDVI

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

---
Back to [Datasets Overview](index.md)  
Next recommended page: [Which dataset should I use?](which_dataset.md)
