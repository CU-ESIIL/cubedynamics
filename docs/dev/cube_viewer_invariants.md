# Cube viewer invariants

## The cube coordinate convention (the invariant)

All cube-attached features use the same coordinate convention. This is the single most important rule for avoiding frustration.

- The cube is centered at the origin of its transform space.
- Cube edge length is `S = var(--cd-cube-size)` (fallback `--cube-size`).
- Half size is `H = 0.5 * S`.

We refer to corners using **front/back**, **left/right**, **bottom/top**.

- **Front** is the face closest to the viewer at the default view.
- **Back** is the opposite face.
- **Left/Right** are from the viewer’s perspective at the default view.
- **Bottom/Top** are vertical.

### Axis rig placement

We anchor axes at two corners:

- **Origin XY** = **front-bottom-left** corner  
- **Origin T**  = **front-bottom-right** corner  

Axis directions:

- **Longitude (X axis)**: along the **front-bottom** edge, left → right  
- **Latitude (Y axis)**: along the **front-left** edge, bottom → top  
- **Time (T axis)**: along the **bottom-right** edge, front → back (“depth”)

Time ordering:

- **Newest time (tN)** is at the **front** where time meets the longitude corner.
- **Oldest time (t0)** is at the **back** end of the time axis.

If you change these conventions, update all axis placement math and tick placement logic together.

### Readable labels and the homepage presentation

Only label faces billboard toward the camera; their axis groups stay attached to
the cube. For a camera `rotateX(x) rotateY(y)`, labels apply
`rotateY(-y) rotateX(-x)` in reverse order. Time labels first cancel their
group's local `rotateY(90deg)`. All intermediate label/tick containers preserve
3D transforms. Axis colors inherit the viewer theme, and the legend's panel and
text colors use the same theme rather than mixing a fixed white card with dark-mode text.
Zoom uses uniform `scale3d` on all three dimensions; 2D `scale` distorts the
depth dimension and prevents the label rotations from cancelling correctly.
`AxisRigSpec.time_format` optionally shortens dates (the default remains
`%d.%m.%Y`); the homepage uses day/month/year labels so each date on the cube
is self-contained, independent of the heading.

The homepage uses `scripts/build_real_data_assets.py` and the small
`docs/assets/styles/hero-cube.css` presentation layer. Rebuild the HTML from the
hash-verified fixtures; do not patch generated HTML. The default PRISM cube's
Celsius scale is explicitly −25 to 20, with a build-time units/range guard.
The dropdown inventory lives in `scripts/hero_examples.py`; each example keeps
its own quantity, units, dates, source notes and fixed color limits. Its manifest
is checked in docs CI before publication. The cube geometry,
front/newest convention, and six measured-data faces are unchanged. The stage
reserves space above the legend and disables horizontal drift in this embed.

Drag or arrow keys rotate; scroll or `+`/`-` zoom; `Home` restores the initial
camera. Optional buttons with `data-cube-control="in"`, `"out"`, or `"reset"`
use these same viewer controls, not a separate homepage camera implementation.
