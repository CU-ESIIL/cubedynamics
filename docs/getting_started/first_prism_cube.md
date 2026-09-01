# First cube (PRISM)

!!! info "Compatibility URL"
    This historical URL is retained for existing links. The maintained lesson
    is [Getting started](../getting_started.md), and the checksum-pinned real
    observation example is the [Quickstart](../quickstart.md).

The current PRISM noun path is explicit and bounded:

```python
from cubedynamics import data, pipe, verbs as v

temperature = data.temperature(
    source="prism",
    statistic="maximum",
    bbox=[-105.35, 39.95, -105.20, 40.10],
    start="2024-01-01",
    end="2024-01-03",
    freq="D",
)

summary = pipe(temperature) | v.mean(over="time", keep_dim=False)
print(summary.explain())
print(summary.validate())
summary | v.plot(title="PRISM mean daily maximum temperature")
```

PRISM requests currently support daily observations. CubeDynamics raises a
clear error for unsupported monthly frequencies rather than silently changing
the temporal meaning. Provider-specific `load_prism_cube(...)` remains public
for compatibility and advanced source control, but new lessons should begin
with `data.temperature(...)` or `data.precipitation(...)`.
