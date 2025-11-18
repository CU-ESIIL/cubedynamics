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
