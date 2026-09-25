# Local climate-tail synchrony: pairs, surfaces, summaries, and scaling

Use this recipe when the question is how cold- and warm-tail climate
synchrony is organized around each focal location. The workflow has four
conceptual steps: **measure → organize → reduce or describe → characterize
spatial scaling**. After pair construction, the grammar branches; it is not one
mandatory linear pipeline.

> **Cold, warm, Delta, and color.** Cold synchrony is lower-tail TMIN
> joint-tail Spearman synchrony. Warm synchrony is upper-tail TMAX joint-tail
> Spearman synchrony. The signed contrast is `Delta S = S_cold - S_warm`:
> positive means cold synchrony is stronger; negative means warm synchrony is
> stronger. Live Delta figures use **blue for positive/cold-stronger** and
> **red for negative/warm-stronger**.

## The verb map

```text
CLIMATE CUBE
    |
    v
local_synchrony_pairs()                 MEASURE S(i,j)
    |
    +---------------------+----------------------+----------------------+
    |                     |                      |                      |
    v                     v                      v                      v
local surface        fixed support          finite range          spatial decay
    |                     |                      |                      |
    v                     v                      v                      v
local_synchrony_     synchrony_             empirical_             empirical_
surface()            signature()            synchrony_range()      synchrony_decay()
    |
    v
synchrony_surface_diagnostics()

landscape_change_signature() is a separate branch from the pair table:
it compares complete center landscapes as the center moves.
```

This map concerns the climate-tail vocabulary. CubeDynamics also has state,
event, occurrence, severity, timing, duration, and biological-coupling
synchrony verbs; see the [synchrony overview](../synchrony/index.md).

## Keep the scientific objects separate

| Object | Meaning | What it is not |
| --- | --- | --- |
| Pair synchrony `S(i,j)` | One symmetric cold, warm, or Delta relationship between two locations | A neighborhood summary or a scale |
| Local surface `S_p(dx,dy)` | Every eligible pair incident to focal location `p`, organized by relative displacement | A single median or radius |
| Center landscape `M_i(j)` | The field obtained by holding center `i` fixed and varying comparison location `j` | The focal surface viewed under an interchangeable index |
| Reduced focal value | One summary of eligible relationships associated with a focal pixel | A lossless representation of their spatial arrangement |
| Landscape change | A comparison of complete center landscapes as the center moves | Within-surface structure or geographic change in reduced focal values |

Distance and bearing are coordinates of a local surface. They do not become
inferred scales merely because they are available.

## 1. Measure canonical pairs

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

# In a production AOI, output_mask selects saved focal cells and
# computation_mask selects every eligible endpoint in the AOI plus halo.
computation_mask = (
    temperature[["tmin", "tmax"]]
    .to_array("variable")
    .notnull()
    .all(("variable", "time"))
)
output_mask = computation_mask

pairs = (
    pipe(temperature)
    | v.local_synchrony_pairs(
        lower_var="tmin",
        upper_var="tmax",
        output_mask=output_mask,
        computation_mask=computation_mask,
        max_radius_km=100,
        window_days=90,
        split_quantile=0.5,
        min_t=10,
    )
).unwrap()
```

For each endpoint pair, finite observations are paired first. If validity masks
differ, each endpoint's tail threshold is calculated on that pair-valid time
support; when all eligible pixels share the same valid dates, the exact
per-pixel threshold/state is safely reused. Cold selects dates where both TMIN
series are at or below their thresholds. Warm selects dates where both TMAX
series are strictly above their thresholds. Spearman correlation is then
calculated separately on the two joint tails, with joint counts retained.

The relationship table stores one canonical undirected edge rather than two
directed copies. It retains `cold_synchrony`, `warm_synchrony`, pairwise
`delta_s`, joint-tail counts, physical distance, bearing, signed grid and
kilometer displacement, endpoint indices, masks, and provenance. Self-pairs
are retained as audit anchors. The fixed-support baseline retains them, while
the empirical range and decay profiles explicitly use non-self relationships.

`max_radius_km` is the maximum observation/search support. It answers “how far
did this pair table look?” It does **not** assert a characteristic synchrony
distance.

### Output mask, computation mask, and halo

The output mask selects focal cells that will receive results. The computation
mask selects cells allowed to participate as either pair endpoint. For a state
or other bounded AOI, read a full `max_radius_km` halo, keep valid neighboring
cells in the computation mask, and retain only the AOI in the output mask. The
output mask must be a subset of the computation mask. A political boundary is
not a climate-neighborhood boundary.

## 2. Organize one focal surface

```python
surface = (
    pipe(pairs)
    | v.local_synchrony_surface(focal_y_index=10, focal_x_index=10)
).unwrap()

