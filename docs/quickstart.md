# Quickstart

Install, request one scientific noun, and apply two verbs. This example uses
live data; for offline learning, use the [Learn setup](learn/index.md#shared-setup).

## Install

```bash
python -m pip install cubedynamics
```

See [installation options](getting_started/install.md) for notebook environments.

## Load observed temperature

```python
from cubedynamics import data, pipe, verbs as v

temperature = data.temperature(
    source="prism", statistic="maximum",
    bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-01-01", end="2024-01-30",
)
```

The [temperature reference](library/nouns/temperature.md) defines returned data
and source constraints. Network access is required; an outage is not replaced
by generated observations.

## Compose the analysis

```python
spatial_anomaly = (
    pipe(temperature)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()
spatial_anomaly.plot()
```

Subtract each cell's mean for the requested dates, then average over space.
This is a departure from the selected period, not a multi-decade climatology.

## Continue

- [Learn](learn/index.md): seven short lessons.
- [Library](library/index.md): environmental nouns and sources.
- [Documents](documentation/index.md): arguments and behavior.
- [Vignettes](vignettes/index.md): complete reproducible analyses.
