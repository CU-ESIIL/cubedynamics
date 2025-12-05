# CubeDynamics (`cubedynamics`)

> Climate cubes with a grammar-of-graphics framework and a streaming-first renderer for scientific-quality 3D visuals.

CubeDynamics turns climate and NDVI rasters into tidy cubes and lets you explore them with ggplot-inspired pipes:

```python
from cubedynamics import pipe, verbs as v

pipe(cube) | v.plot()
```

The cube viewer is **streaming-first** (designed for PRISM, gridMET, Sentinel-2, and other huge archives) and **grammar-based** so you can build layered figures, legends, captions, and facets.

## Quickstart

Install from PyPI or GitHub:

```bash
pip install cubedynamics
# or latest main branch
pip install "git+https://github.com/CU-ESIIL/climate_cube_math.git@main"
```

Render a cube immediately:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(lat=40.0, lon=-105.25, start="2018-01-01", end="2019-12-31")

(pipe(ndvi)
 | v.plot(title="NDVI cube", fig_id=1, fig_title="Front range greenness")
)
```

## Quickstart: 3-D cube viewer

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

# Example: load an NDVI cube (time, y, x)
ndvi = cd.load_example_ndvi_cube()  # or use an existing helper

pipe(ndvi) | v.plot(title="NDVI")
```

`v.plot()` is a high-level, streaming-first 3-D viewer. Under the hood it builds a
`CubePlot` (grammar-of-graphics) and routes frames through the streaming renderer so
you can keep working with in-memory arrays, dask-backed cubes, or `VirtualCube`
streams.

**Interaction tips:**

- Rotate by dragging anywhere in the cube frame (faces or transparent padding).
  A dedicated drag surface captures the pointer so rotation keeps flowing even if
  your cursor slips outside the canvas mid-gesture.
- Zoom with a trackpad pinch or mouse scroll.

## Troubleshooting interactivity

- Trust the notebook output (Jupyter: *File → Trust Notebook*) so the inline
  JavaScript that powers the cube viewer can run.
- Disable script-blocking browser extensions for the notebook domain while
  testing; the viewer attaches dynamic pointer/mouse/touch listeners.
- Try a modern browser (Chrome or Firefox). Safari sometimes throttles
  PointerEvents in embedded outputs; toggling ``debug=True`` surfaces
  ``[CubeViewer debug]`` logs in the developer console so you can confirm
  whether events are firing.
- If interaction still fails, render ``pipe(ndvi) | v.plot(debug=True)`` and
  watch the console for ``pointerdown``, ``mousedown``, ``touchstart``, and
  ``wheel`` messages.

## Developer notes

- The helper ``cubedynamics.plotting.cube_viewer._write_demo_html()`` writes a
  standalone ``cube_demo.html`` with simple color blocks. Open it directly in a
  browser to confirm dragging/zooming work even outside Jupyter—handy before and
  after refactors.

## Why a grammar of graphics for climate cubes?

Climate cubes are small stacks of maps through time (typically `(time, y, x)` and optional `band`). A grammar keeps the visualization expressive while staying readable:

- **Data**: VirtualCube or xarray DataArray
- **Aesthetics (`aes`)**: `fill`, `alpha`, `slice`
- **Stats (`stat_*`)**: `stat_time_mean`, `stat_time_anomaly`, `stat_space_mean`
- **Geoms (`geom_*`)**: `geom_cube`, `geom_slice`, `geom_outline`, `geom_path3d` (stub)
- **Scales**: `ScaleFillContinuous`, `ScaleAlphaContinuous`
- **Coordinates**: `coord_cube`
- **Themes**: `CubeTheme`, `theme_cube_studio`
- **Facets**: `facet_wrap`, `facet_grid`
- **Annotations**: `annot_plane`, `annot_text`

