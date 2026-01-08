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

## Prototyping without editing the repo (patch workflow)

When iterating quickly, it can be useful to prototype by monkeypatching the viewer function in a notebook session rather than editing the repository.

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

## Where to edit what

Use this mental model:

- Change verb behavior / API surface:
  - `cubedynamics/verbs/plot.py`
- Change grammar concepts (layers, scales, themes, captions, faceting):
  - `cubedynamics/plotting/cube_plot.py`
- Change rendered HTML/CSS/JS, cube transforms, face layout, overlays:
  - `cubedynamics/plotting/cube_viewer.py`

## Debugging tips for viewer development

- Add temporary debug labels to the HTML (e.g., watermark text like “RIG V3”) to confirm you are seeing the patched output.
- Print short snippets around key DOM nodes (`cd-cube`, `cube-wrapper`, `cube-rotation`) to verify injection points.
- Keep patch scripts reload-safe to avoid accidental recursion.
