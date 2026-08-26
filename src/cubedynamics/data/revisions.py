"""Source-controlled serving history and safe promotion/rollback queries."""

from __future__ import annotations

from importlib.resources import files
import json

from .lifecycle import RevisionStage, RevisionStatus, ServingRevisionRecord


def serving_history(noun: str, source_flavor: str) -> tuple[ServingRevisionRecord, ...]:
    """Return immutable history entries for one noun/source pair."""

    key = f"{noun.strip().lower()}.{source_flavor.strip().lower()}"
    payload = json.loads(
        files("cubedynamics.data").joinpath("serving_history.json").read_text(encoding="utf-8")
    )
    records = tuple(
        ServingRevisionRecord.from_dict(item)
        for item in payload["revisions"]
        if item["revision_id"].split("@", 1)[0] == key
    )
    if not records:
        raise ValueError(f"No serving history exists for {key!r}.")
    return tuple(sorted(records, key=lambda item: item.revision_id))


def current_revision_record(noun: str, source_flavor: str) -> ServingRevisionRecord:
    """Return the single current revision, rejecting ambiguous history."""

    current = [
        item
        for item in serving_history(noun, source_flavor)
        if item.stage is RevisionStage.CURRENT
    ]
    if len(current) != 1:
        raise ValueError(
            f"Expected exactly one current revision for {noun}.{source_flavor}; found {len(current)}."
        )
    return current[0]


def validate_promotion(
    candidate: ServingRevisionRecord,
    *,
    certification_outcome: str,
) -> None:
    """Validate a proposed promotion without rewriting source-controlled history."""

    if candidate.stage is not RevisionStage.CANDIDATE:
        raise ValueError("Only a CANDIDATE revision can be promoted.")
    if candidate.status is not RevisionStatus.VALIDATED:
        raise ValueError("Promotion requires a VALIDATED candidate.")
    if certification_outcome not in {"PASS", "PASS_WITH_CAVEATS"}:
        raise ValueError("Promotion requires passing certification evidence.")
    if not candidate.schema_fingerprint or not candidate.qa_evidence:
        raise ValueError("Promotion requires schema fingerprint and QA evidence links.")


def rollback_target(noun: str, source_flavor: str) -> ServingRevisionRecord:
    """Return the newest validated retired revision eligible for rollback."""

    eligible = [
        item
        for item in serving_history(noun, source_flavor)
        if item.stage is RevisionStage.RETIRED
        and item.status is RevisionStatus.VALIDATED
    ]
    if not eligible:
        raise ValueError(f"No validated rollback target exists for {noun}.{source_flavor}.")
    return eligible[-1]


__all__ = [
    "current_revision_record",
    "rollback_target",
    "serving_history",
    "validate_promotion",
]
