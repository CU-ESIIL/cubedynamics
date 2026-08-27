# sentinel2 · methods and QA examples

Provider, product, coverage, units and source status have one canonical home:
[sentinel2 source reference](../library/sources/sentinel2.md).
This page preserves the operational example, reviewed figure and source citations.

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

pipe(cube) | v.mean(over="time") | v.plot()
```

### Preview plot

![Reviewed Sentinel-2 red, near-infrared, and NDVI source QA](../assets/source_qa/sentinel2_reflectance.png)

This reviewed observational extract shows the B04 red band, B08
near-infrared band, and the NDVI derived from them over a 640 m South Dakota
window. The panels make orientation, spatial detail, value scale, and the
index transformation inspectable.

### Regenerate this plot

1. Rebuild the small observational fixtures when source review is required:

    ```python
    python scripts/build_phase1_qa_fixtures.py
    ```

2. Run `python scripts/run_source_qa.py`. The offline workflow checks the
   checksum, source, CRS, bands, unique ordered acquisitions, 10 m grid,
   coordinate orientation, missingness, reflectance scale, and NDVI bounds.

See the complete [Phase 1 source QA report](../data/phase1_qa.md).


### Source documentation

See the [Copernicus Sentinel-2 mission](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2)
and [Level-2A band documentation](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html).
The previous MODIS citation on this page described a different sensor and
product and has been removed.

---
Back to [Datasets Overview](index.md)  
Next recommended page: [Which dataset should I use?](which_dataset.md)
