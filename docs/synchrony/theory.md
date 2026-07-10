# Theory Map

Synchrony is coordinated dynamics. Correlation is one tool for measuring it,
but the synchrony grammar is broader: it asks which state was active, which
events were matched, which locations were compared, and which mechanism was
being tested.

## Traditions Being Connected

<div class="sync-card-grid">
  <div class="sync-card">
    <h3>Ecological Synchrony</h3>
    <p>Moran effects, rescue effects, portfolio effects, and community synchrony.</p>
  </div>
  <div class="sync-card">
    <h3>Climate Coherence</h3>
    <p>Spatial covariance, teleconnections, climate networks, and distance decay.</p>
  </div>
  <div class="sync-card">
    <h3>Event Statistics</h3>
    <p>Event synchronization, event coincidence analysis, and matched-event timing.</p>
  </div>
  <div class="sync-card">
    <h3>Tail Dependence</h3>
    <p>Quantile dependence, conditional correlation, and climate extremes.</p>
  </div>
  <div class="sync-card">
    <h3>Compound Events</h3>
    <p>Drought-plus-heat, frost-followed-by-boom, repeated fire, and legacy effects.</p>
  </div>
</div>

## Disentangling the Question

A synchrony result should make five choices visible:

1. What raw process was observed?
2. What state or event rule transformed it?
3. Which synchrony primitive was estimated?
4. Which spatial relationship was compared?
5. Which diagnostics say whether the estimate is trustworthy?

That is why CubeDynamics separates state construction, event detection,
synchrony estimation, and spatial aggregation.

## Data Model

```text
raw cube
  continuous values such as temperature, precipitation, abundance

state cube
  state, magnitude, threshold

event result
  event Dataset plus separate pandas event catalog

synchrony output
  maps, edge tables, regional summaries, block comparisons, or matrices
```

The old center-pixel median-split method still exists, but it is now framed as
one convenience recipe inside this larger grammar.

## What Remains Research-Grade Work?

The roadmap includes null models that preserve autocorrelation and seasonality,
bootstrap confidence intervals, threshold sensitivity surfaces, synchrony-
distance curves, event graphs, and sequence verbs such as `followed_by`,
`recurrence`, and `lagged_response`.

Those are intentionally not exposed as public stubs yet. They need explicit
statistical contracts before they become verbs.

See the full [Synchrony Roadmap](../project/synchrony_roadmap.md).
