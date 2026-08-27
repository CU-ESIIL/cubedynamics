#!/usr/bin/env python3
"""Execute publication vignettes without modifying their source files."""

from __future__ import annotations

import argparse
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile

import nbformat
from PIL import Image
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


ROOT = Path(__file__).resolve().parents[1]
VIGNETTE_DIR = ROOT / "docs" / "vignettes"
DECISION_VIGNETTE_DIR = ROOT / "docs" / "decision_vignettes"
PLOT_MIME_TYPES = {"image/png", "image/svg+xml"}
INLINE_MATPLOTLIB_BACKEND = "module://matplotlib_inline.backend_inline"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "notebooks",
        nargs="*",
        type=Path,
        help=(
            "Specific notebook paths (default: supported notebooks in "
            "docs/vignettes and docs/decision_vignettes)"
        ),
    )
    parser.add_argument("--timeout", type=int, default=120, help="Seconds per cell")
    parser.add_argument("--output-dir", type=Path, help="Optionally retain executed notebooks and a run manifest")
    return parser.parse_args()


def execute(path: Path, *, timeout: int, runtime_dir: Path, output_dir: Path | None = None) -> dict:
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

    minimum_plots = int(metadata.get("minimum_plot_outputs", 1))
    plot_count = _plot_output_count(notebook)
    if metadata.get("plot_required", False) and plot_count < minimum_plots:
        raise RuntimeError(
            f"vignette emitted {plot_count} static plot(s), expected at least "
            f"{minimum_plots}: {path.relative_to(ROOT)}"
        )

    validate_visual_cells(notebook)
    destination = output_dir or runtime_dir
    destination.mkdir(parents=True, exist_ok=True)
    executed = destination / path.name
    nbformat.write(notebook, executed)
    result = {"notebook": str(path.relative_to(ROOT)), "plots": plot_count,
        "visual_steps": sum(bool(c.metadata.get("visual_example")) for c in notebook.cells)}
    print(f"PASS {path.relative_to(ROOT)} ({plot_count} plots)")
    return result


def validate_visual_cells(notebook) -> None:
    """Each opted-in analytical cell must publish its own nonempty result."""
    for cell in notebook.cells:
        contract = cell.metadata.get("visual_example")
        if not contract:
            continue
        payloads = [o.get("data", {}) for o in cell.get("outputs", [])]
        if contract["kind"] == "figure":
            images = [p["image/png"] for p in payloads if "image/png" in p]
            if not images:
                raise RuntimeError(f"Missing inline figure: {contract['key']}")
            for encoded in images:
                raw = base64.b64decode(encoded, validate=False)
                with Image.open(BytesIO(raw)) as image:
                    image.verify()
                with Image.open(BytesIO(raw)) as image:
                    if min(image.size) < 100 or all(low == high for low, high in image.convert("RGB").getextrema()):
                        raise RuntimeError(f"Empty inline figure: {contract['key']}")
        elif not any("<table" in p.get("text/html", "") for p in payloads):
            raise RuntimeError(f"Missing result table: {contract['key']}")


def _has_plot_output(notebook) -> bool:
    """Return whether an executed notebook emitted a portable static figure."""

    return _plot_output_count(notebook) > 0


def _plot_output_count(notebook) -> int:
    """Count outputs containing a portable static figure."""

    count = 0
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            if PLOT_MIME_TYPES.intersection(data):
                count += 1
    return count


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
    paths = args.notebooks or sorted(VIGNETTE_DIR.glob("*.ipynb")) + sorted(
        DECISION_VIGNETTE_DIR.glob("*.ipynb")
    )
    if not paths:
        raise SystemExit("no vignette notebooks found")

    with tempfile.TemporaryDirectory(prefix="cubedynamics-vignettes-") as temp:
        runtime_dir = Path(temp)
        _configure_execution_environment(runtime_dir)
        results = []
        for raw_path in paths:
            path = raw_path if raw_path.is_absolute() else ROOT / raw_path
            results.append(execute(path.resolve(), timeout=args.timeout, runtime_dir=runtime_dir, output_dir=args.output_dir))
        if args.output_dir:
            (args.output_dir / "execution.json").write_text(json.dumps(results, indent=2) + "\n")

    print(f"Executed {len(paths)} supported vignette(s) offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
