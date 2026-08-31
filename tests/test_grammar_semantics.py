"""Regression tests for the lightweight semantic grammar layer."""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

import cubedynamics as cd
from cubedynamics import verbs as v


def _temperature_cube() -> xr.DataArray:
    cube = xr.DataArray(
        np.array(
            [
                [[20.0, 21.0], [22.0, 23.0]],
                [[24.0, 26.0], [23.0, 28.0]],
                [[27.0, 22.0], [29.0, 25.0]],
                [[30.0, 24.0], [31.0, 27.0]],
            ]
        ),
        dims=("time", "y", "x"),
        coords={
            "time": np.array(["2024-07-01", "2024-07-02", "2024-07-03", "2024-07-04"], dtype="datetime64[D]"),
            "y": [40.1, 40.0],
            "x": [-105.2, -105.1],
        },
        name="temperature",
        attrs={
            "units": "degC",
            "crs": "EPSG:4326",
            "source_flavor": "checked_fixture",
            "source_provider": "CubeDynamics tests",
        },
    )
    return cube


def test_pipe_executes_each_callable_once_in_exact_written_order():
    calls: list[str] = []

    def add_one(value: int) -> int:
        calls.append("add_one")
        return value + 1

    def double(value: int) -> int:
        calls.append("double")
        return value * 2

    result = cd.pipe(3) | add_one | double

    assert result.unwrap() == 8
    assert calls == ["add_one", "double"]
    assert [step.verb for step in result.semantic_trace] == ["add_one", "double"]


def test_semantic_trace_records_state_transitions_and_order_note():
    result = (
        cd.pipe(_temperature_cube())
        | v.anomaly(over="time")
        | v.threshold_state(threshold=2.0, direction="above", name="warm departure")
        | v.detect_events(min_duration=1)
    )

    assert [step.verb for step in result.semantic_trace] == [
        "anomaly",
        "threshold_state",
        "detect_events",
    ]
    assert [step.output_state.semantic_kind for step in result.semantic_trace] == [
        "continuous_field",
        "condition",
        "event",
    ]
    assert any(
        message.severity == "ORDER_NOTE"
        for message in result.semantic_trace[1].messages
    )
    assert result.semantic_state.semantic_kind == "event"


def test_explain_is_plain_language_and_states_no_rewrite_guarantee():
    result = (
        cd.pipe(_temperature_cube())
        | v.anomaly(over="time")
        | v.threshold_state(threshold=2.0, direction="above")
    )

    explanation = result.explain()

    assert "Your analysis" in explanation
    assert "Calculate departures from the mean over time" in explanation
    assert "Define a condition" in explanation
    assert "exactly in the order written" in explanation
    assert "no step was rewritten" in explanation


def test_suggestions_are_small_compatible_and_implemented():
    suggestions = cd.pipe(_temperature_cube()).suggest()
    names = {suggestion.verb for suggestion in suggestions}

    assert 1 <= len(suggestions) <= 6
    assert {"anomaly", "threshold_state", "mean"}.issubset(names)
    assert all(cd.grammar.get_verb_spec(name) is not None for name in names)
    assert "near" not in names


def test_validation_report_is_structured_and_readable():
    result = cd.pipe(_temperature_cube()) | v.threshold_state(
        threshold=25.0, direction="above"
    )

    report = result.validate()

    assert report.ok
    assert report.as_dict()["ok"] is True
    assert any(check.code == "crs" for check in report.checks)
    assert any(check.code == "provenance" for check in report.checks)
    assert "Semantic validation: ready" in str(report)


def test_detect_events_on_continuous_values_gives_semantic_guidance():
    with pytest.raises(cd.grammar.SemanticGrammarError) as error:
        cd.pipe(_temperature_cube()) | v.detect_events()

    message = str(error.value)
    assert "there is not yet a condition to group" in message
    assert "threshold_state" in message
    assert "observations" in message


