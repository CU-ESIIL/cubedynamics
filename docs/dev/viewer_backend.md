# Viewer backend: how the HTML cube is built

This page explains how the interactive cube viewer is assembled, where the “edit points” live, and how to avoid common mistakes when working in 3D transform space.

## The mental model

The viewer is plain HTML/CSS/JS. The cube is a DOM element that is rotated in 3D using CSS transforms. Everything that should move *with the cube* must live under the same transform node.

There are three distinct layers:

1. **Scene container**: provides perspective and camera-like effects (CSS `perspective`).
2. **Cube transform node**: the element that receives rotation transforms (drag-to-rotate).
3. **Cube content**: faces (textures) + any cube-attached overlays (axes rig, etc.).

If you inject UI into layer (1) it will look like a screen overlay.  
If you inject UI into layer (3) it will move with the cube.

## Where to edit what

### 1) Geometry (lines, ticks, corner anchors)

Edits to “where things are in 3D” belong in the axis rig geometry and transforms:

- Corner anchor translations (built from ±H)
- Axis backbone placement
- Axis rotations (especially the time axis becoming depth)
- Tick mark anchoring to the backbone

If your tick marks do not intersect the backbone, it is almost always a transform/anchor issue (not a data issue).

### 2) Label faces (readability / billboarding)

Text labels are separate “faces” inside the rig.

Rule: **only the label face billboards**, not the whole rig.

This prevents unintended distortion and avoids changing cube faces/geometry.

Time labels require special handling because the time axis group is rotated to become depth. Time label faces apply a local correction rotation before billboarding so the text reads correctly.

### 3) Data-to-axis mapping (numbers and tick labels)

Axis values and tick labels come from the DataArray coordinates in Python.

- Lon/Lat endpoints come from coordinate bounds (or min/max).
- Time endpoints come from the time coordinate.
- Time ticks are generated in Python (monthly by default) and serialized to JSON for the viewer.

The viewer JS should render ticks from metadata; it should not “scrape” dates from the HTML payload.

## Common mistakes (and quick fixes)

### The axis rig moves but labels are unreadable
You probably billboarded the entire rig or applied billboard transforms at the wrong DOM level. Billboard only the inner label faces.

### The time axis points the wrong way
The time axis is implemented as a depth rail (front → back). If it points outward, you likely flipped the sign or used the wrong rotation direction.

Confirm:
- time axis group rotates into depth
- newest is at the front (x=0 in the time axis local space)
- oldest is at the back (x=S in the time axis local space)

### Tick marks float near the axis but do not touch it
Ticks must be anchored at the backbone y-position. A common error is offsetting ticks outward in y, which visually detaches them.

Fix pattern:
- center tick on its `left:%` with `translateX(-50%)`
- anchor tick top at the backbone with `translateY(-0.5 * line_width)`
- reserve outward offsets for tick labels (not tick marks)

### Endpoint labels land on interior ticks
This happens when you “make room for text” by subtracting a pixel width from the endpoint transform.

Instead:
- anchor endpoints at true ends (x=0 and x=S)
- apply a small configurable nudge outward

## Prototyping: monkey patching the viewer (optional)

For rapid iteration in notebooks, it can be helpful to monkey patch `cube_from_dataarray` to inject alternate CSS/HTML/JS.

This is not the primary development workflow. The canonical workflow is to edit the axis rig implementation and rebuild the package.

If you do monkey patch:
- inject under the cube transform node so it rotates with the cube
- avoid changing cube face transforms
- keep a visible “rig version badge” so you can confirm which patch is active
