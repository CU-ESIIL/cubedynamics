# Transform verbs

**In plain English:**  
Transform verbs reshape or adjust cubes (filtering months, reprojecting, normalizing). They now run tile by tile when a VirtualCube streams large data, so you can apply the same transforms to decade-spanning cubes.

**What this page helps you do:**  
- Learn how transforms behave on streaming cubes
- See examples with VirtualCube inputs
- Know when to materialize for specialized needs

## Streaming-friendly transforms

Most transforms operate independently per tile, so the outputs combine cleanly.

```python
from cubedynamics import pipe, verbs as v

# Stream a tile-aware anomaly
streamed = pipe(cube) | v.anomaly(dim="time") | v.month_filter([6, 7, 8])
```

## Tips for large requests

- Keep transforms that require context (e.g., global normalization) aware of tile size; adjust `time_tile` if needed.
- Use `.debug_tiles()` on the source cube to see how many tiles will flow through the verbs.
- Add `v.peek()` or logging after key transforms when diagnosing unexpected values.

## Visualization after transforms

Plotting still streams:

```python
pipe(cube) | v.variance(dim="time") | v.plot_timeseries()
```

Large AOIs update as each tile finishes; reduce date spans to speed up.

---

This material has been moved to the Legacy Reference page.
