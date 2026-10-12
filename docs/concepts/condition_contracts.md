# Conditions reductions and missing observations

This page carries the detailed interpretation from the retained October 12
manuscript collection, SI S6–S8 (Tables S4–S9). It complements the current
[semantic grammar](semantic_grammar.md) and generated verb references. The SI
reports evidence accessed September 25, 2026; its historical statements do not
extend the public rc3 artifact to later development code.

## Canonical objects

| Operation | Returned interpretation | Definition fields |
| --- | --- | --- |
| [threshold_state](../reference/verbs/threshold_state.md) | Condition Dataset with Boolean `state` | Meaningful magnitude and threshold may be retained |
| [quantile_state](../reference/verbs/quantile_state.md) | Condition Dataset with Boolean `state` | Empirical threshold and associated magnitude may be retained |
| [overlap](../reference/verbs/overlap.md) | Condition Dataset with Boolean `state` | No invented magnitude or threshold |
| [mean](../reference/verbs/mean.md) of a condition | Summary Dataset with floating-point `state` | Auxiliary magnitude and threshold arrays are not averaged |
| Threshold of a summary | A new condition | Its threshold defines a new question on the aggregate |

The condition mean is an unweighted proportion over indexed positions along
the chosen dimension. It does not supply area or exposure weights. If the
question concerns magnitude, select and reduce magnitude explicitly. Variance
squares known physical units (`degC^2`, `mm^2`, `(m s-1)^2`); dimensionless
values remain dimensionless and unknown units remain unknown. This is a
metadata contract, not a complete unit algebra.

## Inclusive comparisons and the denominator

`direction="above"` includes equality (`>=`); `direction="below"` includes
equality (`<=`). The current two-valued condition model compares missing
numerical values as **false**, although a retained magnitude remains missing.
An arithmetic mean of Boolean state counts that indexed position in the
denominator as a non-occurrence.

For values `[2, missing, 4]` and the condition `value >= 3`, the state is
`[false, false, true]`. Its indexed occurrence proportion is `1/3`; the
proportion among the two valid observations would be `1/2`. Those denominators
answer different questions. A condition reduction must not be described as
valid-observation frequency unless finiteness has been established or the
analyst has explicitly managed validity outside this operation.

The SI identifies a validity mask, a declared missing-value policy, and a
three-valued condition as possible remedies. These are design alternatives,
not implemented promises. It also records no package-specific minimum-valid
count or quantile-interpolation parameter. Empirical quantiles delegate to
xarray defaults; archive the dependency version and method, especially for
short samples and ties. The selected time axis is gathered into one Dask
chunk for quantile calculation while spatial chunks are retained.

## Order and retained information

The four documented order categories distinguish required order,
meaning-changing order, removal of required information, and conditional
equivalence. On the field `{0, 2, 4, 6}` with cutoff `T <= 3`, threshold then
spatial mean gives `0.5`; spatial mean then threshold gives `TRUE`. Both are
valid authored statements. See [the order lesson](../learn/order.md).

Subtracting a fixed climatology and spatial averaging can commute when both
paths use identical linear weights and masks: `mean(T - C) = mean(T) -
mean(C)`. Changed masks, missingness, interpolation, weights, or climatology
break those assumptions. The grammar explains such rules without rewriting
the expression.

Event detection requires an ordered temporal condition with remaining
variation. A length-one time coordinate left after reduction does not restore
that variation. Detection yields local-cell events; consolidation into regional
episodes requires declared temporal gaps and spatial connectivity. Metrics
retain that scope. See [events and episodes](events_and_episodes.md).

## Contract status and rendering

| Status used in the SI | Meaning |
| --- | --- |
| Machine-enforced | Execution checks a rule and fails on violation |
| Diagnosed | A maintained message exposes a semantic distinction |
| Metadata-inferred | State derives from dimensions, coordinates, dtype, or attributes |
| Documentary | Interpretation or evidence scope is explained but not independently verified |

These labels are a reporting framework; a submission needs exact test
identifiers to establish which individual rules were exercised. Incorrect or
stale input metadata remain possible in every interpretation.

The SI plotting matrix maps a three-dimensional spatiotemporal field to a cube,
a two-dimensional spatial summary to a map, and a one-dimensional temporal
summary to a line plot. Conditions select `state`; appropriate event views
select `event_active`. An ambiguous general Dataset needs explicit variable
selection. Plotting retains the wrapped value but may materialize data.
Optional Lexcube availability is an environment issue. See
[visualization reference](../api/viz.md) for current dispatch and limitations.

Source: [retained SI, pp. 9–14](../assets/manuscripts/2026-10-12/supplement-11.pdf#page=9).
