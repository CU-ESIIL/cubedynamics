# Getting started with CubeDynamics

CubeDynamics is a small semantic grammar for environmental cubes:

```text
noun → pipe → verb → verb → inspect or export
```

This page is the current, minimal first-use path. For a checksum-pinned real
PRISM extract that runs without a repository checkout, use the
[Quickstart](quickstart.md).

## Install

```bash
python -m pip install cubedynamics==0.1.0rc1
```

The core import does not require optional compiled Sentinel-2/Rasterio
dependencies to initialize successfully. A source-specific loader can still
report its own missing system or Python dependency when that source is called.
See [Installation](getting_started/install.md) for supported environments and
extras.

## Discover a noun and source

```python
from cubedynamics import data, pipe, verbs as v

print(data.describe("temperature", "prism"))
help(data.temperature)
```

Use noun functions in new analyses. They preserve the selected provider,
product, query, units, source mode, and available serving metadata.

## Make a bounded live PRISM request

PRISM access is currently daily. State `freq="D"` explicitly in teaching code
so the temporal meaning remains visible. CubeDynamics does not silently turn
daily observations into monthly values.

```python
temperature = data.temperature(
    source="prism",
    statistic="maximum",
    bbox=[-105.35, 39.95, -105.20, 40.10],
    start="2024-01-01",
    end="2024-01-03",
    freq="D",
)
```

This is a live provider request: network or provider failure stops the example.
There is no synthetic fallback in the noun API.

## Compose and inspect the statement

```python
analysis = (
    pipe(temperature)
    | v.anomaly(over="time")
    | v.mean(over=("y", "x"), keep_dim=False)
)

print(analysis.explain())
print(analysis.validate())
print(analysis.semantic_state)
print(analysis.semantic_trace)
```

The order is meaningful: this subtracts each cell's mean across the requested
three days, then averages those departures over space. `explain()`,
`validate()`, and the semantic trace inspect the authored workflow; they do not
rewrite it or certify that it answers the right scientific question.

## Plot, unwrap, and export

```python
plotted = analysis | v.plot(title="PRISM daily temperature departures")
result = plotted.unwrap()

# Ordinary source and continuous results have NetCDF-safe metadata.
result.to_netcdf("prism_temperature_departure.nc", engine="h5netcdf")

# Prefer the verb for condition/state results: Boolean variables are encoded
# deterministically as int8 in the file without changing the in-memory cube.
warm = pipe(temperature) | v.threshold_state(
    threshold=5,
    direction="above",
    name="warm",
)
warm | v.to_netcdf("prism_warm_state.nc", engine="h5netcdf")
```

`unwrap()` returns the wrapped xarray value; it does not force unrelated lazy
work. `v.to_netcdf()` writes a metadata-safe copy and returns the original value
through the pipe.

## Continue

- [Learn](learn/index.md) explains nouns, verbs, order, and provenance.
- [Library](library/index.md) lists current nouns and their sources.
- [Documents](documentation/index.md) contains the callable reference.
- [Vignettes](vignettes/index.md) develops complete real-data analysis stories.
- [Public documentation generation audit](project/public_docs_generation_audit.md)
  identifies current, compatibility, deprecated, and retired material.
