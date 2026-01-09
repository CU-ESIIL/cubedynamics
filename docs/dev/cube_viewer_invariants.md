# Cube viewer invariants

This page is the authoritative source of truth for how the cube viewer must behave. If a change conflicts with these rules, the change is wrong.

## DOM Invariants

- `.cd-cube` exists and is cube-local.
- Overlays that must rotate live under `.cd-cube`.

## Spatial Invariants

- Cube origin is the center.
- Front face = most recent time.
- Positive Z points toward the viewer.

## Axis Invariants

- Time axis is depth.
- Ticks must be attached to explicit axis containers.
- Fallback ticks must not introduce misleading labels.

## Label Invariants

- Labels may billboard (face the viewer).
- Rails always rotate.

## Prototyping Invariants

- Patch both references.
- Reload before patching.
- Viewer output is always a string of HTML.

## If something looks wrong, check these first

- Is the overlay attached inside `.cd-cube`?
- Are you reasoning from the cube center, not a corner?
- Is time placed so the front is newest and the back is oldest?
- Are ticks anchored to explicit axis containers?
- Are labels billboarding unintentionally or missing inverse rotation?