surface["delta_s"].plot(
    x="offset_x_index",
    y="offset_y_index",
    cmap="RdBu",
    center=0,
    cbar_kwargs={"label": "Delta S (red: warm stronger; blue: cold stronger)"},
)
```

The returned `S_p(dx,dy)` points from the focal pixel to every eligible center.
It retains signed `dx_km` and `dy_km`, distance, and focal-to-center bearing.
Canonical edge orientation is reversed where necessary so one focal surface is
geographically coherent.

The full Cartesian surface can expose directional structure, one-sided
contrasts, boundaries, and non-monotonic patterns that one median cannot
retain. Recover full surfaces for selected audit or sampled pixels rather than
saving a dense focal-by-offset object for every CONUS cell.

## 3. Describe surface structure

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

The output keeps fine radial medians and spread, radially adjusted directional
profiles, first- and second-harmonic strength and orientation, maximum
half-plane contrast, an interpretable low-order 2-D reconstruction, and its
residual error/complexity. Radial turns and candidate plateau status help flag
non-monotonic, multiscale, or boundary-limited behavior.

These are **experimental descriptors**, not a finalized signature or climate-
region classifier. Compare each compact reconstruction with the complete
surface before accepting it. Axis-like anisotropy and a one-sided boundary
contrast are different structures and should stay separate.

## 4. Reduce only when a reduced map is the desired product

```python
summary = (
    pipe(pairs)
    | v.synchrony_signature(radii_km=(25, 50, 75, 100))
).unwrap()
```

`synchrony_signature()` gives exact cumulative summaries at chosen supports:
cold and warm medians, median/IQR/MAD of pairwise Delta, counts, coverage, and
compact directional diagnostics. Nested supports are useful for comparison,
compression, mapping, compatibility, and sensitivity analysis. A requested
25, 50, 75, or 100 km support is not thereby a natural synchrony scale.

This branch is intentionally lossy. It preserves the requested summary but
discards most spatial arrangement after the reduction.

## 5. Ask whether a finite range can be resolved

```python
range_diagnostic = (
    pipe(pairs)
    | v.empirical_synchrony_range(bin_width_km=20)
).unwrap()
```

`empirical_synchrony_range()` asks whether cold and warm synchrony approach an
empirical background clearly and persistently enough to identify a finite
range. The pair table's discovery radius defines where the diagnostic looked;
it is not the answer. Boundary-limited, flat, insufficient, and unresolved
curves remain censored or missing rather than being filled with the discovery
limit.

If both tail ranges resolve, the implementation can report their maximum as a
common diagnostic and can compare a same-neighbor reduction with a fixed
control. That output does not make the common range a preferred production
neighborhood. In the recent single-window gate, a stable common cold/warm range
usually did not resolve, so `R_common` was **not** promoted into a general
adaptive-radius rule. Failure to resolve one scalar range does not mean that
the spatial relationship lacks structure.

Read the [finite-range method and bounded gate](../synchrony/empirical_synchrony_range.md).

## 6. Characterize continuous spatial decay

```python
decay = (
    pipe(pairs)
    | v.empirical_synchrony_decay(bin_width_km=20)
).unwrap()
```

`empirical_synchrony_decay()` asks the less restrictive question: **how does
synchrony change with distance?** It returns the original non-monotonic annular
median curve, annular IQR and counts, the cumulative median, and these compact
descriptors for cold and warm separately:

- `d25`, `d50`, and `d75`: distances where 25%, 50%, and 75% of locally
  elevated synchrony above the empirical background has been lost;
- effective synchrony length `L`: the integrated positive area under the
  normalized excess-synchrony curve;
- initial, near, middle, and far robust slopes, describing distinct parts of
  the spatial relationship; and
- the fraction of local excess synchrony lost by 100 km.

Cold-minus-warm contrasts are emitted only when both component metrics are
valid. These distance or slope contrasts are not pairwise `Delta S`.

The fractional-decay coordinates and `L` are not automatically neighborhood
radii, dispersal distances, kernel bandwidths, or climate-region boundaries.
`L` is an integrated curve property, not a hard cutoff. Synchrony can decline
rapidly near the focal location while a broader, weaker tail persists; one
scalar radius can therefore fail even when spatial decay is strongly
structured.

Read the [continuous-decay interpretation](../synchrony/empirical_synchrony_decay.md).

## Which branch answers which question?

| Question | Verb | Main output | What it means | What it does **not** mean |
| --- | --- | --- | --- | --- |
| What spatial organization exists before reduction? | `local_synchrony_surface()` | `S_p(dx,dy)` with displacement, distance, and bearing | Full local relational geography | A compact scale estimate |
| What is the reduced synchrony summary within chosen support? | `synchrony_signature()` | Nested fixed-support focal summaries | Compression or mapped comparison at declared radii | The radii are natural scales |
| Can a finite convergence distance be identified? | `empirical_synchrony_range()` | Tail-specific ranges, statuses, censoring, fixed control | A diagnostic of resolvable approach to background | A guaranteed adaptive neighborhood |
| How does synchrony change continuously with distance? | `empirical_synchrony_decay()` | Curves, fractional-decay distances, `L`, slopes, 100 km loss | Multiscale decay structure | A hard cutoff or dispersal kernel |

## Landscape change is a separate branch

```python
change = (
    pipe(pairs)
    | v.landscape_change_signature(metric="delta_s", min_overlap=25)
).unwrap()
```

For a center `i`, `M_i(j)` is the complete synchrony landscape obtained by
varying comparison location `j`. `landscape_change_signature()` compares
neighboring center landscapes along east-west and north-south axes. It reports
magnitude, rank, deadbanded sign, gradient, robust-range, and overlap
diagnostics without collapsing them into one universal index.

This is different from structure within one `S_p(dx,dy)` surface and from a
map of geographic change in one reduced focal summary.

## Stack/surface versus immediate reduction

Use a **stack or surface workflow** when the question concerns spatial
organization, direction, anisotropy, boundaries, heterogeneity, shape,
information loss, or representation. `local_synchrony_stack()` preserves many
center landscapes explicitly; the canonical pair table plus
`local_synchrony_surface()` reconstructs selected focal surfaces without a
dense statewide stack.

Use an **immediate-reduction workflow** when the desired product is one mapped
summary per focal cell and the complete local surface is not needed. This made
the retained Colorado and CONUS fixed-support products practical: tiles receive
full halos, canonical relationships are calculated, the requested robust
summary is written, and the tile's pair table can then be discarded. It is not
mathematically equivalent to retaining the surface; spatial arrangement is
intentionally lost after the summary is computed.

The restartable CONUS workflow used distinct output and computation masks and
reproduced every retained Colorado field exactly. That is evidence for tiling,
halo, masking, and immediate-reduction correctness—not evidence for a universal
scale.

## Observational agreement and limits

The CONUS fixed-support result was compared with a spatially balanced,
quality-controlled GHCN-Daily station network. This is **observational
agreement**, not an independent holdout or proof that PRISM is correct. PRISM
incorporates station information, exact station membership was unavailable,
pair edges share stations, and the station graph is spatially sparse. Keep
those dependencies visible when interpreting station-versus-grid agreement.

The current Colorado/CONUS evidence concerns one spatial analysis window. It
does not establish long-term climate change, changing extremes, historical
trends, universal characteristic distances, climate regimes, or dispersal
kernels. Historically anchored tails are a future extension; the current API
uses within-window relative tails.
