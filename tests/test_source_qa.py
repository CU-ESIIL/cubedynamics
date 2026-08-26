"""Guardrails for the Phase 1 source-QA workflow."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_source_qa_writes_real_data_evidence(tmp_path: Path) -> None:
    subprocess.run(
        [sys.executable, "scripts/run_source_qa.py", "--output", str(tmp_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    result_files = [
        "prism_temperature.json",
        "gridmet_temperature.json",
        "sentinel2_surface_reflectance.json",
    ]
    results = [json.loads((tmp_path / name).read_text(encoding="utf-8")) for name in result_files]
    for result in results:
        assert result["qa_result"] == "pass"
        assert all(result["checks"].values())
        assert result["fixture_sha256"]
        assert result["schema_fingerprint"].startswith("sha256:")
        assert result["serving_revision"]
        assert result["source_mode"] == "rolling"
        assert result["revision_status"] == "VALIDATED"
        assert result["upstream_identity"]["endpoint"]
        assert result["upstream_identity"]["observed"]
        assert result["profile_result"]["outcome"] == "PASS"
        assert all(result["profile_result"]["checks"].values())
        assert result["certification"]["mode"] == "offline_baseline"
        assert result["certification"]["outcome"] == "PASS_WITH_CAVEATS"
        assert result["certification"]["gates"]["endpoint_verified"] == "NOT_TESTED"
        assert all(
            outcome == "PASS"
            for gate, outcome in result["certification"]["gates"].items()
            if gate != "endpoint_verified"
        )
        assert (tmp_path / result["figure"]).stat().st_size > 10_000
    assert "temperature" in manifest["implemented_nouns"]
    assert manifest["status"].startswith("Phase 1 source-adapter baseline complete")
    assert {result["source_flavor"] for result in manifest["reviewed_real_data_results"]} == {
        "gridmet",
        "prism",
        "sentinel2",
    }
    assert all(
        item["real_visual_qa"] == "representative source pass"
        for item in manifest["source_status"]
    )
