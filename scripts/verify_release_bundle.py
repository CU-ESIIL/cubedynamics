#!/usr/bin/env python3
"""Verify the exact same-run distribution bundle before publication."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

try:
    from release_metadata import ROOT, release_identity
except ModuleNotFoundError:  # Imported as scripts.verify_release_bundle in tests.
    from scripts.release_metadata import ROOT, release_identity


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checksums(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/]+)", line)
        if match is None or match.group(2) in records:
            raise RuntimeError("SHA256SUMS must contain unique '<sha256>  <filename>' records")
        records[match.group(2)] = match.group(1)
    return records


def verify_bundle(
    directory: Path,
    *,
    root: Path = ROOT,
    ref: str | None = None,
    require_tag: bool = False,
    commit: str | None = None,
) -> dict[str, object]:
    try:
        from run_release_gate import MANDATORY
    except ModuleNotFoundError:  # Imported as scripts.verify_release_bundle in tests.
        from scripts.run_release_gate import MANDATORY

    identity = release_identity(root, ref=ref, require_tag=require_tag, commit=commit)
    directory = Path(directory)
    manifest_name = Path(identity.candidate_manifest).name
    expected_names = {
        identity.wheel_filename,
        identity.sdist_filename,
        "SHA256SUMS",
        manifest_name,
    }
    actual_names = {path.name for path in directory.iterdir() if path.is_file()}
    if actual_names != expected_names:
        raise RuntimeError(
            f"Release bundle inventory differs: expected {sorted(expected_names)}, "
            f"found {sorted(actual_names)}"
        )

    sums = _checksums(directory / "SHA256SUMS")
    distribution_names = {identity.wheel_filename, identity.sdist_filename}
    if set(sums) != distribution_names:
        raise RuntimeError("SHA256SUMS must cover exactly the expected wheel and sdist")
    for name, expected in sums.items():
        if digest(directory / name) != expected:
            raise RuntimeError(f"Unverified release bytes: SHA256 differs for {name}")

    manifest = json.loads((directory / manifest_name).read_text(encoding="utf-8"))
    required_identity = {
        "package": identity.package,
        "version": identity.version,
        "tag": identity.tag,
        "expected_tag": identity.expected_tag,
        "commit_sha": identity.commit_sha,
    }
    for key, expected in required_identity.items():
        if manifest.get(key) != expected:
            raise RuntimeError(
                f"Release manifest {key!r} mismatch: {manifest.get(key)!r} != {expected!r}"
            )
    release_gate = manifest.get("release_gate", {})
    steps = release_gate.get("steps", {})
    if (
        release_gate.get("status") != "PASS"
        or not MANDATORY <= set(steps)
        or any(value != 0 for value in steps.values())
    ):
        raise RuntimeError("Release manifest does not record a complete passing gate")
    for kind, name in (("wheel", identity.wheel_filename), ("sdist", identity.sdist_filename)):
        record = manifest.get("artifacts", {}).get(kind, {})
        if record.get("filename") != name:
            raise RuntimeError(f"Release manifest has the wrong {kind} filename")
        if record.get("sha256") != sums[name] or record.get("bytes") != (directory / name).stat().st_size:
            raise RuntimeError(f"Release manifest does not bind the exact {kind} bytes")
    return {
        "status": "PASS",
        "identity": identity.as_dict(),
        "sha256": sums,
        "manifest": manifest_name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--require-tag", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_bundle(
        args.directory,
        root=args.root,
        ref=args.ref,
        require_tag=args.require_tag,
        commit=args.commit,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
