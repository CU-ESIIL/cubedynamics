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
   import pandas as pd
   import xarray as xr
   import cubedynamics as cd

   # Build a 12-month time series with a datetime coordinate
   time = pd.date_range("2000-01-01", periods=12, freq="MS")
   values = np.arange(12, dtype=float)

   cube = xr.DataArray(
       values,
       dims=["time"],
       coords={"time": time},
       name="example_variable",
   )

   result = (
       cd.pipe(cube)
       | cd.anomaly(dim="time")
       | cd.month_filter([6, 7, 8])
       | cd.variance(dim="time")
   ).unwrap()

   print("Variance of anomalies over JJA:", float(result.values))
   ```

This notebook-safe workflow only depends on `numpy`, `pandas`, `xarray`, and `cubedynamics`. More advanced examples—like streaming PRISM/gridMET data or NDVI synchrony—will live in dedicated notebooks and docs pages as the adapters solidify. See [notebooks/quickstart_cubedynamics.ipynb](https://github.com/CU-ESIIL/climate_cube_math/blob/main/notebooks/quickstart_cubedynamics.ipynb) in the repository for the runnable tutorial notebook.

## Learn more

- Start with the [Getting Started guide](getting_started.md) for installation details and the first notebook pipeline.
- Dive into [Pipe Syntax & Verbs](pipe_syntax.md) to understand how each operation composes.
- Explore the operations references when you need specifics on transforms, stats, or IO helpers.
