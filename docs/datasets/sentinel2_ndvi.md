# Sentinel-2 NDVI

### What this dataset is
The Sentinel-2 Level-2A constellation provides multispectral surface reflectance at 10–60 m resolution with a ~5-day revisit time over global land masses. CubeDynamics derives the Normalized Difference Vegetation Index (NDVI) from the red (B04) and near-infrared (B08) bands at 10 m resolution, producing a `(time, y, x)` vegetation cube over the requested window.

## Quickstart

### Get the stream (CubeDynamics grammar)

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2023-06-01",
    end="2023-07-01",
)

pipe(cube) | v.mean(dim="time") | v.plot()
```

### Preview plot

![Sentinel-2 NDVI preview](../assets/datasets/sentinel2_ndvi-preview.png)

!!! note
    Image placeholder — after running the code below locally, save a screenshot to `docs/assets/datasets/sentinel2_ndvi-preview.png`.

### Regenerate this plot

1. Execute the Quickstart snippet to stream a month of NDVI over the example location.
2. Capture the CubePlot from the pipeline:

    ```python
    viewer = (pipe(cube) | v.mean(dim="time") | v.plot()).unwrap()
    viewer.save("docs/assets/datasets/sentinel2_ndvi-preview.html")
    ```

3. Open `docs/assets/datasets/sentinel2_ndvi-preview.html` in a browser and save a 1200×700 px PNG screenshot to `docs/assets/datasets/sentinel2_ndvi-preview.png`.

### Who collects it and why
The European Space Agency (ESA) and the European Commission operate Sentinel-2 to deliver routine optical imagery for land monitoring, vegetation status, and disaster response. The atmospherically corrected Level-2A product is widely used for vegetation phenology and ecosystem monitoring, making it an authoritative source for NDVI analyses.

### How CubeDynamics accesses it
Sentinel-2 scenes are streamed remotely through the `cubo` API, which signs and reads cloud-optimized GeoTIFF assets without downloading entire archives. NDVI is computed on-the-fly from the requested bands, and the resulting cube remains lazily evaluated so downstream verbs trigger IO only as needed. Long requests can be chunked temporally to avoid large STAC queries while preserving the VirtualCube-style streaming behavior.

### Important variables and dimensions
| Field | Meaning | Units |
|-----|--------|------|
| time | Observation timestamp | ISO date |
| y / x | Spatial coordinates in the native UTM projection | meters |
| NDVI | (NIR − Red) / (NIR + Red) vegetation index | unitless |
| band (optional, when returning raw bands) | Reflectance bands such as B04 (red) and B08 (NIR) | unitless reflectance |

### Source documentation

See the [Copernicus Sentinel-2 mission](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2)
and [Level-2A band documentation](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html).
The previous MODIS citation on this page described a different sensor and
product and has been removed.

---
Back to [Datasets Overview](index.md)  
Next recommended page: [Which dataset should I use?](which_dataset.md)
