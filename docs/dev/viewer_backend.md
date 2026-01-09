# Viewer backend (cube HTML renderer)

This page explains how `v.plot()` produces the interactive “HTML cube” viewer in Cubedynamics, and where to edit the code if you want to change rendering, layout, axes, or styling.

The important idea is: **`v.plot()` itself is a thin wrapper.** The actual cube rendering happens deeper in the plotting backend and ultimately returns a self-contained HTML string that is displayed in a notebook iframe.

---

## High-level flow

When you run:

```python
from cubedynamics import pipe, verbs as v
viewer = (pipe(cube) | v.plot()).unwrap()
viewer
```

the call chain is:

- `cubedynamics.verbs.plot.plot()`
  - validates the input (xarray.DataArray or VirtualCube)
  - infers the (time, y, x) dimension names (unless overridden)
  - builds a CubePlot object and adds geometry layers (e.g. geom_cube)
  - returns the CubePlot viewer object (the pipe contract keeps the cube flowing)
- `cubedynamics.plotting.cube_plot.CubePlot`
  - stores plot options, theme, caption metadata, and layer definitions
  - when displayed in a notebook, Jupyter calls `CubePlot._repr_html_()`
- `CubePlot._repr_html_()` → `CubePlot.to_html()`
  - computes the “stat layer” output (if any stats/transforms are applied)
  - computes fill scale limits / breaks / labels
  - builds axis metadata (`axis_meta`) for labels/ticks
  - calls the low-level viewer function to actually build the HTML
- `cubedynamics.plotting.cube_viewer.cube_from_dataarray()`
  - constructs the HTML/CSS/JS viewer string
  - samples/decimates time frames for responsiveness (`thin_time_factor`)
  - rasterizes faces into images (often base64-encoded PNGs inside the HTML)
  - returns either:
    - a self-contained HTML string (`return_html=True`), or
    - writes to `out_html` and returns a viewer handle, depending on usage
- `show_cube_viewer(...)`
  - writes HTML to a temp file and returns an iframe wrapper for notebook display.

In short:

`v.plot` (verb) → `CubePlot` (grammar container) → `cube_from_dataarray` (HTML builder) → iframe

## The key files (start here)

The viewer backend is split across two main modules:

- `cubedynamics/verbs/plot.py`
  - Entry point for `v.plot()` (pipe-friendly verb wrapper).
- `cubedynamics/plotting/cube_plot.py`
  - The CubePlot class: stores plot configuration, layers, theme, and turns a cube into HTML through `to_html()`.
- `cubedynamics/plotting/cube_viewer.py`
  - The actual HTML/CSS/JS viewer builder. If you want to change DOM structure, CSS classes, cube transforms, face layout, or add new overlay elements, this is typically the file you edit.

Supporting modules you may encounter:

- `cubedynamics/plotting/show.py` (or similarly named)
  - Helpers that write HTML to disk and display it in an iframe in notebooks.

## Expected input shape and dimension conventions

The cube viewer is designed for a 3D data array with dimensions:

- time: the temporal axis
- y: the vertical spatial axis (rows)
- x: the horizontal spatial axis (columns)

Commonly this is an xarray.DataArray with dims like `("time", "y", "x")`.

If your cube uses different dimension names, `v.plot()` attempts to infer them. You can also override the time dimension via the `time_dim=` argument to `v.plot()` (or the underlying CubePlot).

## Cube Coordinate System (Read This First)

The cube is a 3D scene with a cube-local coordinate system. **Origin `(0, 0, 0)` is the center of the cube.**

Axes:

- +X → right (longitude increases)
- −Y → up (latitude increases upward)
- +Z → toward the viewer (out of screen)

Cube faces (with `cube_size` as the total edge length):

- Front face: `z = +0.5 * cube_size`
- Back face:  `z = -0.5 * cube_size`

Time is mapped to **depth (Z)**.

```
          -Y (up)
            ▲
            |
            |
            o ----> +X (right)
           /
          /
       +Z (toward viewer)
```

**State explicitly:** `.cd-cube` is the *canonical attachment point* for cube-relative visuals. Anything that must rotate and scale with the cube (axes, ticks, overlays) belongs inside `.cd-cube`.

For authoritative rules and invariants, see [Cube viewer invariants](cube_viewer_invariants.md).

## Time Direction Invariant

The cube front always represents the **most recent time**, and the cube back always represents the **oldest time**. Therefore:

- Time axis labels often need to be reversed.
- `tN` (newest) appears at the front corner.
- `t0` (oldest) appears at the back.

This is a *design invariant*, not a styling choice. If labels or tick positions disagree, the labels should be adjusted to preserve this invariant.

