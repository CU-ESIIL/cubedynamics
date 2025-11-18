"""Ensure library code avoids eager compute or disk IO calls."""

from __future__ import annotations

from pathlib import Path

BANNED_SUBSTRINGS = [
    ".compute(",
    ".to_netcdf(",
    ".to_zarr(",
]


def test_no_eager_compute_or_io_in_library_code():
    root = Path("code/cubedynamics")
    py_files = list(root.rglob("*.py"))
    assert py_files, "No Python files found under code/cubedynamics"

    bad_hits: list[tuple[str, str]] = []
    for path in py_files:
        text = path.read_text()
        for token in BANNED_SUBSTRINGS:
            if token in text:
                bad_hits.append((str(path), token))

    assert not bad_hits, f"Found forbidden calls in library code: {bad_hits}"
