# Synchrony Verbs

Synchrony verbs live in `cubedynamics.verbs` and are pipe-friendly.

## State constructors

- `v.threshold_state(threshold, direction, variable=None, name=None)`
- `v.quantile_state(quantile, direction, rolling_window=None, climatology=None, variable=None, name=None)`
- `v.binary_state(variable=None, name=None)`
- `v.change_state(change, threshold, lag, variable=None, name=None)`
- `v.exceedance(...)`, alias for `v.threshold_state(...)`

Each constructor returns a Dataset with `state`, `magnitude`, and `threshold`.

## Events

- `v.detect_events(state_var="state", magnitude_var="magnitude", min_duration=1, max_gap=0)`

Returns an `EventResult` with `.dataset` and `.catalog`.

## Synchrony primitives

- `v.occurrence_synchrony(...)`: Jaccard, joint probability, or phi occurrence synchrony.
- `v.severity_synchrony(...)`: magnitude co-variation during jointly active states.
- `v.timing_synchrony(...)`: one-to-one event timing synchrony.
- `v.duration_synchrony(...)`: one-to-one event duration synchrony.

Spatial modes include `reference`, `neighbors`, `all_pairs`, `regional`, and
`blocks`. Use `reference="center"` for center-pixel compatibility.

## Biology and coupling

- `v.rasterize_observations(observations, template, ...)`
- `v.align_cube(like, spatial_method="nearest", temporal_method="nearest", tolerance=None)`
- `v.sync_with(other, synchrony="occurrence", spatial_relation="same_pixel", lags=("0D",))`

`v.sync_with` currently supports same-pixel lagged occurrence coupling.
