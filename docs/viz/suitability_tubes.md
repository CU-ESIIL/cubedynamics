# Suitability tubes

`v.tubes()` provides a high-level way to discover and visualize "spacetime tubes" in a cube. Tubes are 3D connected components in `(time, y, x)` defined by a suitability rule (for example, NDVI thresholds).

Under the hood, `v.tubes()`:

1. Builds a suitability mask (default: NDVI in [0.3, 0.8]).
2. Labels 3D connected components ("tubes") in (time, y, x).
3. Computes per-tube metrics such as duration and size.
4. Selects one tube (e.g., the longest one).
5. Converts that tube into a `VaseDefinition` (a time-varying polygon hull).
6. Plots it using the same 3D cube viewer as `v.vase()`.

## Minimal example

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2023-01-01",
    end="2024-12-31",
)

# Longest NDVI suitability tube, plotted as a vase
pipe(ndvi) | v.tubes(lo=0.3, hi=0.8, select="longest")

# Largest tube by total voxel count
pipe(ndvi) | v.tubes(select="largest")

# Explicit tube id (from tube metrics)
pipe(ndvi) | v.tubes(select=5)
```

Conceptually:
Vase: a single time-varying hull (one polygon per time slice).
Tubes: many data-driven trajectories in (time, y, x) derived from the cube; `v.tubes()` chooses one of them and renders it as a vase.

For workflow context, pair tube extraction with the [Recipes Overview](../recipes/index.md) or the [Verbs & Examples](../capabilities/textbook_verbs.md) reference when composing pipelines.

---
Back to [Visualization Overview](index.md)  
Next recommended page: [Cube viewer (v.plot)](cube_viewer.md)
