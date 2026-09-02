# Event life-history and regime grammar: design boundary

This note records deliberately deferred long-record operations. Names here are
design candidates, not implemented public APIs.

## Event-relative trajectories

An eventual `align_events` or `event_trajectory` operation must require an
anchor (`start`, `peak`, or `end`), pre/post window, overlap policy when events
share observations, spatial extraction policy, and temporal-support alignment
choice. Its result should preserve absolute time, event ID, `event_day`, anchor
definition, source support, and missing-window behavior. Implementing only an
index shift would conceal scientific choices, so this pass does not expose the
verb.

## Period signatures and trends

`event_metrics(period="year")` already returns unit-labeled ordinary xarray
variables, one row per year. A later `period_signature` should assemble several
compatible metric objects only after feature names, missing periods, mixed
units, and source scopes have a stable contract.

A future linear `trend` verb would need an explicit independent coordinate,
calendar-unit conversion, missing-data policy, slope units, uncertainty model,
and autocorrelation caveat. It should not be a thin wrapper that presents an
ordinary regression as a universally valid environmental trend.

## Change points and event types

A change-point operation must state its supported methods, null statement,
uncertainty, minimum segment length, and representation of multiple candidate
changes. No arbitrary algorithm is promoted here.

Event classification should begin with inspectable features: duration, onset
rate, decay, severity, footprint, participation, trajectories, and ordering of
coupled variables. Opaque clustering remains downstream until those features
and regional episode semantics are mature.

## Plotting

Event catalogs and metrics remain ordinary pandas/xarray objects and can use
their native plotting methods. Specialized defaults for timelines, lag curves,
and trajectories are deferred until the underlying scientific objects settle;
the plotting layer must not define event meaning.
