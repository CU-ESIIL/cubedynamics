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
    temporal_resolution: str | None = None
    temporal_support_type: str | None = None
    temporal_support_known: bool | None = None
    temporal_label_convention: str | None = None
    temporal_reference_timezone: str | None = None
    temporal_support_start_offset: str | None = None
    temporal_support_end_offset: str | None = None
    temporal_alignment_coordinates: str | None = None
    temporal_alignment_support: str | None = None
    temporal_alignment_note: str | None = None

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
            "temporal_resolution": self.temporal_resolution,
            "temporal_support_type": self.temporal_support_type,
            "temporal_support_known": self.temporal_support_known,
            "temporal_label_convention": self.temporal_label_convention,
            "temporal_reference_timezone": self.temporal_reference_timezone,
            "temporal_support_start_offset": self.temporal_support_start_offset,
            "temporal_support_end_offset": self.temporal_support_end_offset,
            "temporal_alignment_coordinates": self.temporal_alignment_coordinates,
            "temporal_alignment_support": self.temporal_alignment_support,
            "temporal_alignment_note": self.temporal_alignment_note,
        }


@dataclass(frozen=True)
class VerbSpec:
    """Machine-readable semantic contract for one public verb."""

    name: str
    human_description: str
    accepts: tuple[str, ...]
    returns: str
    requires: tuple[str, ...] = ()
    preserves: tuple[str, ...] = ()
    removes: tuple[str, ...] = ()
    category: str = "primitive"
    examples: tuple[str, ...] = ()
    side_effect: bool = False

    @property
    def description(self) -> str:
        """Concise compatibility alias used by the explanation renderer."""

        return self.human_description

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "human_description": self.human_description,
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
        "threshold_state", "turn continuous values or a summary into a named true/false condition", _FIELD_KINDS + ("summary",),
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
        "exceedance", "alias for threshold_state", _FIELD_KINDS + ("summary",), "condition",
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
    "align_time": _spec(
        "align_time", "make a time-label or exact-support alignment decision explicit",
        _ANY_KINDS, "same", requires=("time",),
        preserves=("coordinates", "values", "provenance"),
        examples=("v.align_time(other, mode='exact_support')",), category="semantic",
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
        "severity_synchrony", "compare condition magnitude where states co-occur", ("condition",),
        "relationship", category="semantic", examples=("v.severity_synchrony()",),
    ),
    "plot": _spec(
        "plot", "render a cube, spatial map, or temporal line view", _ANY_KINDS, "same",
        category="integration", side_effect=True,
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
        "inferred", category="integration", examples=("v.apply(function)",),
    ),
}

