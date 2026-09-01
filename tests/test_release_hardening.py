"""Release gates must reject source leakage and repository payloads."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
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
    assert declared == __version__ == root_citation["version"] == "0.1.0rc1"
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


def archive_origin(sha256, style):
    if style == "legacy":
        return {"hash": "sha256=" + sha256}
    if style == "modern":
        return {"hashes": {"sha256": sha256}}
    return {"hash": "sha256=" + sha256, "hashes": {"sha256": sha256}}


@pytest.mark.parametrize("style", ["legacy", "modern", "both"])
def test_archive_sha256_accepts_pip_metadata_formats(style):
    expected = "ab" * 32
    assert artifact.archive_sha256(archive_origin(expected, style)) == expected


@pytest.mark.parametrize("info", [
    None, [], {}, {"hashes": None}, {"hashes": []}, {"hashes": {}},
    {"hash": None}, {"hash": 123}, {"hash": "sha256"},
    {"hash": "sha256="}, {"hash": "sha256=not-hex"},
    {"hash": "sha256=" + "a" * 63}, {"hash": "md5=" + "a" * 32},
    {"hashes": {"sha256": 123}}, {"hashes": {"sha256": "z" * 64}},
    {"hashes": {"md5": "a" * 32}},
    # A legacy field must not override or rescue conflicting modern metadata.
    {"hashes": {}, "hash": "sha256=" + "a" * 64},
    {"hashes": {"sha256": "b" * 64}, "hash": "sha256=" + "a" * 64},
])
def test_archive_sha256_rejects_missing_malformed_or_conflicting_metadata(info):
    with pytest.raises(RuntimeError, match="archive|SHA256|hash"):
        artifact.archive_sha256(info)


def mock_external_distribution(monkeypatch, installed, origin):
    dist = SimpleNamespace(
        locate_file=lambda name: installed / name,
        read_text=lambda name: json.dumps({"archive_info": origin}),
    )
    monkeypatch.setattr(artifact.metadata, "distribution", lambda name: dist)
    monkeypatch.setattr(sys, "prefix", str(installed.parent))


@pytest.mark.parametrize("style", ["legacy", "modern", "both"])
def test_wrong_wheel_sha256_still_fails_for_every_metadata_format(tmp_path, monkeypatch, style):
    wheel = tmp_path / "wrong.whl"
    wheel.write_bytes(b"a different artifact")
    mock_external_distribution(monkeypatch, tmp_path / "site-packages", archive_origin("0" * 64, style))
    with pytest.raises(RuntimeError, match="SHA256 differs"):
        artifact.check_installed_wheel(wheel, ROOT)


@pytest.mark.parametrize("style", ["legacy", "modern", "both"])
def test_matching_archive_hash_does_not_hide_modified_installed_code(tmp_path, monkeypatch, style):
    wheel = tmp_path / "release.whl"
    installed = tmp_path / "site-packages"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name in artifact.REQUIRED:
            archive.writestr(name, b"original runtime bytes")
            path = installed / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"original runtime bytes")
    (installed / "cubedynamics/piping.py").write_bytes(b"modified runtime bytes")
    mock_external_distribution(monkeypatch, installed, archive_origin(artifact.digest(wheel), style))
    with pytest.raises(RuntimeError, match="Installed wheel file changed: cubedynamics/piping.py"):
        artifact.check_installed_wheel(wheel, ROOT)


@pytest.mark.parametrize("workflow, environment", [
    ("tests.yml", "cubedynamics-wheel"), ("publish.yml", "cubedynamics-release"),
])
def test_ci_upgrades_the_fresh_environments_pip_before_installing_wheel(workflow, environment):
    document = yaml.safe_load((ROOT / ".github/workflows" / workflow).read_text())
    blocks = [step["run"] for job in document["jobs"].values() for step in job["steps"]
              if "run" in step and f'python -m venv "$RUNNER_TEMP/{environment}"' in step["run"]]
    assert len(blocks) == 1
    commands = blocks[0].splitlines()
    create = commands.index(f'python -m venv "$RUNNER_TEMP/{environment}"')
    upgrade = commands.index(f'"$RUNNER_TEMP/{environment}/bin/python" -m pip install --upgrade pip')
    install = commands.index(f'"$RUNNER_TEMP/{environment}/bin/python" -m pip install dist/cubedynamics-0.1.0rc1-py3-none-any.whl')
    assert create < upgrade < install


def test_release_gate_requires_upgrade_with_the_wheel_interpreter():
    assert "upgrade-installer" in gate.MANDATORY
    tree = ast.parse((ROOT / "scripts/run_release_gate.py").read_text())
    calls = {node.args[0].value: node for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == "run" and isinstance(node.args[0], ast.Constant)}
    assert calls["create-environment"].lineno < calls["upgrade-installer"].lineno < calls["install-wheel"].lineno
    command = calls["upgrade-installer"].args[1].elts
    assert command[0].id == "wheel_python"
    assert [node.value for node in command[1:]] == ["-m", "pip", "install", "--upgrade", "pip"]


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


def test_package_only_smoke_requires_truthful_summary_metadata():
    import numpy as np
    import xarray as xr
    from cubedynamics import pipe, verbs as v

    cube = xr.DataArray(
        np.arange(12.0).reshape(3, 2, 2),
        dims=("time", "y", "x"),
        attrs={"units": "K"},
    )
    result = (pipe(cube) | v.mean(over="time", keep_dim=False)).unwrap()

    artifact.verify_mean_semantics(cube, result)
    assert result.attrs["semantic_kind"] == "summary"


def test_source_changes_invalidate_previously_passed_gate(tmp_path):
    (tmp_path / "gate.json").write_text(json.dumps({"status": "PASS",
        "steps": {name: {"exit_code": 0} for name in gate.MANDATORY}, "release_inputs": {}}))
    with pytest.raises(RuntimeError, match="Release inputs changed"):
        gate.write_candidate(tmp_path)
