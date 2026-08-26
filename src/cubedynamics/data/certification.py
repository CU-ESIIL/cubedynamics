"""Shared live-source certification built on the reusable QA profiles."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from .lifecycle import CertificationOutcome, CertificationRecord, LiveHealth
from .qa import evaluate_qa_profile
from .schema import compare_normalized_schemas, normalize_xarray_schema, schema_fingerprint


def certify_live_sample(
    sample: Any,
    *,
    qa_profile: str,
    serving_revision: str,
    endpoint_verified: bool,
    bounded_access_verified: bool,
    upstream_identity_verified: bool | None,
    expected_schema: Mapping[str, Any] | None = None,
    caveats: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Certify one tiny remote sample with the same profile used offline."""

    profile = evaluate_qa_profile(qa_profile, sample, caveats=caveats)
    observed_schema = normalize_xarray_schema(sample)
    drift = (
        compare_normalized_schemas(expected_schema, observed_schema)
        if expected_schema is not None
        else None
    )
    schema_ok = drift is None or bool(drift["matches"])
    gates = {
        "endpoint_verified": _gate(endpoint_verified),
        "sample_retrieved": CertificationOutcome.PASS,
        "bounded_access_verified": _gate(bounded_access_verified),
        "schema_validated": _gate(schema_ok),
        "numerical_qa": profile.outcome,
        "visual_qa": CertificationOutcome.NOT_TESTED,
        "upstream_identity_verified": _optional_gate(upstream_identity_verified),
    }
    blocking = {CertificationOutcome.FAIL, CertificationOutcome.BLOCKED}
    if any(value in blocking for value in gates.values()):
        outcome = CertificationOutcome.FAIL
        health = LiveHealth.DEGRADED
    elif caveats or CertificationOutcome.NOT_TESTED in gates.values():
        outcome = CertificationOutcome.PASS_WITH_CAVEATS
        health = LiveHealth.DEGRADED
    else:
        outcome = CertificationOutcome.PASS
        health = LiveHealth.HEALTHY
    record = CertificationRecord(
        mode="live_source",
        outcome=outcome,
        gates=gates,
        serving_revision=serving_revision,
        last_validated=datetime.now(timezone.utc).isoformat(),
        evidence={
            "schema_fingerprint": schema_fingerprint(sample),
            "schema_drift": drift,
            "qa_profile": profile.as_dict(),
        },
        caveats=caveats,
    )
    return {"live_health": health.value, "certification": record.as_dict()}


def blocked_live_certification(
    *, serving_revision: str, reason: str
) -> dict[str, Any]:
    """Represent unavailable credentials/services without inventing a pass."""

    record = CertificationRecord(
        mode="live_source",
        outcome=CertificationOutcome.BLOCKED,
        gates={
            "endpoint_verified": CertificationOutcome.BLOCKED,
            "sample_retrieved": CertificationOutcome.NOT_TESTED,
            "bounded_access_verified": CertificationOutcome.NOT_TESTED,
            "schema_validated": CertificationOutcome.NOT_TESTED,
            "numerical_qa": CertificationOutcome.NOT_TESTED,
            "visual_qa": CertificationOutcome.NOT_TESTED,
            "upstream_identity_verified": CertificationOutcome.NOT_TESTED,
        },
        serving_revision=serving_revision,
        last_validated=datetime.now(timezone.utc).isoformat(),
        caveats=(reason,),
    )
    return {"live_health": LiveHealth.UNAVAILABLE.value, "certification": record.as_dict()}


def write_live_certification(result: Mapping[str, Any], output: Path) -> None:
    """Persist health/certification evidence as an uploadable JSON artifact."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _gate(value: bool) -> CertificationOutcome:
    return CertificationOutcome.PASS if value else CertificationOutcome.FAIL


def _optional_gate(value: bool | None) -> CertificationOutcome:
    if value is None:
        return CertificationOutcome.NOT_TESTED
    return _gate(value)


__all__ = [
    "blocked_live_certification",
    "certify_live_sample",
    "write_live_certification",
]
