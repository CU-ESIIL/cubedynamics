# 5. Compose a question

## Concept

Separate conditions before combining them. Where was a day both at or below freezing
and in the coldest fifth of the observed period? Run the [shared setup](index.md#shared-setup).

## Tiny example

```python
cold = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()
unusual = (pipe(cube) | v.quantile_state(quantile=0.2, direction="below")).unwrap()
coincidence = (pipe(cold) | v.overlap(unusual)).unwrap()
```

## Explanation

[overlap](../reference/verbs/overlap.md) requires exactly aligned coordinates;
it does not silently reproject or resample. The relative threshold is local
to each cell and this short period, not a definition of an extreme climate event.

## Try it / worked example

```python
frequency = (pipe(coincidence) | v.mean(dim="time", keep_dim=False)).unwrap()
frequency["state"].plot(cbar_kwargs={"label": "Fraction of observed days"})
plt.show()
```

`overlap` returns a condition Dataset containing only Boolean `state`. It does
not invent a magnitude or threshold for a logical intersection. After `mean`,
the `state` variable is explicitly labeled as a proportion summary. Read it as
the fraction of observed days satisfying both conditions.
Do not infer damage or risk from co-occurrence alone.

## What to learn next

[6. Inspect the result](inspect.md) · [quantile_state](../reference/verbs/quantile_state.md) ·
[Working lands vignette](../decision_vignettes/working_lands.ipynb)
