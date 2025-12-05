# VirtualCube

**In plain English:**  
VirtualCube is the streaming engine inside CubeDynamics. It slices huge climate or NDVI requests into small tiles in time and space, processes each tile, and stitches the results together so you never load the full dataset into memory.

**What this page helps you do:**  
- Understand why VirtualCube exists and what it does
- See how tile-based streaming behaves for time and space
- Debug or tune streaming when you want more control

## Why VirtualCube exists

Large AOIs or decades of data used to risk memory errors. VirtualCube keeps the pipe + verbs experience identical while handling the heavy lifting in the background. You write the same code for a city or a continent.

## How tile-based streaming works

Behind the scenes:
- The loader checks the request size.
- If it is too large, a **VirtualCube** object is returned instead of a fully materialized cube.
- VirtualCube defines **time tiles** and **spatial tiles**.
- Each tile is fetched, processed, and reduced, updating running statistics.
- The final output is a standard DataArray/Dataset.

```
+---------------------------+
|    VirtualCube object     |
+---------------------------+
   | time tiles
   | spatial tiles
   v
 small DataArray chunks --> verbs --> online statistics --> final result
```

## Time tiling

Time tiles break long periods into manageable windows (for example, yearly or five-year slices). Verbs such as `v.mean`, `v.variance`, and `v.std` keep incremental counters so the final numbers match an all-at-once calculation.

## Spatial tiling

Large bounding boxes are split into smaller regions. Each region is downloaded and processed before the next region starts. Spatial tiles are especially helpful for continental NDVI or climate pulls.

## Same pipe, same verbs

You do not need new verbs for streaming. The pipe expression stays unchanged:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(
    bbox=[-125, 24, -66.5, 49],
    start="1985",
    end="2024",
)

series = pipe(ndvi) | v.mean(dim=("y", "x"))
```

Whether `ndvi` is in-memory or virtual, the output is the same.

## Reductions in streaming mode

- `v.mean`, `v.std`, `v.variance`: maintain running sums and counts.
- `v.anomaly`: computes the baseline incrementally and applies it tile by tile.
- `v.correlation` and related verbs: accumulate products across tiles.

## Forcing or disabling streaming

```python
ndvi_stream = cd.ndvi(lat=40.0, lon=-105.25, start="1970", end="2020", streaming_strategy="virtual")
ndvi_full = cd.ndvi(lat=40.0, lon=-105.25, start="2019", end="2020", streaming_strategy="materialize")
```

`streaming_strategy="virtual"` opts in even for modest sizes. `materialize` forces a full in-memory cube—use only when you know it will fit.

## Inspecting tiles

```python
ndvi_stream.debug_tiles()  # prints time and spatial tile boundaries
print(ndvi_stream.time_tile)
print(ndvi_stream.spatial_tile)
```

Use smaller tiles if you see rate limits or memory pressure.

## Visualization and VirtualCube

Visualization verbs stream tiles into the plot. For example:

```python
pipe(ndvi_stream) | v.variance(dim=("y", "x")) | v.plot_timeseries()
```

The plot updates after each tile finishes; for a fast preview, narrow the time range or AOI.

### Update (2025): Cube and map viewers on streamed data

You can now send streamed cubes directly into the new viewers:

```python
pipe(ndvi_stream) | v.plot(kind="cube")
pipe(ndvi_stream) | v.map()
```

The cube viewer renders the `(time, y, x)` DataArray as a rotatable HTML cube (map face plus two time–space curtains) with Lexcube-style axis labels hugging each edge. Progress is streamed in the notebook output (no blocking HTML overlay), and the map viewer selects a time slice (defaults to the last) and displays it in a pydeck map that you can pan and zoom.

## Limitations and tradeoffs

- Tile boundaries may introduce slight timing differences if your custom verb assumes full-context data.
- Provider rate limits can slow very large pulls; reduce tile size to minimize retries.
- `.materialize()` is still required for operations that truly need the entire cube at once.

## Diagnosing slow performance

- Call `.debug_tiles()` to confirm how many tiles are in play.
- Reduce `time_tile` (e.g., from `10y` to `2y`) for long requests.
- Shrink the bounding box or use coarser resolution where possible.
- Check network connectivity; streaming relies on remote fetches.

---

This material has been moved to the Legacy Reference page.
