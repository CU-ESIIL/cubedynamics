---
description: "Why CubeDynamics distinguishes computational repeatability from scientific inspectability, and how statements, state, trace, sources, and evidence fit together."
---

# Scientific inspectability

Environmental questions that sound simple often compress choices about
observations, statistics, transformations, and assumptions into a short script.
Rerunning that script can establish computational repeatability without making
the scientific question easy to recover.

CubeDynamics addresses that gap by placing an **inspectable environmental
grammar** around ordinary scientific Python objects. It does not replace xarray,
Dask, NumPy, or geospatial libraries. It keeps the meaning of an analytical
statement available while those libraries perform the numerical work.

## A readable expression and an inspectable foundation

The grammar connects two levels:

| Level | What it contains | What it lets a reader ask |
| --- | --- | --- |
| Analytical expression | A source-qualified noun, configured verbs, explicit parameters, and authored order | What question did the code ask? |
| Inspectable foundation | Semantic state, ordered trace, source records, provenance, contracts, tests, and bounded QA | What changed, what evidence supports the abstraction, and where are its limits? |

The compact expression is useful only when a reader can move downward from it.
That relationship motivates a design maxim from the current manuscript draft:

> The shorter the analytical expression becomes, the stronger the evidence
> underneath it must become.

## Source-qualified nouns

A noun names the environmental information being analyzed. Its source flavor
identifies the provider and product that give the noun observational meaning.

```python
from cubedynamics import data

prism_temperature = data.temperature(
    source="prism",
    statistic="maximum",
    bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-01-01",
    end="2024-01-30",
)
```

The shared noun is a common entry point, not a claim of equivalence. PRISM and
gridMET temperature retain different native variables, units, grids, statistics,
revision behavior, and provenance. Unit conversion or regridding may create
computational compatibility without making two products scientifically
interchangeable.

[Compare the temperature sources →](../library/nouns/temperature.md)

## Semantic verbs and explicit modifiers

A configured verb describes a transformation and carries a semantic contract.
Its parameters say how the operation is performed—for example, over which
dimension, in which direction, or at which threshold.

```python
from cubedynamics import pipe, verbs as v

analysis = (
    pipe(prism_temperature)
    | v.anomaly(dim="time")
    | v.variance(dim="time", keep_dim=False)
)
```

Not every argument is merely a modifier. The second observation passed to a
combining verb such as `overlap` is another scientific operand. The public
reference documents each callable's actual convention instead of forcing every
operation into one shape.

## Authored order is scientific syntax

CubeDynamics calls every stage once, from left to right, exactly where the
researcher wrote it. It never rearranges a pipeline. That guarantee matters
because order can change the question:

| Authored sequence | Scientific object produced |
| --- | --- |
| threshold cells → spatial mean | Fraction of cells satisfying a condition |
| spatial mean → threshold | One regional Boolean state |

Both can be reproducible and mathematically valid. They are not the same
analysis. Order rules therefore explain required, meaning-changing,
information-removing, or conditionally equivalent sequences; authority remains
with the researcher.

[Work through the order lesson →](../learn/order.md)

## State and trace make the statement recoverable

After each completed stage, semantic state describes the current scientific
object: its role, dimensions, units, CRS, spatial and temporal status, remaining
variation, source flavor, and available provenance. The trace records completed
operations, parameters, and state transitions in authored order.

```python
print(analysis.explain())
print(analysis.semantic_state.as_dict())
print([step.as_dict() for step in analysis.semantic_trace])
report = analysis.validate()
result = analysis.unwrap()
```

These inspection methods are metadata-only. They do not rewrite the workflow,
choose a scientifically appropriate source, or compute lazy arrays solely to
infer semantics. `unwrap()` is a local statement boundary: it returns the
ordinary Python value, but does not force computation, certify the result, or
complete the wider workflow.

## Evidence has distinct jobs

Concise source access rests on several kinds of evidence. They should not be
collapsed into one broad claim.

| Evidence | Supports | Does not establish |
| --- | --- | --- |
| Retrieval and live health | The requested bytes and access behavior were available at a recorded time | Continued endpoint availability |
| Fixture and provenance | The reviewed bytes, query bounds, checksum, and upstream identity | All places, periods, or provider observations |
| Structural interpretation | Variables, dimensions, coordinates, units, CRS, masks, and schema | Observational accuracy |
| Numerical and visual review | Plausibility and adapter behavior for a bounded example | Causation, decision fitness, or universal source validity |

A serving revision identifies CubeDynamics' adapter and interpretation contract,
not a provider's scientific version. A successful fixture check is not a live
certification, and a trace is not complete workflow provenance: work before
`pipe(...)` and after `unwrap()` remains outside it.

[See the validation evidence →](../validation/index.md)

## Scope of the claim

CubeDynamics aims to compress implementation complexity without compressing
away scientific meaning. It does not select the right source for a question,
remove observational bias, make products interchangeable, schedule a workflow,
certify provider observations, or establish that a result is fit for a decision.

The current release candidate demonstrates a small linear grammar and a bounded
two-noun composition. A complete branch-and-join language and very-large
many-dataset synthesis remain design challenges, not current capability claims.

This page adapts the conceptual framing of the
[current manuscript draft](../documentation/main-17.pdf). The manuscript is
editorial material and a dated snapshot; the [public API](../project/public_api.md),
runtime, tests, and generated references remain the sources of truth for
implemented behavior.

## Continue

[Learn the grammar](../learn/index.md) ·
[Inspect semantic behavior](semantic_grammar.md) ·
[Browse source-qualified nouns](../library/index.md) ·
[Run real-data vignettes](../vignettes/index.md)
