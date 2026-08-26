"""Small source-lifecycle value objects used by the existing data catalog.

These types describe source maintenance and certification without changing the
public noun-and-pipe programming model.  The authoritative noun/source records
remain in :mod:`cubedynamics.data.catalog`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import re
from typing import Any, Mapping


class SourceMode(str, Enum):
    """How upstream content advances without implying a provider version scheme."""

    SNAPSHOT = "snapshot"
    ROLLING = "rolling"


class RevisionStatus(str, Enum):
    """Scientific validity of an immutable CubeDynamics serving revision."""

    NOT_VALIDATED = "NOT_VALIDATED"
    VALIDATED = "VALIDATED"
    SUPERSEDED = "SUPERSEDED"
    ROLLED_BACK = "ROLLED_BACK"


class RevisionStage(str, Enum):
    """Promotion stage for an immutable serving revision."""

    CANDIDATE = "CANDIDATE"
    CURRENT = "CURRENT"
    RETIRED = "RETIRED"


class LiveHealth(str, Enum):
    """Current endpoint condition, kept separate from revision validity."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"


class CertificationOutcome(str, Enum):
    """Allowed machine-readable outcomes for a QA or certification gate."""

    NOT_TESTED = "NOT_TESTED"
    PASS = "PASS"
    PASS_WITH_CAVEATS = "PASS_WITH_CAVEATS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class SourceChange(str, Enum):
    """Maintenance-relevant classes of upstream change."""

    CONTENT_EXTENSION = "CONTENT_EXTENSION"
    NEW_SNAPSHOT_RELEASE = "NEW_SNAPSHOT_RELEASE"
    SCHEMA_CHANGE = "SCHEMA_CHANGE"
    SEMANTIC_CHANGE = "SEMANTIC_CHANGE"
    HISTORICAL_REVISION = "HISTORICAL_REVISION"
    SERVICE_HEALTH_CHANGE = "SERVICE_HEALTH_CHANGE"


_REVISION_PATTERN = re.compile(
    r"^(?P<noun>[a-z][a-z0-9_]*)\."
    r"(?P<source_flavor>[a-z][a-z0-9_]*)@"
    r"(?P<created>\d{4}-\d{2}-\d{2})\."
    r"(?P<sequence>[1-9][0-9]*)$"
)


@dataclass(frozen=True, order=True)
class ServingRevision:
    """Immutable identifier for one CubeDynamics interpretation of a source."""

    noun: str
    source_flavor: str
    created: date
    sequence: int

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.noun):
            raise ValueError("Serving revision noun must be a normalized identifier.")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.source_flavor):
            raise ValueError("Serving revision source flavor must be a normalized identifier.")
        if self.sequence < 1:
            raise ValueError("Serving revision sequence must be positive.")

    @classmethod
    def parse(cls, value: str) -> "ServingRevision":
        """Parse ``noun.source@YYYY-MM-DD.N`` and reject ambiguous identifiers."""

        if not isinstance(value, str):
            raise ValueError("Serving revision must be a string.")
        match = _REVISION_PATTERN.fullmatch(value.strip())
        if match is None:
            raise ValueError(
                "Serving revision must match noun.source@YYYY-MM-DD.N, "
                "for example temperature.prism@2026-08-26.1."
            )
        try:
            created = date.fromisoformat(match.group("created"))
        except ValueError as exc:
            raise ValueError("Serving revision contains an invalid calendar date.") from exc
        return cls(
            noun=match.group("noun"),
            source_flavor=match.group("source_flavor"),
            created=created,
            sequence=int(match.group("sequence")),
        )

    def __str__(self) -> str:
        return (
            f"{self.noun}.{self.source_flavor}@"
            f"{self.created.isoformat()}.{self.sequence}"
        )


@dataclass(frozen=True)
class UpstreamIdentity:
    """Provider-native identity observed for one bounded retrieval."""

    provider: str
    product: str
    endpoint: str
    strategy: Mapping[str, Any]
    observed: Mapping[str, Any] = field(default_factory=dict)
    retrieved_at: str | None = None

    def __post_init__(self) -> None:
        if not all((self.provider, self.product, self.endpoint)):
            raise ValueError("Upstream identity requires provider, product, and endpoint.")
        if not isinstance(self.strategy, Mapping) or not self.strategy.get("kind"):
            raise ValueError("Upstream identity strategy requires a non-empty 'kind'.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "product": self.product,
            "endpoint": self.endpoint,
            "strategy": _json_safe(self.strategy),
            "observed": _json_safe(self.observed),
            "retrieved_at": self.retrieved_at,
        }


