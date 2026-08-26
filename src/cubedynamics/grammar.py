"""Semantic metadata and coaching for the CubeDynamics pipe grammar.

This module observes pipelines; it never reorders, rewrites, or executes a
stage.  The runtime contract remains ``pipe(noun) | verb() | verb()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import inspect
from typing import Any, Callable, Iterable, Mapping


SEMANTIC_KINDS = (
    "observation",
    "continuous_field",
    "categorical_field",
    "condition",
    "event",
    "feature",
    "relationship",
    "summary",
    "network",
)

REQUIRED_ORDER = "REQUIRED_ORDER"
ORDER_CHANGES_MEANING = "ORDER_CHANGES_MEANING"
ORDER_REMOVES_REQUIRED_INFORMATION = "ORDER_REMOVES_REQUIRED_INFORMATION"
ORDER_EQUIVALENT_OR_NEAR_EQUIVALENT = "ORDER_EQUIVALENT_OR_NEAR_EQUIVALENT"
ORDER_CATEGORIES = (
    REQUIRED_ORDER,
    ORDER_CHANGES_MEANING,
    ORDER_REMOVES_REQUIRED_INFORMATION,
    ORDER_EQUIVALENT_OR_NEAR_EQUIVALENT,
)


@dataclass(frozen=True)
class SemanticState:
    """Small, serializable description of the value at one pipeline stage."""

    semantic_name: str
    semantic_kind: str
    category: str | None = None
    dimensions: tuple[str, ...] = ()
    shape: tuple[int, ...] = ()
    units: str | None = None
    crs: str | None = None
    geometry_type: str | None = None
    temporal: bool = False
    spatial: bool = False
    time_ordered: bool | None = None
    has_time_variation: bool | None = None
    source_flavor: str | None = None
    source_provider: str | None = None
    provenance: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "semantic_name": self.semantic_name,
            "semantic_kind": self.semantic_kind,
            "category": self.category,
            "dimensions": list(self.dimensions),
            "shape": list(self.shape),
            "units": self.units,
            "crs": self.crs,
            "geometry_type": self.geometry_type,
            "temporal": self.temporal,
            "spatial": self.spatial,
            "time_ordered": self.time_ordered,
            "has_time_variation": self.has_time_variation,
            "source_flavor": self.source_flavor,
            "source_provider": self.source_provider,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class VerbSpec:
    """Machine-readable semantic contract for one public verb."""

    name: str
    description: str
    accepts: tuple[str, ...]
    returns: str
    requires: tuple[str, ...] = ()
    preserves: tuple[str, ...] = ()
    removes: tuple[str, ...] = ()
    category: str = "primitive"
    examples: tuple[str, ...] = ()
    side_effect: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "accepts": list(self.accepts),
            "returns": self.returns,
            "requires": list(self.requires),
            "preserves": list(self.preserves),
            "removes": list(self.removes),
            "category": self.category,
            "examples": list(self.examples),
            "side_effect": self.side_effect,
        }


@dataclass(frozen=True)
class GrammarMessage:
    severity: str
    code: str
    text: str

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "code": self.code, "text": self.text}


@dataclass(frozen=True)
class TraceStep:
    index: int
    verb: str
    parameters: Mapping[str, Any]
    input_state: SemanticState
    output_state: SemanticState
    messages: tuple[GrammarMessage, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "verb": self.verb,
            "parameters": dict(self.parameters),
            "input": self.input_state.as_dict(),
            "output": self.output_state.as_dict(),
            "messages": [message.as_dict() for message in self.messages],
        }


@dataclass(frozen=True)
class OrderRule:
    first: str
    second: str
    category: str
    explanation: str
    alternative: str | None = None
    implemented: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "first": self.first,
            "second": self.second,
            "category": self.category,
            "explanation": self.explanation,
            "alternative": self.alternative,
            "implemented": self.implemented,
        }


@dataclass(frozen=True)
class Suggestion:
    verb: str
    reason: str
    example: str

    def __str__(self) -> str:
        return f"{self.verb}: {self.reason} Example: {self.example}"


@dataclass(frozen=True)
class ValidationCheck:
    severity: str
    code: str
    text: str

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "code": self.code, "text": self.text}


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    checks: tuple[ValidationCheck, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": [check.as_dict() for check in self.checks]}

    def __str__(self) -> str:
        status = "ready" if self.ok else "needs attention"
        lines = [f"Semantic validation: {status}"]
        lines.extend(f"- {check.severity}: {check.text}" for check in self.checks)
        return "\n".join(lines)


class SemanticGrammarError(ValueError):
    """Raised when a known verb cannot operate on the current semantic state."""


_FIELD_KINDS = ("observation", "continuous_field", "categorical_field")
_ANY_KINDS = SEMANTIC_KINDS


def _spec(
    name: str,
    description: str,
    accepts: Iterable[str],
    returns: str,
    **kwargs: Any,
) -> VerbSpec:
    return VerbSpec(name, description, tuple(accepts), returns, **kwargs)


_VERB_SPECS: dict[str, VerbSpec] = {
    "mean": _spec(
        "mean", "average values over a named dimension", _FIELD_KINDS + ("condition",),
        "summary", preserves=("metadata", "laziness"), removes=("variation over reduced dimension",),
        examples=("v.mean(over='time')",),
    ),
    "variance": _spec(
        "variance", "measure variation over a named dimension", _FIELD_KINDS,
        "summary", preserves=("metadata", "laziness"), removes=("variation over reduced dimension",),
        examples=("v.variance(over='time')",),
    ),
    "anomaly": _spec(
        "anomaly", "express values as departures from a mean", _FIELD_KINDS,
        "continuous_field", requires=("time", "time_variation"), preserves=("dimensions", "laziness"),
        examples=("v.anomaly(over='time')",),
    ),
    "zscore": _spec(
        "zscore", "standardize values relative to their mean and spread", _FIELD_KINDS,
        "continuous_field", requires=("time", "time_variation"), preserves=("dimensions", "laziness"),
        examples=("v.zscore(over='time')",),
    ),
    "month_filter": _spec(
        "month_filter", "retain observations from selected calendar months", _FIELD_KINDS,
        "continuous_field", requires=("time",), preserves=("units", "spatial coordinates"),
        examples=("v.month_filter([6, 7, 8])",),
    ),
    "threshold_state": _spec(
        "threshold_state", "turn continuous values into a named true/false condition", _FIELD_KINDS,
        "condition", preserves=("dimensions", "provenance"),
        examples=("v.threshold_state(threshold=30, direction='above')",),
    ),
    "quantile_state": _spec(
        "quantile_state", "define a condition relative to an empirical quantile", _FIELD_KINDS,
        "condition", requires=("time", "time_variation"), preserves=("dimensions", "provenance"),
        examples=("v.quantile_state(quantile=0.9, direction='above')",),
    ),
    "binary_state": _spec(
        "binary_state", "normalize a binary mask into the state-cube contract",
        ("categorical_field", "condition"), "condition", preserves=("dimensions", "provenance"),
        examples=("v.binary_state()",),
    ),
    "change_state": _spec(
        "change_state", "define a condition from lagged change", _FIELD_KINDS,
        "condition", requires=("time", "time_variation"), preserves=("dimensions", "provenance"),
        examples=("v.change_state(change='absolute', threshold=1, lag=1)",),
    ),
    "exceedance": _spec(
        "exceedance", "alias for threshold_state", _FIELD_KINDS, "condition",
        preserves=("dimensions", "provenance"), examples=("v.exceedance(threshold=30, direction='above')",),
    ),
    "detect_events": _spec(
        "detect_events", "group consecutive true periods into events", ("condition",), "event",
        requires=("time", "ordered_time", "time_variation"), preserves=("spatial coordinates", "provenance"),
        examples=("v.detect_events(min_duration=2)",), category="semantic",
    ),
    "overlap": _spec(
        "overlap", "identify coincident truth in two exactly aligned conditions", ("condition",),
        "condition", requires=("exact_alignment",), preserves=("dimensions",),
        examples=("v.overlap(other_state)",), category="semantic",
    ),
    "occurrence_synchrony": _spec(
        "occurrence_synchrony", "compare co-occurrence among state cubes", ("condition",),
        "relationship", requires=("time",), category="semantic",
        examples=("v.occurrence_synchrony()",),
    ),
    "timing_synchrony": _spec(
        "timing_synchrony", "compare the timing of detected events", ("event",),
        "relationship", category="semantic", examples=("v.timing_synchrony()",),
    ),
    "duration_synchrony": _spec(
        "duration_synchrony", "compare the duration of detected events", ("event",),
        "relationship", category="semantic", examples=("v.duration_synchrony()",),
    ),
    "severity_synchrony": _spec(
        "severity_synchrony", "compare the severity of detected events", ("event",),
        "relationship", category="semantic", examples=("v.severity_synchrony()",),
    ),
    "plot": _spec(
        "plot", "render an interactive cube view", _ANY_KINDS, "observation",
        requires=("spatial",), category="integration", side_effect=True,
        examples=("v.plot()",),
    ),
    "plot_mean": _spec(
        "plot_mean", "render a spatial-mean time series", _FIELD_KINDS + ("condition",),
        "observation", requires=("time", "spatial"), category="integration", side_effect=True,
        examples=("v.plot_mean()",),
    ),
    "show_cube_lexcube": _spec(
        "show_cube_lexcube", "render a cube while preserving it in the pipe", _ANY_KINDS,
        "observation", requires=("time", "spatial"), category="integration", side_effect=True,
        examples=("v.show_cube_lexcube()",),
    ),
    "apply": _spec(
        "apply", "apply a user-supplied function without changing pipe syntax", _ANY_KINDS,
        "observation", category="integration", examples=("v.apply(function)",),
    ),
}


_ORDER_RULES: tuple[OrderRule, ...] = (
    OrderRule("anomaly", "threshold", REQUIRED_ORDER,
              "Thresholding anomalies asks where departures are unusual; reversing the order changes the question.",
              "Use threshold_state before anomaly only when the thresholded state itself is the quantity of interest."),
    OrderRule("threshold", "events", REQUIRED_ORDER,
              "Event detection groups consecutive true periods, so a condition must be defined first.",
              "Create a condition with threshold_state, quantile_state, binary_state, or change_state."),
    OrderRule("events", "duration", REQUIRED_ORDER,
              "Duration is an event property and requires events to be identified first.", implemented=False),
    OrderRule("events", "frequency", REQUIRED_ORDER,
              "Frequency counts identified events and therefore follows event detection.", implemented=False),
    OrderRule("events", "magnitude", REQUIRED_ORDER,
              "Event magnitude summarizes identified event intervals and therefore follows event detection.", implemented=False),
    OrderRule("mean", "events", ORDER_REMOVES_REQUIRED_INFORMATION,
              "A mean over time removes the temporal variation needed to identify event runs.",
              "Detect events before reducing over time."),
    OrderRule("aggregate", "onset", ORDER_REMOVES_REQUIRED_INFORMATION,
              "Aggregation can remove the first transition needed to identify onset.", implemented=False),
    OrderRule("filter", "change", ORDER_CHANGES_MEANING,
              "Filtering before change measures change only within the retained observations; changing first filters the derived changes.",
              "Choose the order that matches the scientific question.", implemented=False),
    OrderRule("transition", "summarize", REQUIRED_ORDER,
              "A transition summary requires transitions to be identified first.", implemented=False),
    OrderRule("summarize", "change", ORDER_REMOVES_REQUIRED_INFORMATION,
              "Some summaries remove the sequence needed to estimate change.", implemented=False),
    OrderRule("subtract", "divide", ORDER_CHANGES_MEANING,
              "Subtracting then dividing is a relative contrast; dividing then subtracting is a difference of ratios.", implemented=False),
    OrderRule("normalize", "threshold", ORDER_CHANGES_MEANING,
              "A threshold after normalization is expressed in standardized units, not source units.", implemented=False),
    OrderRule("near", "density", ORDER_CHANGES_MEANING,
              "Density near a target and proximity to dense areas answer different spatial questions.", implemented=False),
    OrderRule("intersect", "density", ORDER_CHANGES_MEANING,
              "Density within an intersection differs from intersecting a density surface.", implemented=False),
    OrderRule("intersect", "summarize", ORDER_CHANGES_MEANING,
              "Summarizing an intersection differs from intersecting already summarized objects.", implemented=False),
    OrderRule("clip", "summarize", ORDER_CHANGES_MEANING,
              "Clipping first summarizes only the study area; summarizing first may include values outside it.", implemented=False),
    OrderRule("exposure", "summarize", REQUIRED_ORDER,
              "An exposure summary requires exposure to be computed first.", implemented=False),
    OrderRule("near", "summarize", ORDER_CHANGES_MEANING,
              "Summarizing nearby observations differs from measuring proximity to a summary.", implemented=False),
    OrderRule("upstream", "intersect", ORDER_CHANGES_MEANING,
              "Intersecting an upstream network differs from asking what is upstream of an intersection.", implemented=False),
)


_ALIASES = {
    "threshold_state": "threshold",
    "quantile_state": "threshold",
    "binary_state": "threshold",
    "change_state": "threshold",
    "exceedance": "threshold",
    "detect_events": "events",
    "zscore": "normalize",
    "month_filter": "filter",
}


def get_verb_spec(name: str) -> VerbSpec | None:
    """Return the registered contract for ``name``, if one is known."""

    return _VERB_SPECS.get(name)


def list_verb_specs() -> tuple[VerbSpec, ...]:
    """Return registered contracts in deterministic name order."""

    return tuple(_VERB_SPECS[name] for name in sorted(_VERB_SPECS))


def get_order_rules() -> tuple[OrderRule, ...]:
    """Return the curated order knowledge, including not-yet-implemented concepts."""

    return _ORDER_RULES


def infer_semantic_state(value: Any) -> SemanticState:
    """Infer a semantic state from public metadata without computing data values."""

    if hasattr(value, "dataset") and hasattr(value, "catalog"):
        base = infer_semantic_state(value.dataset)
        return replace(base, semantic_name="detected events", semantic_kind="event", category="event")

    attrs = getattr(value, "attrs", {}) or {}
    dims_obj = getattr(value, "dims", ())
    if isinstance(dims_obj, Mapping):
        dimensions = tuple(str(dim) for dim in dims_obj)
    else:
        dimensions = tuple(str(dim) for dim in dims_obj)
    sizes = getattr(value, "sizes", {}) or {}
    shape = tuple(int(sizes[dim]) for dim in dimensions if dim in sizes)

    name = str(
        attrs.get("semantic_name")
        or attrs.get("scientific_noun")
        or attrs.get("state_name")
        or getattr(value, "name", None)
        or type(value).__name__
    ).replace("_", " ")
    kind = attrs.get("semantic_kind")
    analysis = attrs.get("analysis")
    if not kind and analysis == "state_cube":
        kind = "condition"
    elif not kind and analysis == "detected_events":
        kind = "event"
    elif not kind and _looks_boolean(value):
        kind = "condition"
    elif not kind and dimensions:
        kind = "continuous_field"
    elif not kind:
        kind = "observation"

    temporal = "time" in dimensions
    spatial = ({"x", "y"}.issubset(dimensions) or {"lon", "lat"}.issubset(dimensions))
    time_ordered = _time_is_ordered(value) if temporal else None
    time_size = int(sizes.get("time", 0)) if temporal else 0
    has_time_variation = time_size > 1 if temporal else None
    units = attrs.get("semantic_units") or attrs.get("units")
    if units is None and kind == "condition":
        units = "boolean"
    crs = attrs.get("crs") or attrs.get("spatial_ref")
    provenance = any(
        key in attrs
        for key in ("source_flavor", "source_provider", "source_product", "source", "provenance")
    )
    return SemanticState(
        semantic_name=name,
        semantic_kind=str(kind),
        category=attrs.get("semantic_category"),
        dimensions=dimensions,
        shape=shape,
        units=str(units) if units is not None else None,
        crs=str(crs) if crs is not None else None,
        geometry_type=attrs.get("geometry_type"),
        temporal=temporal,
        spatial=spatial,
        time_ordered=time_ordered,
        has_time_variation=has_time_variation,
        source_flavor=attrs.get("source_flavor"),
        source_provider=attrs.get("source_provider"),
        provenance=provenance,
    )


def inspect_stage(func: Callable[..., Any]) -> tuple[str, dict[str, Any]]:
    """Return a stable semantic stage name and simple bound factory arguments."""

    target = getattr(func, "func", func)
    explicit = getattr(func, "_cd_semantic_name", None) or getattr(target, "_cd_semantic_name", None)
    qualname = getattr(target, "__qualname__", "")
    name = str(explicit or _factory_name(qualname) or getattr(target, "__name__", type(target).__name__))
    parameters: dict[str, Any] = {}
    try:
        bound = inspect.getclosurevars(target).nonlocals
    except (TypeError, ValueError):
        bound = {}
    for key, value in sorted(bound.items()):
        if key.startswith("_") or callable(value):
            continue
        simple = _simple_value(value)
        if simple is not None:
            parameters[key] = simple
    return name, parameters


def preflight(name: str, state: SemanticState) -> None:
    """Raise a semantic error before a known invalid stage is technically executed."""

    spec = get_verb_spec(name)
    if spec is None:
        return
    if state.semantic_kind not in spec.accepts:
        if name == "detect_events":
            raise SemanticGrammarError(
                "detect_events() groups consecutive true periods into events. "
                f"The current object is a {state.semantic_kind.replace('_', ' ')} named "
                f"{state.semantic_name!r}, so there is not yet a condition to group. "
                "A common pattern is: observations → threshold_state(...) → detect_events()."
            )
        accepted = ", ".join(kind.replace("_", " ") for kind in spec.accepts)
        raise SemanticGrammarError(
            f"{name}() expects {accepted}; the current object is "
            f"{state.semantic_kind.replace('_', ' ')} ({state.semantic_name!r})."
        )
    if "time" in spec.requires and not state.temporal:
        raise SemanticGrammarError(
            f"{name}() needs a time dimension, but the current object has dimensions "
            f"{state.dimensions or '(none)'}."
        )
    if "time_variation" in spec.requires and state.has_time_variation is False:
        raise SemanticGrammarError(
            f"{name}() needs variation through time, but an earlier step removed it. "
            "Apply this verb before reducing over time."
        )
    if "ordered_time" in spec.requires and state.time_ordered is False:
        raise SemanticGrammarError(
            f"{name}() needs time coordinates in increasing order. Sort the cube by time first."
        )
    if "spatial" in spec.requires and not state.spatial:
        raise SemanticGrammarError(
            f"{name}() needs spatial dimensions; the current dimensions are {state.dimensions or '(none)'}."
        )


def transition_state(
    name: str,
    parameters: Mapping[str, Any],
    before: SemanticState,
    result: Any,
) -> SemanticState:
    """Describe a completed stage using its result plus known information effects."""

    after = infer_semantic_state(result)
    spec = get_verb_spec(name)
    if spec is None:
        return after
    if spec.side_effect and result is not None:
        return replace(before, semantic_name=before.semantic_name)
    kind = spec.returns
    if name in {"mean", "variance"}:
        kind = "summary"
    if name in {"threshold_state", "quantile_state", "binary_state", "change_state", "exceedance", "overlap"}:
        return replace(after, semantic_kind="condition", category="state", units="boolean")
    if name == "detect_events":
        return replace(after, semantic_kind="event", category="event")
    if name in {"anomaly", "zscore", "month_filter"}:
        units = "standard deviations" if name == "zscore" else after.units or before.units
        return replace(after, semantic_kind="continuous_field", units=units)
    if name in {"mean", "variance"}:
        reduced = parameters.get("over", parameters.get("dim", "time"))
        time_variation = after.has_time_variation
        if reduced == "time" or reduced == ["time"] or reduced == ("time",):
            time_variation = False
        return replace(after, semantic_kind=kind, has_time_variation=time_variation)
    return replace(after, semantic_kind=kind)


def order_messages(trace: Iterable[TraceStep], next_name: str) -> tuple[GrammarMessage, ...]:
    """Return applicable order notes for a newly appended stage."""

    steps = tuple(trace)
    if not steps:
        return ()
    previous = _ALIASES.get(steps[-1].verb, steps[-1].verb)
    current = _ALIASES.get(next_name, next_name)
    notes = []
    for rule in _ORDER_RULES:
        if rule.first == previous and rule.second == current:
            notes.append(GrammarMessage("ORDER_NOTE", rule.category, rule.explanation))
    return tuple(notes)


def explain_pipeline(initial: SemanticState, trace: Iterable[TraceStep]) -> str:
    """Build a deterministic, plain-language explanation of a semantic trace."""

    steps = tuple(trace)
    source = ""
    if initial.source_flavor:
        source = f" from {initial.source_flavor}"
    lines = ["Your analysis", f"1. Start with {initial.semantic_name} ({initial.semantic_kind.replace('_', ' ')}){source}."]
    for index, step in enumerate(steps, start=2):
        lines.append(f"{index}. {_describe_step(step)}")
    current = steps[-1].output_state if steps else initial
    lines.extend(
        [
            "",
            "Current result",
            f"- Semantic kind: {current.semantic_kind.replace('_', ' ')}",
            f"- Dimensions: {', '.join(current.dimensions) if current.dimensions else 'not declared'}",
            f"- Units: {current.units or 'not declared'}",
        ]
    )
    notes = [message.text for step in steps for message in step.messages if message.severity == "ORDER_NOTE"]
    if notes:
        lines.extend(["", "Order notes"])
        lines.extend(f"- {note}" for note in dict.fromkeys(notes))
    lines.extend(["", "CubeDynamics executed the verbs exactly in the order written; no step was rewritten."])
    return "\n".join(lines)


def suggest_next(state: SemanticState) -> tuple[Suggestion, ...]:
    """Suggest only implemented verbs whose contracts fit the current state."""

    candidates = {
        "continuous_field": ("anomaly", "zscore", "threshold_state", "quantile_state", "mean", "variance", "plot"),
        "observation": ("anomaly", "threshold_state", "mean", "plot"),
        "categorical_field": ("binary_state", "plot"),
        "condition": ("detect_events", "overlap", "occurrence_synchrony", "mean", "plot"),
        "event": ("timing_synchrony", "duration_synchrony", "severity_synchrony"),
        "summary": ("plot",),
        "relationship": (),
        "feature": (),
        "network": (),
    }.get(state.semantic_kind, ())
    suggestions = []
    for name in candidates:
        spec = get_verb_spec(name)
        if spec is None or not _requirements_fit(spec, state):
            continue
        suggestions.append(Suggestion(name, spec.description.capitalize() + ".", spec.examples[0]))
    return tuple(suggestions[:6])


def validate_pipeline(initial: SemanticState, trace: Iterable[TraceStep]) -> ValidationReport:
    """Validate semantic metadata and ordering without reading array values."""

    steps = tuple(trace)
    current = steps[-1].output_state if steps else initial
    checks = [
        ValidationCheck("INFO", "semantic_kind", f"Current result is classified as {current.semantic_kind.replace('_', ' ')}."),
        ValidationCheck("INFO", "dimensions", f"Tracked dimensions: {', '.join(current.dimensions) if current.dimensions else 'not declared'}."),
    ]
    if current.temporal:
        severity = "INFO" if current.time_ordered is not False else "ERROR"
        text = "Time coordinates are ordered." if current.time_ordered is not False else "Time coordinates are not in increasing order."
        checks.append(ValidationCheck(severity, "time_order", text))
    if current.spatial:
        severity = "INFO" if current.crs else "CHECK"
        text = f"Spatial CRS is {current.crs}." if current.crs else "Spatial dimensions are present, but CRS metadata is not declared."
        checks.append(ValidationCheck(severity, "crs", text))
    if current.units:
        checks.append(ValidationCheck("INFO", "units", f"Units are {current.units}."))
    else:
        checks.append(ValidationCheck("CHECK", "units", "Units are not declared for the current result."))
    if current.provenance:
        checks.append(ValidationCheck("INFO", "provenance", "Source provenance metadata is present."))
    else:
        checks.append(ValidationCheck("CHECK", "provenance", "Source provenance metadata is not declared."))
    for step in steps:
        for message in step.messages:
            checks.append(ValidationCheck(message.severity, message.code, message.text))
    return ValidationReport(not any(check.severity == "ERROR" for check in checks), tuple(checks))


def _looks_boolean(value: Any) -> bool:
    dtype = getattr(value, "dtype", None)
    if dtype is not None and str(dtype) == "bool":
        return True
    data_vars = getattr(value, "data_vars", {})
    try:
        return "state" in data_vars or "event_active" in data_vars
    except TypeError:
        return False


def _time_is_ordered(value: Any) -> bool | None:
    try:
        index = value.indexes.get("time")
    except Exception:
        index = None
    if index is None:
        return None
    monotonic = getattr(index, "is_monotonic_increasing", None)
    return bool(monotonic) if monotonic is not None else None


def _factory_name(qualname: str) -> str | None:
    marker = ".<locals>."
    if marker not in qualname:
        return None
    return qualname.split(marker, 1)[0].split(".")[-1]


def _simple_value(value: Any) -> Any | None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, tuple) and all(isinstance(item, (str, int, float, bool)) for item in value):
        return value
    if isinstance(value, list) and all(isinstance(item, (str, int, float, bool)) for item in value):
        return list(value)
    return None


def _requirements_fit(spec: VerbSpec, state: SemanticState) -> bool:
    if state.semantic_kind not in spec.accepts:
        return False
    if "time" in spec.requires and not state.temporal:
        return False
    if "time_variation" in spec.requires and state.has_time_variation is False:
        return False
    if "ordered_time" in spec.requires and state.time_ordered is False:
        return False
    if "spatial" in spec.requires and not state.spatial:
        return False
    return True


def _describe_step(step: TraceStep) -> str:
    p = step.parameters
    if step.verb == "anomaly":
        return f"Calculate departures from the mean over {p.get('over', p.get('dim', 'time'))}."
    if step.verb == "zscore":
        return f"Standardize departures over {p.get('over', p.get('dim', 'time'))}."
    if step.verb in {"threshold_state", "exceedance"}:
        return f"Define a condition for values {p.get('direction', 'relative to')} {p.get('threshold', 'the threshold')}."
    if step.verb == "quantile_state":
        return f"Define a condition using quantile {p.get('quantile', 'the selected quantile')}."
    if step.verb == "detect_events":
        return f"Group consecutive true periods into events (minimum duration {p.get('min_duration', 1)})."
    if step.verb in {"mean", "variance"}:
        action = "Average" if step.verb == "mean" else "Measure variation in"
        return f"{action} values over {p.get('over', p.get('dim', 'time'))}."
    spec = get_verb_spec(step.verb)
    if spec:
        return spec.description.capitalize() + "."
    return f"Apply {step.verb}()."


__all__ = [
    "GrammarMessage",
    "ORDER_CATEGORIES",
    "ORDER_CHANGES_MEANING",
    "ORDER_EQUIVALENT_OR_NEAR_EQUIVALENT",
    "ORDER_REMOVES_REQUIRED_INFORMATION",
    "OrderRule",
    "REQUIRED_ORDER",
    "SEMANTIC_KINDS",
    "SemanticGrammarError",
    "SemanticState",
    "Suggestion",
    "TraceStep",
    "ValidationCheck",
    "ValidationReport",
    "VerbSpec",
    "explain_pipeline",
    "get_order_rules",
    "get_verb_spec",
    "infer_semantic_state",
    "list_verb_specs",
    "suggest_next",
    "validate_pipeline",
]
