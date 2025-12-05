# Statistics verbs

**In plain English:**  
Statistics verbs compute summaries like mean, variance, std, and anomalies. With VirtualCube they now track running totals across tiles, so you get the same answer whether data streams or sits fully in memory.

**What this page helps you do:**  
- Apply statistical verbs to streaming cubes
- Understand how incremental calculations work
- Debug slow or surprising outputs on very large requests

## Streaming statistics example

```python
from cubedynamics import pipe, verbs as v

variance_ts = (
    pipe(cube)
    | v.month_filter([6, 7, 8])
    | v.variance(dim=("y", "x"))
)
```

For large cubes, each tile updates running variance trackers; the final result matches an in-memory calculation.

## Behind the scenes

- **Mean/variance/std**: Online algorithms maintain sums and counts per tile.
- **Anomalies**: The baseline is computed incrementally, then applied to each tile.
- **Correlations**: Tile-level products are accumulated and normalized at the end.

## Debugging statistical verbs

- Print the cube to confirm `VirtualCube` is active when expected.
- Call `.debug_tiles()` to see tile boundaries if a result seems slow.
- Use `.materialize()` before running a verb only when the dataset is small enough to fit in memory.

---

This material has been moved to the Legacy Reference page.
