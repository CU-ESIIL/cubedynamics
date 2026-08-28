"""Source-controlled serving history and safe promotion/rollback queries."""

from __future__ import annotations

from importlib.resources import files
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import warnings

from .lifecycle import CertificationRecord, CertificationOutcome, RevisionStage, RevisionStatus, ServingRevisionRecord


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
    warnings.warn("Outcome-only validation is a legacy structural check, not a production release gate. "
                  "Use validate_source_promotion with bound certification and artifacts.",
                  DeprecationWarning, stacklevel=2)


PRODUCTION_GATES = frozenset({"contract", "offline", "scientific_review", "bounded_access",
                             "package", "visual_review", "documentation"})


def validate_source_promotion(candidate: ServingRevisionRecord, certification: CertificationRecord,
                              *, artifact_root: Path, now: datetime | None = None,
                              max_age_days: int = 30) -> None:
    """Fail closed unless exact candidate identity and reviewed evidence match.

    This is a read-only gate, not publication or automatic promotion. Required
    gates must explicitly PASS, even for a PASS_WITH_CAVEATS overall result.
    Evidence must name noun/source, adapter version, normalization contract,
    schema fingerprint, supported scope, reviewer, and SHA256-bound artifacts.
    Scientific review is a recorded decision, never inferred from HTTP success.
    Live health remains independent from interpretation validity.
    """
    if candidate.stage is not RevisionStage.CANDIDATE or candidate.status is not RevisionStatus.VALIDATED:
        raise ValueError("Production promotion requires a VALIDATED CANDIDATE")
    if certification.serving_revision != candidate.revision_id:
        raise ValueError("Certification belongs to a different serving revision")
    if certification.outcome not in (CertificationOutcome.PASS, CertificationOutcome.PASS_WITH_CAVEATS):
        raise ValueError("Production certification must pass")
    missing = sorted(k for k in PRODUCTION_GATES if certification.gates.get(k) is not CertificationOutcome.PASS)
    if missing:
        raise ValueError(f"Production gates are not PASS: {', '.join(missing)}")
    evidence = certification.evidence
    noun, flavor = candidate.revision_id.split("@", 1)[0].split(".", 1)
    expected = {"noun": noun, "source_flavor": flavor, "adapter_version": candidate.adapter_version,
                "normalization_contract": candidate.normalization_contract,
                "schema_fingerprint": candidate.schema_fingerprint}
    for key, value in expected.items():
        if not value or evidence.get(key) != value:
            raise ValueError(f"Certification {key} does not match candidate")
    if not evidence.get("supported_scope") or not evidence.get("reviewer"):
        raise ValueError("Production evidence requires supported scope and reviewer")
    if type(max_age_days) is not int or max_age_days < 1:
        raise ValueError("max_age_days must be a positive integer")
    timestamp = datetime.fromisoformat(certification.last_validated.replace("Z", "+00:00"))
    now = now or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or now.tzinfo is None or not timedelta(0) <= now - timestamp <= timedelta(days=max_age_days):
        raise ValueError("Certification timestamp is missing timezone, future-dated or stale")
    artifacts = evidence.get("artifact_sha256", {})
    if not artifacts or candidate.qa_evidence not in artifacts:
        raise ValueError("Candidate QA evidence must be bound to an artifact checksum")
    root = Path(artifact_root).resolve()
    for relative, digest in artifacts.items():
        path = (root / relative).resolve()
        if Path(relative).is_absolute() or not path.is_relative_to(root):
            raise ValueError("Evidence artifact escapes artifact_root")
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Expected a full SHA256 artifact digest")
        checksum = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                checksum.update(block)
        if checksum.hexdigest() != digest:
            raise ValueError(f"Evidence checksum mismatch: {relative}")


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
    "validate_source_promotion",
]
