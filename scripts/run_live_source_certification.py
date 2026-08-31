#!/usr/bin/env python3
"""Write bounded live-source health and certification evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from cubedynamics import data
from cubedynamics.data.certification import (
    blocked_live_certification,
    certify_live_sample,
    write_live_certification,
)
from cubedynamics.data.daymet import load_daymet_candidate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "source_qa" / "live"


def _prism() -> tuple[object, str, str]:
    sample = data.temperature(
        source="prism",
        statistic="maximum",
        bbox=[-105.35, 39.95, -105.20, 40.10],
        start="2024-07-01",
        end="2024-07-03",
        freq="D",
        show_progress=False,
    )
    revision = data.describe("temperature", "prism")["current_serving_revision"]
    return sample, revision, "climate_continuous_daily"


def _daymet() -> tuple[object, str, str]:
    sample = load_daymet_candidate(
        variable="tmax",
        bbox=[-105.35, 39.95, -105.20, 40.10],
        start="2020-07-01",
        end="2020-07-03",
    )
    return sample, "temperature.daymet@2026-08-26.1", "climate_continuous_daily"


LOADERS = {"prism": _prism, "daymet": _daymet}


def _diagnostics(result: dict[str, object]) -> list[str]:
    """Return compact failure context suitable for a CI log."""

    certification = result["certification"]
    assert isinstance(certification, dict)
    lines = []
    failed_gates = sorted(
        name
        for name, outcome in certification.get("gates", {}).items()
        if outcome in {"FAIL", "BLOCKED"}
    )
    if failed_gates:
        lines.append(f"  failed gates: {', '.join(failed_gates)}")
    evidence = certification.get("evidence", {})
    profile = evidence.get("qa_profile", {}) if isinstance(evidence, dict) else {}
    failed_checks = sorted(
        name for name, passed in profile.get("checks", {}).items() if not passed
    )
    if failed_checks:
        lines.append(f"  failed QA checks: {', '.join(failed_checks)}")
    for caveat in certification.get("caveats", []):
        lines.append(f"  caveat: {caveat}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", choices=sorted(LOADERS))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    sources = args.source or sorted(LOADERS)
    failed = False
    for source in sources:
        try:
            sample, revision, profile = LOADERS[source]()
            result = certify_live_sample(
                sample,
                qa_profile=profile,
                serving_revision=revision,
                endpoint_verified=True,
                bounded_access_verified=True,
                upstream_identity_verified=(
                    True if sample.attrs.get("source_url") else None
                ),
                caveats=("Visual QA remains in the reviewed offline baseline.",),
            )
            failed = failed or result["certification"]["outcome"] == "FAIL"
        except Exception as exc:
            revision = (
                "temperature.daymet@2026-08-26.1"
                if source == "daymet"
                else data.describe("temperature", source)["current_serving_revision"]
            )
            result = blocked_live_certification(
                serving_revision=revision,
                reason=f"{type(exc).__name__}: {exc}",
            )
        result = {"source_flavor": source, **result}
        write_live_certification(result, args.output / f"{source}.json")
        print(f"{source}: {result['certification']['outcome']}")
        if result["certification"]["outcome"] in {"FAIL", "BLOCKED"}:
            print("\n".join(_diagnostics(result)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
