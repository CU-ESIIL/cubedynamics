# Streaming large data

**In plain English:**  
This page shows when CubeDynamics switches to VirtualCube, how it chooses tiles, and how you can debug or adjust streaming for very large climate or NDVI analyses.

**What this page helps you do:**  
- Know when streaming activates automatically
- Understand tile boundaries for time and space
- Troubleshoot slow or error-prone large requests

## When does CubeDynamics switch to streaming?

CubeDynamics checks the requested time span, spatial extent, and provider limits. If the request is too large to hold comfortably in memory, it returns a VirtualCube that streams tiles. You can also force this by passing `streaming_strategy="virtual"` to loaders.

## How tile boundaries are chosen

- **Time chunks**: by default, long spans are split into multi-year windows (for example, 5-year slices). Shorter windows reduce memory per tile.
- **Spatial chunks**: wide bounding boxes are broken into smaller rectangles. Each rectangle is fetched and processed separately.

## Time chunks vs spatial chunks

Some requests only need time tiling (long history, small AOI). Others only need spatial tiling (wide AOI, short time). Very large jobs may need both.

## What happens if both are too large (time × space tiling)

VirtualCube creates a grid of tiles that cover every time window and spatial rectangle. Each tile is processed independently, then merged. Running statistics guarantee consistent outputs.

## What about NDVI z-scores?

NDVI z-score loaders stream just like other cubes. Baseline statistics are computed incrementally across tiles before z-scores are applied, so you can request decades of vegetation data without special code.

## How VirtualCube fits into the broader pipe/verb system

Pipes and verbs remain unchanged. Streaming only changes how data is fed into the verbs, not which verbs you call.

```python
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(..., streaming_strategy="virtual")
pipe(ndvi) | v.variance(dim=("y", "x")) | v.plot_timeseries()
```

## Practical debugging tips

- Use `.debug_tiles()` to print tile boundaries.
- Reduce `time_tile` or `spatial_tile` if you see rate limits or timeouts.
- Force materialization with `.materialize()` only for small validation runs.
- Log intermediate shapes with lightweight verbs if a custom step misbehaves.

## Examples of errors and how to fix them

- **MemoryError or slow progress**: shrink `time_tile`, narrow the AOI, or both.
- **Provider rate-limit warnings**: lower tile sizes to reduce concurrent requests.
- **Unexpected statistics**: ensure custom verbs do not assume full-context data; otherwise, materialize first.

## Planning a long NDVI or climate analysis responsibly

- Check provider terms and rate limits before launching continent-scale requests.
- Schedule large pulls during off-peak hours when possible.
- Save intermediate summaries instead of raw tiles when you only need aggregates.

---

This material has been moved to the Legacy Reference page.
