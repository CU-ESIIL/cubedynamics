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
- Displays a colorbar at the bottom with dynamic min/max labels.

### Loading screen behavior

For large cubes, `v.plot(kind="cube")` shows a full-screen loading page immediately (a black background with a simple progress bar) while Python computes faces and writes the HTML. Once ready, the cube replaces the loading page in the notebook cell.

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

## Legacy Technical Reference (kept for context)
# Lexcube integration

**In plain English:**  
Lexcube is an interactive viewer for `(time, y, x)` cubes.
CubeDynamics includes verbs and helpers so you can send a cube to Lexcube with one line and keep working.

**You will learn:**  
- How to display a cube in Lexcube from inside a pipe
- How to call the helper directly without the pipe
- Where the original technical notes live for reference

## What this is

The verb `v.show_cube_lexcube` and helper `cd.show_cube_lexcube` open a Lexcube widget for exploration.
They display the data as a side effect and return the original cube so your analysis can continue.

## Why it matters

Seeing the cube helps you spot patterns, cloud issues, or extreme events before running heavier statistics.
The one-line verb keeps visualization close to your computations, which is great for teaching and quick QA.

## How to use it

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

pipe(cube) \
    | v.month_filter([6, 7, 8]) \
    | v.show_cube_lexcube(title="PRISM JJA precipitation", cmap="RdBu_r")
```
This filters to summer months, opens the Lexcube widget, and leaves the cube intact for more processing.

You can also call the helper outside a pipe:

```python
cd.show_cube_lexcube(cube, cmap="RdBu_r")
```
This is handy when you already have an `xarray` object and just want a quick look.

Lexcube widgets render only in live notebook environments (JupyterLab, VS Code, Colab, Binder).
On the static docs site you will see screenshots or Binder links instead.

---

## Original Reference (kept for context)
# Lexcube integration

Lexcube provides interactive 3D exploration of `(time, y, x)` climate cubes. CubeDynamics exposes both a pipe verb (`v.show_cube_lexcube`) and a functional helper (`cd.show_cube_lexcube`) so you can embed the widget anywhere in your workflow. The verb displays the widget as a side effect and returns the original cube so the pipe chain can continue unchanged.

## Example workflow

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_prism_cube(
    lat=40.0,
    lon=-105.25,
    start="2000-01-01",
    end="2020-12-31",
    variable="ppt",
)

# Focus on summer months and show the cube in Lexcube
pipe(cube) \
    | v.month_filter([6, 7, 8]) \
    | v.show_cube_lexcube(title="PRISM JJA precipitation", cmap="RdBu_r")
```

Pick whichever AOI input fits your workflow—`lat`/`lon` point, `bbox`, or a
GeoJSON feature via `aoi_geojson`. Only one AOI option may be set per call.

Behind the scenes the verb routes `(time, y, x)` data into Lexcube's widget API. As long as the cube is a 3D `xarray.DataArray` (or a Dataset with a single variable), the visualization launches instantly in a live notebook.

You can also call the helper directly when you are not inside a pipe:

```python
cd.show_cube_lexcube(cube, cmap="RdBu_r")
```

## Notebook-only behavior

Lexcube widgets run only in live Python environments (JupyterLab, VS Code, Colab, Binder). They will not render on the static documentation site, so screenshots and Binder links are provided for reference.

![Stylized Lexcube example](img/lexcube_example.svg)

*The SVG is a stylized capture so the documentation can ship a "screenshot" without introducing binary assets.*

[🔗 Launch this example on Binder](https://mybinder.org/v2/gh/CU-ESIIL/climate_cube_math/HEAD?labpath=notebooks/lexcube_example.ipynb)