# Public project and integration verbs share the same registry shape. Their
# contracts are intentionally broad where the implementation accepts several
# scientific objects; project packages can refine them without changing Pipe.
_VERB_SPECS.update(
    {
        "rolling_median_split_synchrony": _spec(
            "rolling_median_split_synchrony", "measure rolling median-split synchrony",
            _FIELD_KINDS, "relationship", requires=("time", "time_variation"), category="semantic",
            examples=("v.rolling_median_split_synchrony(window=30)",),
        ),
        "rolling_tail_dep_vs_center": _spec(
            "rolling_tail_dep_vs_center", "compare rolling tail behavior with the center",
            _FIELD_KINDS, "relationship", requires=("time", "time_variation"), category="semantic",
            examples=("v.rolling_tail_dep_vs_center(window=30)",),
        ),
        "correlation_cube": _spec(
            "correlation_cube", "calculate a correlation field", _FIELD_KINDS,
            "relationship", requires=("time",), category="semantic",
            examples=("v.correlation_cube()",),
        ),
        "sync_with": _spec(
            "sync_with", "compare an input cube with another aligned temporal cube", _FIELD_KINDS + ("condition",),
            "relationship", requires=("time", "spatial"), category="semantic",
            examples=("v.sync_with(other)",),
        ),
        "block_signature": _spec(
            "block_signature", "summarize a cube as a named spatial-block signature", _FIELD_KINDS,
            "summary", requires=("time", "spatial"), category="semantic",
            examples=("v.block_signature(name='study area')",),
        ),
        "aoi_signature": _spec(
            "aoi_signature", "compatibility alias for block_signature", _FIELD_KINDS,
            "summary", requires=("time", "spatial"), category="semantic",
            examples=("v.aoi_signature(name='study area')",),
        ),
        "collect_blocks": _spec(
            "collect_blocks", "collect compatible block signatures", ("summary",),
            "summary", category="semantic", examples=("v.collect_blocks(other_block)",),
        ),
        "compare_blocks": _spec(
            "compare_blocks", "compare collected spatial-block signatures", ("summary",),
            "relationship", category="semantic", examples=("v.compare_blocks()",),
        ),
        "compare_aoi_signature": _spec(
            "compare_aoi_signature", "compatibility alias for comparing block signatures", ("summary",),
            "relationship", category="semantic", examples=("v.compare_aoi_signature()",),
        ),
        "flatten_space": _spec(
            "flatten_space", "stack spatial dimensions into a pixel dimension", _FIELD_KINDS,
            "continuous_field", requires=("spatial",), removes=("separate x and y dimensions",),
            examples=("v.flatten_space()",),
        ),
        "flatten_cube": _spec(
            "flatten_cube", "stack non-time dimensions into a sample dimension", _FIELD_KINDS,
            "continuous_field", requires=("time",), removes=("separate non-time dimensions",),
            examples=("v.flatten_cube()",),
        ),
        "fit_model": _spec(
            "fit_model", "fit a configured statistical model", _FIELD_KINDS + ("summary",),
            "summary", category="semantic", examples=("v.fit_model(model)",),
        ),
        "ndvi_from_s2": _spec(
            "ndvi_from_s2", "derive NDVI from Sentinel-2 red and near-infrared bands", _FIELD_KINDS,
            "continuous_field", category="integration", examples=("v.ndvi_from_s2()",),
        ),
        "rasterize_observations": _spec(
            "rasterize_observations", "place feature observations onto a reference cube grid", ("feature",),
            "continuous_field", requires=("spatial",), category="integration",
            examples=("v.rasterize_observations(reference=reference_cube)",),
        ),
        "align_cube": _spec(
            "align_cube", "align a field to a reference cube", _FIELD_KINDS,
            "continuous_field", requires=("spatial",), category="integration",
            examples=("v.align_cube(reference_cube)",),
        ),
        "diagnostic_panel": _spec(
            "diagnostic_panel", "render a diagnostic panel", _ANY_KINDS, "same",
            category="integration", side_effect=True, examples=("v.diagnostic_panel()",),
        ),
        "climate_hist": _spec(
            "climate_hist", "render a climate distribution", _FIELD_KINDS, "same",
            category="integration", side_effect=True, examples=("v.climate_hist()",),
        ),
        "to_netcdf": _spec(
            "to_netcdf", "write an explicit NetCDF output", _ANY_KINDS, "same",
            category="integration", side_effect=True, examples=("v.to_netcdf(path)",),
        ),
        "landsat8_mpc": _spec(
            "landsat8_mpc", "load Landsat observations through the MPC integration", _ANY_KINDS,
            "continuous_field", category="integration", examples=("v.landsat8_mpc(...) ",),
        ),
        "landsat_vis_ndvi": _spec(
            "landsat_vis_ndvi", "prepare a visualization-friendly Landsat NDVI cube", _FIELD_KINDS,
            "continuous_field", category="integration", examples=("v.landsat_vis_ndvi(...) ",),
        ),
        "landsat_ndvi_plot": _spec(
            "landsat_ndvi_plot", "render a Landsat NDVI view", _FIELD_KINDS, "same",
            category="integration", side_effect=True, examples=("v.landsat_ndvi_plot(...) ",),
        ),
        "extract": _spec(
            "extract", "attach fire-hull climate summaries to a cube", _FIELD_KINDS,
            "same", requires=("time", "spatial"), category="semantic", examples=("v.extract(fired_event=event)",),
        ),
        "vase": _spec(
            "vase", "construct a configured fire VASE representation", _FIELD_KINDS,
            "feature", requires=("time", "spatial"), category="semantic", examples=("v.vase(...) ",),
        ),
        "vase_extract": _spec(
            "vase_extract", "extract cube values for a VASE geometry", _FIELD_KINDS,
            "summary", requires=("time", "spatial"), category="semantic", examples=("v.vase_extract(...) ",),
        ),
        "vase_mask": _spec(
            "vase_mask", "mask a cube with a VASE geometry", _FIELD_KINDS,
            "continuous_field", requires=("time", "spatial"), category="semantic", examples=("v.vase_mask(...) ",),
        ),
        "vase_demo": _spec(
            "vase_demo", "build a demonstration VASE object", _ANY_KINDS,
            "feature", category="integration", examples=("v.vase_demo()",),
        ),
        "fire_plot": _spec(
            "fire_plot", "render one fire event and its climate context", _ANY_KINDS, "same",
            category="integration", side_effect=True, examples=("v.fire_plot(...) ",),
        ),
        "fire_panel": _spec(
            "fire_panel", "render a compact fire-event diagnostic panel", _ANY_KINDS, "same",
            category="integration", side_effect=True, examples=("v.fire_panel(...) ",),
        ),
        "fire_vase_panel": _spec(
            "fire_vase_panel", "render a multi-event VASE panel", _ANY_KINDS, "same",
            category="integration", side_effect=True, examples=("v.fire_vase_panel(...) ",),
        ),
        "fire_derivative": _spec(
            "fire_derivative", "derive a configured fire-event product", _ANY_KINDS,
            "summary", category="semantic", examples=("v.fire_derivative(...) ",),
        ),
        "tubes": _spec(
            "tubes", "construct a tube representation from a spatiotemporal cube", _FIELD_KINDS,
            "feature", requires=("time", "spatial"), category="semantic", examples=("v.tubes(...) ",),
        ),
    }
)


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
    OrderRule("threshold", "mean", ORDER_CHANGES_MEANING,
              "Averaging a thresholded condition measures its prevalence over the reduced dimensions, rather than averaging the source measurements.",
              "Use mean before threshold_state when the intended condition is defined from an aggregate value."),
    OrderRule("mean", "threshold", ORDER_CHANGES_MEANING,
              "Thresholding a mean defines a condition from an aggregate value, rather than measuring how often individual observations meet the condition.",
              "Use threshold_state before mean when the intended summary is condition prevalence."),
    OrderRule("aggregate", "onset", ORDER_REMOVES_REQUIRED_INFORMATION,
              "Aggregation can remove the first transition needed to identify onset.", implemented=False),
    OrderRule("filter", "change", ORDER_CHANGES_MEANING,
              "Filtering before change measures change only within the retained observations; changing first filters the derived changes.",
              "Choose the order that matches the scientific question.", implemented=False),
    OrderRule("change", "filter", ORDER_CHANGES_MEANING,
              "Calculating change before filtering retains change across the full sequence and then selects derived changes.",
              "Filter first when change should be calculated only within the retained observations.", implemented=False),
    OrderRule("transition", "summarize", REQUIRED_ORDER,
              "A transition summary requires transitions to be identified first.", implemented=False),
    OrderRule("summarize", "change", ORDER_REMOVES_REQUIRED_INFORMATION,
              "Some summaries remove the sequence needed to estimate change.", implemented=False),
    OrderRule("subtract", "divide", ORDER_CHANGES_MEANING,
              "Subtracting then dividing is a relative contrast; dividing then subtracting is a difference of ratios.", implemented=False),
    OrderRule("divide", "subtract", ORDER_CHANGES_MEANING,
              "Dividing before subtraction compares ratios, which is different from scaling a difference.",
              "Subtract first when the intended quantity is a difference expressed relative to a denominator.", implemented=False),
    OrderRule("normalize", "threshold", ORDER_CHANGES_MEANING,
              "A threshold after normalization is expressed in standardized units, not source units.", implemented=False),
    OrderRule("threshold", "normalize", ORDER_CHANGES_MEANING,
              "Normalizing a thresholded result describes the distribution of the condition, not standardized source measurements.",
              "Normalize first when the threshold should be expressed in standardized units.", implemented=False),
    OrderRule("near", "density", ORDER_CHANGES_MEANING,
              "Density near a target and proximity to dense areas answer different spatial questions.", implemented=False),
    OrderRule("density", "near", ORDER_CHANGES_MEANING,
              "Calculating density first creates a field everywhere, then near selects or annotates values relative to the target.",
              "Use near before density to calculate density only from nearby features.", implemented=False),
    OrderRule("intersect", "density", ORDER_CHANGES_MEANING,
              "Density within an intersection differs from intersecting a density surface.", implemented=False),
    OrderRule("density", "intersect", ORDER_CHANGES_MEANING,
              "Intersecting after density clips or samples an already calculated density field.",
              "Intersect first to calculate density using only features in the intersection.", implemented=False),
    OrderRule("intersect", "summarize", ORDER_CHANGES_MEANING,
              "Summarizing an intersection differs from intersecting already summarized objects.", implemented=False),
    OrderRule("summarize", "intersect", ORDER_REMOVES_REQUIRED_INFORMATION,
              "A summary may remove geometry needed for a later intersection.",
              "Intersect before summarizing when the summary should describe the shared area.", implemented=False),
    OrderRule("clip", "summarize", ORDER_CHANGES_MEANING,
              "Clipping first summarizes only the study area; summarizing first may include values outside it.", implemented=False),
    OrderRule("summarize", "clip", ORDER_REMOVES_REQUIRED_INFORMATION,
              "A summary may remove the spatial support needed for clipping.",
              "Clip before summarizing when the summary should describe only the clipped area.", implemented=False),
    OrderRule("exposure", "summarize", REQUIRED_ORDER,
              "An exposure summary requires exposure to be computed first.", implemented=False),
    OrderRule("near", "summarize", ORDER_CHANGES_MEANING,
              "Summarizing nearby observations differs from measuring proximity to a summary.", implemented=False),
    OrderRule("upstream", "intersect", ORDER_CHANGES_MEANING,
              "Intersecting an upstream network differs from asking what is upstream of an intersection.", implemented=False),
    OrderRule("intersect", "upstream", ORDER_CHANGES_MEANING,
              "Finding upstream elements after intersection follows connectivity only from the intersected network.",
              "Find upstream elements first when the intersection should be applied to the full upstream network.", implemented=False),
    OrderRule("intersect", "intersect", ORDER_EQUIVALENT_OR_NEAR_EQUIVALENT,
              "Repeated set intersections are order-equivalent when geometry and coordinate alignment are unchanged.",
              "Confirm that each input uses the same spatial reference and boundary convention.", implemented=False),
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

    time_dim = next((dim for dim in dimensions if dim == "time" or "time" in dim.lower()), None)
    temporal = time_dim is not None
    spatial = ({"x", "y"}.issubset(dimensions) or {"lon", "lat"}.issubset(dimensions))
    time_ordered = _time_is_ordered(value, time_dim) if time_dim else None
    has_time_variation = (
        int(sizes[time_dim]) > 1 if time_dim is not None and time_dim in sizes else None
    )
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
        temporal_resolution=(str(attrs["temporal_resolution"]) if temporal and attrs.get("temporal_resolution") is not None else None),
        temporal_support_type=(str(attrs["temporal_support_type"]) if temporal and attrs.get("temporal_support_type") is not None else None),
        temporal_support_known=(_metadata_bool(attrs.get("temporal_support_known")) if temporal else None),
        temporal_label_convention=(str(attrs["temporal_label_convention"]) if temporal and attrs.get("temporal_label_convention") is not None else None),
        temporal_reference_timezone=(str(attrs["temporal_reference_timezone"]) if temporal and attrs.get("temporal_reference_timezone") is not None else None),
        temporal_support_start_offset=(str(attrs["temporal_support_start_offset"]) if temporal and attrs.get("temporal_support_start_offset") is not None else None),
        temporal_support_end_offset=(str(attrs["temporal_support_end_offset"]) if temporal and attrs.get("temporal_support_end_offset") is not None else None),
        temporal_alignment_coordinates=(str(attrs["temporal_alignment_coordinates"]) if attrs.get("temporal_alignment_coordinates") is not None else None),
        temporal_alignment_support=(str(attrs["temporal_alignment_support"]) if attrs.get("temporal_alignment_support") is not None else None),
        temporal_alignment_note=(str(attrs["temporal_alignment_note"]) if attrs.get("temporal_alignment_note") is not None else None),
    )


