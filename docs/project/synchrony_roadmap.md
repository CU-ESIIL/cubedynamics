# Synchrony Roadmap

This roadmap records the design intent behind the CubeDynamics synchrony
framework. The goal is to support synchrony as coordinated dynamics, not simply
as correlation.

## Scientific Foundations

The synchrony grammar is intended to bridge several research traditions:

- Ecological synchrony, including the Moran effect, rescue effects, portfolio
  effects, and community synchrony.
- Climate coherence, teleconnections, spatial covariance, and climate networks.
- Event synchronization and event coincidence analysis.
- Conditional dependence, quantile dependence, and tail statistics.
- Compound, sequential, and state-dependent environmental events.

The manuscript framing should position CubeDynamics as an implementation of an
event-based synchrony grammar: raw fields become states, states become event
histories, and synchrony operators ask mechanism-specific questions about those
histories.

## Canonical Data Model

- Raw cubes: continuous environmental or biological values over time and space.
- State cubes: boolean or weighted conditions with `state`, `magnitude`, and
  `threshold` variables.
- Event catalogs: one row per event with timing, duration, magnitude,
  recurrence, and links to previous events where available.
- Synchrony outputs: maps, edge tables, block comparisons, matrices, and
  regional summaries.
- Legacy and response cubes: future support for time-since-event, cumulative
  exposure, response kernels, and event graphs.

## Primitive Operators

The first implementation provides four primitive synchrony verbs:

- Occurrence synchrony: shared event or state occurrence.
- Severity synchrony: shared magnitude during joint occurrence.
- Timing synchrony: similarity in onset, peak, end, or threshold crossing.
- Duration synchrony: similarity in event persistence.

Future primitives may include legacy synchrony, recurrence synchrony,
event-sequence synchrony, and graph-based mechanism workflows.

## Spatial Modes

The shared spatial comparison engine should continue to support:

- Reference pixel or reference series comparisons.
- Neighborhood synchrony maps.
- All-pairs edge outputs for small problems.
- Regional summaries and synchrony-distance curves.
- Block comparisons and climate-network style analyses.

Relational results should remain relational. All-pairs and network outputs
should not be forced into fake `(time, y, x)` cubes.

## QA and Validation Plan

Synchrony operators need diagnostics beyond a single score:

- Event prevalence maps.
- Synchrony-versus-distance curves.
- Local synchrony maps.
- Threshold sensitivity surfaces.
- Joint sample-size diagnostics.
- Bootstrap confidence intervals, preferably with block methods.
- Null models preserving autocorrelation and seasonality.
- Metric comparison panels.
- Matched-event timelines.
- Cross-process lag curves.

Synthetic truth cases should demonstrate:

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

Each primitive should recover only the feature it is designed to measure.

## Development Phases

1. State cubes and occurrence synchrony.
2. Severity synchrony and compatibility with the rolling median-split recipe.
3. Event catalogs, timing synchrony, and duration synchrony.
4. Biological cubes and `sync_with`.
5. Event graphs, legacy effects, sequence analysis, null models, and climate
   networks.

The current implementation covers the first reviewable pass across phases 1-4.
Phase 5 remains intentionally deferred.

## Manuscript Path

Possible paper sequence:

1. What is synchrony?
2. Climate synchrony.
3. Primitive synchrony operators.
4. Mechanism-specific synchrony.
5. Complex ecological grammars.

The long-term target is a formal grammar for state-dependent environmental
synchrony, implemented as composable CubeDynamics verbs.
