# Cloud Sources

CubeDynamics is designed to operate on cloud-hosted environmental data without turning cloud access into the central abstraction.

The goal is not to make users think in terms of provider-specific plumbing.

The goal is to make this stable:

```python
cube = load_data(...)
result = pipe(cube) | some_verb()
```

## Why Cloud Matters

Cloud-hosted archives make it possible to:

- avoid managing massive local datasets
- move from notebook experiments to larger workflows
- orchestrate the same computation in automated systems

## Role In CubeDynamics

Cloud access is part of the streaming interface, not the whole product.

CubeDynamics sits above the storage and retrieval layer and focuses on consistent environmental computation once data enters the cube interface.

## Global Climate Cubes

For global climate archives, the preferred generic path is to open the remote
dataset with xarray and pass the lazy object to `stream_global_climate_cube`.

```python
import xarray as xr
import cubedynamics as cd

source = xr.open_zarr("s3://example-bucket/terraclimate.zarr", chunks={"time": 12})

cube = cd.stream_global_climate_cube(
    source,
    variables=["tmax", "tmin"],
    bbox=[-105.5, 39.8, -105.0, 40.2],
    source_name="terraclimate_zarr",
)
```

The adapter does not download, cache, or authenticate on behalf of the caller.
It normalizes dimensions to `(time, y, x)`, applies an optional AOI slice, and
keeps the original lazy chunks intact for downstream verbs.

## Related Reading

- [Streaming Environmental Data](index.md)
- [Datasets](../datasets/index.md)
