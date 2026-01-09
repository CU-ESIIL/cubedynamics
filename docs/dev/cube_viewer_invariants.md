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
