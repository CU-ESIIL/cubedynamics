# Glossary

Canonical terms used throughout CubeDynamics and the documentation.

## Core objects

- **Cube**: An xarray `DataArray` with dimensions `(time, y, x [, band])` carrying spatial metadata.
- **VirtualCube**: A lazy, streaming-aware cube that defers materialization until needed.
- **Pipe**: The `cubedynamics.pipe` helper that wraps a cube and enables `|` operator chaining.
- **Verb**: A callable from `cubedynamics.verbs` designed to compose inside a pipe chain.
- **Vase**: A 3-D hull defined by lofting time-stamped polygons through `(time, y, x)`.
- **Event hull**: The time-aware outline generated from wildfire events or other geospatial drivers.
- **Synchrony**: Correlated behavior between locations or variables across time.
- **Variance**: Dispersion of a cube along a dimension; typically computed with `v.variance`.
- **Anomaly**: Departure from a baseline; often computed with `v.anomaly` or `v.zscore`.
- **Climatology**: A long-term baseline (e.g., multi-year mean) used for anomaly detection.

## Old term → new term

| Old term            | New term / canonical vocabulary |
| ------------------- | -------------------------------- |
| cubelet             | cube                             |
| flow / pipeline     | pipe                             |
| function            | verb                             |
| hull volume         | vase                             |
| fire hull           | event hull                       |
| co-occurrence       | synchrony                        |
| deviation           | anomaly                          |

Use the new terms in code, docs, and examples to keep the vocabulary consistent.
