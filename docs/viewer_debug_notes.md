# Viewer debug notes

## 1. Call graph
- `v.plot()` builds a `PlotOptions` object and wraps an inner `_plot` that materializes virtual cubes, infers dims, and returns a configured `CubePlot` with geom/axes/theme set. The function returns either the `Verb` or the resulting `CubePlot`. 【F:src/cubedynamics/verbs/plot.py†L17-L108】
- `CubePlot.to_html()` prepares stats/annotations and calls `_render_viewer`, which constructs the viewer HTML via `cube_from_dataarray` with styling and legend metadata. `_repr_html_` simply delegates to `to_html()`. 【F:src/cubedynamics/plotting/cube_plot.py†L582-L804】【F:src/cubedynamics/plotting/cube_plot.py†L836-L839】
- `_render_viewer` hands off to `cube_from_dataarray` in `cube_viewer.py`, which renders faces/interior slices to base64 PNGs and assembles the WebGL viewer template. This template is the only HTML/JS builder on the Python side. 【F:src/cubedynamics/plotting/cube_plot.py†L629-L684】【F:src/cubedynamics/plotting/cube_viewer.py†L1-L120】

## 2. Python types
Running `python tools/debug_viewer_pipeline.py` prints:
```
CubePlot type: <class 'cubedynamics.plotting.cube_plot.CubePlot'>
v.plot return type: <class 'cubedynamics.plotting.cube_plot.CubePlot'>
```
So `v.plot()` still returns a `CubePlot` object. 【27a0d3†L1-L2】

## 3. Logging
- Added logging hooks: `v.plot()` now logs the cube name/dims when invoked; `CubePlot._repr_html_` logs when the HTML repr is requested. 【F:src/cubedynamics/verbs/plot.py†L81-L84】【F:src/cubedynamics/plotting/cube_plot.py†L836-L839】
- Enable by configuring `logging.basicConfig(level=logging.INFO)` in a notebook/kernel; watch stdout/stderr for calls when rendering.

## 4. HTML/JS template
- The viewer HTML is entirely generated in `cube_from_dataarray` and `_render_cube_html`. It currently uses a custom WebGL wireframe cube (`canvas.getContext("webgl")` plus manual shaders) rather than the previous Lexcube integration—no references to Lexcube remain. 【F:src/cubedynamics/plotting/cube_viewer.py†L90-L195】【F:src/cubedynamics/plotting/cube_viewer.py†L374-L520】
- The HTML builds a cube wrapper with `<canvas id="cube-canvas-{fig_id}">` and overlays axis labels/legend, but the JS only draws a wireframe cube; face textures are never applied to the canvas. PNG faces are still generated, but `_render_cube_html` only uses them as CSS backgrounds for `div` planes, which are missing in the current WebGL path. 【F:src/cubedynamics/plotting/cube_viewer.py†L30-L88】【F:src/cubedynamics/plotting/cube_viewer.py†L471-L520】
- No alternative templates are present; the current template is the single path invoked by `CubePlot`.

## 5. JS console
- Added guard logging around the viewer script; browser consoles should now show `[CubeViewer] script starting` and report `[CubeViewer] top-level error` if the script throws early. 【F:src/cubedynamics/plotting/cube_viewer.py†L369-L520】
- To capture errors: open DevTools → Console after running `pipe(ndvi) | v.plot()`; watch for those messages alongside any WebGL errors.

## 6. Double render?
- Searches show no `IPython.display.display` calls in plotting/verbs; rendering relies solely on the `CubePlot` return value and its `_repr_html_`. No evidence of double display. 【dbd202†L1-L1】

## 7. Eager loads
- Face PNGs and interior planes call `.values` on slices; this is necessary for encoding small 2D images. Bulk operations include downsampling via `coarsen(...).mean()` for interior planes. Potentially heavy if the cube is large and `thin_time_factor` is small. 【F:src/cubedynamics/plotting/cube_viewer.py†L638-L718】【F:src/cubedynamics/plotting/cube_viewer.py†L828-L868】
- Coordinate metadata lookups use `coord.values` but are lightweight. 【F:src/cubedynamics/plotting/cube_plot.py†L446-L474】

## 8. Hypotheses
- **H1:** Viewer shows blank center because the JS path now draws only a green wireframe cube; PNG face textures (data slices) are not being mapped anywhere in the WebGL canvas. The DOM also lacks the Lexcube/CSS 3D elements that previously displayed face images. 【F:src/cubedynamics/plotting/cube_viewer.py†L374-L520】【F:src/cubedynamics/plotting/cube_viewer.py†L30-L88】
- **H2:** Any WebGL init failure would now surface via `[CubeViewer] top-level error`; if errors appear, the script may be failing before draw (e.g., shader issues), leaving a blank canvas. 【F:src/cubedynamics/plotting/cube_viewer.py†L369-L520】
- **H3:** Slowness likely comes from full-face `.values` extraction and color mapping for each face plus interior downsampling; large cubes will still materialize multiple slices eagerly before rendering. 【F:src/cubedynamics/plotting/cube_viewer.py†L638-L718】【F:src/cubedynamics/plotting/cube_viewer.py†L828-L868】
