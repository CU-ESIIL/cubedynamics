"""Outside-user installation and publication must remain consistent."""
import hashlib
import io
from pathlib import Path
import re
import subprocess

import matplotlib.pyplot as plt
import pytest
import yaml

from scripts.check_release_source import check
from scripts.release_metadata import release_identity
from scripts.run_release_gate import check_commit, step_environment

ROOT = Path(__file__).resolve().parents[1]


def test_rc_version_is_consistent_in_development_lockfile_and_citations():
    lock = (ROOT / "uv.lock").read_text()
    assert 'name = "cubedynamics"\nversion = "0.1.0rc2"' in lock
    for path in ("CITATION.cff", "docs/CITATION.cff"):
        assert yaml.safe_load((ROOT / path).read_text())["version"] == "0.1.0rc2"


def test_docs_gate_uses_inline_outputs_without_changing_script_backend():
    base = {"MPLBACKEND": "Agg", "MPLCONFIGDIR": "/tmp/example-cache"}
    assert step_environment(base, "docs") == {
        **base, "MPLBACKEND": "module://matplotlib_inline.backend_inline",
    }
    assert step_environment(base, "offline") == base
    assert base["MPLBACKEND"] == "Agg"


@pytest.mark.parametrize("page", ["README.md", "docs/index.md", "docs/quickstart.md",
                                  "docs/getting_started/install.md", "docs/project/release_0_1_0.md"])
def test_install_entry_points_disclose_published_rc(page):
    text = (ROOT / page).read_text()
    assert "0.1.0rc1" in text
    assert re.search(r"(?:is|was|contains) published|published .*0\.1\.0rc1|PyPI contains", text, re.I)
    assert not re.search(r"0\.1\.0rc1[^\n.]*not (yet )?published", text, re.I)
    if "releases/download/" in text:
        assert re.search(r"[Ff]uture|[Aa]fter.*[Pp]ublication|[Aa]fter.*published", text)


def test_next_candidate_cannot_be_described_as_overwriting_public_rc1():
    text = (ROOT / "RELEASING.md").read_text()
    assert re.search(r"`?0\.1\.0rc1`? is public on PyPI", text)
    assert "must not be described as public" in text
    assert "new committed version and matching tag" in text


def test_external_quickstart_exact_code_uses_checked_public_data(monkeypatch):
    blocks = dict(re.findall(r"<!-- external-quickstart: (\w+) -->\s*```python\n(.*?)```",
                             (ROOT / "docs/quickstart.md").read_text(), re.S))
    payload = (ROOT / "tests/fixtures/real_data/prism_boulder_january_2024.nc").read_bytes()
    requests = []
    def download(url, timeout):
        requests.append((url, timeout))
        return io.BytesIO(payload)
    monkeypatch.setattr("urllib.request.urlopen", download)
    shown = []
    monkeypatch.setattr(plt, "show", lambda: shown.append(bool(plt.gcf().axes)))
    namespace = {}
    try:
        for name in ("observations", "analysis", "discovery"):
            exec(compile(blocks[name], f"quickstart/{name}", "exec"), namespace)
        assert shown == [True]
        assert namespace["expected"] == hashlib.sha256(payload).hexdigest()
        assert requests == [(namespace["url"], 30)]
        assert "862a80aed8a2781b40e6e5293fd6cfbcba887aa4" in requests[0][0]
        monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(b"wrong"))
        with pytest.raises(RuntimeError, match="differ"):
            exec(blocks["observations"], {})
    finally:
        plt.close("all")


def test_publication_requires_explicit_authorization_full_gate_and_matrix():
    document = yaml.safe_load((ROOT / ".github/workflows/publish.yml").read_text())
    trigger = document.get("on", document.get(True))
    assert trigger["workflow_dispatch"]["inputs"]["destination"]["default"] == "verify"
    assert trigger["workflow_dispatch"]["inputs"]["release_tag"]["required"] is True
    jobs = document["jobs"]
    assert jobs["compatibility"]["strategy"]["matrix"]["python-version"] == ["3.9", "3.10", "3.11", "3.12"]
    assert any("scripts/run_release_gate.py" in s.get("run", "") for s in jobs["build"]["steps"])
    workflow_text = (ROOT / ".github/workflows/publish.yml").read_text()
    assert "0.1.0rc1" not in workflow_text
    assert "scripts/release_metadata.py" in workflow_text
    for name, destination in (("github-release", "github"), ("publish", "pypi")):
        job = jobs[name]
        assert set(job["needs"]) == {"build", "compatibility"}
        assert "github.event_name == 'workflow_dispatch'" in job["if"]
        assert f"inputs.destination == '{destination}'" in job["if"]
        commands = "\n".join(step.get("run", "") for step in job["steps"])
        assert "check_release_source.py" in commands
        assert "verify_release_bundle.py" in commands
        assert "python -m build" not in commands
    upload = "\n".join(step.get("run", "") for step in jobs["github-release"]["steps"])
    assert "--verify-tag" in upload
    assert 'if [[ "$PRERELEASE" == "true" ]]' in upload
    assert "release-bundle/$WHEEL" in upload
    assert "release-bundle/$SDIST" in upload
    assert "release-bundle/SHA256SUMS" in upload
    assert 'release-bundle/$(basename "$MANIFEST")' in upload
    assert "--clobber" not in upload
    assert jobs["publish"]["permissions"]["id-token"] == "write"


def test_dirty_source_and_wrong_tag_cannot_pass(monkeypatch, tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0rc2"\n')
    version_file = tmp_path / "src/cubedynamics/version.py"
    version_file.parent.mkdir(parents=True)
    version_file.write_text('__version__ = "0.1.0rc2"\n')
    monkeypatch.setattr(subprocess, "check_output", lambda command, **kwargs: " M README.md\n")
    with pytest.raises(RuntimeError, match="clean committed"):
        check(tmp_path, "refs/tags/v0.1.0rc2")
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda command, **kwargs: "" if command[1] == "status" else "test-sha\n",
    )
    with pytest.raises(RuntimeError, match="match the package version"):
        check(tmp_path, "refs/tags/v0.1.0")
    assert check(tmp_path, "refs/tags/v0.1.0rc2") == "0.1.0rc2"
    assert release_identity(tmp_path).version == "0.1.0rc2"


def test_identical_files_do_not_allow_a_different_release_commit(monkeypatch):
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: "new-sha\n")
    with pytest.raises(RuntimeError, match="Source commit changed"):
        check_commit({"git_sha": "tested-sha"})
