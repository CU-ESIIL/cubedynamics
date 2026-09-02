"""Reusable tag, artifact, and publication refusal contracts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.check_release_source import check
from scripts.release_metadata import release_identity
from scripts.run_release_gate import MANDATORY
from scripts.verify_release_bundle import verify_bundle


ROOT = Path(__file__).resolve().parents[1]


def release_workflow() -> dict:
    import yaml

    return yaml.safe_load((ROOT / ".github/workflows/publish.yml").read_text())


@pytest.mark.parametrize("job_name", ["compatibility", "github-release", "publish"])
def test_clean_source_is_checked_before_artifact_download(job_name: str) -> None:
    """Workflow-created bundles must not invalidate the strict source guard."""

    steps = release_workflow()["jobs"][job_name]["steps"]
    source_checks = [
        index
        for index, step in enumerate(steps)
        if "check_release_source.py" in step.get("run", "")
    ]
    downloads = [
        index
        for index, step in enumerate(steps)
        if step.get("uses", "").startswith("actions/download-artifact@")
    ]
    bundle_checks = [
        index
        for index, step in enumerate(steps)
        if "verify_release_bundle.py" in step.get("run", "")
    ]

    assert len(source_checks) == len(downloads) == len(bundle_checks) == 1
    assert source_checks[0] < downloads[0] < bundle_checks[0]


def test_github_release_defines_the_verified_manifest_asset() -> None:
    steps = release_workflow()["jobs"]["github-release"]["steps"]
    release = next(step for step in steps if "gh \"${args[@]}\"" in step.get("run", ""))
    assert release["env"]["MANIFEST"] == "${{ needs.build.outputs.candidate_manifest }}"


def write_project(root: Path, version: str, runtime: str | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "cubedynamics"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    runtime_file = root / "src/cubedynamics/version.py"
    runtime_file.parent.mkdir(parents=True, exist_ok=True)
    runtime_file.write_text(
        f'__version__ = "{runtime or version}"\n', encoding="utf-8"
    )


@pytest.mark.parametrize(
    ("version", "prerelease"),
    [("0.1.0rc2", True), ("0.2.0a1", True), ("0.2.0b3", True), ("0.1.0", False)],
)
def test_release_identity_parses_prerelease_and_stable_versions(
    tmp_path: Path, version: str, prerelease: bool
) -> None:
    write_project(tmp_path, version)
    identity = release_identity(
        tmp_path,
        ref=f"refs/tags/v{version}",
        require_tag=True,
        commit="a" * 40,
    )
    assert identity.version == version
    assert identity.prerelease is prerelease
    assert identity.wheel_filename == f"cubedynamics-{version}-py3-none-any.whl"
    assert identity.sdist_filename == f"cubedynamics-{version}.tar.gz"
    assert identity.candidate_manifest == f"manifests/releases/v{version}-candidate.json"
    assert identity.output_dir == f"artifacts/release-{version}"
    assert identity.artifact_name == f"python-package-distributions-{version}-aaaaaaaaaaaa"


def test_release_identity_rejects_runtime_tag_and_branch_mismatches(tmp_path: Path) -> None:
    write_project(tmp_path, "0.1.0rc2", runtime="0.1.0rc1")
    with pytest.raises(RuntimeError, match="Runtime version"):
        release_identity(tmp_path)

    write_project(tmp_path, "0.1.0rc2")
    with pytest.raises(RuntimeError, match="does not match.*package version"):
        release_identity(tmp_path, ref="refs/tags/v0.1.0rc1")
    with pytest.raises(RuntimeError, match=r"requires an existing v\* tag"):
        release_identity(tmp_path, ref="refs/heads/main", require_tag=True)


def test_release_identity_reads_only_the_project_version_table(tmp_path: Path) -> None:
    write_project(tmp_path, "0.1.0rc2")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[build-system]\nversion = "99.0"\n\n'
        '[project]\nname = "cubedynamics"\nversion = "0.1.0rc2"\n',
        encoding="utf-8",
    )
    assert release_identity(tmp_path).version == "0.1.0rc2"


def test_release_artifact_checker_starts_under_isolated_python() -> None:
    completed = subprocess.run(
        [sys.executable, "-I", ROOT / "scripts/check_release_artifact.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def test_release_source_requires_existing_tag_at_checked_out_commit(tmp_path: Path) -> None:
    write_project(tmp_path, "0.1.0rc2")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "Release test")
    _git(tmp_path, "config", "user.email", "release-test@localhost")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "candidate")
    _git(tmp_path, "tag", "v0.1.0rc2")

    assert check(tmp_path, "refs/tags/v0.1.0rc2", require_tag=True) == "0.1.0rc2"
    with pytest.raises(RuntimeError, match=r"requires an existing v\* tag"):
        check(tmp_path, "refs/heads/main", require_tag=True)

    (tmp_path / "README.md").write_text("new commit\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-qm", "later commit")
    with pytest.raises(RuntimeError, match="not checked-out commit"):
        check(tmp_path, "refs/tags/v0.1.0rc2", require_tag=True)


def make_bundle(root: Path, bundle: Path, *, commit: str = "b" * 40) -> tuple[Path, object]:
    write_project(root, "0.1.0rc2")
    identity = release_identity(
        root,
        ref="refs/tags/v0.1.0rc2",
        require_tag=True,
        commit=commit,
    )
    bundle.mkdir()
    wheel = bundle / identity.wheel_filename
    sdist = bundle / identity.sdist_filename
    wheel.write_bytes(b"tested wheel bytes")
    sdist.write_bytes(b"tested sdist bytes")
    sums = {wheel.name: hashlib.sha256(wheel.read_bytes()).hexdigest(),
            sdist.name: hashlib.sha256(sdist.read_bytes()).hexdigest()}
    (bundle / "SHA256SUMS").write_text(
        "".join(f"{value}  {name}\n" for name, value in sums.items()), encoding="utf-8"
    )
    manifest = {
        "package": "cubedynamics",
        "version": identity.version,
        "tag": identity.tag,
        "expected_tag": identity.expected_tag,
        "commit_sha": commit,
        "release_gate": {"status": "PASS", "steps": {name: 0 for name in MANDATORY}},
        "artifacts": {
            "wheel": {"filename": wheel.name, "sha256": sums[wheel.name], "bytes": wheel.stat().st_size},
            "sdist": {"filename": sdist.name, "sha256": sums[sdist.name], "bytes": sdist.stat().st_size},
        },
    }
    manifest_path = bundle / Path(identity.candidate_manifest).name
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, identity


def test_verified_bundle_binds_version_commit_manifest_and_exact_bytes(tmp_path: Path) -> None:
    root, bundle = tmp_path / "source", tmp_path / "bundle"
    _, identity = make_bundle(root, bundle)
    result = verify_bundle(
        bundle,
        root=root,
        ref="refs/tags/v0.1.0rc2",
        require_tag=True,
        commit="b" * 40,
    )
    assert result["status"] == "PASS"
    assert result["identity"]["artifact_name"] == identity.artifact_name


def test_bundle_refuses_changed_unverified_bytes(tmp_path: Path) -> None:
    root, bundle = tmp_path / "source", tmp_path / "bundle"
    _, identity = make_bundle(root, bundle)
    (bundle / identity.wheel_filename).write_bytes(b"different bytes")
    with pytest.raises(RuntimeError, match="Unverified release bytes"):
        verify_bundle(
            bundle, root=root, ref="refs/tags/v0.1.0rc2",
            require_tag=True, commit="b" * 40,
        )


@pytest.mark.parametrize("failure", ["extra-file", "wrong-tag", "incomplete-gate"])
def test_bundle_refuses_wrong_inventory_identity_or_gate(tmp_path: Path, failure: str) -> None:
    root, bundle = tmp_path / "source", tmp_path / "bundle"
    manifest_path, _ = make_bundle(root, bundle)
    if failure == "extra-file":
        (bundle / "old-release.whl").write_bytes(b"old")
        message = "inventory differs"
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if failure == "wrong-tag":
            manifest["tag"] = "v0.1.0rc1"
            message = "manifest 'tag' mismatch"
        else:
            manifest["release_gate"]["steps"].pop("browser")
            message = "complete passing gate"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RuntimeError, match=message):
        verify_bundle(
            bundle, root=root, ref="refs/tags/v0.1.0rc2",
            require_tag=True, commit="b" * 40,
        )
