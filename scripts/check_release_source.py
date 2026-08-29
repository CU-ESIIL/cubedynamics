#!/usr/bin/env python3
"""Reject dirty release sources and mismatched publication tags (no writes)."""
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT, ref=None):
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, text=True
    ).strip()
    if status:
        raise RuntimeError("Release gate requires a clean committed source snapshot")
    version = re.search(r'^version = "([^"]+)"', (root / "pyproject.toml").read_text(), re.M).group(1)
    ref = os.environ.get("GITHUB_REF", "") if ref is None else ref
    if ref.startswith("refs/tags/") and ref != "refs/tags/v" + version:
        raise RuntimeError("Release tag must match the package version exactly")
    print(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip())
    return version


if __name__ == "__main__":
    check()
