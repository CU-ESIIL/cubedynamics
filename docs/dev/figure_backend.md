# Figure backend (v.plot)

This page documents how CubeDynamics turns a streaming xarray cube into an interactive “cube figure” in notebooks and on exported HTML. It is written to be **operational**: if you need to change axis labeling, camera behavior, styling, or the underlying HTML/JS, this is the map.

## High-level architecture

**Data → Viewer pipeline**

1. **Input**: a 3D data cube, typically an `xarray.DataArray` with dims like `(time, y, x)` (or a `VirtualCube` that materializes to a `DataArray`).
2. **Verb**: `v.plot()` is a *side-effect* verb in the pipe grammar:
   - it produces a viewer (`CubePlot`) for notebook display,
   - and **returns the original cube unchanged** so the pipeline continues.
3. **Viewer**: `CubePlot` composes cube geometry + theme + overlays (e.g. vase outlines), then renders a self-contained HTML viewer string.
4. **Notebook display**: in notebooks, `CubePlot._repr_html_()` wraps the HTML into an iframe using `show_cube_viewer(...)`.

In short:

`pipe(cube) | v.plot(...)  →  CubePlot  →  CubePlot.to_html()  →  cube_from_dataarray(...)  →  HTML/CSS/JS  →  iframe`

## Concrete call chain (what calls what)

When you run:

```python
from cubedynamics import pipe, verbs as v
viewer = (pipe(cube) | v.plot()).unwrap()
viewer
the call chain is:
cubedynamics.verbs.plot.plot(...)
Builds PlotOptions
Defines an inner function _plot(value)
Wraps _plot in Verb(...)
If da is not None, executes the verb immediately
_plot(value) (inside v.plot)
Materializes VirtualCube if needed
Infers dims (time, y, x)
Creates a CubePlot(...)
Applies cube layers (cube.geom_cube(...))
Optionally overlays vase outlines (cube.stat_vase(...).geom_vase_outline(...))
Applies theme (cube.theme_cube_studio(...))
Returns the CubePlot instance
CubePlot._repr_html_() (notebook display hook)
Calls html_out = self.to_html()
Wraps it via show_cube_viewer(html_out, ...)
Returns an iframe HTML snippet
CubePlot.to_html()
Applies stats to the primary layer
Builds caption HTML, annotation HTML, theme vars
Calls cube_from_dataarray(..., return_html=True, axis_meta=axis_meta, ...)
Wraps the resulting viewer HTML in a figure container with CSS
cube_from_dataarray(...)
Lives in cubedynamics/plotting/cube_viewer.py
This is the “backend” that turns a DataArray into the interactive cube HTML/JS
Key files (edit points)
If you want to change something, these are the first files to open:
cubedynamics/verbs/plot.py
plot(...) verb wrapper and the user-facing plot options
cubedynamics/plotting/cube_plot.py
CubePlot grammar object
CubePlot.to_html() figure container + theme variables
CubePlot._repr_html_() notebook iframe wrapper
cubedynamics/plotting/cube_viewer.py
cube_from_dataarray(...) the core HTML/CSS/JS viewer generator
cubedynamics/plotting/show.py (or similar)
show_cube_viewer(...) helper that writes HTML and returns an iframe handle
If names differ, search for:
class CubePlot
def cube_from_dataarray
def show_cube_viewer
_repr_html_
What languages are used
Python: orchestrates the grammar (verbs), metadata, and HTML assembly.
HTML: contains the viewer container and any embedded metadata.
CSS: handles cube face layout and (typically) 3D transforms.
JavaScript: handles interactive behavior (rotation, drag, controls, tick/label rendering if present).
The viewer output is designed to be self-contained HTML, suitable for:
notebook iframe display
CubePlot.save("something.html")
static export workflows
Data flow and “keeping the cube flowing”
v.plot is a side-effect verb. That means:
The viewer is produced (as a CubePlot object), but the cube is not consumed.
A pipe chain can continue to operate on the cube after plotting.
Practically:
v.plot() returns a Verb when called with no da.
The verb calls _plot(value) and returns a CubePlot.
Pipe wrappers provide .unwrap() for retrieving the inner value.
This enables:
cube = cd.ndvi(...)
viewer = (pipe(cube) | v.plot()).unwrap()
# cube is still usable for downstream computations
Coordinate systems and axis conventions
The cube viewer uses a “cube-local” coordinate system expressed in CSS 3D transforms.
Important conventions to document and preserve:

The cube has a size controlled by --cube-size (pixels).
Many cube viewers center geometry at the origin; others use a corner-origin.
In a centered cube system, cube coordinates typically span:
x: [-size/2 .. +size/2]
y: [-size/2 .. +size/2]
z: [-size/2 .. +size/2]
In CSS 3D, positive Z is toward the viewer (“out of the screen”).
CubeDynamics axis conventions (current)
The front face is the “spatial image” face.
Time is depth.
Current behavior: most recent time is on the front face, and oldest time is on the rear face.
If your axis-meta uses min=oldest and max=newest, a time axis running front→back should be inverted so max labels appear at the front.
If you change camera defaults, be careful: the “front” face and the time direction must remain consistent with labels.
axis_meta: where it comes from and what it’s for
CubePlot.to_html() passes axis_meta into cube_from_dataarray(...).
axis_meta is intended to carry:

axis display names (name)
min/max labels (min, max)
optional explicit tick breaks/labels (breaks, labels)
Typical shape:
axis_meta = {
  "time": {"name": "Time", "min": "...", "max": "..."},
  "x": {"name": "Longitude", "min": "...", "max": "..."},
  "y": {"name": "Latitude", "min": "...", "max": "..."},
}
If only time is present today, we should extend _build_axis_meta(...) to include x/y using coordinate values from da.coords.
How to edit the figure backend (practical workflow)
Editing in the repo (the “real” implementation)
For permanent changes:
Edit cubedynamics/plotting/cube_viewer.py:
this is where the HTML/CSS/JS viewer is created
changes here affect both notebook display and HTML export
If you need new metadata or options:
add parameters to cubedynamics/verbs/plot.py (v.plot(...))
plumb them into CubePlot(...)
plumb them into cube_from_dataarray(...)
Styling defaults are often in:
CubeTheme (theme colors, fonts)
CSS variables set in CubePlot.to_html()
Rapid prototyping in a notebook (no repo edits)
When iterating on HTML/CSS/JS quickly, monkeypatch the viewer function in a notebook. This allows you to experiment with axis placement, tick rendering, and layout without touching the repo.
Important: CubePlot.to_html() typically imports cube_from_dataarray into cube_plot.py at import time, e.g.:

from .cube_viewer import cube_from_dataarray
So patching only cubedynamics.plotting.cube_viewer.cube_from_dataarray may not affect CubePlot.to_html(). Patch both references.
Safe patch recipe (avoid recursion):

import importlib
import cubedynamics.plotting.cube_viewer as cube_viewer
import cubedynamics.plotting.cube_plot as cube_plot

# 1) reload to reset prior patches
cube_viewer = importlib.reload(cube_viewer)
cube_plot = importlib.reload(cube_plot)

# 2) capture the true original
_ORIG = cube_viewer.cube_from_dataarray

def patched_cube_from_dataarray(*args, **kwargs):
    html_or_obj = _ORIG(*args, **kwargs)
    if not isinstance(html_or_obj, str):
        return html_or_obj

    html = html_or_obj

    # --- prototype edits here ---
    html = html.replace(
        "</body>",
        "<div style='position:fixed;bottom:10px;right:10px;z-index:999999;"
        "background:rgba(0,0,0,0.75);color:white;padding:6px 10px;border-radius:10px;"
        "font:12px system-ui;'>PATCH ACTIVE</div></body>",
        1,
    )
    return html

# 3) patch BOTH references
cube_viewer.cube_from_dataarray = patched_cube_from_dataarray
cube_plot.cube_from_dataarray = patched_cube_from_dataarray
This guarantees:
you’re patching the function actually used by CubePlot.to_html()
you avoid recursion caused by stacking patches on top of patches
Testing changes
Recommended smoke tests:
Notebook display:
viewer = (pipe(cube) | v.plot()).unwrap(); viewer
HTML export:
viewer.save("tmp.html") and open it in a browser
Visual invariants:
time direction (front=newest, back=oldest)
axis labels remain attached to cube, not screen
legend remains readable and non-overlapping
Where to implement “science figure” axes (rails + ticks)
The “axis rig” belongs in cube_viewer.py (HTML/CSS/JS), because it is part of the viewer.
Implementation outline:

build 3 rails slightly lifted off cube surfaces (avoid z-fighting)
compute tick positions in normalized space p ∈ [0,1]
map to cube-local positions:
x axis: x = -size/2 + p*size
y axis: y = +size/2 - p*size (up is negative y in CSS)
time axis: z = +size/2 - p*size (front to back)
tick labels:
use axis_meta[axis].labels if provided
otherwise generate “nice” ticks from numeric min/max or use min/max strings
consider label readability:
labels attached in 3D can mirror when rotated
future enhancement: billboard labels to camera orientation
Developer quick reference (search terms)
v.plot
class CubePlot
_repr_html_
to_html
cube_from_dataarray
axis_meta
--cube-size
show_cube_viewer
