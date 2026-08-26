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
    result = json.loads((tmp_path / "prism_temperature.json").read_text(encoding="utf-8"))

    assert result["qa_result"] == "pass"
    assert all(result["checks"].values())
    assert result["fixture_sha256"]
    assert (tmp_path / result["figure"]).stat().st_size > 10_000
    assert "temperature" in manifest["implemented_nouns"]
    assert manifest["status"].startswith("partial")
    assert all(item["real_visual_qa"] != "pass" or (
        item["noun"] == "temperature" and item["source_flavor"] == "prism"
    ) for item in manifest["source_status"])
