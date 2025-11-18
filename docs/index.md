# CubeDynamics

Streaming-first climate cube math with ggplot-style piping.

## Why CubeDynamics?

- **Streaming climate cubes** assembled from PRISM, gridMET, NDVI, and other archives without local mirroring.
- **Pipe-based math** so you can write `cd.pipe(cube) | cd.anomaly() | cd.variance()` and get reproducible workflows.
- **Focused verbs under `cubedynamics.ops`** covering transforms, stats, and IO helpers for on-disk storage.

## Quickstart in a Jupyter notebook

Open a fresh notebook, install CubeDynamics from GitHub, and run the following:

1. Install CubeDynamics from GitHub (terminal or notebook cell):

   ```bash
   pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
   ```

2. Create a tiny in-memory cube and run a pipe chain:

   ```python
   import numpy as np
   import xarray as xr
   import cubedynamics as cd
   
   time = np.arange(6)
   values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
   
   cube = xr.DataArray(
       values,
       dims=["time"],
       coords={"time": time},
       name="example_variable",
   )
   
   result = (
       cd.pipe(cube)
       | cd.anomaly(dim="time")
       | cd.variance(dim="time")
   ).unwrap()
   
   result
   ```

This notebook-safe workflow only depends on `numpy`, `xarray`, and `cubedynamics`. More advanced examples—like streaming PRISM/gridMET data or NDVI synchrony—will live in dedicated notebooks and docs pages as the adapters solidify. See [notebooks/quickstart_cubedynamics.ipynb](https://github.com/CU-ESIIL/climate_cube_math/blob/main/notebooks/quickstart_cubedynamics.ipynb) in the repository for the runnable tutorial notebook.

## Learn more

- Start with the [Getting Started guide](getting_started.md) for installation details and the first notebook pipeline.
- Dive into [Pipe Syntax & Verbs](pipe_syntax.md) to understand how each operation composes.
- Explore the operations references when you need specifics on transforms, stats, or IO helpers.
