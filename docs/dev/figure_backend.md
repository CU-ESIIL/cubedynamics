# Figure backend (v.plot)

## The mental model

The viewer is plain HTML/CSS/JS. The cube is a DOM element that is rotated in 3D using CSS transforms. Everything that should move *with the cube* must live under the same transform node.

There are three distinct layers:

1. **Scene container**: provides perspective and camera-like effects (CSS `perspective`).
2. **Cube transform node**: the element that receives rotation transforms (drag-to-rotate).
3. **Cube content**: faces (textures) + any cube-attached overlays (axes rig, etc.).

If you inject UI into layer (1) it will look like a screen overlay.  
If you inject UI into layer (3) it will move with the cube.

## 3) Data-to-axis mapping (numbers and tick labels)

Axis values and tick labels come from the DataArray coordinates in Python.

- Lon/Lat endpoints come from coordinate bounds (or min/max).
- Time endpoints come from the time coordinate.
- Time ticks are generated in Python (monthly by default) and serialized to JSON for the viewer.

The viewer JS should render ticks from metadata; it should not “scrape” dates from the HTML payload.