def test_reducing_time_before_event_detection_explains_lost_information():
    reduced = cd.pipe(_temperature_cube()) | v.mean(over="time")

    assert reduced.semantic_state.has_time_variation is False
    with pytest.raises(cd.grammar.SemanticGrammarError) as error:
        reduced | v.detect_events()

    message = str(error.value)
    assert "earlier reduction removed" in message
    assert "Detect events before reducing over time" in message


def test_threshold_then_mean_is_a_prevalence_summary_with_truthful_metadata():
    result = (
        cd.pipe(_temperature_cube())
        | v.threshold_state(threshold=25.0, direction="below", name="cool")
        | v.mean(dim=("time", "y", "x"), keep_dim=False)
    )

    summary = result.unwrap()
    expected = (_temperature_cube() <= 25.0).mean().item()
    assert result.semantic_state.semantic_kind == "summary"
    assert result.semantic_state.has_time_variation is False
    assert summary.attrs["semantic_kind"] == "summary"
    assert summary["state"].attrs["semantic_units"] == "proportion"
    assert summary["state"].item() == pytest.approx(expected)
    assert any(
        message.code == cd.grammar.ORDER_CHANGES_MEANING
        for message in result.semantic_trace[-1].messages
    )
    assert "Semantic kind: summary" in result.explain()
    assert "prevalence" in result.explain()


def test_mean_then_threshold_is_allowed_and_defines_aggregate_condition():
    result = (
        cd.pipe(_temperature_cube())
        | v.mean(dim=("time", "y", "x"), keep_dim=False)
        | v.threshold_state(threshold=25.0, direction="below", name="cool mean")
    )

    condition = result.unwrap()
    expected = _temperature_cube().mean().item() <= 25.0
    assert result.semantic_state.semantic_kind == "condition"
    assert condition.attrs["semantic_kind"] == "condition"
    assert condition["state"].item() == expected
    assert any(
        message.code == cd.grammar.ORDER_CHANGES_MEANING
        for message in result.semantic_trace[-1].messages
    )
    assert "Semantic kind: condition" in result.explain()
    assert "aggregate value" in result.explain()


def test_summary_suggests_threshold_state_as_an_implemented_next_step():
    summary = cd.pipe(_temperature_cube()) | v.mean(over="time")

    assert "threshold_state" in {item.verb for item in summary.suggest()}


@pytest.mark.parametrize("verb", [v.mean, v.variance, v.anomaly, v.zscore])
def test_over_alias_matches_dim_and_conflicts_are_explicit(verb):
    cube = _temperature_cube()
    xr.testing.assert_identical(
        (cd.pipe(cube) | verb(dim="time")).unwrap(),
        (cd.pipe(cube) | verb(over="time")).unwrap(),
    )

    with pytest.raises(ValueError, match="either dim= or over="):
        verb(dim="x", over="time")


def test_registry_has_small_state_vocabulary_and_all_order_categories():
    assert set(cd.grammar.SEMANTIC_KINDS) == {
        "observation",
        "continuous_field",
        "categorical_field",
        "condition",
        "event",
        "feature",
        "relationship",
        "summary",
        "network",
    }
    assert {rule.category for rule in cd.grammar.get_order_rules()} == set(
        cd.grammar.ORDER_CATEGORIES
    )
    assert cd.grammar.get_verb_spec("detect_events").accepts == ("condition",)


def test_every_exported_public_verb_has_registry_metadata():
    missing = [
        name
        for name in v.__all__
        if callable(getattr(v, name, None)) and cd.grammar.get_verb_spec(name) is None
    ]
    assert missing == []


@pytest.mark.parametrize(
    "rule",
    cd.grammar.get_order_rules(),
    ids=lambda rule: f"{rule.first}-then-{rule.second}",
)
def test_each_curated_order_rule_is_specific_and_machine_readable(rule):
    assert rule.first
    assert rule.second
    assert rule.category in cd.grammar.ORDER_CATEGORIES
    assert len(rule.explanation) >= 30
    assert "wrong" not in rule.explanation.lower()
    assert rule.as_dict()["implemented"] is rule.implemented


