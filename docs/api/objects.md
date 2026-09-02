# Objects

Reference objects used by the public grammar. Signatures and methods below
come from Python docstrings. Not every object is a raster cube.

## Pipe

Wraps a value and records the written operation sequence.

::: cubedynamics.piping.Pipe
    options:
      members: [unwrap, explain, suggest, validate, semantic_state, semantic_trace]
      show_docstring_examples: false

## VirtualCube

Defers source reads and materialization. See [streaming](../streaming/index.md)
for source and tile contracts.

::: cubedynamics.streaming.VirtualCube
    options:
      members: [materialize]
      show_docstring_examples: false

## State and event results

Conditions are xarray Datasets with a Boolean `state` variable. Threshold and
quantile constructors additionally expose scientifically defined `magnitude`
and `threshold` variables; logical `overlap` contains only `state` and operand
metadata. [detect_events](../reference/verbs/detect_events.md) turns a temporal
condition into an event result with a dataset and catalog. See the
[state/event analysis](../vignettes/states_and_events.ipynb). Its
`event_scope` states whether one row is a local-cell instance or consolidated
regional episode; catalog length is not scientifically interpretable without
that scope. [consolidate_events](../reference/verbs/consolidate_events.md) and
[event_metrics](../reference/verbs/event_metrics.md) preserve it.

::: cubedynamics.events.EventResult
    options:
      members: [unwrap, explain, event_scope, spatial_identity_fields]
      show_docstring_examples: false

## Runtime identity

`version_info()` distinguishes an installed artifact from a VCS installation
or development checkout even when both intentionally retain the same semantic
version.

::: cubedynamics.runtime.RuntimeInfo
    options:
      members: [as_dict, development]
      show_docstring_examples: false

## Fire geometry

FireEventDaily and FireHull are the canonical event/geometry model. TimeHull
is a compatibility name. A VaseDefinition describes a time-varying polygon
volume; it is not itself a provider dataset.

::: cubedynamics.ops_fire.time_hull.FireEventDaily
    options:
      show_docstring_examples: false

::: cubedynamics.vase.VaseDefinition
    options:
      show_docstring_examples: false

## See also

[Fire architecture](../dev/fire_plot_architecture.md) · [Semantic grammar](../concepts/semantic_grammar.md) ·
[Source revision objects](data.md) · [Public API stability](../project/public_api.md)
