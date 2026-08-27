# 4. Order can change meaning

## Concept

“How much of the region is at or below freezing?” differs from “Is the regional
mean at or below freezing?” Run the [shared setup](index.md#shared-setup) first.

## Tiny example

```python
cold_cells = (pipe(cube) | v.threshold_state(threshold=0, direction="below")).unwrap()
regional_mean = (pipe(cube) | v.mean(dim=("y", "x"), keep_dim=False)).unwrap()
```

## Explanation

[threshold_state](../reference/verbs/threshold_state.md) makes the comparison
explicit. Thresholding cells before averaging produces a fraction;
thresholding the spatial mean produces one Boolean per day. These operations
answer different questions.

## Try it / worked example

```python
fraction_cold = cold_cells.state.mean(("y", "x"))
mean_is_cold = (pipe(regional_mean) | v.threshold_state(threshold=0, direction="below")).unwrap()
fraction_cold.plot(label="Fraction of cells at or below freezing")
mean_is_cold.state.astype(float).plot(label="Regional mean at or below freezing")
plt.legend()
plt.show()
```

These are unweighted cell summaries, not area-weighted estimates. Look for
days when the curves differ before choosing a summary for your question.

## What to learn next

[5. Compose a question](compose.md) · [mean](../reference/verbs/mean.md) ·
[States and events vignette](../vignettes/states_and_events.ipynb)
