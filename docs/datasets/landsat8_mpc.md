# Landsat Collection 2 Level-2 from Microsoft Planetary Computer

`v.landsat_mpc` is a source verb for the MPC `landsat-c2-l2` collection.
It discovers STAC observations, signs asset URLs and uses stackstac to stream
remote cloud-optimized GeoTIFF windows lazily into a Dask-backed xarray
DataArray with dimensions `(time, band, y, x)`. Full scenes are not downloaded
up front. Discovery retrieves metadata; `.compute()` triggers imagery reads.

```python
from cubedynamics import pipe, verbs as v

cube = (
    pipe(None)
    | v.landsat_mpc(
        bbox=[-105.35, 39.90, -105.15, 40.10],
        start="2024-07-01",
        end="2024-09-01",
        bands=("red", "nir08"),
        max_cloud_cover=20,
        epsg=32613,
        resolution=30,
        chunksize=1024,
    )
)
da = cube.unwrap()
assert da.chunks is not None
red = da.sel(band="red")
nir = da.sel(band="nir08")
ndvi = (nir - red) / (nir + red)  # still lazy
small_ndvi = ndvi.isel(time=0, y=slice(300, 332), x=slice(250, 282)).compute()
```

Optical values are physical **surface reflectance**. Stackstac applies STAC
`raster:bands` scale/offset exactly once: **do not apply `* 0.0000275 - 0.2`
again**. Valid reflectance can fall outside 0–1. No NDVI or pixel-level cloud
mask is baked into the source. `max_cloud_cover` is a strict scene-level
percentage filter, not pixel-level cloud masking. For a pipe-based NDVI stage,
the existing configurable index helper works with these names:

```python
ndvi_pipe = pipe(da) | v.ndvi_from_s2(nir_band="nir08", red_band="red")
```

Use MPC asset keys: `blue`, `green`, `red`, `nir08`, `swir16`, `swir22`.
Landsat 8/9 also have `coastal`. `qa_pixel` and `qa_radsat` contain encoded
quality bits; `qa_aerosol` is specific to the Landsat 8/9 processing path.
Select QA assets explicitly to construct a scientifically appropriate mask.
They share the floating array dtype (with missing values); convert finite
values to integers before bit operations. Stackstac honors asset nodata
metadata. Do not treat QA values as reflectance. See the
[USGS QA definitions](https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands).

The collection includes Landsat 4–9. Common optical asset names avoid
mission-specific numbered-band mapping; this does not harmonize sensors or
QA semantics. Request `platforms=("landsat-8", "landsat-9")` to restrict
missions. Missing requested assets raise an error, including mission-specific
assets absent from older scenes. See the
[MPC collection history](https://planetarycomputer.microsoft.com/docs/changelogs/history).

The bbox is WGS84 lon/lat and is transformed using `bounds_latlon` into the
output CRS. Resolution is in output CRS units; 30 means meters for EPSG:32613.
That CRS is appropriate for Boulder, not a global default. With `epsg=None`,
the adapter uses only complete, unanimous item/asset `proj:epsg` or EPSG
`proj:code` metadata. Missing or mixed projection metadata requires explicit
`epsg=`. Output bounds snap outward to the resolution grid; coordinates label
the upper-left pixel corners. The output grid is rectangular, but scene edges,
missing observations and nodata can still leave empty pixels.

Direct invocation is `v.landsat_mpc(None, **options)`; calling without the input
creates a pipe stage. Core installation declares pystac-client,
planetary-computer and stackstac. Signed URLs expire: rebuild the source stage
for later remote computations. Chunk size controls Dask tasks, not a total IO
budget; STAC search materializes the item catalog.

`v.landsat8_mpc` and the existing visualization helpers remain compatibility
interfaces. The Landsat 8 stage retains `band_aliases=("red", "nir")`,
`chunks_xy={"x": 1024, "y": 1024}`, float32 output and the `nir` coordinate,
with a verified `platform="landsat-8"` filter. It now correctly returns scaled
reflectance and accepts `epsg=` and `resolution=`; provide EPSG if metadata
cannot infer it. No new deprecation warning is imposed. Visualization helpers
materialize data intentionally and also accept `epsg=`. Prefer the new source
stage for analysis and separate NDVI from visualization.

Run the bounded live Boulder check explicitly:

```bash
CUBEDYNAMICS_TEST_LANDSAT_MPC=1 python -m pytest tests/verbs/test_landsat_mpc.py -k boulder_live -q
```

The live test is marked `online`, `integration`, and `streaming`; normal offline
validation excludes it. It checks the projected bbox, lazy bands and NDVI,
small remote reads and plausible values without imposing 0–1 on every pixel.
