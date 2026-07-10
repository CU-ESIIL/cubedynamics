# Roadmap and Validation

The synchrony framework is intentionally phased. The current implementation
covers the first reviewable pass across state cubes, events, four primitive
operators, spatial modes, biological cubes, and same-pixel coupling.

## Current Implementation

<div class="sync-card-grid">
  <div class="sync-card">
    <h3>Implemented</h3>
    <p>State constructors, event detection, occurrence, severity, timing, duration, biological rasterization, alignment, and same-pixel coupling.</p>
  </div>
  <div class="sync-card">
    <h3>Partly Implemented</h3>
    <p>Neighbor summaries, all-pairs outputs, block hooks, and event matching are usable but still early.</p>
  </div>
  <div class="sync-card">
    <h3>Deferred</h3>
    <p>Null models, bootstrap intervals, event graphs, recurrence, followed-by logic, climate networks, and streaming-scale event catalogs.</p>
  </div>
</div>

## Synthetic Truth Cases

The roadmap calls for deterministic examples where each primitive recovers only
the feature it is supposed to measure:

- Independent fields.
- Shared events.
- Lagged events.
- Shared occurrence with independent severity.
- Shared timing with different duration.
- Distance-decay synchrony.
- Spatial modules.
- Frost followed by biological boom.
- Repeated fire with recurrence effects.
- Compound drought-plus-heat events.

The current website assets exercise shared events, lagged responses, timing
lags, and duration differences. More synthetic validation notebooks should be
added as the grammar matures.

## Diagnostics Still Needed

- Event prevalence maps.
- Synchrony-distance curves.
- Threshold sensitivity surfaces.
- Bootstrap confidence intervals with block methods.
- Null models preserving autocorrelation and seasonality.
- Metric comparison panels.
- Matched-event timelines.
- Cross-process lag curves for multiple mechanisms.

## Developer Reference

The repo-native design roadmap is here:
[Synchrony Roadmap](../project/synchrony_roadmap.md).

The public verb reference is here:
[Synchrony Verbs](../reference/verbs_synchrony.md).
