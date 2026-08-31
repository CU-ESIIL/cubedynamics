---
description: "How CubeDynamics describes nouns, verbs, semantic states, order, explanations, suggestions, and validation without rewriting a pipeline."
---

# Semantic Grammar and Analysis Coaching

CubeDynamics keeps its public language deliberately small:

```python
pipe(noun) | verb() | verb()
```

The semantic grammar describes that sentence while it runs. It does **not**
create a second language, reorder verbs, optimize a workflow, or replace plain
Python callables. Every stage is called once, from left to right, exactly where
the author wrote it.

This makes the pipeline more than a compact spelling of function calls: it is
an executable scientific statement whose authored syntax can be inspected.
Computational repeatability answers whether the statement can run again;
scientific inspectability also asks which observations entered, what object
each stage produced, and what evidence supports the path to the result. See
[Scientific inspectability](scientific_inspectability.md) for the full framing.

```text
scientific noun      configured verb       configured verb
      │                     │                     │
      ▼                     ▼                     ▼
  pipe(cube) ─────────► anomaly() ─────────► threshold_state()
      │                     │                     │
      └─ field metadata     └─ trace step         └─ condition metadata

                    execution is never rewritten
```

## The small state vocabulary

The grammar uses a compact vocabulary to describe what flows through the pipe.
This is semantic metadata, not a new set of runtime container classes.

| State | Meaning |
|---|---|
| `observation` | A value whose more specific role is not yet known |
| `continuous_field` | Numeric measurements distributed in space and/or time |
| `categorical_field` | Labels or categories distributed in space and/or time |
| `condition` | A true/false scientific state, with optional magnitude and threshold |
| `event` | One or more identified intervals or occurrences |
| `feature` | A discrete geometry or observation feature |
| `relationship` | A comparison, association, or synchrony result |
| `summary` | A reduction that no longer retains all source variation |
| `network` | Connected features with graph or flow semantics |

`SemanticState` also records dimensions, shape, units, CRS, temporal and
spatial status, time ordering, remaining time variation, source flavor, and
whether source provenance is present. Inference reads metadata and coordinates;
it does not compute array values.

## Verb contracts

The registry in `cubedynamics.grammar` describes a maintained starter set of
verbs. A `VerbSpec` names accepted and returned states, required information,
preserved or removed information, ownership category, and runnable examples.

```python
import cubedynamics as cd

event_contract = cd.grammar.get_verb_spec("detect_events")
print(event_contract.accepts)       # ('condition',)
print(event_contract.requires)      # time, ordered time, time variation

all_contracts = cd.grammar.list_verb_specs()
```

Unregistered callables still work normally. They appear in the trace by their
Python function name, and their result state is inferred from public metadata.
Projects therefore do not need a base class or registration step to create a
custom verb.

## Explain, suggest, and validate

The pipe exposes three optional coaching tools. None changes the value or
executes another analysis stage.

```python
analysis = (
    pipe(temperature)
    | v.anomaly(over="time")
    | v.threshold_state(threshold=2.0, direction="above")
)

print(analysis.explain())
analysis.suggest()
print(analysis.validate())
```

- `explain()` narrates the starting noun, each completed verb, the current
  state, and relevant order notes. It always states the no-rewrite guarantee.
- `suggest()` returns at most six compatible, implemented next verbs with a
  reason and runnable spelling. Conceptual or future verbs are never presented
  as runnable suggestions.
- `validate()` returns a structured `ValidationReport` and a readable summary.
  It checks semantic state, dimensions, ordered time, CRS, units, provenance,
  and order notes using metadata only. `CHECK` asks for human confirmation;
  only `ERROR` makes the report unsuccessful.

The immutable `semantic_trace` and current `semantic_state` are public for
notebooks, documentation, and agent tooling:

```python
analysis.semantic_state.as_dict()
analysis.semantic_trace[0].as_dict()
```

The trace covers only the inspected statement. Preparation before `pipe(...)`
and work after `unwrap()` remain outside it, so a semantic trace complements
rather than replaces general workflow provenance.

## Useful failures

Known incompatible steps fail before their technical implementation produces a
lower-level error. Messages identify what the verb expects, what the current
object represents, and a common repair. For example, `detect_events()` accepts
a temporal `condition`, not raw continuous temperature measurements:

