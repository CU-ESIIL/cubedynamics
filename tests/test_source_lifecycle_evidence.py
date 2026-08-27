"""Release figures come from catalog/code/evidence, not manuscript constants."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import source_lifecycle_evidence as evidence
from cubedynamics import data


def test_inventory_matches_runtime_and_supported_notebooks():
    result = evidence.inventory()
    assert result["noun_count"] == len(data.list_sources())
    assert result["source_count"] == len({s for choices in data.list_sources().values() for s in choices})
    assert result["public_callable_count"] == len(evidence.public_verbs())
    assert "month_filter" in result["callable_statuses"]["implemented"]
    assert result["supported_notebooks"]
    assert result["supported_python_versions"]


def test_junit_counts_and_manifest_do_not_invent_certifications(tmp_path):
    report = tmp_path / "tests.xml"
    report.write_text('<testsuites><testsuite tests="8" failures="1" errors="1" skipped="2"/></testsuites>')
    result = evidence.release_manifest(tmp_path / "release.json", reports=[report], qa_roots=[tmp_path / "missing"])
    assert result["test_reports"][str(report)]["passed"] == 4
    assert result["certification_records"] == []
    assert result["generated_reference_page_count"] == len(result["generated_reference_pages"])
    assert result["supported_notebook_count"] == len(result["supported_notebooks"])


def test_baseline_cannot_be_silently_overwritten(tmp_path):
    existing = tmp_path / "baseline.json"
    existing.write_text('{"historical": true}')
    with pytest.raises(FileExistsError, match="pre-change baseline"):
        evidence.baseline(tmp_path)
    assert existing.read_text() == '{"historical": true}'
