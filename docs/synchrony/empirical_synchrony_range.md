# Empirical local synchrony range

The empirical synchrony-range experiment asks how far focal-centered climate
synchrony remains detectably organized before its annular response approaches a
distant, potentially nonzero background. It does not estimate dispersal,
mechanistic correlation length, or a distance-decay kernel.

## Relationship to the validated workflow

The experiment reuses `v.local_synchrony_pairs(...)` without changing its
scientific semantics:

- cold synchrony is exact Spearman dependence on joint lower-tail TMIN days,
  where both endpoints are at or below their own pair-valid median;
- warm synchrony is exact Spearman dependence on joint upper-tail TMAX days,
  where both endpoints are strictly above their own pair-valid median;
- pairwise `Delta_S = S_cold - S_warm`;
- distance is great-circle distance in kilometers;
- canonical undirected pairs are calculated once within each bounded input;
- the self-pair is excluded before reduction.

`v.empirical_synchrony_range(...)` consumes that sparse relationship Dataset.
It does not stack local maps, align overlapping landscapes, run a second
convolution, or apply distance weights.

## Empirical criterion

The default experiment uses 20 km annuli inside a 500 km discovery radius. For
cold, warm, and Delta it retains annular median, IQR, count, and cumulative
median. Cold and warm ranges are estimated separately.

Three empirical background definitions are retained for comparison:

1. the median of the four most distant well-supported annular medians;
2. the median of the corresponding three-shell median-smoothed profile;
3. the median of the distant-pair reference distribution.

The first is the predeclared primary background. A candidate range is the outer
edge of the first of three consecutive, well-supported annuli that:

- are within an adaptive tolerance of the selected background;
- have successive cumulative-median changes no larger than 0.01; and
- are followed by at least 80% of supported annuli within twice the annular
  tolerance.

The annular tolerance is the larger of 0.03 and 1.5 robust standard deviations
of the outer annular medians, capped at 0.10. A response with total supported
profile range below 0.04 is recorded as flat/no identifiable focal signal. A
candidate at or beyond 80% of the discovery radius, or a response with no
qualifying candidate, is unresolved. The discovery boundary is never assigned
as the range.

The primary adaptive Delta uses one neighbor set. When both tail ranges resolve,

```text
R_common = max(R_cold, R_warm)
Delta_adaptive = median[S_cold(i,j) - S_warm(i,j), d(i,j) <= R_common]
```

Tail-specific adaptive cold and warm summaries are also retained, but they are
not subtracted to construct the primary Delta.

## Bounded real-data gate

The retained PRISM window is 2023-11-01 through 2024-01-30. Five representative
CONUS pixels and 25 spatially balanced Colorado pilot sites were tested with
10, 20, and 40 km bins and 200, 300, 400, and 500 km discovery radii. The fixed
100 km control reproduced the validated Colorado baseline exactly, and manual
annular counts and reductions passed.

The scientific scale-up gate is on **HOLD**:

- zero of five representative pixels resolved a common range at the primary
  500 km/20 km setting;
- one of 25 Colorado pilot sites resolved a common range;
- 96% of Colorado common ranges were censored or unresolved; and
- zero of 25 Colorado sites had a common range stable between the 400 and
  500 km primary-bin analyses.

These results do not show that synchrony has no spatial structure. They show
that this deterministic kernel-agnostic criterion does not yet identify a
stable scalar common range for this single winter window. Full-state and CONUS
adaptive-range maps are therefore withheld instead of filling unresolved cells
with 500 km.

## Outputs and limitations

Evidence is under `artifacts/empirical-synchrony-range/`, including the pair
checkpoints, annular pilot Dataset, representative curves, sensitivity tables,
anisotropy diagnostic, figures, decision gate, performance record, provenance,
and exact reproduction command.

The 25-site Colorado product is a bounded method pilot, not a statewide raster.
The single winter window does not establish temporal stability. Directional
sector estimates are frequently unresolved, so a scalar isotropic range is not
validated. A future experiment should test longer discovery support or a
different predeclared empirical criterion on independent temporal windows
before considering a production-scale run.

