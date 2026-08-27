# 3. Pipes establish order

## Concept

Read a pipe from top to bottom: each stage receives the previous result.
Run the [shared setup](index.md#shared-setup) first.

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
underlying result. The pipe does not choose a baseline or units automatically.

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
