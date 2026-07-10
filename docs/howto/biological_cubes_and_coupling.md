# Biological Cubes and Coupling

Biological observations can enter the same state and synchrony grammar without
taxon-specific assumptions.

```python
from cubedynamics import pipe, verbs as v

bio_cube = v.rasterize_observations(
    observations,
    template=climate_cube,
    time_col="date",
    value_col="abundance",
    reducer="sum",
)
```

`NaN` means unobserved. Numeric zero remains available for observed absences or
true zero abundance.

Align the biological cube to another cube:

```python
bio_aligned = (
    pipe(bio_cube)
    | v.align_cube(
        like=climate_cube,
        spatial_method="nearest",
        temporal_method="nearest",
        tolerance="15D",
    )
).unwrap()
```

Build a biological state:

```python
boom = (
    pipe(bio_aligned)
    | v.change_state(change="relative", threshold=0.5, lag="1Y")
).unwrap()
```

Then compare climate and biology as coupling rather than within-cube spatial
synchrony:

```python
climate_biology = (
    pipe(frost_state)
    | v.sync_with(
        boom,
        synchrony="occurrence",
        spatial_relation="same_pixel",
        lags=["0D", "90D", "180D", "365D"],
    )
).unwrap()
```

The first coupling implementation supports same-pixel lagged occurrence
synchrony. Cross-location coupling and permutation/null diagnostics are reserved
for later phases.
