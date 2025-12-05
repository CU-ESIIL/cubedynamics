# Semantic variable loaders

**In plain English:**  
Semantic loaders give you common variables (temperature, precipitation, NDVI) without memorizing provider field names. They now return VirtualCubes automatically for large AOIs or long time ranges so you can request decades of data safely.

**What this page helps you do:**  
- Pick the right semantic loader for climate or NDVI
- See how loaders behave when streaming activates
- Debug tile settings when you want to peek under the hood

## Simple semantic requests

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(lat=40.0, lon=-105.25, start="1985", end="2024")
pipe(ndvi) | v.mean(dim=("y", "x"))
```

The code above streams automatically if the span is large. You do not need to change the verb chain.

## Working With Large Datasets (New in 2025)

CubeDynamics can now work with extremely large climate or NDVI datasets — 
even decades of data or very large spatial areas — without loading everything 
into memory at once.

It does this using a new system called **VirtualCube**, which streams data in 
small 'tiles'. You can think of these tiles as puzzle pieces. CubeDynamics 
processes each piece, keeps track of running statistics, and never holds the 
whole puzzle in memory.

## Loader tips for streaming

- Add `streaming_strategy="virtual"` to force streaming.
- Use `time_tile="5y"` or similar if you want to control time slices.
- Large bounding boxes may trigger spatial tiles; call `.debug_tiles()` to see the layout.

## Example: NDVI z-scores at scale

```python
ndvi_z = cd.ndvi_zscore(
    bbox=[-125, 24, -66.5, 49],
    start="1984",
    end="2024",
)

# Streamed anomaly over space
anomaly_ts = pipe(ndvi_z) | v.anomaly(dim="time") | v.mean(dim=("y", "x"))
```

## Debugging semantic loaders

- `print(loader_output)` shows whether you received a VirtualCube.
- `.debug_tiles()` prints time and spatial slices used for streaming.
- `.materialize()` turns the virtual object into an in-memory cube; use only for small AOIs.

---

This material has been moved to the Legacy Reference page.
