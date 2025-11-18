# CubeDynamics

A streaming-first climate cube math library.

## What it Does

- **Streaming climate data ingestion** for PRISM, gridMET, NDVI, and other gridded products.
- **Multi-dimensional correlation/variance analysis** that works on any `xarray` cube.
- **Climate-to-ecological synchrony workflows** powered by anomaly, trend, and synchrony verbs.
- **ggplot-style pipe syntax** so you can express workflows like `pipe(cube) | anomaly() | variance()` with readable intent.

## Example

```python
import cubedynamics as cd
import xarray as xr

# Example cube (placeholder)
cube = xr.DataArray(
    [1, 2, 3, 4, 5, 6],
    dims=["time"],
)

result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.month_filter([6])
    | cd.variance(dim="time")
).unwrap()

print(result)
```

## Getting Started

Read the [Getting Started guide](getting_started.md) for installation commands, dependency notes, and tips for loading streamed cubes.

## Concepts

- **Cubes** – `xarray.DataArray` or `xarray.Dataset` objects that hold climate variables over shared spatial/temporal axes.
- **Verbs** – functions such as `anomaly`, `month_filter`, or `variance` that transform cubes and can be chained in a pipe.
- **Pipes** – chaining syntax using `|` to build declarative workflows: `cd.pipe(cube) | cd.anomaly(dim="time") | cd.to_netcdf("out.nc")`.

Dive into the rest of the documentation to explore streaming adapters, write custom verbs, and build advanced CubeDynamics pipelines.
