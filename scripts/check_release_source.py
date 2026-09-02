#!/usr/bin/env python3
"""Reject dirty release sources and mismatched publication tags (no writes)."""
import argparse
import os
from pathlib import Path
import subprocess

try:
    from release_metadata import release_identity
except ModuleNotFoundError:  # Imported as scripts.check_release_source in tests.
    from scripts.release_metadata import release_identity

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT, ref=None, *, require_tag=False):
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, text=True
    ).strip()
    if status:
        raise RuntimeError("Release gate requires a clean committed source snapshot")
    ref = os.environ.get("GITHUB_REF", "") if ref is None else ref
    identity = release_identity(root, ref=ref, require_tag=require_tag)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if identity.tag is not None:
        try:
            tagged = subprocess.check_output(
                ["git", "rev-parse", f"refs/tags/{identity.tag}^{{commit}}"],
                cwd=root,
                text=True,
                stderr=subprocess.STDOUT,
            ).strip()
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Release tag {identity.tag!r} does not exist in this checkout") from exc
        if tagged != head:
            raise RuntimeError(
                f"Release tag {identity.tag!r} resolves to {tagged}, not checked-out commit {head}"
            )
    print(head)
    return identity.version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    parser.add_argument("--require-tag", action="store_true")
    args = parser.parse_args()
    check(ref=args.ref, require_tag=args.require_tag)