def inspect_stage(func: Callable[..., Any]) -> tuple[str, dict[str, Any]]:
    """Return a stable semantic stage name and simple bound factory arguments."""

    target = getattr(func, "func", func)
    explicit = getattr(func, "_cd_semantic_name", None) or getattr(target, "_cd_semantic_name", None)
    qualname = getattr(target, "__qualname__", "")
    callable_name = getattr(target, "__name__", type(target).__name__)
    factory_name = _factory_name(qualname) if callable_name.startswith("_") else None
    name = str(explicit or factory_name or callable_name)
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


def preflight(
    name: str,
    state: SemanticState,
    *,
    func: Callable[..., Any] | None = None,
) -> None:
    """Raise a semantic error before a known invalid stage is technically executed."""

    spec = get_verb_spec(name)
    if spec is None:
        return
    if state.semantic_kind not in spec.accepts:
        if name == "detect_events":
            if state.has_time_variation is False:
                raise SemanticGrammarError(
                    "detect_events() needs a condition that still varies through time. "
                    "An earlier reduction removed that variation, so event runs can no longer be identified. "
                    "Detect events before reducing over time."
                )
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
    target = getattr(func, "func", func)
    context = getattr(func, "_cd_semantic_context", None) or getattr(
        target, "_cd_semantic_context", {}
    )
    other = context.get("other") if isinstance(context, Mapping) else None
    if name == "overlap" and isinstance(other, SemanticState):
        if state.crs and other.crs and state.crs != other.crs:
            raise SemanticGrammarError(
                "overlap() requires both conditions to use the same CRS. "
                f"The current condition uses {state.crs}, while the other uses {other.crs}. "
                "Reproject one input explicitly before combining them."
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
    if name == "align_time":
        return replace(after, semantic_kind=before.semantic_kind, category=before.category)
    if name == "detect_events":
        return replace(after, semantic_kind="event", category="event")
    if name in {"anomaly", "zscore", "month_filter"}:
        units = "standard deviations" if name == "zscore" else after.units or before.units
        return replace(after, semantic_kind="continuous_field", units=units)
    if name in {"mean", "variance"}:
        reduced = parameters.get("over", parameters.get("dim", "time"))
        time_variation = after.has_time_variation
        reduced_dimensions = (
            tuple(reduced) if isinstance(reduced, (list, tuple, set)) else (reduced,)
        )
        if "time" in reduced_dimensions:
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
    if current.temporal:
        if current.temporal_support_known:
            lines.append(
                "- Temporal support: "
                f"{current.temporal_support_type or 'known'} "
                f"({current.temporal_label_convention or 'source-declared convention'})"
            )
        elif current.temporal_support_known is False:
            lines.append("- Temporal support: not verified")
    alignment_states = [
        step.output_state for step in steps if step.output_state.temporal_alignment_support
    ]
    if alignment_states:
        aligned = alignment_states[-1]
        lines.extend(
            [
                "",
                "Temporal alignment",
                f"- Coordinate labels: {aligned.temporal_alignment_coordinates}",
                f"- Observation support: {aligned.temporal_alignment_support}",
            ]
        )
        if aligned.temporal_alignment_note:
            lines.append(f"- {aligned.temporal_alignment_note}")
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
        "summary": ("threshold_state", "plot"),
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
        if current.temporal_support_known is True:
            checks.append(
                ValidationCheck(
                    "INFO",
                    "temporal_support",
                    "Observation temporal support is declared as "
                    f"{current.temporal_support_type or 'known'} "
                    f"({current.temporal_label_convention or 'source convention'}).",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    "CHECK",
                    "temporal_support_unknown",
                    "A time coordinate is present, but observation temporal support is not verified.",
                )
            )
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
        support_status = step.output_state.temporal_alignment_support
        if support_status == "different":
            checks.append(
                ValidationCheck(
                    "WARNING",
                    "temporal_support_different",
                    step.output_state.temporal_alignment_note
                    or "Inputs share time labels but represent different observation intervals.",
                )
            )
        elif support_status == "unknown":
            checks.append(
                ValidationCheck(
                    "CHECK",
                    "temporal_support_compatibility_unknown",
                    step.output_state.temporal_alignment_note
                    or "Time labels are compatible, but temporal-support compatibility could not be verified.",
                )
            )
        elif support_status == "exact":
            checks.append(
                ValidationCheck(
                    "INFO",
                    "temporal_support_exact",
                    "Time labels and declared observation support are compatible.",
                )
            )
    return ValidationReport(not any(check.severity == "ERROR" for check in checks), tuple(checks))


def _metadata_bool(value: Any) -> bool | None:
    """Interpret NetCDF-safe flags while retaining an unknown state."""

    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "known"}
    return bool(value)


def _looks_boolean(value: Any) -> bool:
    dtype = getattr(value, "dtype", None)
    if dtype is not None and str(dtype) == "bool":
        return True
    data_vars = getattr(value, "data_vars", {})
    try:
        return "state" in data_vars or "event_active" in data_vars
    except TypeError:
        return False


def _time_is_ordered(value: Any, time_dim: str) -> bool | None:
    try:
        index = value.indexes.get(time_dim)
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
