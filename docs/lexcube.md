# Lexcube integration

**In plain English:**  
Lexcube lets you explore cubes interactively in the browser. VirtualCube keeps this experience smooth for large datasets by streaming tiles to the viewer instead of loading everything at once.

**What this page helps you do:**  
- Send cubes (including VirtualCubes) into Lexcube
- Understand how streaming affects visualization
- Debug slow loads or tiling issues

## Quick Lexcube stream

```python
from cubedynamics import pipe, verbs as v

lex = pipe(cube) | v.show_cube_lexcube(title="Streaming cube view")
```

If `cube` is huge, Lexcube requests tiles on demand. You see updates as each tile finishes processing.

## Visualization tips for large data

- Keep `time_tile` reasonable when sending 40+ years of data to Lexcube.
- If the AOI is wide, expect Lexcube to fetch spatial tiles separately.
- Use `v.plot_timeseries()` for quick summaries before opening a full Lexcube view.

## Update (2025): New `v.plot` cube viewer

We’ve added a new HTML-based cube viewer wired into `verbs.plot`, which visualizes any `(time, y, x)` DataArray as a rotatable “Lexcube-style” cube.

### Basic usage

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2024-12-31",
)

# New cube-based viewer
pipe(ndvi) | v.plot(kind="cube")
```

This call:
- Infers which dimension is time and which are spatial (y, x).
- Extracts three faces of the cube:
  - A map face (y, x) at the most recent time step.
  - A time–y curtain at x=0.
  - A time–x curtain at y=max.
- Applies a colormap and unified color scaling based on the 2nd and 98th percentiles of all face values.
- Renders a CSS 3D cube that you can:
  - Click-and-drag to rotate.
  - Scroll to zoom.
  - Drag anywhere inside the cube frame (faces or transparent padding); pointer capture keeps the rotation responsive even if the cursor slips past the cube during the drag.
- Displays a colorbar at the bottom with dynamic min/max labels.
- Adds Lexcube-style axis labels around the cube, with axis names near the edges and min/max tick labels tucked beside each axis rather than in a tall block below the viewer.
- Streams progress inline in the notebook cell without a blocking loading overlay, so subsequent cells stay responsive while faces are being encoded.

### Customization

```python
pipe(ndvi) | v.plot(
    kind="cube",
    out_html="ndvi_cube.html",
    cmap="RdBu_r",
    size_px=420,
    thin_time_factor=4,
)
```

- `out_html`: filename for the generated HTML cube.
- `cmap`: matplotlib colormap name.
- `size_px`: pixel size of the cube faces.
- `thin_time_factor`: if time is very long, only every Nth time step is used when building the curtains, which speeds up rendering.

### When to use the cube viewer

Use `v.plot(kind="cube")` when you care about the **geometry of the data cube** itself—e.g., understanding how variance and anomalies are arranged along both spatial and temporal axes for NDVI, PRISM, or climate cubes.

For map-first tasks (zoom, pan, overlay boundaries), see the new `v.map()` function below.

## Debugging Lexcube with VirtualCube

- Call `.debug_tiles()` on the source cube to understand the request pattern.
- Watch provider rate limits; large visualization requests may queue tiles.
- For small validation checks, call `.materialize()` and view a subset first.

---

This material has been moved to the Legacy Reference page.