def test_order_library_covers_requested_bidirectional_concepts():
    pairs = {(rule.first, rule.second) for rule in cd.grammar.get_order_rules()}
    assert {
        ("near", "density"),
        ("density", "near"),
        ("intersect", "density"),
        ("density", "intersect"),
        ("intersect", "summarize"),
        ("summarize", "intersect"),
        ("clip", "summarize"),
        ("summarize", "clip"),
        ("anomaly", "threshold"),
        ("threshold", "events"),
        ("events", "duration"),
        ("events", "frequency"),
        ("events", "magnitude"),
        ("mean", "events"),
        ("threshold", "mean"),
        ("mean", "threshold"),
        ("aggregate", "onset"),
        ("filter", "change"),
        ("change", "filter"),
        ("transition", "summarize"),
        ("summarize", "change"),
        ("subtract", "divide"),
        ("divide", "subtract"),
        ("normalize", "threshold"),
        ("threshold", "normalize"),
        ("exposure", "summarize"),
        ("near", "summarize"),
        ("upstream", "intersect"),
        ("intersect", "upstream"),
    }.issubset(pairs)


def test_overlap_rejects_obvious_crs_conflict_before_combining():
    left = (
        cd.pipe(_temperature_cube())
        | v.threshold_state(threshold=25.0, direction="above")
    ).unwrap()
    other_cube = _temperature_cube().assign_attrs(
        {**_temperature_cube().attrs, "crs": "EPSG:3857"}
    )
    right = (
        cd.pipe(other_cube)
        | v.threshold_state(threshold=25.0, direction="above")
    ).unwrap()

    with pytest.raises(cd.grammar.SemanticGrammarError) as error:
        cd.pipe(left) | v.overlap(right)

    message = str(error.value)
    assert "same CRS" in message
    assert "EPSG:4326" in message
    assert "EPSG:3857" in message


def test_state_and_event_outputs_carry_semantic_metadata():
    states = (
        cd.pipe(_temperature_cube())
        | v.threshold_state(threshold=25.0, direction="above", name="hot day")
    ).unwrap()
    assert states.attrs["semantic_kind"] == "condition"
    assert states.attrs["semantic_units"] == "boolean"

    events = (cd.pipe(states) | v.detect_events()).unwrap()
    assert events.dataset.attrs["semantic_kind"] == "event"
    assert events.dataset.attrs["semantic_category"] == "event"


@pytest.mark.parametrize(
    ("stages", "expected_kind"),
    [
        ((v.anomaly(over="time"),), "continuous_field"),
        ((v.anomaly(over="time"), v.zscore(over="time")), "continuous_field"),
        (
            (
                v.anomaly(over="time"),
                v.zscore(over="time"),
                v.threshold_state(threshold=0.5, direction="above"),
            ),
            "condition",
        ),
        (
            (
                v.anomaly(over="time"),
                v.zscore(over="time"),
                v.threshold_state(threshold=0.5, direction="above"),
                v.detect_events(min_duration=1),
            ),
            "event",
        ),
    ],
)
def test_curated_legal_chains_of_length_one_to_four(stages, expected_kind):
    result = cd.pipe(_temperature_cube())
    for stage in stages:
        result = result | stage

    assert result.semantic_state.semantic_kind == expected_kind
    assert len(result.semantic_trace) == len(stages)


@pytest.mark.parametrize(
    ("first_stage", "invalid_stage", "guidance"),
    [
        (v.mean(over="time"), v.detect_events(), "earlier reduction removed"),
        (v.anomaly(over="time"), v.detect_events(), "threshold_state"),
    ],
)
def test_curated_invalid_chains_are_rejected_with_semantic_guidance(
    first_stage, invalid_stage, guidance
):
    result = cd.pipe(_temperature_cube()) | first_stage

    with pytest.raises(cd.grammar.SemanticGrammarError, match=guidance):
        result | invalid_stage
