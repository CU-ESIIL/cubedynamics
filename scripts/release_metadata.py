#!/usr/bin/env python3
"""Derive one reusable release identity from committed project metadata.

The tag never rewrites the package version.  It may only confirm that an
already-committed canonical version is the revision being verified.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "cubedynamics"
_CANONICAL_VERSION = re.compile(
    r"^(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*))+"
    r"(?:(?:a|b|rc)(?:0|[1-9]\d*))?"
    r"(?:\.post(?:0|[1-9]\d*))?"
    r"(?:\.dev(?:0|[1-9]\d*))?$"
)


@dataclass(frozen=True)
class ReleaseIdentity:
    package: str
    version: str
    tag: str | None
    expected_tag: str
    prerelease: bool
    wheel_filename: str
    sdist_filename: str
    candidate_manifest: str
    output_dir: str
    artifact_name: str
    commit_sha: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _matched_value(path: Path, pattern: str, label: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise RuntimeError(f"Could not read {label} from {path}")
    return match.group(1)


def project_version(root: Path = ROOT) -> str:
    """Return the canonical ``[project].version`` value."""
    path = Path(root) / "pyproject.toml"
    in_project = False
    for line in path.read_text(encoding="utf-8").splitlines():
        table = re.fullmatch(r"\s*\[([^]]+)]\s*(?:#.*)?", line)
        if table:
            in_project = table.group(1).strip() == "project"
            continue
        if in_project:
            match = re.fullmatch(r'\s*version\s*=\s*"([^"]+)"\s*(?:#.*)?', line)
            if match:
                return match.group(1)
    raise RuntimeError(f"Could not read project version from {path}")


def runtime_version(root: Path = ROOT) -> str:
    """Return the runtime mirror used by ``cubedynamics.__version__``."""

    return _matched_value(
        Path(root) / "src/cubedynamics/version.py",
        r'^__version__\s*=\s*"([^"]+)"',
        "runtime version",
    )


def tag_from_ref(ref: str | None) -> str | None:
    """Return a tag from a full GitHub ref; branches intentionally return none."""

    if not ref:
        return None
    if ref.startswith("refs/tags/"):
        tag = ref.removeprefix("refs/tags/")
        if not tag.startswith("v") or len(tag) == 1:
            raise RuntimeError("Release tags must use the form v<PEP-440-version>")
        return tag
    return None


def git_commit(root: Path = ROOT) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def release_identity(
    root: Path = ROOT,
    *,
    ref: str | None = None,
    require_tag: bool = False,
    commit: str | None = None,
) -> ReleaseIdentity:
    """Validate and describe the release selected by ``ref``."""

    root = Path(root)
    version = project_version(root)
    runtime = runtime_version(root)
    if runtime != version:
        raise RuntimeError(
            f"Runtime version {runtime!r} does not match project version {version!r}"
        )
    if _CANONICAL_VERSION.fullmatch(version) is None:
        raise RuntimeError(
            "Project version must use supported canonical PEP 440 spelling "
            f"(numeric release with optional a/b/rc, post, or dev suffix): {version!r}"
        )

    tag = tag_from_ref(ref)
    expected_tag = "v" + version
    if require_tag and tag is None:
        raise RuntimeError("Publication requires an existing v* tag, not a branch or pull-request ref")
    if tag is not None and tag != expected_tag:
        raise RuntimeError(
            f"Release tag {tag!r} does not match the package version {version!r}; "
            f"expected {expected_tag!r}"
        )

    commit = commit or git_commit(root)
    artifact_name = f"python-package-distributions-{version}"
    if commit:
        artifact_name += f"-{commit[:12]}"
    return ReleaseIdentity(
        package=PACKAGE,
        version=version,
        tag=tag,
        expected_tag=expected_tag,
        prerelease=bool(re.search(r"(?:a|b|rc)\d+|\.dev\d+$", version)),
        wheel_filename=f"{PACKAGE}-{version}-py3-none-any.whl",
        sdist_filename=f"{PACKAGE}-{version}.tar.gz",
        candidate_manifest=f"manifests/releases/v{version}-candidate.json",
        output_dir=f"artifacts/release-{version}",
        artifact_name=artifact_name,
        commit_sha=commit,
    )


def write_github_output(path: Path, identity: ReleaseIdentity) -> None:
    values = {
        "release_tag": identity.tag or "",
        "expected_tag": identity.expected_tag,
        "release_version": identity.version,
        "wheel_filename": identity.wheel_filename,
        "sdist_filename": identity.sdist_filename,
        "candidate_manifest": identity.candidate_manifest,
        "output_dir": identity.output_dir,
        "artifact_name": identity.artifact_name,
        "prerelease": str(identity.prerelease).lower(),
        "commit_sha": identity.commit_sha or "",
    }
    with Path(path).open("a", encoding="utf-8") as stream:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise RuntimeError(f"Unsafe multiline GitHub output: {key}")
            stream.write(f"{key}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    identity = release_identity(
        args.root, ref=args.ref, require_tag=args.require_tag, commit=args.commit
    )
    if args.github_output:
        write_github_output(args.github_output, identity)
    print(json.dumps(identity.as_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