@dataclass(frozen=True)
class CertificationRecord:
    """Machine-readable evidence summary for offline or live source QA."""

    mode: str
    outcome: CertificationOutcome
    gates: Mapping[str, CertificationOutcome]
    serving_revision: str
    last_validated: str
    evidence: Mapping[str, Any] = field(default_factory=dict)
    caveats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ServingRevision.parse(self.serving_revision)
        if self.mode not in {"offline_baseline", "live_source"}:
            raise ValueError("Certification mode must be offline_baseline or live_source.")
        outcome = _coerce_enum(
            self.outcome, CertificationOutcome, "certification outcome"
        )
        gates = {
            str(name): _coerce_enum(value, CertificationOutcome, "gate outcome")
            for name, value in self.gates.items()
        }
        if not gates:
            raise ValueError("Certification requires at least one named gate.")
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "gates", gates)
        blocking = {CertificationOutcome.FAIL, CertificationOutcome.BLOCKED}
        if outcome in {
            CertificationOutcome.PASS,
            CertificationOutcome.PASS_WITH_CAVEATS,
        } and any(value in blocking for value in gates.values()):
            raise ValueError("A passing certification cannot contain a failed or blocked gate.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "outcome": self.outcome.value,
            "gates": {name: value.value for name, value in sorted(self.gates.items())},
            "serving_revision": self.serving_revision,
            "last_validated": self.last_validated,
            "evidence": _json_safe(self.evidence),
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class ServingRevisionRecord:
    """Durable metadata that links an immutable revision to its evidence."""

    revision_id: str
    stage: RevisionStage
    status: RevisionStatus
    created_at: str
    promoted_at: str | None = None
    adapter_version: str | None = None
    schema_fingerprint: str | None = None
    qa_evidence: str | None = None
    normalization_contract: str | None = None
    caveats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ServingRevision.parse(self.revision_id)
        object.__setattr__(self, "stage", _coerce_enum(self.stage, RevisionStage, "revision stage"))
        object.__setattr__(self, "status", _coerce_enum(self.status, RevisionStatus, "revision status"))
        if self.stage is RevisionStage.CURRENT and self.status is not RevisionStatus.VALIDATED:
            raise ValueError("A current serving revision must be VALIDATED.")
        if self.stage is RevisionStage.CURRENT and not self.promoted_at:
            raise ValueError("A current serving revision requires promoted_at evidence.")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ServingRevisionRecord":
        return cls(
            revision_id=str(value["revision_id"]),
            stage=RevisionStage(value["stage"]),
            status=RevisionStatus(value["status"]),
            created_at=str(value["created_at"]),
            promoted_at=value.get("promoted_at"),
            adapter_version=value.get("adapter_version"),
            schema_fingerprint=value.get("schema_fingerprint"),
            qa_evidence=value.get("qa_evidence"),
            normalization_contract=value.get("normalization_contract"),
            caveats=tuple(value.get("caveats", ())),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "stage": self.stage.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "promoted_at": self.promoted_at,
            "adapter_version": self.adapter_version,
            "schema_fingerprint": self.schema_fingerprint,
            "qa_evidence": self.qa_evidence,
            "normalization_contract": self.normalization_contract,
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class ChangeDecision:
    """Required maintenance response to one classified upstream change."""

    creates_candidate_revision: bool
    scientific_review: bool
    adapter_review: bool
    compare_history: bool
    health_only: bool
    reason: str


def decide_source_change(
    change: SourceChange | str,
    *,
    source_mode: SourceMode | str,
) -> ChangeDecision:
    """Translate a classified provider change into a deterministic response."""

    change = _coerce_enum(change, SourceChange, "source change")
    source_mode = _coerce_enum(source_mode, SourceMode, "source mode")

    if change is SourceChange.SERVICE_HEALTH_CHANGE:
        return ChangeDecision(False, False, False, False, True, "Update live health only.")
    if change is SourceChange.CONTENT_EXTENSION:
        if source_mode is SourceMode.ROLLING:
            return ChangeDecision(
                False,
                False,
                False,
                False,
                False,
                "Record retrieval/query time; interpretation and revision remain unchanged.",
            )
        return ChangeDecision(
            True,
            False,
            False,
            False,
            False,
            "A snapshot cannot extend in place; certify a new candidate revision.",
        )
    if change is SourceChange.NEW_SNAPSHOT_RELEASE:
        return ChangeDecision(
            True,
            False,
            False,
            False,
            False,
            "Certify the new release as a candidate.",
        )
    if change is SourceChange.SCHEMA_CHANGE:
        return ChangeDecision(
            True, False, True, False, False, "Review adapter and schema assumptions."
        )
    if change is SourceChange.SEMANTIC_CHANGE:
        return ChangeDecision(
            True,
            True,
            True,
            False,
            False,
            "Require scientific and adapter review.",
        )
    return ChangeDecision(
        True,
        True,
        False,
        True,
        False,
        "Compare old and new historical values before promotion.",
    )


def validate_source_lifecycle(
    *,
    noun: str,
    source_flavor: str,
    definition: Mapping[str, Any],
) -> None:
    """Validate lifecycle fields embedded in one existing catalog record."""

    required = {
        "lifecycle_state",
        "source_mode",
        "access_backend",
        "update_cadence",
        "upstream_identity_strategy",
        "source_endpoint",
        "current_serving_revision",
        "qa_profile",
        "revision_status",
        "live_health",
    }
    missing = sorted(required.difference(definition))
    if missing:
        raise ValueError(
            f"Catalog record {noun}.{source_flavor} is missing lifecycle fields: {missing}."
        )
    _coerce_enum(definition["source_mode"], SourceMode, "source mode")
    _coerce_enum(definition["revision_status"], RevisionStatus, "revision status")
    _coerce_enum(definition["live_health"], LiveHealth, "live health")
    revision = ServingRevision.parse(str(definition["current_serving_revision"]))
    if (revision.noun, revision.source_flavor) != (noun, source_flavor):
        raise ValueError(
            "Catalog serving revision identity does not match its noun/source record."
        )
    strategy = definition["upstream_identity_strategy"]
    if not isinstance(strategy, Mapping) or not strategy.get("kind"):
        raise ValueError("Upstream identity strategy requires a non-empty 'kind'.")


def _coerce_enum(value: Any, enum_type: type[Enum], label: str):
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(item.value for item in enum_type)
        raise ValueError(f"Invalid {label} {value!r}. Expected one of: {allowed}.") from exc


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


__all__ = [
    "CertificationOutcome",
    "CertificationRecord",
    "ChangeDecision",
    "LiveHealth",
    "RevisionStatus",
    "RevisionStage",
    "ServingRevision",
    "ServingRevisionRecord",
    "SourceChange",
    "SourceMode",
    "UpstreamIdentity",
    "decide_source_change",
    "validate_source_lifecycle",
]
