# Build State Cubes

State cubes turn raw environmental or biological values into a standard
condition representation.

```python
from cubedynamics import pipe, verbs as v

hot = (
    pipe(tmax_cube)
    | v.threshold_state(threshold=35.0, direction="above")
).unwrap()
```

The result is a Dataset with `state`, `magnitude`, and `threshold`.

Use quantile thresholds when the definition should be relative to each pixel's
own distribution:

```python
cold = (
    pipe(tmin_cube)
    | v.quantile_state(
        quantile=0.5,
        direction="below",
        rolling_window=90,
    )
).unwrap()
```

Use `v.binary_state()` when you already have a boolean mask:

```python
presence = pipe(mask_cube) | v.binary_state(name="presence")
```

For biological change states:

```python
boom = (
    pipe(abundance_cube)
    | v.change_state(change="relative", threshold=0.5, lag="1Y")
).unwrap()
```

State metadata records the threshold method, direction, source variable, and
window or lag settings where applicable.
