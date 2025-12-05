# Interactive cube viewer (`v.plot`)

The cube viewer turns a 3D climate cube into an interactive HTML scene. Call
`v.plot()` on an `xarray.DataArray` with dims like `(time, y, x)` to render the
cube inline in Jupyter or export standalone HTML.

The viewer is designed to:

- show temporal slices along one axis and spatial slices on the other faces;
- support rotation and zoom via mouse, touch, or trackpad;
- stream frames so large NDVI/PRISM/gridMET cubes stay responsive.

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2023-01-01",
    end="2024-12-31",
)

pipe(ndvi) | v.plot()
```

## Controls

- **Rotate:** click + drag (or touch and drag) anywhere on the cube.
- **Zoom:** mouse scroll wheel, trackpad scroll, or pinch on touch devices.
- **Reset view:** not yet implemented; re-run the cell to reset the camera.
- The viewer renders into a canvas inside the notebook output. The same HTML
  can be opened standalone for debugging.

## Saving and opening as HTML

Use the returned `CubePlot` to save a standalone HTML file for easier
inspection (no Jupyter iframe wrappers):

```python
plot = pipe(ndvi) | v.plot(title="NDVI cube")
plot.save("ndvi_cube.html")
```

Open the HTML directly from your file browser or, in JupyterLab, right-click
`ndvi_cube.html` and choose **Open in new browser tab**. Standalone HTML is the
recommended way to debug interactivity because it bypasses notebook sandboxing
and extension blockers.

## Performance and downsampling

`v.plot()` automatically downscales large cubes to keep the viewer responsive:

- time steps are capped around 120;
- spatial steps use every 2nd pixel when width/height exceed ~512.

This decimation only affects the rendered view; the original DataArray is not
modified. To preview snappier cubes yourself:

```python
small = ndvi.isel(time=slice(0, 60, 2), x=slice(None, None, 2), y=slice(None, None, 2))
pipe(small) | v.plot(title="Quick preview")
```

Pass `full_res=True` to `v.plot` when you need the complete cube for inspection,
but expect heavier rendering:

```python
pipe(ndvi) | v.plot(full_res=True)
```

## Troubleshooting interactivity

- **Notebook trust:** trust the notebook so JavaScript can run.
- **Browser:** use a modern browser; Chrome or Firefox are recommended.
- **Script blockers:** disable ad/script blockers for the notebook domain.
- **Try standalone HTML:** save to `cube.html`, open it in a new tab, and check
  whether rotation/zoom works there.
- **Warnings:** if you see “Interactive controls need JavaScript” or similar,
  open DevTools and look for console messages prefixed with `[CubeViewer]`.
- **Debug flag:** enable verbose logs for gesture handling:

  ```python
  pipe(ndvi) | v.plot(debug=True)
  ```

  Console logs like `[CubeViewer debug] drag move` and `[CubeViewer debug] wheel`
  confirm events are wired correctly.

## Developer notes: cube viewer invariants (do not break these)

Public API

- `pipe(cube) | v.plot()` must remain the primary entry point for an interactive
  3D cube. Additional keyword args (e.g., `debug`, `save`, `full_res`) stay
  optional with sensible defaults.
- `v.plot()` accepts an `xarray.DataArray` shaped like `(time, y, x)` (or dims
  inferred the same way) and should keep inferring dim names automatically.

DOM / HTML structure

- The root element uses `id="cube-figure-<uuid>"` and class `cube-figure` with
  data attributes `data-fig-id`, `data-debug`, and the initial rotation/zoom
  values.
- Child elements must preserve IDs/classes:
  - `cube-container` (class), `cube-wrapper-<uuid>` (id),
    `cube-drag-<uuid>` (id, drag surface), `cube-rotation-<uuid>` (id),
    `cube-js-warning-<uuid>` (id, JS fallback message).
- If IDs/classes change, update tests and this document together, ensuring the
  viewer stays interactive.

Event handling

- The drag surface registers **pointer**, **mouse**, and **touch** families:
  `pointerdown/move/up/cancel`, `mousedown/mousemove/mouseup`, and
  `touchstart/touchmove/touchend/touchcancel` must all update the same rotation
  and zoom state.
- Scroll/trackpad zoom uses a non-passive wheel handler (`{ passive: false }`)
  and calls `preventDefault()` to avoid page scroll.
- Disabling one event family in the future must not leave the viewer without
  drag or zoom support.

Render loop and performance

- The viewer should not spin an infinite `requestAnimationFrame` loop; redraws
  occur on init, drag, zoom, or resize.
- Downsampling for interactivity must only affect the view; the underlying
  DataArray must not be modified in place.
- WebGL failures must fail gracefully, falling back to CSS rotation instead of
  crashing the notebook output.

Debugging

- The `debug` flag must keep emitting console logs prefixed with
  `[CubeViewer debug]` for initialization and event handling.
- When initialization fails, show the `cube-js-warning-<uuid>` element with a
  human-readable message and log a `[CubeViewer] init error` (or similar) to the
  console.

Testing guardrails

- Keep a test that renders a tiny cube to HTML and asserts:
  - root `cube-figure-*` id + class exist;
  - drag surface (`cube-drag-*`) is present;
  - the script registers pointer/mouse/touch/wheel handlers;
  - the JS warning node (`cube-js-warning-*`) is in the markup.
- If DOM IDs/classes or script names change, update the tests alongside the
  implementation so interactivity cannot silently regress.

> Note for automated refactors (Copilot / Codex and similar): do **not** remove
> or rename the `v.plot` API, cube viewer root structure, or event registration
> logic without updating this section and the tests under `tests/`. Making the
> cube visible but non-interactive counts as a regression.
