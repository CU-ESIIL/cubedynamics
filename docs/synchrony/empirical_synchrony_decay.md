# Empirical synchrony decay

`v.empirical_synchrony_decay(...)` asks **how synchrony changes with physical
distance**. It does not require the relationship to end at one finite radius.
That distinction matters because a rapid near-field decline can coexist with a
weaker, broader spatial tail.

The verb consumes the sparse relationships from
`v.local_synchrony_pairs(...)`. It reuses physical distance, lower-tail TMIN
synchrony, strictly upper-tail TMAX synchrony, and pairwise
`Delta S = S_cold - S_warm`. It does not reacquire observations, fit a
parametric kernel, apply distance weights, or force the empirical curve to be
monotonic.

```python
from cubedynamics import pipe, verbs as v

decay = (
    pipe(pairs)
    | v.empirical_synchrony_decay(
        discovery_radius_km=500,
        bin_width_km=20,
        min_annulus_count=30,
        background_shell_count=4,
        background_method="outer_annuli",
        local_shell_count=2,
        crossing_persistence_bins=2,
        min_local_excess=0.04,
        initial_window_km=100,
    )
).unwrap()
```

Every argument above is in the current public signature. Omit
`discovery_radius_km` to use the pair table's available support.

## Read the outputs in plain language

The complete empirical evidence remains available before any scalar
description:

- the annular median synchrony curve;
- annular quartiles and IQR;
- the number of valid relationships in each annulus;
- the cumulative median curve;
- the lightly smoothed curve used only for persistent fractional crossings;
  and
- normalized excess synchrony above the selected empirical background.

The compact fields are calculated independently for cold and warm synchrony:

| Output | Plain-language meaning |
| --- | --- |
| `d25` | Distance where 25% of locally elevated synchrony above background has been lost |
| `d50` | Distance where 50% of that local excess has been lost |
| `d75` | Distance where 75% of that local excess has been lost |
| Effective length `L` | Integrated positive area under the normalized excess-synchrony curve |
| Initial slope | Robust change across the configured initial distance window |
| Near slope | Robust change over 0–100 km |
| Middle slope | Robust change over 100–300 km |
| Far slope | Robust change over 300–500 km |
| Fraction lost by 100 km | Share of the initial excess synchrony no longer present at 100 km |

`d25`, `d50`, and `d75` are **fractional-decay coordinates**. They are not
automatically neighborhood radii, dispersal distances, kernel bandwidths, or
climate-region boundaries. A crossing must persist; unreached or
poorly-supported fractions remain right-censored or unresolved.

Effective synchrony length `L` integrates the positive normalized excess curve
from the focal neighborhood toward the discovery boundary. It is not a hard
cutoff. Boundary excess and the fraction of integrated area in the last 100 km
are retained so an apparently finite `L` can be marked boundary-dependent.

The slopes describe different parts of the spatial relationship rather than
one fitted law. They are robust Theil–Sen slopes of supported annular medians,
reported per 100 km. The initial slope is background-free; near, middle, and
far slopes make multiscale behavior visible.

## Why one scalar radius can fail

Imagine synchrony falling quickly in the first 100 km and then declining only
slightly across several hundred more kilometers. The near slope is steep, the
far slope is shallow, and fractional-decay distances may still be resolvable.
Yet no sharp endpoint exists. That is structured spatial decay, not an absence
of spatial structure.

This is why the decay verb answers a different question from
[`empirical_synchrony_range()`](empirical_synchrony_range.md). Range asks
whether a persistent approach to background supports a finite convergence
distance. Decay describes the continuous relationship even when the range
question remains unresolved.

## Cold, warm, and contrasts

Cold and warm metrics are estimated independently. The Dataset reports a
cold-minus-warm contrast for `d50`, `L`, or initial slope only when both
component metrics have resolved status. Those contrasts compare spatial extent
or rate. They are not `Delta S`, which is the pairwise synchrony-strength
contrast at a particular relationship.

## Bounded evidence, not an API guarantee

The retained 25-site Colorado table and five representative CONUS pair tables
were reused without pair recomputation. At the primary 500 km / 20 km setting,
tail-specific `d50` resolved much more often than the earlier common finite
range. Near-field decay was often steeper than far-field decay. However, warm
`d50` did not meet the predeclared discovery-stability gate, effective length
was boundary-sensitive, and the cold initial slope was bin-width-sensitive.
The candidates therefore remained on **HOLD** for statewide mapping.

That result motivates the public interpretation but is not hard-coded as an
API outcome. Other inputs can legitimately return resolved, censored,
insufficient-support, or nonpositive-local-excess statuses.

## Reproduce the bounded pilot

```bash
.venv/bin/python scripts/run_empirical_synchrony_decay_pilot.py
```

The command validates saved-pair checkpoint hashes and fails if required input
is missing. It does not silently acquire PRISM observations or launch a full
Colorado or CONUS analysis.

Return to the [complete local synchrony workflow](../recipes/spatial_synchrony_signature.md).
