# Conditions and missing observations

This is the canonical condition and denominator contract for current
development behavior. It complements the [semantic model](semantic_grammar.md)
and [data contract](scientific_data_contract.md). Tests, rather than the
retained manuscript prose, establish behavior; see
[claim-to-evidence](../validation/methods.md#claim-to-evidence-matrix).

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

[The order lesson](../learn/order.md) owns the threshold/mean example and
conditional equivalence. [Events and episodes](events_and_episodes.md) owns
local detection, explicit consolidation, connectivity and metric scope. A
reduction that erases temporal variation cannot be repaired by retaining a
length-one coordinate.

## Numeric masks need a separate validity decision

The callable returned by `binary_state()` currently uses Boolean casting when
called directly on a numeric array. Finite zero becomes false, a
nonzero value becomes true, and **numeric NaN also becomes true**. This differs
from threshold comparison. It does not provide an invalid or unknown state.
Supply a reviewed Boolean mask rather than assuming every numeric mask is
missing-aware. The pipe preflight rejects an inferred continuous field for
`binary_state`; direct invocation does not perform that pipe-level check.

This deterministic example illustrates the contract; it is not environmental
measurement or scientific evidence.

<!-- condition-contract-example -->
```python
import numpy as np
import xarray as xr
from cubedynamics import pipe, verbs as v

values = xr.DataArray([2., np.nan, 4.], dims="time",
                      coords={"time": [0, 1, 2]})
condition = (pipe(values) | v.threshold_state(
    threshold=3, direction="above"
)).unwrap()
indexed = (pipe(condition) | v.mean(dim="time", keep_dim=False)).unwrap()["state"]
valid = values.notnull()  # This analytical choice is outside the condition.
valid_only = condition["state"].where(valid).mean("time")
cast_mask = v.binary_state()(values)["state"]  # Direct callable, without pipe preflight.
print(condition["state"].values.tolist())  # [False, False, True]
print(float(indexed), float(valid_only))   # 1/3 versus 1/2
print(cast_mask.values.tolist())          # [True, True, True]
```

| Term | What the implementation records | Scientific consequence |
| --- | --- | --- |
| False | Boolean non-occurrence | Threshold comparison cannot tell a failed criterion from a missing numerical input |
| Missing | May survive in magnitude; not a third state | Retain validity from the input if needed |
| Excluded | Analyst explicitly masks/drops positions before a valid-observation calculation | Record the changed support and denominator; not an automatic package policy |
| Invalid | No general quality-invalid state distinct from missing/false | Apply and document source QA masks yourself |

The optional magnitude/threshold fields describe a condition; they are not
general validity flags. The occurrence summary retains its definition metadata,
but it does not add a valid-observation count or prove finiteness. Metadata
alone cannot resolve which denominator is scientifically appropriate.

Rendering and export are owned by [visualization](../api/viz.md) and
[serialization](scientific_data_contract.md#serialization). Exact current
signatures belong in the generated verb reference.