```python
from cubedynamics.plotting.cube_plot import CubePlot

p = (CubePlot(ndvi)
     .aes(fill="ndvi")
     .stat_time_anomaly(time_dim="time")
     .geom_cube()
     .scale_fill_continuous(center=0, palette="diverging")
     .coord_cube(elev=35, azim=45)
     .theme_cube_studio()
     .annot_plane(axis="time", value="2018-07-01", text="Fire event")
)

p.save("ndvi_anomaly.html")
```

## Streaming-first rendering

VirtualCube streams large datasets lazily without ever calling `.values` on the full cube:

- Iterates over time slices and encodes only 2D frames
- Shows an inline progress bar in notebooks
- Facets subset cubes one slice at a time with shared scales
- Works for multi-year NDVI, NEON towers, PRISM and gridMET pulls
- Automatically downsamples very large cubes for interactive viewing; pass
  ``full_res=True`` to ``v.plot`` to bypass the decimation when testing
  full-fidelity outputs.

Performance tips:

- Use chunked data and keep cubes lazy (`dask` arrays)
- Avoid forcing `.compute()`; let the viewer stream
- Lower `thin_time_factor` for quick previews

## Scientific-quality defaults

Captions support figure numbers, markdown, and math; legends inherit palettes from `ScaleFillContinuous`; CSS variables expose theme colors for polished exports. The studio theme ships with balanced background, axis, and legend colors suited for reports.

## Example: NDVI anomaly cube

```python
from cubedynamics import verbs as v, pipe
from cubedynamics.plotting.cube_plot import CubePlot

ndvi = cd.ndvi(lat=40.0, lon=-105.25, start="2017-01-01", end="2020-12-31")

figure = (CubePlot(ndvi, title="NDVI anomaly")
          .aes(fill="ndvi")
          .stat_time_anomaly(time_dim="time")
          .geom_cube()
          .scale_fill_continuous(center=0, palette="diverging")
          .coord_cube(elev=30, azim=60)
          .facet_wrap(by="year")
          .annot_plane(axis="time", value="2018-06-10", text="Smoke plume")
          .theme_cube_studio()
)
figure.save("ndvi_anomaly_facets.html")
```

See the [CubePlot Grammar of Graphics](docs/cubeplot_grammar.md) and the [Streaming-First Renderer](docs/streaming_renderer.md) pages for the full narrative and gallery examples.

## Vase Volumes: Cutting 3-D Shapes Out of Climate Cubes

A **vase volume** is a time-varying polygon cross-section over `(x, y)` that traces out a 3-D hull as it moves through `(time, y, x)`.
Use `VaseDefinition` to describe the polygons, `v.vase_extract(...)` to mask the cube, and let `v.plot()`
auto-detect and overlay the vase outline.

```python
import numpy as np
import shapely.geometry as geom
from cubedynamics import pipe, verbs as v
from cubedynamics.plotting import CubePlot
from cubedynamics.vase import VaseSection, VaseDefinition

cube = ndvi  # DataArray (time, y, x)

t0, t1 = cube.time.values[[0, -1]]
y_center = float(cube.y.mean())
x_center = float(cube.x.mean())
radius = 0.2 * min(float(cube.x.max()-cube.x.min()),
                  float(cube.y.max()-cube.y.min()))

poly_t0 = geom.Point(x_center, y_center).buffer(radius)
poly_t1 = geom.Point(x_center, y_center).buffer(1.5 * radius)

sections = [VaseSection(time=t0, polygon=poly_t0),
            VaseSection(time=t1, polygon=poly_t1)]
vase = VaseDefinition(sections=sections, interp="nearest")

vase_cube = v.vase_extract(cube, vase)

# High-level pilot viewer
pipe(vase_cube) | v.plot(title="NDVI inside vase")

# Grammar-of-graphics control
p = (CubePlot(cube)
     .stat_vase(vase)
     .geom_cube()
     .geom_vase_outline(color="limegreen", alpha=0.6))
p
```

- Vases are analytic volumes in `(time, y, x)` defined by polygons through time.
- `v.vase_extract` masks the cube and attaches the vase definition in `attrs["vase"]`.
- `v.plot()` auto-detects `attrs["vase"]` and adds the outline overlay.
