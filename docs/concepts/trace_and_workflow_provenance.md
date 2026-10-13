# Local traces and workflow provenance

The main manuscript §3 and SI S4–S5 separate an analytical statement from the
wider computational workflow. A concise pipe sits above source-qualified
nouns, configured transformations, state, trace, source queries, provenance,
fixtures, QA, and tests. Decision context remains outside software authority.
These layers let a reviewer descend into the evidence beneath the expression.

## Local record boundary

The [semantic model](semantic_grammar.md) owns the state vocabulary and
inspection methods. A trace covers completed stages in one pipe. Provenance
also identifies source inputs, derivations, environment and work before
`pipe()` or after `unwrap()`. Those wider records need explicit retention.

## Branches require separate records

In Working Lands, temperature and precipitation each produce a condition in
their own pipe. The final pipe receives the unwrapped conditions, combines
them, and reduces time. It records overlap definitions and exact alignment,
but does not automatically merge both complete upstream histories.

| Object to retain | Accompanying record |
| --- | --- |
| Temperature branch | Source query, units, quantile parameters, messages, state transitions |
| Precipitation branch | Source query, units, inclusive threshold, messages, state transitions |
| Final overlap and mean | Selected variables, overlap definition, alignment requirement, reduction dimension, final state |
| Percent presentation | Multiplication by 100 after unwrapping, recorded in the notebook or project |

Retaining only the final pipe loses part of the analytical argument. SI Table
S17 specifies these record types; it does not provide the exact serialized
outputs. The [worked protocol](../documentation/working_lands_protocol.md)
keeps that evidence boundary explicit.

## User callables and ordinary arrays

An ordinary callable can participate without subclassing or registration.
`apply` forwards the current object to user code and infers output state from
the returned public object. Values, dimensions, and shape are controlled by
that callable. Its scientific intent is not validated by a maintained verb
contract, and the trace does not archive its source code or implementation
revision. Project provenance must retain those identifiers and tests.

Nouns and conditions remain ordinary xarray objects. NumPy or Dask execution
belongs to the underlying stack when the operation permits it. A lazy array
does not demonstrate bounded remote transport. Record transport behavior
separately from array evaluation.

Use [runtime identity](../getting_started/runtime_identity.md) to record the
version, imported path, artifact kind, and available Git identity. A semantic
version alone cannot distinguish rc3 from a later checkout or stale kernel.
That report also does not archive the rest of the environment.

Continue with [custom verbs](../extending/custom_verbs.md),
[provenance](../learn/provenance.md), and
[submission evidence](../project/manuscript_evidence_2026_10.md).

Source: [main, pp. 5–7](../assets/manuscripts/2026-10-12/main-39.pdf#page=5)
and [SI, pp. 5–9](../assets/manuscripts/2026-10-12/supplement-11.pdf#page=5).
