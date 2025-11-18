# CubeDynamics: Climate Cube Math

CubeDynamics (`cubedynamics`) is a streaming-first library for assembling
multi-source climate cubes (PRISM, gridMET, Sentinel-derived NDVI, etc.) and
computing correlations, variance, synchrony, and trends without bulk
downloads.

## What is CubeDynamics?

CubeDynamics packages a set of composable `xarray`-based helpers that turn
streamed imagery and gridded climate products into **lexcubes**: structured
space-time cubes filled with statistics that summarize variability, anomalies,
and cross-sensor relationships. The package is purpose-built for environmental
researchers who need to analyze climate dynamics on laptops, clusters, or cloud
workflows without mirroring entire archives.

## Key capabilities

- Streaming adapters for PRISM, gridMET, and Sentinel data services
- Cube math primitives for anomalies, z-scores, variance, rolling correlation,
  and tail dependence
- Lexcube generators for comparing NDVI synchrony with precipitation or
  temperature drivers
- Built-in hooks for exporting to NetCDF/Zarr and visual QA plots
- Notebook-friendly APIs that run the same in batch pipelines

## Quickstart

```python
import cubedynamics as cd

# Stream a gridMET precipitation cube and compute a variance lexcube
cube = cd.stream_gridmet_to_cube(
    aoi_geojson,
    variable="pr",
    dates=("2000-01", "2020-12"),
)
var_cube = cd.variance_cube(cube)
var_cube.to_netcdf("gridmet_variance.nc")
```

See the [Getting Started](getting_started.md) page for environment setup,
streaming credentials, and notebook tips.

## Use cases

- **PRISM variance cubes** for drought monitoring and precipitation anomaly
  mapping.
- **NDVI synchrony analysis** by correlating vegetation z-score cubes with
  weather drivers or anchor pixels.
- **Climate-to-population pipelines** where lexcubes feed resilience, fire, or
  ecosystem models without full-scene downloads.
- **Lexcube dashboards** that render CubeDynamics outputs in lightweight
  notebooks or web visualizations.

## Learn more

The navigation links cover concepts, API details, and recipes. Head over to the
[Concepts overview](concepts.md) to understand the architecture or explore the
[API & Examples](climate_cubes.md) section for concrete workflows.
