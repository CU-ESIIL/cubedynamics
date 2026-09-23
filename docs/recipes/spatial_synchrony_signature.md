# Local climate-tail synchrony surfaces

Use this recipe to study how nearby center locations organize the synchrony
around a focal pixel. The full local surface is the scientific object:

```text
climate cube -> pair synchrony S(i,j) -> local surface S_p(dx,dy)
                                             |       |       |
                                           radial  angular  2-D shape
                                             \       |       /
                                              candidate signature

center landscapes M_i --------------------------------> landscape change
```

Distance and direction are coordinates of `S_p(dx,dy)`. They are not, by
themselves, the inferred synchrony scale or final signature.

## Build canonical pairs

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

temperature = cd.load_prism_cube(
    variables=["tmin", "tmax"],
    bbox=(-106.2, 39.0, -104.0, 41.0),
    start="2023-11-01",
    end="2024-01-30",
    freq="D",
    chunks={"time": 31, "y": 64, "x": 64},
    allow_synthetic=False,
)

pairs = (
    pipe(temperature)
    | v.local_synchrony_pairs(
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output_mask,
        max_radius_km=100,
        window_days=90,
        split_quantile=0.5,
        min_t=10,
    )
).unwrap()
```

`max_radius_km=100` is the observation radius: the farthest center observed
around each focal pixel. It is not an assumed 100 km characteristic scale.
Each eligible undirected pair is calculated once and stores cold, warm,
pairwise `cold - warm`, signed displacement, distance, and bearing.

## Recover a complete audit surface

```python
surface = (
    pipe(pairs)
    | v.local_synchrony_surface(focal_y_index=10, focal_x_index=10)
).unwrap()

surface["delta_s"].plot(x="offset_x_index", y="offset_y_index")
```

The returned values point from the focal pixel to each center. If the focal is
the canonical target of a stored edge, displacement is negated and bearing is
rotated 180 degrees. Cold, warm, and Delta surfaces remain available side by
side.

Do this for selected audit or sampled pixels. Do not save a dense
`focal_y × focal_x × offset_y × offset_x` object statewide.

## Evaluate compact descriptions

```python
diagnostics = (
    pipe(surface)
    | v.synchrony_surface_diagnostics(
        metric="delta_s",
        radial_bin_width_km=5,
        angular_bin_width_degrees=15,
        min_count=3,
    )
).unwrap()
```

The result contains fine radial and radially detrended angular profiles plus
candidate harmonic, half-plane, characteristic-scale, and low-order 2-D
reconstruction diagnostics. These fields are experimental. A scale near the
observation limit is labeled right-censored or unresolved; a surface may have
no identifiable scale or multiple candidate scales.

Compare candidate reconstructions to the full surface before promoting any
descriptor. In particular, keep axis-like anisotropy distinct from one-sided
boundary-like contrast.

## Nested radii are a baseline

```python
baseline = (
    pipe(pairs)
    | v.synchrony_signature(radii_km=(25, 50, 75, 100))
).unwrap()
```

This exact cumulative calculation remains useful for measuring compression
loss and for Phase 1 compatibility. It is not the primary representation.
Likewise, median and IQR describe overall magnitude and heterogeneity but do
not preserve spatial organization.

## Output geometry and computation halo

Political or study boundaries define output focal cells, not climate
neighborhoods. Use `expand_spatial_domain(geometry, 100)` for the computation
geometry and `spatial_output_mask(cube, geometry)` for retained outputs. A
Colorado analysis reads the 100 km neighboring-state halo but saves Colorado
focal pixels only.

`tiled_synchrony_signature(...)` remains the restartable statewide baseline
orchestrator. Every output tile receives its full observation-radius halo;
cross-tile endpoint recomputation changes cost, not values.

## Landscape change is separate

```python
change = (
    pipe(pairs)
    | v.landscape_change_signature(metric="delta_s", min_overlap=25)
).unwrap()
```

This compares complete center landscapes when the center moves. It is distinct
from within-surface structure and from geographic change in surface
descriptors.

The verbs accept any compatible observed latitude/longitude climate cube.
PRISM is the Phase 2 example, not a hidden requirement. The workflow does not
silently substitute synthetic data, approximate the synchrony kernel, infer
regimes, or claim a characteristic scale beyond its observation window.
