# 4. Order can change meaning

## Concept

“How much of the region is at or below freezing?” differs from “Is the regional
mean at or below freezing?” Run the [shared setup](index.md#shared-setup) first.

## Tiny example

```python
cold_cells = pipe(cube) | v.threshold_state(threshold=0, direction="below")
regional_mean = pipe(cube) | v.mean(dim=("y", "x"), keep_dim=False)
```

## Explanation

[threshold_state](../reference/verbs/threshold_state.md) makes the comparison
explicit. Thresholding cells before averaging produces a fraction;
thresholding the spatial mean produces one Boolean per day. These operations
answer different questions even when both scripts are perfectly rerunnable.
Authored order is therefore scientific syntax, not just formatting.

## Try it / worked example

```python
fraction_cold = cold_cells | v.mean(dim=("y", "x"), keep_dim=False)
mean_is_cold = regional_mean | v.threshold_state(threshold=0, direction="below")

print(fraction_cold.explain())  # current result: summary
print(mean_is_cold.explain())   # current result: condition

fraction = fraction_cold.unwrap()["state"]
mean_condition = mean_is_cold.unwrap()["state"].astype(float)
fraction.plot(label="Fraction of cells at or below freezing")
mean_condition.plot(label="Regional mean at or below freezing")
plt.legend()
plt.show()
```

These are unweighted cell summaries, not area-weighted estimates. Look for
days when the curves differ before choosing a summary for your question.
CubeDynamics preserves the written order and records an
`ORDER_CHANGES_MEANING` note for either path; it does not rewrite one into the
other. Reducing a condition labels the result and its `state` variable as a
summary proportion rather than leaving stale Boolean-condition metadata.

## What to learn next

[5. Compose a question](compose.md) · [mean](../reference/verbs/mean.md) ·
[States and events vignette](../vignettes/states_and_events.ipynb)
