# CubeDynamics (`cubedynamics`)

CubeDynamics is a streaming-first climate cube math library for building
multi-source climate data cubes (PRISM, gridMET, NDVI/Sentinel, etc.) and
computing correlations, variance, and trends without downloading entire
collections.

## Features

- **Streaming and chunked access** to climate datasets so analyses can begin
  before downloads finish.
- **Climate lexcubes** – multi-dimensional cubes of climate statistics for
  comparing vegetation, weather, and derived metrics over shared axes.
- **Correlation, synchrony, and variance cubes** that summarize temporal
  patterns such as drought stress, phenology shifts, and teleconnections.
- **Notebook-friendly helpers** for Jupyter, VS Code, and workflow runners.
- **Cloud and big-data ready** primitives that lean on `xarray`, `dask`, and
  lazy execution.

## Installation

Once the package is published on PyPI you will be able to install it with:

```bash
pip install cubedynamics
```

Until then install directly from GitHub:

```bash
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

Developers can work against the repo in editable mode:

```bash
python -m pip install -e .
```

## Quickstart

```python
import cubedynamics as cd

# Example: stream a gridMET cube for a region and compute a variance cube
cube = cd.stream_gridmet_to_cube(
    aoi_geojson,
    variable="pr",
    dates=("2000-01", "2020-12"),
)
var_cube = cd.variance_cube(cube)
var_cube.to_netcdf("gridmet_variance.nc")
```

Pipe ggplot-style operations with ``|`` for quick cube math:

```python
import cubedynamics as cd

cube = ...  # any xarray DataArray or Dataset

result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.month_filter([6, 7, 8])
    | cd.variance(dim="time")
).unwrap()
```

Additional helpers can build NDVI z-score cubes, compute rolling correlation vs
an anchor pixel, or export “lexcubes” for downstream dashboards. Follow the docs
for more end-to-end examples while the streaming implementations are finalized.

## Documentation

Full documentation: https://cu-esiil.github.io/climate_cube_math/

The GitHub Pages site hosts the narrative docs, quickstart, concepts, and API
notes for CubeDynamics. Use `mkdocs serve` to preview changes locally.

## Contributing

Contributions are welcome! Open an issue or pull request if you would like to
add new data sources, improve the streaming primitives, or expand the
statistical recipes. Please keep tests streaming-first (favor chunked I/O and
mocked responses when possible) and include documentation updates alongside code
changes.

## Citation

If you use CubeDynamics in academic work, cite the project using the metadata in
[`CITATION.cff`](CITATION.cff). A formal publication is planned; until then
please cite the software release and repository.
