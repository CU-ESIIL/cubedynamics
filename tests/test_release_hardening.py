"""Release gates must reject source leakage and repository payloads."""
import importlib.util
import json
from pathlib import Path
import re
import sys
import zipfile

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_release_artifact as artifact
import run_vignettes as runner
import run_release_gate as gate


def test_release_versions_citation_and_maturity_are_consistent():
    pyproject = (ROOT / "pyproject.toml").read_text()
    declared = re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1)
    from cubedynamics import __version__
    root_citation = yaml.safe_load((ROOT / "CITATION.cff").read_text())
    assert root_citation == yaml.safe_load((ROOT / "docs/CITATION.cff").read_text())
    assert declared == __version__ == root_citation["version"] == "0.1.0"
    assert "Development Status :: 3 - Alpha" in pyproject
    assert "doi" not in root_citation
    assert 'exclude = ["cubedynamics.tests", "cubedynamics.tests.*"]' in pyproject
    assert "prune tests" in (ROOT / "MANIFEST.in").read_text()


@pytest.mark.parametrize("name", ["cubedynamics/tests/test_example.py", "tests/fixture.nc",
    "paper/draft.md", "docs/manuscripts/paper.md", "notebooks/run.ipynb",
    "source_projects/proof.json", "outputs/result.csv", "../escape.py", "/absolute.py"])
def test_archive_inventory_rejects_development_payload(name):
    with pytest.raises(RuntimeError):
        artifact.check_members([name])


def test_archive_inventory_allows_required_runtime_assets():
    artifact.check_members(artifact.REQUIRED)


def test_missing_wheel_data_is_a_failure(tmp_path):
    wheel = tmp_path / "empty.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("cubedynamics/__init__.py", "")
    with pytest.raises(RuntimeError, match="Missing wheel assets"):
        artifact.inspect_distributions(wheel)


def test_editable_checkout_cannot_pass_installed_wheel_check(tmp_path):
    # The ordinary test environment resolves the checkout or its editable venv.
    with pytest.raises(RuntimeError, match="checkout|Editable|wheel test|supplied wheel"):
        artifact.check_installed_wheel(tmp_path / "missing.whl", ROOT)


def test_release_kernel_uses_exact_python_and_ignores_user_pythonpath(tmp_path):
    python = tmp_path / "external-venv/bin/python"
    manager = runner.release_kernel(tmp_path, python)
    assert manager.kernel_name == "cubedynamics-release"
    assert manager.kernel_spec.argv[:4] == [str(python), "-I", "-m", "ipykernel_launcher"]
    assert str(ROOT / "src") not in json.dumps(manager.kernel_spec.to_dict())


def test_release_guard_checks_artifact_not_just_module_name(tmp_path):
    code = runner.release_guard(tmp_path / "release.whl")
    assert "check_installed_wheel" in code and "release.whl" in code
    assert "sys.path.insert" not in code


def test_failed_or_incomplete_gate_cannot_be_recorded_ready(tmp_path):
    (tmp_path / "gate.json").write_text(json.dumps({"status": "PASS", "steps": {}}))
    with pytest.raises(RuntimeError, match="Every mandatory"):
        gate.write_candidate(tmp_path)


def test_source_changes_invalidate_previously_passed_gate(tmp_path):
    (tmp_path / "gate.json").write_text(json.dumps({"status": "PASS",
        "steps": {name: {"exit_code": 0} for name in gate.MANDATORY}, "release_inputs": {}}))
    with pytest.raises(RuntimeError, match="Release inputs changed"):
        gate.write_candidate(tmp_path)
