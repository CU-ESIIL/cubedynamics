# Glossary

Terms for the [semantic model](semantic_grammar.md). They describe software
interpretation, not independent verification of scientific meaning.

| Term | Meaning and boundary |
| --- | --- |
| Environmental product | Provider-published observations/estimates with a procedure, coverage, support, units and revision history |
| Observation | A product value, including measured, interpolated, remotely retrieved, modeled or derived values |
| Noun | Readable environmental input name; provider/product source qualifier retains observational identity |
| Verb | Named operation; a configured factory stage accepts the current value. Some public helpers are direct calls rather than factories |
| Parameter | Explicit setting such as dimension, threshold, comparator, quantile or connectivity |
| Cube | Labeled multidimensional scientific object; common rasters have `time`, `y`, `x` and optional `band`, but the grammar also accepts static, vector, station and summary shapes |
| Pipe | Wrapper passing the value through callables in authored order and recording local inspection state; not a scheduler |
| Analysis/workflow | The analysis is the sequence interpreted scientifically; the workflow also includes preparation, environment, storage and later work |
| Condition | Dataset with Boolean `state`, optionally defined magnitude/threshold; not a general unknown/invalid-value model |
| Reduction/summary | Removal of named variation; a condition mean is an indexed occurrence proportion rather than a Boolean condition |
| Branch | Separately composed pipe; unwrapping before combination does not merge complete upstream histories |
| Semantic state | Declared or metadata-inferred current role and context; not a new container hierarchy or scientific certification |
| Trace | Completed stages, parameters, messages and transitions within one pipe; work before `pipe()` and after `unwrap()` is outside it |
| Provenance | Source, request, processing and derivation records; broader than the local trace |
| Observation support | Area/time interval represented by a value; coordinate equality alone does not establish matching support |
| Alignment | Explicit computational relationship of operands; not evidence of product interchangeability |
| Anomaly | Departure from a declared baseline; subtracting a selected-month mean is not necessarily a climatological anomaly |
| Climatology | Explicitly defined longer-term reference, with period and method; not a synonym for every selected-period mean |
| Co-occurrence | Conditions satisfied together under declared alignment; does not by itself establish synchrony, causality or impact |
| Synchrony | Project methods measuring temporal/spatial association under specific definitions; not interchangeable with every overlap statistic |
| Fixture/QA | Fixed reviewed bytes and bounded checks with source, query, hashes and scope; not universal scientific truth |
| Vignette | Executable scientific question, data, code, figures, interpretation and reproduction record |
| Guardrail | Rule that rejects or reports a cataloged mismatch; successful execution still needs scientific review |
| VirtualCube | Deferred representation whose specific operations/materialization contract determines laziness |
| Fire VASE/hull | Project vocabulary for time-indexed fire geometry; not a competing definition of the minimal grammar |

The nine runtime roles are `observation`, `continuous_field`,
`categorical_field`, `condition`, `event`, `feature`, `relationship`, `summary`,
and `network`. Detailed [data](scientific_data_contract.md),
[condition](condition_contracts.md), and
[branch](trace_and_workflow_provenance.md) contracts own their boundaries.
Everyday words such as function, workflow, overlap, event and anomaly should
not be mechanically replaced by verb, pipe, synchrony, regional episode or
climatology: each has its own scope.
