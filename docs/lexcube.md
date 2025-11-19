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
