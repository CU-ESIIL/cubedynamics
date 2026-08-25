#!/usr/bin/env python3
"""Execute publication vignettes without modifying their source files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


ROOT = Path(__file__).resolve().parents[1]
VIGNETTE_DIR = ROOT / "docs" / "vignettes"
PLOT_MIME_TYPES = {"image/png", "image/svg+xml"}
INLINE_MATPLOTLIB_BACKEND = "module://matplotlib_inline.backend_inline"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "notebooks",
        nargs="*",
        type=Path,
        help="Specific notebook paths (default: every docs/vignettes/*.ipynb)",
    )
    parser.add_argument("--timeout", type=int, default=120, help="Seconds per cell")
    return parser.parse_args()


def execute(path: Path, *, timeout: int, runtime_dir: Path) -> None:
    notebook = nbformat.read(path, as_version=4)
    metadata = notebook.metadata.get("cubedynamics", {})
    if not metadata.get("supported_vignette", False):
        raise ValueError(f"{path} is not marked as a supported vignette")
    if metadata.get("network", True):
        raise ValueError(f"{path} does not declare network=false")

    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    try:
        client.execute()
    except CellExecutionError as exc:
        raise RuntimeError(f"vignette failed: {path.relative_to(ROOT)}") from exc

    if metadata.get("plot_required", False) and not _has_plot_output(notebook):
        raise RuntimeError(
            f"vignette did not emit a static plot: {path.relative_to(ROOT)}"
        )

    executed = runtime_dir / path.name
    nbformat.write(notebook, executed)
    print(f"PASS {path.relative_to(ROOT)}")


def _has_plot_output(notebook) -> bool:
    """Return whether an executed notebook emitted a portable static figure."""

    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            if PLOT_MIME_TYPES.intersection(data):
                return True
    return False


def _configure_execution_environment(runtime_dir: Path) -> None:
    """Configure kernels for portable, publication-ready notebook output."""

    # CI uses Agg for ordinary tests, but Agg does not publish figures into a
    # notebook's output cells. The vignette contract requires portable image
    # output, so the execution runner must deliberately override that default.
    os.environ["MPLBACKEND"] = INLINE_MATPLOTLIB_BACKEND
    os.environ.setdefault("MPLCONFIGDIR", str(runtime_dir / "matplotlib"))
    os.environ.setdefault("IPYTHONDIR", str(runtime_dir / "ipython"))
    os.environ.setdefault("JUPYTER_RUNTIME_DIR", str(runtime_dir / "jupyter"))


def main() -> int:
    args = parse_args()
    paths = args.notebooks or sorted(VIGNETTE_DIR.glob("*.ipynb"))
    if not paths:
        raise SystemExit("no vignette notebooks found")

    with tempfile.TemporaryDirectory(prefix="cubedynamics-vignettes-") as temp:
        runtime_dir = Path(temp)
        _configure_execution_environment(runtime_dir)
        for raw_path in paths:
            path = raw_path if raw_path.is_absolute() else ROOT / raw_path
            execute(path.resolve(), timeout=args.timeout, runtime_dir=runtime_dir)

    print(f"Executed {len(paths)} supported vignette(s) offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
