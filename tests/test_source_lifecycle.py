"""Contracts for source lifecycle, serving revisions, and certification states."""

from __future__ import annotations

import pytest

from cubedynamics import data


def test_every_catalog_record_has_a_valid_serving_lifecycle() -> None:
    for noun, flavors in data.list_sources().items():
        for flavor in flavors:
            record = data.describe(noun, flavor)
            revision = data.ServingRevision.parse(record["current_serving_revision"])
            assert revision.noun == noun
            assert revision.source_flavor == flavor
            assert record["source_flavor"] == flavor
            assert record["source_mode"] in {"snapshot", "rolling"}
            assert record["qa_profile"] in data.list_qa_profiles()
            assert record["revision_status"] == "VALIDATED"
            assert record["live_health"] == "STALE"


def test_revision_validity_and_live_health_are_independent_states() -> None:
    revision_status = data.RevisionStatus.VALIDATED
    live_health = data.LiveHealth.UNAVAILABLE

    assert revision_status.value == "VALIDATED"
    assert live_health.value == "UNAVAILABLE"


@pytest.mark.parametrize(
    ("change", "mode", "candidate", "health_only"),
    [
        (data.SourceChange.CONTENT_EXTENSION, data.SourceMode.ROLLING, False, False),
        (data.SourceChange.CONTENT_EXTENSION, data.SourceMode.SNAPSHOT, True, False),
        (data.SourceChange.NEW_SNAPSHOT_RELEASE, data.SourceMode.SNAPSHOT, True, False),
        (data.SourceChange.SCHEMA_CHANGE, data.SourceMode.ROLLING, True, False),
        (data.SourceChange.SEMANTIC_CHANGE, data.SourceMode.ROLLING, True, False),
        (data.SourceChange.HISTORICAL_REVISION, data.SourceMode.ROLLING, True, False),
        (data.SourceChange.SERVICE_HEALTH_CHANGE, data.SourceMode.ROLLING, False, True),
    ],
)
def test_change_classification_has_a_deterministic_response(
    change, mode, candidate, health_only
) -> None:
    decision = data.decide_source_change(change, source_mode=mode)

    assert decision.creates_candidate_revision is candidate
    assert decision.health_only is health_only
    assert decision.reason


def test_serving_revision_rejects_wrong_identity_shape() -> None:
    with pytest.raises(ValueError, match="noun.source"):
        data.ServingRevision.parse("gridmet-2026")


def test_passing_certification_cannot_hide_a_failed_gate() -> None:
    with pytest.raises(ValueError, match="passing certification"):
        data.CertificationRecord(
            mode="offline_baseline",
            outcome=data.CertificationOutcome.PASS,
            gates={"schema": data.CertificationOutcome.FAIL},
            serving_revision="temperature.gridmet@2026-08-26.1",
            last_validated="2026-08-26",
        )


def test_certification_outcome_vocabulary_is_closed_and_machine_readable() -> None:
    assert {outcome.value for outcome in data.CertificationOutcome} == {
        "NOT_TESTED",
        "PASS",
        "PASS_WITH_CAVEATS",
        "FAIL",
        "BLOCKED",
    }


def test_source_mode_validation_rejects_undeclared_modes() -> None:
    with pytest.raises(ValueError, match="Invalid source mode"):
        data.decide_source_change(data.SourceChange.CONTENT_EXTENSION, source_mode="hybrid")
