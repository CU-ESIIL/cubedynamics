# Getting Started

This page walks through installing CubeDynamics, configuring credentials, and
verifying that streaming climate cubes work in your environment.

## Install the package

CubeDynamics follows a standard `pyproject.toml` layout inside `src/`.

```bash
# clone the repo
 git clone https://github.com/CU-ESIIL/climate_cube_math.git
 cd climate_cube_math

# install dependencies in editable mode for development
 python -m pip install -e .
```

Once the project is on PyPI the install will be as simple as `pip install
cubedynamics`.

## Configure environment variables

Some streaming backends (Cubo, Microsoft Planetary Computer, Google Earth
Engine) require API tokens. Store them in environment variables or `.env` files
and load them before requesting cubes. For example:

```bash
export CUBO_API_TOKEN="..."
export PLANETARY_COMPUTER_SUBSCRIPTION="..."
```

The loaders look for these variables automatically when establishing remote
sessions.

## Verify a streaming request

Open a Python session or notebook and request a small cube to confirm your setup
works:

```python
import cubedynamics as cd

aoi = {
    "min_lon": -105.4,
    "max_lon": -105.3,
    "min_lat": 40.0,
    "max_lat": 40.1,
}

cube = cd.stream_gridmet_to_cube(
    aoi,
    variable="tmmx",
    dates=("2020-01-01", "2020-12-31"),
    prefer_streaming=True,
)
print(cube)
```

If the call succeeds you are ready to work through the [Concepts](concepts.md)
and [API & Examples](climate_cubes.md) sections.

## Pipe syntax (ggplot-style verbs)

CubeDynamics now exposes a ``pipe()`` helper and pipeable verbs under
``cubedynamics.ops``. Wrap any xarray ``DataArray`` or ``Dataset`` with
``cd.pipe()`` and compose operations with the ``|`` operator:

```python
import cubedynamics as cd

cube = ...

result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.month_filter([6, 7, 8])
    | cd.variance(dim="time")
    | cd.to_netcdf("out.nc")
).unwrap()
```

Pipeable verbs are factories. You can create your own by following the same
pattern:

```python
def my_custom_op(scale):
    def _inner(cube):
        return cube * scale
    return _inner

result = cd.pipe(cube) | my_custom_op(0.5)
```

This keeps the streaming-first philosophy: each verb simply transforms or
reduces the cube provided by the pipe without forcing eager downloads.
