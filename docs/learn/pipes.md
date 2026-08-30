# 3. Pipes establish order

## Concept

Read a pipe from top to bottom: each stage receives the previous result, and
the authored order becomes the syntax of the analytical statement. Run the
[shared setup](index.md#shared-setup) first.

## Tiny example

```python
daily_anomaly = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()
```

## Explanation

Subtract each cell's mean over the observed period, then average those departures
across space. Parentheses let the pipe span lines; `.unwrap()` returns the
underlying result. CubeDynamics calls stages once, from left to right, and does
not rearrange them. The pipe does not choose a baseline or units automatically.

`unwrap()` is a local statement boundary, not a compute or certification step.
It returns the ordinary xarray value and leaves any Dask-backed work deferred.

## Try it / worked example

```python
daily_anomaly.plot()
plt.axhline(0, color="black", linewidth=0.8)
plt.show()
```

Negative values mean colder than this January extract's mean, not necessarily
colder than a multi-decade climate normal.

## What to learn next

[4. Order can change meaning](order.md) · [Pipe](../api/pipe.md) ·
[anomaly](../reference/verbs/anomaly.md) · [Grammar vignette](../vignettes/grammar_basics.ipynb)
