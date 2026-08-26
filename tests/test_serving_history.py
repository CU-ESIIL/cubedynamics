"""Persistent revision history, promotion, and rollback contracts."""

from __future__ import annotations

import pytest

from cubedynamics import data


def test_every_catalog_current_revision_is_in_source_controlled_history() -> None:
    for noun, flavors in data.list_sources().items():
        for flavor in flavors:
            catalog = data.describe(noun, flavor)
            record = data.current_revision_record(noun, flavor)
            assert record.revision_id == catalog["current_serving_revision"]
            assert record.stage is data.RevisionStage.CURRENT
            assert record.status is data.RevisionStatus.VALIDATED


def test_daymet_is_a_blocked_candidate_not_a_discoverable_source() -> None:
    candidate = data.serving_history("temperature", "daymet")[0]
    assert candidate.stage is data.RevisionStage.CANDIDATE
    assert candidate.status is data.RevisionStatus.NOT_VALIDATED
    assert "daymet" not in data.sources("temperature")
    with pytest.raises(ValueError, match="VALIDATED"):
        data.validate_promotion(candidate, certification_outcome="PASS")


def test_rollback_refuses_when_no_validated_retired_revision_exists() -> None:
    with pytest.raises(ValueError, match="No validated rollback target"):
        data.rollback_target("temperature", "prism")
