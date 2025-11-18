# Getting Started

CubeDynamics (`cubedynamics`) runs anywhere `xarray` does—laptops, clusters, or serverless jobs. Use this guide to install the package, import the core helpers, and prepare for streaming climate data once adapters are wired in.

## Installation

### Install from GitHub today

```bash
python -m pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

### Install from PyPI when released

```bash
python -m pip install cubedynamics
```

### Editable installs for development

```bash
git clone https://github.com/CU-ESIIL/climate_cube_math.git
cd climate_cube_math
python -m pip install -e .[dev]
```

## Import pattern

The `cubedynamics` namespace exposes the primary verbs directly alongside the `pipe` helper:

```python
import cubedynamics as cd
```

Every example in the docs uses this alias so pipe chains read cleanly: `cd.pipe(cube) | cd.anomaly(dim="time")`.

## Minimal example

```python
import cubedynamics as cd
import xarray as xr

cube = xr.DataArray([1, 2, 3, 4], dims=["time"])

result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.variance(dim="time")
).unwrap()
```

The `.unwrap()` call runs the pipeline and returns the final `xarray` object.

## Loading streamed climate data

CubeDynamics is built for streaming PRISM, gridMET, NDVI, and related datasets directly into `xarray` cubes. While the adapters are being finalized, design your code around the expectation that loaders will return `DataArray`/`Dataset` objects:

```python
prism_cube = cd.ops.io.stream_prism_to_cube(aoi, variable="tmean", dates=("2005-01", "2015-12"))
```

Once adapters land, swap the placeholder call with the real function and keep the downstream pipe chain unchanged.

## Next steps

- Learn the [pipe syntax](pipe_syntax.md) for building readable cube workflows.
- Explore [operations references](ops_transforms.md) for available verbs.
- Review [development practices](development.md) if you plan to contribute new streaming sources or operations.