```text
detect_events() groups consecutive true periods into events. The current
object is a continuous field ... so there is not yet a condition to group.
A common pattern is: observations → threshold_state(...) → detect_events().
```

A retained length-one `time` dimension after `mean(over="time")` does not fool
the grammar. The trace records that time variation was removed and recommends
detecting events before the reduction.

## Order knowledge

Order rules are explanatory knowledge, never rewrite instructions.

| Category | Meaning |
|---|---|
| `REQUIRED_ORDER` | The later operation requires a product of the earlier one |
| `ORDER_CHANGES_MEANING` | Both orders may run but answer different questions |
| `ORDER_REMOVES_REQUIRED_INFORMATION` | The earlier operation can erase information needed later |
| `ORDER_EQUIVALENT_OR_NEAR_EQUIVALENT` | The order is equivalent only under stated assumptions |

The curated library includes current paths such as anomaly → threshold,
threshold → events, threshold → mean, mean → threshold, and mean-over-time →
events. The two threshold/mean orders are both executable because they answer
different questions: the first measures condition prevalence, while the second
defines a condition from an aggregate. The trace records
`ORDER_CHANGES_MEANING`; it never substitutes one sentence for the other. It
also records spatial and
event concepts such as near/density, intersect/summarize, events/duration, and
upstream/intersect for future project vocabularies. Every rule has an
`implemented` flag. A conceptual rule is available to documentation and agent
tools but cannot become a `.suggest()` result until a corresponding public verb
actually exists.

For example, these two spatial sentences are both meaningful, but they do not
say the same thing:

| Written order | Plain-language interpretation |
|---|---|
| `buildings → near(streams) → density()` | Select buildings near streams, then calculate the density of those selected buildings |
| `buildings → density() → near(streams)` | Calculate building density everywhere, then inspect or annotate density relative to streams |

`near()` and `density()` are order-library concepts rather than current
CubeDynamics core verbs. They are documented here to show how a project verb
package can share the same coach. The `implemented=False` flag prevents either
one from being suggested as runnable core API.

```python
rules = cd.grammar.get_order_rules()
future_rules = [rule for rule in rules if not rule.implemented]
```

## Readable dimension keywords

Core reducers and normalizers accept the grammatical `over=` spelling:

```python
pipe(cube) | v.mean(over="time")
pipe(cube) | v.anomaly(over="time")
```

The established `dim=` spelling remains supported. Supplying conflicting
values for both names raises a direct error instead of guessing.

Reducers also replace inherited condition labels with summary metadata. For a
condition Dataset, `mean(...)` returns a summary Dataset containing only the
reduced `state` proportion. The condition's threshold definition remains in
Dataset metadata, but CubeDynamics does not silently average auxiliary
`magnitude` or `threshold` arrays. Reduce magnitude explicitly when that is the
scientific question. A later `threshold_state(...)` may consume a scalar or
spatial summary and creates a new condition with its own explicit threshold.

Variance summaries keep source and provenance metadata while changing physical
units deterministically: `degC` becomes `degC^2`, `mm` becomes `mm^2`, and a
compound unit such as `m s-1` becomes `(m s-1)^2`. Dimensionless variance stays
`1`; missing or explicitly unknown units are not invented.

## Statement boundary

The adoption path is deliberately reversible:

```text
xarray object → pipe → semantic operations and inspection → unwrap → xarray object
```

`unwrap()` acts as a local boundary marker between the inspected statement and
ordinary Python. It returns the wrapped value; it does not force computation,
certify the analysis, complete the wider workflow, or prevent the value from
entering another pipe.

## Architectural boundary

```text
┌──────────────────────────────────────────────────────────────┐
│ Public analysis: pipe(noun) | ordinary configured callables  │
└──────────────────────────────┬───────────────────────────────┘
                               │ observes completed stages
┌──────────────────────────────▼───────────────────────────────┐
│ Semantic layer: state + trace + contracts + order notes      │
│ explain()          suggest()          validate()              │
└──────────────────────────────┬───────────────────────────────┘
                               │ metadata only
┌──────────────────────────────▼───────────────────────────────┐
│ Existing xarray, streaming, event, and rendering runtimes    │
└──────────────────────────────────────────────────────────────┘
```

This boundary keeps the grammar useful to scientists and agents while leaving
runtime ownership with the established verb implementations.
