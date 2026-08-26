# Surface observation nouns

Phase 1 preserves the existing Sentinel-2 integration while giving it
scientific names.

## Surface reflectance

```python
from cubedynamics import data, pipe, verbs as v

reflectance = data.surface_reflectance(
    source="sentinel2",
    lat=40.0,
    lon=-105.25,
    start="2024-06-01",
    end="2024-06-10",
    variables=["B02", "B03", "B04", "B08"],
)

result = pipe(reflectance) | v.mean(dim="time") | v.plot()
```

The result remains Dask-backed. `cubo` performs the STAC search and reads the
cloud-hosted assets lazily. The source product is Sentinel-2 Level-2A. Native
band resolutions are 10, 20, or 60 m; the current CubeDynamics default requests
10 m output. Band definitions and resolutions follow the [Copernicus Sentinel-2
L2A documentation](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html).

Scene-level cloud filtering is not pixel-level cloud masking. A low reported
scene cloud percentage does not guarantee that every returned pixel is clear.

## Vegetation index

```python
ndvi = data.vegetation_index(
    source="sentinel2",
    index="ndvi",
    lat=40.0,
    lon=-105.25,
    start="2024-06-01",
    end="2024-06-10",
)

anomaly = pipe(ndvi) | v.anomaly(dim="time")
```

This noun is explicitly derived. Provenance records B08 and B04 plus the NDVI
formula, and `data_state="derived"` distinguishes it from raw reflectance.
NDVI represents a normalized red/NIR contrast. It is not a direct measurement
of biomass, vegetation type, or ecological condition.

## Current boundary

Only Sentinel-2 is registered. HLS, Landsat, MODIS, VIIRS, ECOSTRESS, GEDI,
NAIP, and NEON AOP remain later-phase work until each has bounded real-data
tests, numerical checks, reviewed figures, provenance, and source-choice docs.