## What Rotates With the Cube vs What Faces the Viewer

- Geometry (faces, rails, ticks) rotates with `.cube-rotation`.
- Text labels may optionally **billboard** (face the viewer).
- Billboarding is implemented by applying inverse rotation to label faces.
- This keeps text readable without breaking spatial meaning.

## Common Edit Points

| Task | Where to Edit |
| ---- | ---- |
| Move axis position | CSS on `.cd-origin-*` to shift the axis origin anchor without changing data mapping. |
| Change axis length | `--cd-rig-cube-size` to adjust the cube-size reference used by rails/ticks. |
| Fix tick alignment | `.cd-axis-* .cd-ticks` container to correct spacing or orientation offsets. |
| Reverse time direction | Time tick placement logic to re-map normalized depth so newest is always at the front. |
| Make labels face viewer | Label face transforms to apply inverse cube rotation (billboarding). |
| Add new overlay | Inject inside `.cd-cube` so the overlay rotates with the cube. |

## Debugging checklist

- Is the overlay attached inside `.cd-cube`?
- Are you reasoning from cube center, not a corner?
- Are you mixing screen-space offsets with cube-space transforms?
- Does your time label logic respect “front = newest”?
- Are tick containers explicitly sized?

## Coordinate orientation (how the cube is interpreted)

The cube viewer uses a “front face” and “depth axis” convention:

- The front face represents the spatial slice at one end of time.
- The depth axis represents progression through time (older → newer, or vice versa depending on the chosen convention).
- The CoordCube / camera settings determine the initial “iso” viewing angle and zoom.

When working on axes or annotations, treat the viewer as a 3D scene with a consistent cube-local coordinate system. Overlay elements should be attached to the cube DOM so they rotate/scale with the cube.

## Output artifacts and file naming

CubePlot has an `out_html` path (default is typically `cube_da.html`). When faceting is enabled, `CubePlot.to_html()` may write multiple panel files with a suffix like:

- `cube_da_facet0.html`
- `cube_da_facet1.html`
- ...

In notebook display mode, the viewer is typically written to a temp location and shown via an iframe.

## Where the HTML comes from

The low-level `cube_from_dataarray(...)` function returns a complete HTML document (or fragment) containing:

- `<style>` blocks for the cube viewer CSS
- DOM elements for the cube wrapper and faces
- JavaScript for rotation/drag/interaction
- embedded imagery for the faces (often as base64 PNGs)

This design means the viewer output can be saved and shared as a standalone HTML artifact.

## Where to edit what

Use this mental model:

- Change verb behavior / API surface:
  - `cubedynamics/verbs/plot.py`
- Change grammar concepts (layers, scales, themes, captions, faceting):
  - `cubedynamics/plotting/cube_plot.py`
- Change rendered HTML/CSS/JS, cube transforms, face layout, overlays:
  - `cubedynamics/plotting/cube_viewer.py`

## Prototyping & Monkeypatching the Viewer

This section is for **development-only** prototyping without editing the repository. It is intentionally separate from the invariants above.

When iterating quickly, it can be useful to monkeypatch the viewer function in a notebook session rather than editing the repository.

A common pattern is:

- Import the viewer function(s)
- Capture the original function
- Replace it with a wrapper that:
  - calls the original
  - modifies the returned HTML string (e.g., inject CSS/DOM overlays)
  - returns the modified HTML

Important notes:

- Patch both references if needed:
  - `cubedynamics.plotting.cube_viewer.cube_from_dataarray`
  - and any module that imported it by value (e.g., cube_plot may hold a reference)
- Reload modules first (`importlib.reload`) to avoid stacking patches or causing recursion.
- Keep patches “HTML-injection only” when prototyping layout and overlays.

Example skeleton (for documentation only — adapt in your notebook):

```python
import importlib
import cubedynamics.plotting.cube_viewer as cube_viewer_mod
import cubedynamics.plotting.cube_plot as cube_plot_mod

cube_viewer_mod = importlib.reload(cube_viewer_mod)
cube_plot_mod = importlib.reload(cube_plot_mod)

_ORIG = cube_viewer_mod.cube_from_dataarray

def patched(*args, **kwargs):
    out = _ORIG(*args, **kwargs)
    if not isinstance(out, str):
        return out
    # TODO: inject CSS/HTML into out
    return out

cube_viewer_mod.cube_from_dataarray = patched
cube_plot_mod.cube_from_dataarray = patched
```

This approach lets you experiment quickly with:

- axis overlays
- new labels/ticks
- CSS themes
- DOM structure changes

…without touching the installed package or the repository.

For how semantic data flows into the viewer, see [Figure backend](figure_backend.md).
