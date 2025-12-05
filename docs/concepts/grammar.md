# Pipe verbs

**In plain English:**  
Pipe verbs are small functions you chain with the `|` operator. They now work seamlessly with VirtualCube, so streaming tiles pass through the same verbs you already use on small cubes.

**What this page helps you do:**  
- See how to read and write pipe expressions
- Understand verb behavior in streaming mode
- Debug tile-aware runs without changing your code

## Pipe refresher with streaming

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.month_filter([6, 7, 8])
    | v.mean(dim=("y", "x"))
)
```

If `cube` is a VirtualCube, each tile flows through the same chain, and the reductions keep incremental statistics under the hood.

## Verb behavior in streaming mode

- **Transforms** run on each tile independently.
- **Reductions** (mean, variance, std, anomaly) keep running totals so the final output matches in-memory results.
- **IO and visualization** verbs request tiles lazily; plotting functions stream data without loading the whole cube first.

## Debugging verbs with tiles

- Print the pipe input to confirm whether it is virtual.
- Use `v.peek()` or similar custom verbs to log shapes per tile.
- If a verb needs full context (rare), call `.materialize()` first, but only for manageable sizes.

---

This material has been moved to the Legacy Reference page.
